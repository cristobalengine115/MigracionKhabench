import pandas as pd
from arango import ArangoClient
import os
import json
import xml.etree.ElementTree as ET
import numpy as np


# ✅ Conexión con ArangoDB
client = ArangoClient(hosts="http://127.0.0.1:7101")
db = client.db("KhaBench", username="root", password="")
data_dir = "/home/khabench/Desktop/test/data/Global"

# 📌 Función para vaciar una colección
def clear_collection(collection_name):
    collection = db.collection(collection_name)
    if collection.count() > 0:
        collection.truncate()
        print(f"✅ Eliminados todos los datos de {collection_name}")
    else:
        print(f"⚠️ La colección {collection_name} ya está vacía")

# 📌 Función para insertar datos en ArangoDB
def insert_data(df, collection_name):
    if df.empty:
        print(f"⚠️ No hay datos para insertar en {collection_name}.")
        return
    
    collection = db.collection(collection_name)
    batch_size = 1000

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size].to_dict(orient="records")
        try:
            collection.insert_many(batch, overwrite=False)  # No sobrescribir para evitar pérdida de datos
            print(f"✅ Insertados {len(batch)} documentos en {collection_name}")
        except Exception as e:
            print(f"❌ Error en inserción: {e}")
            print(f"🔍 Documentos problemáticos: {batch[:3]}")

def insert_json(data, collection_name):
    try:
        collection = db.collection(collection_name)
        batch_size = 1000
        inserted_count = 0

        # Imprimir un ejemplo de documento antes de empezar la inserción
        if data:
            print(f"🔍 Ejemplo de documento a insertar en {collection_name}: {data[0]}")

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]

            # Confirmar el tamaño del lote
            print(f"🔍 Insertando un lote de {len(batch)} documentos en {collection_name}...")

            try:
                collection.insert_many(batch, overwrite=True)
                inserted_count += len(batch)
                print(f"✅ Insertados {len(batch)} documentos en {collection_name}")
            except Exception as e:
                print(f"❌ Error al insertar el lote en {collection_name}: {e}")
                # Opcional: imprimir algunos documentos problemáticos para análisis
                print(f"🔍 Documentos problemáticos: {batch[:5]}")

        print(f"🎉 Carga de {collection_name} completada. Total insertados: {inserted_count}")

    except Exception as e:
        print(f"❌ Error en insert_json para {collection_name}: {e}")

# 📌 Función para cargar datos en Invoice
def validate_invoice(invoice):
    try:
        invoice_id = invoice.find("OrderId").text
        order_id = invoice.find("OrderId").text
        issued_date = invoice.find("OrderDate").text
        total_amount = invoice.find("TotalPrice").text

        if not all([invoice_id, order_id, issued_date, total_amount]):
            return None

        # Asegurar que `TotalAmount` es numérico
        total_amount = float(total_amount)

        return {
            "_key": invoice_id,
            "InvoiceId": invoice_id,
            "OrderId": order_id,
            "IssuedDate": issued_date,
            "TotalAmount": total_amount
        }
    except (AttributeError, ValueError):
        return None

def insert_documents(collection_name, documents, batch_size=1000):
    collection = db.collection(collection_name)
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        try:
            collection.insert_many(batch, overwrite=False)
            print(f"✅ Insertados {len(batch)} documentos en {collection_name}")
        except Exception as e:
            print(f"❌ Error en inserción: {e}")
            print(f"🔍 Documentos problemáticos: {batch[:3]}")

def load_edge(file_name, edge_name, from_prefix, to_prefix, drop_columns=[]):
    file_path = os.path.join(data_dir, file_name)
    print(f"📂 Cargando {file_path} en {edge_name}")
    df = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")
    
    if drop_columns:
        df = df.drop(columns=drop_columns, errors="ignore")  # Eliminar columnas extra

    if len(df.columns) != 2:
        print(f"❌ Error: Se detectaron {len(df.columns)} columnas en lugar de 2 en {edge_name}.")
        return

    df.columns = ["_from", "_to"]
    df["_from"] = from_prefix + df["_from"]
    df["_to"] = to_prefix + df["_to"]
    insert_data(df, edge_name)

