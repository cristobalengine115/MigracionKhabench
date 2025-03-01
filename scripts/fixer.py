import os
import pandas as pd
import requests
import json
import unicodedata
import gc
import traceback
# ✅ Configuración de OrientDB
ORIENTDB_HOST = "http://localhost:2480"
DB_NAME = "KhaBench"
USERNAME = "root"
PASSWORD = "rootpwd"
HEADERS = {"Accept": "application/json"}

# ✅ Ruta de datos
DATA_DIR = "/home/khabench/Desktop/test/Dataset/"
already_executed = False 


# ✅ Normalización de texto
def normalize_text(text):
    if isinstance(text, str):
        return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
    return text

def get_rid_map_limited(class_name, id_field, limit=50000):
    """Obtiene un diccionario de RIDs en lotes más pequeños para reducir el consumo de memoria."""
    print(f"📡 Obteniendo RIDs para {class_name} en lotes de {limit}...")

    rid_map = {}
    offset = 0

    while True:
        sql = f"SELECT {id_field}, @rid FROM {class_name} LIMIT {limit} SKIP {offset}"
        response = execute_query(sql)

        if not response or "result" not in response:
            print(f"⚠️ No se pudieron obtener más RIDs para {class_name}.")
            break

        # 🔥 Convertir las claves a str y eliminar espacios en blanco
        batch = {str(record[id_field]).strip(): record["@rid"] for record in response["result"]}
        rid_map.update(batch)

        if len(batch) < limit:
            break  # No hay más registros

        offset += limit

        print(f"🔍 {class_name} RIDs obtenidos (ejemplo): {list(rid_map.items())[:10]}")

        del response, batch
        gc.collect()

    return rid_map


# 📌 **Inserción en Lotes con COMMIT y ROLLBACK**
def insert_batch(class_name, records, batch_size=5000):
    """Inserta datos en lotes pequeños para evitar consumo excesivo de memoria."""

    if not records:
        return

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        sql_statements = ["BEGIN"]  
        sql_statements += [f"INSERT INTO {class_name} CONTENT {json.dumps(record)}" for record in batch]
        sql_statements.append("COMMIT")  

        batch_query = ";\n".join(sql_statements)
        response = execute_query(batch_query, transaction=True)

        if response and "errors" in response:
            execute_query("ROLLBACK;", transaction=True)

        # 🧹 **Liberamos memoria tras cada lote**
        del batch, sql_statements, batch_query
        gc.collect()


def insert_edge_batch(edge_class, file_name, from_rids, to_rids, from_field, to_field, batch_size=5000):
    global already_executed

    if already_executed:
        print("⚠️ `insert_edge_batch()` ya se ejecutó una vez. Saliendo...")
        return  # 🔥 Evita múltiples ejecuciones

    already_executed = True  # 🔥 Marcamos la función como ejecutada

    file_path = os.path.join(DATA_DIR, "SocialNetwork", file_name)
    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando {edge_class}...")
        return

    total_inserted = 0  # 🔥 Contador de inserciones

    chunks = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip", chunksize=batch_size)

    for i, df in enumerate(chunks):
        if total_inserted >= 187810:
            print(f"✅ Se alcanzó el límite de registros ({total_inserted}). Carga finalizada.")
            return  # 🔥 Sale completamente de la función

        print(f"🔍 Procesando lote {i+1} con {len(df)} registros...")

        # ✅ **Renombrar columnas si es necesario**
        if "from" in df.columns and "to" in df.columns:
            df.rename(columns={"from": "FROM_ID", "to": "TO_ID"}, inplace=True)

        batch_queries = ["BEGIN"]  # 🔥 Reiniciar `batch_queries` en cada lote
        inserted_in_batch = 0  # 🔥 Contador de registros en este lote

        for _, record in df.iterrows():
            if total_inserted >= 187810:
                print(f"⏹️ Detenido dentro del lote {i+1}. Límite alcanzado.")
                break  # 🔥 DETENER INSERCIONES EN ESTE LOTE

            from_id = str(record["FROM_ID"]) if "FROM_ID" in df.columns and pd.notna(record["FROM_ID"]) else None
            to_id = str(record["TO_ID"]) if "TO_ID" in df.columns and pd.notna(record["TO_ID"]) else None
            creation_date = record["creationDate"] if "creationDate" in df.columns else None

            if from_id is None or to_id is None:
                continue
            if from_id not in from_rids or to_id not in to_rids:
                continue

            from_rid = from_rids[from_id]
            to_rid = to_rids[to_id]

            query = f"CREATE EDGE {edge_class} FROM {from_rid} TO {to_rid} SET creationDate = '{creation_date}'"
            batch_queries.append(query)

            total_inserted += 1
            inserted_in_batch += 1

        if total_inserted >= 187810:
            print(f"⏹️ Límite alcanzado antes de ejecutar `BATCH SCRIPT`. Deteniendo carga.")
            return

        batch_queries.append("COMMIT")  

        if inserted_in_batch > 0:
            batch_query = ";\n".join(batch_queries)

            print(f"🔍 Ejecutando `BATCH SCRIPT` con {inserted_in_batch} inserciones...")
            response = execute_query(batch_query, transaction=True)

            if response and "errors" in response:
                print(f"❌ Error en la inserción, ejecutando ROLLBACK...")
                execute_query("ROLLBACK;", transaction=True)
            else:
                print(f"✅ Lote {i+1} insertado correctamente en {edge_class} con {inserted_in_batch} registros.")

        del df, batch_queries
        gc.collect()

    print(f"🎉 Carga finalizada. Total de registros insertados: {total_inserted}")


