#!/bin/bash

# Configuración
DB_NAME="KhaBench"
DB_TYPE="plocal"
USERNAME="root"
PASSWORD="rootpwd"
SERVER_URL="http://localhost:2480"
CONTAINER_NAME="orientdb-node1"

echo "🔍 Verificando si el contenedor $CONTAINER_NAME está en ejecución..."
if ! docker ps --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: El contenedor $CONTAINER_NAME no está corriendo."
    exit 1
fi
echo "✅ Contenedor encontrado."

# Crear la base de datos
echo "🛠️ Creando la base de datos '$DB_NAME'..."
curl -u $USERNAME:$PASSWORD -X POST \
     -d "name=$DB_NAME&type=$DB_TYPE&username=$USERNAME&password=$PASSWORD" \
     $SERVER_URL/database/$DB_NAME/$DB_TYPE

if [ $? -eq 0 ]; then
    echo "✅ Base de datos '$DB_NAME' creada exitosamente."
else
    echo "❌ Error al crear la base de datos."
    exit 1
fi

# 🛠️ Crear usuario `root` en la base de datos
echo "🔐 Creando usuario 'root' en la base de datos..."
docker exec -i "$CONTAINER_NAME" /bin/bash -c "/orientdb/bin/console.sh <<EOF
CONNECT remote:127.0.0.1/$DB_NAME root rootpwd;
INSERT INTO OUser SET name = 'root', password = 'rootpwd', status = 'ACTIVE', roles = (SELECT FROM ORole WHERE name = 'admin');
EXIT;
EOF"

if [ $? -eq 0 ]; then
    echo "✅ Usuario 'root' creado exitosamente."
else
    echo "❌ Error al crear el usuario 'root'."
    exit 1
fi

echo "🎉 Configuración de la base de datos y usuario completada exitosamente."