# 📌 Función para cargar datos en Customer
def load_customer():
    file_path = os.path.join(data_dir, "person_0_0.csv")
    print(f"📂 Cargando {file_path} en Customer")

    df = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

    # 🔍 Asegurar que place sea numérico
    df["place"] = pd.to_numeric(df["place"], errors="coerce")

    # 🔹 Filtrar datos por fragmento
    df_north = df[df["place"].between(0, 500)]
    df_center = df[df["place"].between(501, 1000)]
    df_south = df[df["place"] > 1000]

    # ✅ Insertar datos en cada fragmento
    insert_data(df_north, "Customer_North")
    insert_data(df_center, "Customer_Center")
    insert_data(df_south, "Customer_South")

    # ✅ Insertar datos en la colección global
    insert_data(df, "Customer")

# 📌 Función para cargar datos en Person
def load_person():
    file_path = os.path.join(data_dir, "person_0_0.csv")
    print(f"📂 Cargando {file_path} en Person")

    df = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")
    insert_data(df, "Person")

# 📌 Función para cargar datos en Feedback
def load_feedback():
    file_path = os.path.join(data_dir, "Feedback.csv")
    print(f"📂 Cargando {file_path} en Feedback")
    df = pd.read_csv(file_path, sep="|", dtype=str, quotechar="'", skipinitialspace=True, on_bad_lines="skip")
    # 🔄 Renombrar columnas
    df.columns = ["productId", "personId", "review"]
    # ✅ Crear un _key único combinando productId y personId
    df["_key"] = df["productId"] + "_" + df["personId"]
    # ✅ Limpiar la columna review
    df["review"] = df["review"].str.strip("'")
    # ✅ Reorganizar las columnas para que _key vaya primero
    df = df[["_key", "productId", "personId", "review"]]
    # 🔄 Insertar datos en ArangoDB
    insert_data(df, "Feedback")


def load_invoice():
    file_path = os.path.join(data_dir, "Invoice.xml")
    print(f"📂 Cargando {file_path} en Invoice...")

    if not os.path.exists(file_path):
        print(f"❌ Error: Archivo {file_path} no encontrado.")
        return

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        invoices = []
        for invoice in root.findall("Invoice"):
            invoice_data = validate_invoice(invoice)
            if invoice_data:
                invoices.append(invoice_data)

        print(f"📊 Total de documentos validados: {len(invoices)}")
        insert_documents("Invoice", invoices)

    except Exception as e:
        print(f"❌ Error procesando Invoice.xml: {e}")


# 📌 Función para cargar datos en Tag
def load_tag():
    file_path = os.path.join(data_dir, "Tag.csv")
    print(f"📂 Cargando {file_path} en Tag")

    if not os.path.exists(file_path):
        print(f"❌ Error: Archivo {file_path} no encontrado.")
        return

    try:
        # 🔹 Cargar el archivo CSV
        df = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

        # 🔍 Validar columnas esperadas
        if len(df.columns) != 2:
            print(f"❌ Error: Se detectaron {len(df.columns)} columnas en lugar de 2.")
            return

        # 🔹 Renombrar columnas correctamente
        df.columns = ["_key", "title"]  # `_key` para que ArangoDB lo use como identificador único

        # ✅ Insertar datos en ArangoDB
        insert_data(df, "Tag")

    except Exception as e:
        print(f"❌ Error procesando Tag.csv: {e}")

