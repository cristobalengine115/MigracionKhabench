#!/bin/bash

# Configuración
db_name="KhaBench"
username="root"
password="tu_contraseña"
coordinator_url="http://localhost:7101"

# Verificar conexión con ArangoDB
echo "🔍 Verificando conexión con ArangoDB..."
curl --silent --fail "$coordinator_url/_api/version" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ No se pudo conectar a ArangoDB en $coordinator_url"
    exit 1
fi
echo "✅ Conexión exitosa con ArangoDB."

# Verificar si la base de datos existe
exists=$(curl --silent --user "$username:$password" "$coordinator_url/_api/database/user" | grep -o "$db_name")
if [ "$exists" == "$db_name" ]; then
    echo "⚠️ La base de datos '$db_name' ya existe."
    exit 0
fi

# Crear la base de datos
echo "🛠️ Creando la base de datos '$db_name'..."
curl --silent --user "$username:$password" --request POST \
    --data '{"name": "'$db_name'"}' \
    "$coordinator_url/_api/database"

if [ $? -eq 0 ]; then
    echo "✅ Base de datos '$db_name' creada exitosamente."
else
    echo "❌ Error al crear la base de datos."
    exit 1
fi
