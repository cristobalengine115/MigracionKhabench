import pandas as pd

# Ruta al archivo CSV
csv_path = "/home/khabench/Desktop/test/Dataset/Feedback/Feedback.csv"

# Cargar CSV
df = pd.read_csv(csv_path, sep="|", dtype=str, quotechar='"', skipinitialspace=True, on_bad_lines="skip")

# Filtrar filas donde CUSTOMER_ID o PRODUCT_ID estén vacíos
df = df.dropna(subset=["CUSTOMER_ID", "PRODUCT_ID"])

# Reemplazar REVIEW vacíos con un mensaje por defecto
df["REVIEW"] = df["REVIEW"].fillna("No review provided").str.strip()

# Guardar el CSV corregido
df.to_csv(csv_path, sep="|", index=False, quotechar='"')

print("✅ Archivo CSV de Feedback corregido y guardado.")