#!/bin/bash

# Configuración
CONTAINER_NAME="orientdb-node1"
DB_NAME="KhaBench"
USERNAME="root"
PASSWORD="rootpwd"
SQL_FILE="orientdb_create_schema.sql"

# Verifica si el archivo SQL existe antes de copiarlo
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: No se encontró el archivo SQL en $(pwd)"
    exit 1
fi

echo "🔍 Verificando si el contenedor $CONTAINER_NAME está en ejecución..."
if ! docker ps --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: El contenedor $CONTAINER_NAME no está corriendo."
    exit 1
fi
echo "✅ Contenedor encontrado. Conectando a OrientDB..."

# Verificar si la base de datos ya existe antes de crearla
echo "🛠️ Verificando la existencia de la base de datos '$DB_NAME'..."
DB_EXISTS=$(docker exec -i "$CONTAINER_NAME" /bin/bash -c "/orientdb/bin/console.sh <<EOF
CONNECT remote:localhost root $PASSWORD;
LIST DATABASES;
EXIT;
EOF" | grep -w "$DB_NAME")

if [ -z "$DB_EXISTS" ]; then
    echo "🆕 Creando la base de datos '$DB_NAME'..."
    docker exec -i "$CONTAINER_NAME" /bin/bash -c "/orientdb/bin/console.sh <<EOF
    CONNECT remote:localhost root $PASSWORD;
    CREATE DATABASE remote:localhost/$DB_NAME root $PASSWORD plocal graph;
    EXIT;
EOF"
else
    echo "✅ La base de datos '$DB_NAME' ya existe. Continuando..."
fi

# Copiar el archivo SQL dentro del contenedor antes de ejecutar
echo "📂 Copiando archivo SQL al contenedor..."
docker cp "$(pwd)/$SQL_FILE" "$CONTAINER_NAME:/orientdb/"

# Verificar que el archivo se copió correctamente dentro del contenedor
echo "🔍 Verificando que el archivo existe en el contenedor..."
docker exec -i "$CONTAINER_NAME" /bin/bash -c "ls -lah /orientdb/$SQL_FILE"

# Ejecutar el script principal (creación de clases, relaciones y propiedades)
echo "🚀 Ejecutando el script de creación de entidades..."
docker exec -i "$CONTAINER_NAME" /bin/bash -c "/orientdb/bin/console.sh <<EOF
CONNECT remote:localhost/$DB_NAME $USERNAME $PASSWORD;
LOAD SCRIPT /orientdb/$SQL_FILE;
EXIT;
EOF"

# Validar la ejecución
if [ $? -eq 0 ]; then
    echo "🎉 Creación de entidades completada exitosamente."
else
    echo "❌ Error en la creación de entidades."
fi