# 📌 Función para cargar datos en Vendor
def load_vendor():
    file_path = os.path.join(data_dir, "Vendor.csv")
    print(f"📂 Cargando {file_path} en Vendor")

    # 📌 Intentar detectar el separador automáticamente
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline()
        detected_sep = "|" if "|" in first_line else ","

    df = pd.read_csv(
        file_path, 
        sep=detected_sep, 
        dtype=str, 
        quotechar='"', 
        skipinitialspace=True, 
        on_bad_lines="skip"
    )

    # 🔍 Validar columnas
    if len(df.columns) != 3:
        print(f"❌ Error: Se detectaron {len(df.columns)} columnas en lugar de 3.")
        return

    df.columns = ["id", "country", "industry"]

    # ✅ Asignar `_key` a `id`
    df["_key"] = df["id"]
    # ✅ Remover la columna `id` (ya que `_key` la sustituye)
    df.drop(columns=["id"], inplace=True)

    # 🔍 Mostrar estructura final antes de insertar
    print(f"📌 Primeros registros después de la transformación:")
    print(df.head())

    # ✅ Insertar en ArangoDB
    insert_data(df, "Vendor")



# 📌 Función para cargar datos en Orders
def load_orders():
    file_path = os.path.join(data_dir, "Order.json")
    print(f"📂 Cargando {file_path} en las colecciones de órdenes")

    # Leer el archivo JSON completo con json.load
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error al cargar el archivo JSON: {e}")
        return

    print(f"🔍 Total de registros cargados: {len(data)}")
    if len(data) > 0:
        print(f"🔍 Ejemplo de registro cargado: {data[0]}")
    
    # Asegurar que _key sea igual a OrderId y validar los datos
    valid_data = []
    for order in data:
        # Asignar _key desde OrderId
        if "OrderId" in order:
            order["_key"] = order["OrderId"]
        else:
            print("❌ Registro sin OrderId detectado, omitiendo:", order)
            continue

        # Validar campos requeridos
        required_fields = ["PersonId", "OrderDate", "TotalPrice", "Orderline"]
        missing_fields = [field for field in required_fields if field not in order]
        if missing_fields:
            print(f"❌ Registro con campos faltantes ({missing_fields}), omitiendo:", order)
            continue

        # Validar tipos
        if not isinstance(order["TotalPrice"], (int, float)):
            print("❌ TotalPrice no es numérico, omitiendo:", order)
            continue

        if not isinstance(order["OrderDate"], str):
            print("❌ OrderDate no es una cadena, omitiendo:", order)
            continue

        valid_data.append(order)

    print(f"🔍 Total de registros válidos después de la validación: {len(valid_data)}")
    if len(valid_data) > 0:
        print(f"🔍 Ejemplo de registro válido: {valid_data[0]}")

    # Definir fecha de la pandemia
    pandemic_date = "2020-03-11"

    # Fragmentar los datos según la fecha
    data_pre_pandemic = [order for order in valid_data if order["OrderDate"] < pandemic_date]
    data_post_pandemic = [order for order in valid_data if order["OrderDate"] >= pandemic_date]

    print(f"🔍 Total registros pre-pandemia: {len(data_pre_pandemic)}")
    if len(data_pre_pandemic) > 0:
        print(f"🔍 Ejemplo de registro pre-pandemia: {data_pre_pandemic[0]}")

    print(f"🔍 Total registros post-pandemia: {len(data_post_pandemic)}")
    if len(data_post_pandemic) > 0:
        print(f"🔍 Ejemplo de registro post-pandemia: {data_post_pandemic[0]}")

    # Inserción homogénea para las tres colecciones
    try:
        print("⚙️ Insertando en Order")
        insert_json(valid_data, "Order")
        print("✅ Insertados en Order")
    except Exception as e:
        print(f"❌ Error al insertar en Order: {e}")

    try:
        insert_json(data_pre_pandemic, "Order_Pre_Pandemic")
        print(f"✅ Registros pre-pandemia insertados: {len(data_pre_pandemic)}")
    except Exception as e:
        print(f"❌ Error al insertar en Order_Pre_Pandemic: {e}")

    try:
        insert_json(data_post_pandemic, "Order_Post_Pandemic")
        print(f"✅ Registros post-pandemia insertados: {len(data_post_pandemic)}")
    except Exception as e:
        print(f"❌ Error al insertar en Order_Post_Pandemic: {e}")