def execute_query(sql, transaction=False):
    url = f"{ORIENTDB_HOST}/batch/{DB_NAME}"
    data = {
        "transaction": transaction,
        "operations": [{"type": "cmd", "language": "sql", "command": sql}]
    }
    try:
        response = requests.post(url, auth=(USERNAME, PASSWORD), json=data, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error en query ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"❌ Excepción en query: {e}")
        return None

# 📌 **Carga de Datos para `Customer` y sus Fragmentos con Transacción**
def load_customer_data(entity_name, file_name):
    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando {entity_name}...")
        return

    print(f"📂 Cargando {file_name} en {entity_name}...")

    df = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

    # ✅ Renombrar columnas para coincidir con el esquema
    df.rename(columns={
        "ID": "CUSTOMER_ID",
        "FIRSTNAME": "FIRST_NAME",
        "LASTNAME": "LAST_NAME",
        "GENDER": "GENDER",
        "BIRTHDAY": "BIRTHDAY",
        "CREATION_DATE": "CREATE_DATE",
        "LOCATION_IP": "LOCATION_IP",
        "BROWSER_USED": "BROWSER_USED",
        "PLACE": "PLACE"
    }, inplace=True)

    # ✅ Convertir fechas al formato correcto
    df["BIRTHDAY"] = pd.to_datetime(df["BIRTHDAY"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    df["CREATE_DATE"] = pd.to_datetime(df["CREATE_DATE"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    df["PLACE"] = df["PLACE"].astype(int)

    

    print(f"📌 Insertando {len(df)} registros en {entity_name} dentro de una transacción...")
    insert_batch(entity_name, df.to_dict(orient="records"))
    print(f"✅ Carga de {entity_name} completada.")

def load_person_data(entity_name, file_name):
    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando {entity_name}...")
        return

    print(f"📂 Cargando {file_name} en {entity_name}...")

    df = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

    # ✅ Renombrar columnas para coincidir con el esquema
    df.rename(columns={
        "ID": "PERSON_ID",
        "FIRSTNAME": "FIRST_NAME",
        "LASTNAME": "LAST_NAME",
        "GENDER": "GENDER",
        "BIRTHDAY": "BIRTHDAY",
        "CREATION_DATE": "CREATE_DATE",
        "LOCATION_IP": "LOCATION_IP",
        "BROWSER_USED": "BROWSER_USED",
        "PLACE": "PLACE"
    }, inplace=True)

    # ✅ Convertir fechas al formato correcto
    df["BIRTHDAY"] = pd.to_datetime(df["BIRTHDAY"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    df["CREATE_DATE"] = pd.to_datetime(df["CREATE_DATE"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    df["PLACE"] = df["PLACE"].astype(int)

    

    print(f"📌 Insertando {len(df)} registros en {entity_name}...")
    insert_batch(entity_name, df.to_dict(orient="records"))
    print(f"✅ Carga de {entity_name} completada.")




def load_post_data(entity_name, file_name):
    file_path = os.path.join(DATA_DIR, "SocialNetwork", file_name)

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando {entity_name}...")
        return

    print(f"📂 Cargando {file_name} en {entity_name} en lotes de 500,000...")

    batch_size = 100000  # 🔥 Leer en partes para evitar memoria alta
    chunks = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip", chunksize=batch_size)

    for i, df in enumerate(chunks):
        print(f"🔄 Procesando lote {i+1} de {entity_name} con {len(df)} registros...")

        # ✅ Renombrar columnas para coincidir con el esquema en OrientDB
        df.rename(columns={
            "POST_ID": "POST_ID",
            "CONTENT": "CONTENT",
            "IMAGE_FILE": "IMAGE_FILE",
            "LOCATION_IP": "LOCATION_IP",
            "BROWSER_USED": "BROWSER_USED",
            "CREATE_DATE": "CREATE_DATE",
            "LENGTH": "LENGTH"
        }, inplace=True)

        # ✅ Convertir fechas y valores
        df["CREATE_DATE"] = pd.to_datetime(df["CREATE_DATE"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
        df["LENGTH"] = df["LENGTH"].astype(int)

        print(f"📌 Insertando {len(df)} registros en {entity_name}...")
        insert_batch(entity_name, df.to_dict(orient="records"), batch_size=1000)

    print(f"✅ Carga de {entity_name} completada.")

# 📌 **Carga de `Tag`**
def load_tag(entity_name,file_name):
    file_path = os.path.join(DATA_DIR, "SocialNetwork", file_name)  

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando `Tag`...")
        return

    print(f"📂 Cargando {file_path} en `Tag`...")

    df = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

    # ✅ Renombrar columnas para coincidir con el esquema
    df.rename(columns={"ID": "TAG_ID", "TITLE": "TITLE"}, inplace=True)


    print(f"📌 Insertando {len(df)} registros en `Tag`...")
    insert_batch("Tag", df.to_dict(orient="records"))
    print(f"✅ Carga de `Tag` completada.")

def load_post_has_creator():
    file_name = "post_hasCreator_person_0_0.csv"
    file_path = os.path.join(DATA_DIR, "SocialNetwork", file_name)

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando POST_HAS_CREATOR_PERSON...")
        return

    print(f"📂 Cargando {file_path} en POST_HAS_CREATOR_PERSON...")

    batch_size = 50000  # 🔥 Procesamos en lotes de 50,000 para evitar sobrecarga
    chunks = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip", chunksize=batch_size)

    for i, df in enumerate(chunks):
        print(f"🔄 Procesando lote {i+1} con {len(df)} relaciones...")

        df.rename(columns={"POST_ID": "FROM_ID", "PERSON_ID": "TO_ID"}, inplace=True)

        # 🔍 **DEBUG: Imprimir las primeras filas del CSV**
        print("🔍 Primeras filas del CSV:")
        print(df.head())

        # 🔥 Obtener SOLO los RIDs del lote actual
        post_rids = get_rid_map_limited("Post", "POST_ID", limit=batch_size)
        person_rids = get_rid_map_limited("Person", "PERSON_ID", limit=batch_size)

        # 🔍 **DEBUG: Mostrar claves obtenidas**
        print(f"🔍 Claves en post_rids: {list(post_rids.keys())[:10]}")
        print(f"🔍 Claves en person_rids: {list(person_rids.keys())[:10]}")

        insert_edge_batch("POST_HAS_CREATOR_PERSON", file_name, post_rids, person_rids, "FROM_ID", "TO_ID", batch_size=2000)

        # 🧹 **Liberamos memoria tras cada lote**
        del df, post_rids, person_rids
        gc.collect()

    print(f"✅ Carga de POST_HAS_CREATOR_PERSON completada.")


def load_customer_knows_person():
    print("🔍 `load_customer_knows_person()` fue llamada desde:")
    traceback.print_stack()  # 🔥 Esto imprimirá dónde se está llamando la función
    file_name = "person_knows_person_0_0.csv"
    file_path = os.path.join(DATA_DIR, "SocialNetwork", file_name)

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando Customer_Knows_Person...")
        return

    print(f"📂 Cargando {file_path} en Customer_Knows_Person...")

    batch_size = 10000  
    chunks = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip", chunksize=batch_size)

    for i, df in enumerate(chunks):
        print(f"🔄 Procesando lote {i+1} con {len(df)} relaciones...")

        # ✅ **Corregir nombres de columnas**
        df.rename(columns={"from": "FROM_ID", "to": "TO_ID"}, inplace=True)

        # ✅ **Depuración: Verificar los primeros valores**
        print(f"🔍 Primeras filas del CSV:\n{df.head()}")

        # ✅ **Obtener SOLO los RIDs necesarios**
        customer_rids = get_rid_map_limited("Customer", "CUSTOMER_ID", limit=batch_size)
        person_rids = get_rid_map_limited("Person", "PERSON_ID", limit=batch_size)

        # ✅ **Depuración: Revisar si los RIDs se están obteniendo correctamente**
        print(f"🔍 Claves en customer_rids (ejemplo): {list(customer_rids.keys())[:10]}")
        print(f"🔍 Claves en person_rids (ejemplo): {list(person_rids.keys())[:10]}")

        # ✅ **Insertar las relaciones**
        insert_edge_batch("CUSTOMER_KNOWS_PERSON", file_name, customer_rids, person_rids, "FROM_ID", "TO_ID", batch_size=10000)

        # 🧹 **Liberar memoria**
        del df, customer_rids, person_rids
        gc.collect()

    print(f"✅ Carga de Customer_Knows_Person completada.")

def load_post_has_tag():
    file_name = "post_hasTag_tag_0_0.csv"
    file_path = os.path.join(DATA_DIR, "SocialNetwork", file_name)

    if not os.path.exists(file_path):
        return

    batch_size = 100000  
    chunks = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip", chunksize=batch_size)

    for df in chunks:
        df.rename(columns={"POST_ID": "POST_ID", "TAG_ID": "TAG_ID"}, inplace=True)

        post_rids = get_rid_map_limited("Post", "POST_ID", limit=200000)
        tag_rids = get_rid_map_limited("Tag", "TAG_ID", limit=200000)

        insert_edge_batch("POST_HAS_TAG", file_name, post_rids, tag_rids, "POST_ID", "TAG_ID", batch_size=1000)

        del df, post_rids, tag_rids
        gc.collect()


def load_person_has_interest_tag():
    file_name = "person_hasInterest_tag_0_0.csv"
    file_path = os.path.join(DATA_DIR, "SocialNetwork", file_name)

    if not os.path.exists(file_path):
        return

    batch_size = 100000  
    chunks = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip", chunksize=batch_size)

    for df in chunks:
        df.rename(columns={"PERSON_ID": "PERSON_ID", "TAG_ID": "TAG_ID"}, inplace=True)

        person_rids = get_rid_map_limited("Person", "PERSON_ID", limit=200000)
        tag_rids = get_rid_map_limited("Tag", "TAG_ID", limit=200000)

        insert_edge_batch("PERSON_HAS_INTEREST_TAG", file_name, person_rids, tag_rids, "PERSON_ID", "TAG_ID", batch_size=1000)

        del df, person_rids, tag_rids
        gc.collect()




load_customer_data("Customer", "Customer/person_0_0.csv")
load_customer_data("Customer_North", "Customer/person_0_0_north.csv")
load_customer_data("Customer_Center", "Customer/person_0_0_center.csv")
load_customer_data("Customer_South", "Customer/person_0_0_south.csv")

load_person_data("Person", "Customer/person_0_0.csv")
load_person_data("Person_North", "Customer/person_0_0_north.csv")
load_person_data("Person_Center", "Customer/person_0_0_center.csv")
load_person_data("Person_South", "Customer/person_0_0_south.csv")

load_customer_knows_person()

# load_post_data("Post", "post_0_0.csv")
# load_post_data("Post_Short", "post_0_0_short.csv")
# load_post_data("Post_Medium", "post_0_0_medium.csv")
# load_post_data("Post_Long", "post_0_0_long.csv")

# load_post_has_creator()

# load_tag("TAG", "tag.csv")

# load_post_has_tag()
# load_person_has_interest_tag()


print("🎉 Carga de entidades y fragmentos completada con COMMIT y ROLLBACK.")