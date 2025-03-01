#!/bin/bash

# Directorio donde están los scripts
SCRIPT_DIR="$(dirname "$0")"

# 🚀 Paso 1: Detener y eliminar los contenedores
echo "🛑 Deteniendo y eliminando contenedores de OrientDB..."
docker compose -f "$SCRIPT_DIR/docker-compose-orientdb.yml" down -v

# 🚀 Paso 2: Levantar los contenedores de nuevo
echo "🔄 Reiniciando OrientDB..."
docker compose -f "$SCRIPT_DIR/docker-compose-orientdb.yml" up -d

# Esperar a que los contenedores estén listos
echo "⏳ Esperando a que OrientDB esté listo..."
sleep 30  # Ajusta el tiempo según sea necesario

# 🚀 Paso 3: Crear la base de datos
echo "🛠️ Creando la base de datos..."
bash "$SCRIPT_DIR/orientdb_createdb.sh"

# 🚀 Paso 4: Crear entidades y esquemas
echo "📌 Creando entidades y esquemas..."
bash "$SCRIPT_DIR/orientdb_create_entities.sh"

# 🚀 Paso 5: Verificar si OrientDB está corriendo
echo "🔍 Verificando estado de OrientDB..."
docker ps --format "table {{.Names}}\t{{.Status}}"

echo "🎉 OrientDB ha sido reiniciado y configurado exitosamente."