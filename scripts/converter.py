import json
import xml.etree.ElementTree as ET
import os

# 📂 Rutas de los archivos
DATASET_DIR = "../Dataset/Invoice/"
INPUT_FILE = "../Dataset/Order/Order.json"  # Usamos el archivo corregido con Vendor_ID numérico
OUTPUT_FILE = os.path.join(DATASET_DIR, "Invoice3.xml")

# 📂 Crear la raíz del XML
root = ET.Element("Invoices")

# 📂 Leer el JSON de órdenes
print(f"📂 Cargando {INPUT_FILE} en Order...")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    orders = [json.loads(line) for line in f]

# 🔄 Convertir cada orden en un elemento XML
for order in orders:
    invoice = ET.SubElement(root, "Invoice")

    ET.SubElement(invoice, "ORDER_ID").text = order["ORDER_ID"]
    ET.SubElement(invoice, "CUSTOMER_ID").text = order["CUSTOMER_ID"]
    ET.SubElement(invoice, "ORDER_DATE").text = order["ORDER_DATE"]
    ET.SubElement(invoice, "TOTAL_PRICE").text = str(order["TOTAL_PRICE"])

    # 🔍 Convertir cada línea de orden en XML
    for item in order["ORDER_LINE"]:
        order_line = ET.SubElement(invoice, "ORDER_LINE")
        ET.SubElement(order_line, "SKU").text = item["SKU"]
        ET.SubElement(order_line, "PRODUCT_ID").text = item["PRODUCT_ID"]
        ET.SubElement(order_line, "TITLE").text = item["TITLE"]
        ET.SubElement(order_line, "PRICE").text = str(item["PRICE"])
        ET.SubElement(order_line, "VENDOR_ID").text = str(item["VENDOR_ID"]) if item["VENDOR_ID"] else "NULL"

# 📂 Guardar el XML con formato y saltos de línea
def prettify(elem, level=0):
    """ Agrega indentación y saltos de línea para un XML más legible """
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        for subelem in elem:
            prettify(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
    elif level:
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent

prettify(root)

# 📂 Guardar el archivo XML correctamente formateado
tree = ET.ElementTree(root)
with open(OUTPUT_FILE, "wb") as f:
    tree.write(f, encoding="utf-8", xml_declaration=True)

print(f"✅ Archivo `Invoice.xml` generado con formato legible en {OUTPUT_FILE}")
