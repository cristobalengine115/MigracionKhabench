#!/bin/bash

# Nombre de la pila en Docker Swarm
STACK_NAME="khab"

# Directorio base donde están los archivos de Docker Compose
BASE_DIR=~/MigracionKhabench/compose-files

# Lista de carpetas con archivos docker-compose.yml
FOLDERS=("KHAB-1" "KHAB-2" "KHAB-3" "KHAB-4")

# Crear la red overlay si no existe
docker network inspect khab-network > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Creando la red overlay 'khab-network'..."
    docker network create -d overlay --attachable khab-network
else
    echo "La red 'khab-network' ya existe."
fi

# Desplegar cada archivo docker-compose.yml
for folder in "${FOLDERS[@]}"; do
    COMPOSE_FILE="${BASE_DIR}/${folder}/${folder,,}-compose.yml"
    if [ -f "$COMPOSE_FILE" ]; then
        echo "Desplegando servicios desde ${COMPOSE_FILE}..."
        docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME"
    else
        echo "Archivo ${COMPOSE_FILE} no encontrado, omitiendo..."
    fi
done

# Comprobar el estado de los servicios
echo "Comprobando el estado de los servicios..."
docker stack services "$STACK_NAME"

echo "Despliegue completado."
