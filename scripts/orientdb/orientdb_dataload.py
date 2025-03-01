import os
import pandas as pd
import requests
import json
import unicodedata
import gc


# ✅ Configuración de OrientDB
ORIENTDB_HOST = "http://localhost:2480"
DB_NAME = "KhaBench"
USERNAME = "root"
PASSWORD = "rootpwd"
HEADERS = {"Accept": "application/json"}

# ✅ Ruta de datos
DATA_DIR = "/home/khabench/Desktop/test/Dataset/"

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

def load_vendor_data(entity_name, file_name):
    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando {entity_name}...")
        return

    print(f"📂 Cargando {file_path} en {entity_name}...")

    # 📌 Leer CSV con separador de coma
    df = pd.read_csv(file_path, sep=",", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

    # 📌 Verificar que contiene las columnas necesarias
    expected_columns = {"VENDOR_ID", "COMPANY", "COUNTRY", "INDUSTRY"}
    missing_columns = expected_columns - set(df.columns)
    if missing_columns:
        print(f"❌ ERROR: Faltan las columnas {missing_columns} en el CSV de {entity_name}.")
        return

    # ✅ Convertir tipos de datos
    df["VENDOR_ID"] = df["VENDOR_ID"].astype(str).str.strip()
    df["COMPANY"] = df["COMPANY"].astype(str).str.strip()
    df["COUNTRY"] = df["COUNTRY"].astype(str).str.strip()
    df["INDUSTRY"] = df["INDUSTRY"].astype(str).str.strip()

    # 📌 Imprimir un ejemplo de los datos antes de insertarlos
    print(f"🔍 Primeras filas de {entity_name}:\n{df.head()}")

    print(f"📌 Insertando {len(df)} registros en {entity_name}...")
    insert_batch(entity_name, df.to_dict(orient="records"))
    print(f"✅ Carga de {entity_name} completada.")


def load_product_data(entity_name, file_name):
    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando {entity_name}...")
        return

    print(f"📂 Cargando {file_path} en {entity_name}...")

    df = pd.read_csv(file_path, sep=",", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

    # ✅ Renombrar columnas
    df.rename(columns={
        "PRODUCT_ID": "PRODUCT_ID",
        "TITLE": "TITLE",
        "PRICE": "PRICE",
        "IMG_URL": "IMG_URL",
        "SKU": "SKU",
        "VENDOR_ID": "VENDOR_ID"
    }, inplace=True)

    # ✅ Convertir precio a float
    df["PRICE"] = df["PRICE"].astype(float)

    # 📡 Obtener mapeo de `VENDOR_ID` a `@rid`
    print("📡 Obteniendo RIDs de Vendor...")
    vendor_rid_map = {}
    response = execute_query("SELECT VENDOR_ID, @rid FROM Vendor")

    if response and "result" in response:
        vendor_rid_map = {str(record["VENDOR_ID"]): record["@rid"] for record in response["result"]}

    print(f"🔍 Mapeo de Vendor cargado: {list(vendor_rid_map.items())[:10]}")

    # ✅ Reemplazar `VENDOR_ID` con su `@rid`
    df["VENDOR_ID"] = df["VENDOR_ID"].map(vendor_rid_map)

    # 🔥 Filtrar productos con `VENDOR_ID` no encontrado en la base de datos
    df.dropna(subset=["VENDOR_ID"], inplace=True)

    print(f"📌 Insertando {len(df)} registros en {entity_name} dentro de una transacción...")
    insert_batch(entity_name, df.to_dict(orient="records"))
    print(f"✅ Carga de {entity_name} completada.")

def load_feedback_data():
    file_name = "Feedback/Feedback.csv"
    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.exists(file_path):
        print(f"⚠️ Archivo {file_path} no encontrado. Saltando Feedback...")
        return

    print(f"📂 Cargando {file_path} en Feedback...")

    batch_size = 5000
    chunks = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip", chunksize=batch_size)

    for i, df in enumerate(chunks):
        print(f"🔄 Procesando lote {i+1} con {len(df)} registros...")

        # Obtener IDs únicos de Customer y Product en el lote
        customer_ids = df["CUSTOMER_ID"].dropna().astype(str).str.strip().unique().tolist()
        product_ids = df["PRODUCT_ID"].dropna().astype(str).str.strip().unique().tolist()

        print(f"🔍 IDs de Customer en este lote: {customer_ids[:10]}")
        print(f"🔍 IDs de Product en este lote: {product_ids[:10]}")

        customer_rids = {}
        product_rids = {}

        # ⚠️ Evitar consultas vacías
        if customer_ids:
            customer_ids_str = ", ".join(f"'{cid}'" for cid in customer_ids)
            customer_rids_query = f"SELECT CUSTOMER_ID, @rid FROM Customer WHERE CUSTOMER_ID IN [{customer_ids_str}]"
            customer_rids_response = execute_query(customer_rids_query)

            if customer_rids_response and "result" in customer_rids_response:
                customer_rids = {record["CUSTOMER_ID"]: record["@rid"] for record in customer_rids_response["result"]}

        if product_ids:
            product_ids_str = ", ".join(f"'{pid}'" for pid in product_ids)
            product_rids_query = f"SELECT PRODUCT_ID, @rid FROM Product WHERE PRODUCT_ID IN [{product_ids_str}]"
            product_rids_response = execute_query(product_rids_query)

            if product_rids_response and "result" in product_rids_response:
                product_rids = {record["PRODUCT_ID"]: record["@rid"] for record in product_rids_response["result"]}

        print(f"🔍 Claves en customer_rids (ejemplo): {list(customer_rids.keys())[:5]}")
        print(f"🔍 Claves en product_rids (ejemplo): {list(product_rids.keys())[:5]}")

        batch_records = []
        for _, row in df.iterrows():
            product_id = str(row["PRODUCT_ID"]).strip()
            customer_id = str(row["CUSTOMER_ID"]).strip()
            rate = row["RATE"]
            review = row["REVIEW"]

            if product_id in product_rids and customer_id in customer_rids:
                batch_records.append({
                    "PRODUCT_ID": product_rids[product_id],
                    "CUSTOMER_ID": customer_rids[customer_id],
                    "RATE": float(rate),
                    "REVIEW": review
                })

        print(f"📌 Insertando {len(batch_records)} registros en Feedback...")
        insert_batch("Feedback", batch_records, batch_size=batch_size)

    print(f"✅ Carga de Feedback completada.")

load_customer_data("Customer", "Customer/person_0_0.csv")
load_customer_data("Customer_North", "Customer/person_0_0_north.csv")
load_customer_data("Customer_Center", "Customer/person_0_0_center.csv")
load_customer_data("Customer_South", "Customer/person_0_0_south.csv")

load_person_data("Person", "Customer/person_0_0.csv")
load_person_data("Person_North", "Customer/person_0_0_north.csv")
load_person_data("Person_Center", "Customer/person_0_0_center.csv")
load_person_data("Person_South", "Customer/person_0_0_south.csv")


# 📌 Cargar Vendor
load_vendor_data("Vendor", "Vendor/Vendor.csv")

# 📌 Cargar Product y sus fragmentos
load_product_data("Product", "Product/Product.csv")
load_product_data("Product_Cheap", "Product/Product_Cheap.csv")
load_product_data("Product_Expensive", "Product/Product_Expensive.csv")

load_feedback_data()