def load_posts():
    file_path = os.path.join(data_dir, "post_0_0.csv")
    print(f"📂 Cargando {file_path} en las colecciones de Post")

    # Leer el archivo de datos
    df = pd.read_csv(file_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

    # Renombrar columnas para alinearlas con el esquema esperado
    df.columns = ["_key", "imageFile", "createDate", "location", "browserUsed", "language", "content", "length"]

    # Asegurar que `_key` es una cadena
    df["_key"] = df["_key"].astype(str)

    # Convertir `length` a tipo numérico y manejar valores no válidos
    df["length"] = pd.to_numeric(df["length"], errors="coerce").fillna(0)

    # Reemplazar valores nulos en columnas relevantes
    df["imageFile"] = df["imageFile"].fillna("")
    df["content"] = df["content"].fillna("")
    df["language"] = df["language"].fillna("unknown")

    # Verificar las primeras filas del DataFrame para garantizar el formato correcto
    print("🔍 Registros preparados para la carga:")
    print(df.head())

    # Fragmentar los datos según la longitud
    df_short = df[df["length"] < 15]
    df_medium = df[(df["length"] >= 16) & (df["length"] < 100)]
    df_long = df[df["length"] >= 100]

    # Insertar todos los datos en la colección global
    insert_data(df, "Post")

    # Insertar datos fragmentados en las colecciones correspondientes

    print("Ejemplo de datos en Post_Short:", df_short.head())
    print("Ejemplo de datos en Post_Medium:", df_medium.head())
    print("Ejemplo de datos en Post_Long:", df_long.head())
    insert_data(df_short, "Post_Short")
    insert_data(df_medium, "Post_Medium")
    insert_data(df_long, "Post_Long")


def load_products():
    file_path = os.path.join(data_dir, "Product.csv")
    print(f"📂 Cargando {file_path} en las colecciones de Product")

    # Leer el archivo de datos
    df = pd.read_csv(file_path, sep=",", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

    # Convertir la columna price a tipo numérico para aplicar filtros
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Fragmentar los datos según el precio
    df_cheap = df[df["price"] < 100]
    df_expensive = df[df["price"] >= 100]

    # Insertar todos los datos en la colección global
    insert_data(df, "Product")

    # Insertar productos baratos en Product_Cheap
    insert_data(df_cheap, "Product_Cheap")

    # Insertar productos caros en Product_Expensive
    insert_data(df_expensive, "Product_Expensive")


def load_knows():
    load_edge("person_knows_person_0_0.csv", "CustomerKnowsPerson", "Customer/", "Person/", ["creationDate"])

def load_has_interest():
    load_edge("person_hasInterest_tag_0_0.csv", "PersonHasInterestTag", "Person/", "Tag/")

def load_create():
    load_edge("post_hasCreator_person_0_0.csv", "PostHasCreatorPerson", "Post/", "Person/")

def load_has():
    load_edge("post_hasTag_tag_0_0.csv", "PostHasTag", "Post/", "Tag/")

# 📌 Vaciado de todas las colecciones antes de la carga
clear_collection("Customer_North")
clear_collection("Customer_Center")
clear_collection("Customer_South")
clear_collection("Customer")

clear_collection("Person")

clear_collection("Feedback")

clear_collection("Invoice")

clear_collection("Tag")

clear_collection("Vendor")

clear_collection("Order")
clear_collection("Order_Pre_Pandemic")
clear_collection("Order_Post_Pandemic")

clear_collection("Post")
clear_collection("Post_Short")
clear_collection("Post_Medium")
clear_collection("Post_Long")

clear_collection("Product")
clear_collection("Product_Cheap")
clear_collection("Product_Expensive")

# 🚀 Ejecutar la carga de datos
load_customer()
load_person()
load_feedback()
load_invoice()
load_tag()
load_vendor()
load_orders()
load_products()
load_posts()

load_knows()
load_has_interest()
load_create()
load_has()

print("🎉 Carga de datos completada.")