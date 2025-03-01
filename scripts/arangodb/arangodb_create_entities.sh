#!/bin/bash

# Configuración
DB_NAME="KhaBench"
USERNAME="root"
PASSWORD="tu_contraseña"
COORDINATOR_URL="http://localhost:7101"

# Verificar conexión con ArangoDB
echo "🔍 Verificando conexión con ArangoDB..."
if ! curl --silent --fail "$COORDINATOR_URL/_api/version" > /dev/null; then
    echo "❌ No se pudo conectar a ArangoDB en $COORDINATOR_URL"
    exit 1
fi
echo "✅ Conexión exitosa con ArangoDB."

# Verificar si la base de datos existe
EXISTS=$(curl --silent --user "$USERNAME:$PASSWORD" "$COORDINATOR_URL/_api/database/user" | grep -o "$DB_NAME")
if [ "$EXISTS" == "$DB_NAME" ]; then
    echo "⚠️ La base de datos '$DB_NAME' ya existe."
else
    echo "🛠️ Creando la base de datos '$DB_NAME'..."
    curl --silent --user "$USERNAME:$PASSWORD" --request POST --data "{\"name\": \"$DB_NAME\"}" "$COORDINATOR_URL/_api/database"
    echo "✅ Base de datos '$DB_NAME' creada exitosamente."
fi

# Crear colecciones con esquema
declare -A schemas
schemas["Person"]='{
    "name": "Person",
    "type": 2,
    "leader": "DBServer0004",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Person",
        "rule": {
            "type": "object",
            "properties": {
                "_key": { "type": "string" },
                "place": { "type": "number" },
                "firstName": { "type": "string" },
                "lastName": { "type": "string" },
                "gender": { "type": "string" },
                "birthday": { "type": "string" },
                "createDate": { "type": "string" },
                "location": { "type": "string" },
                "browserUsed": { "type": "string" }
            },
            "required": ["_key"]
        }
    }
}'
schemas["Customer"]='{
    "name": "Customer",
    "type": 2,
    "leader": "DBServer0004",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Customer",
        "rule": {
            "type": "object",
            "properties": {
                "_key": { "type": "string" },
                "place": { "type": "number" },
                "firstName": { "type": "string" },
                "lastName": { "type": "string" },
                "gender": { "type": "string" },
                "birthday": { "type": "string" },
                "createDate": { "type": "string" },
                "location": { "type": "string" },
                "browserUsed": { "type": "string" }
            },
            "required": ["_key"]
        }
    }
}'
schemas["Customer_North"]='{
    "name": "Customer_North",
    "type": 2,
    "shardKeys": ["place"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0001",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Customer_North",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "place": {"type": "number"},
                "firstName": {"type": "string"},
                "lastName": {"type": "string"},
                "gender": {"type": "string"},
                "birthday": {"type": "string"},
                "createDate": {"type": "string"},
                "location": {"type": "string"},
                "browserUsed": {"type": "string"}
            },
            "required": ["_key"]
        }
    }
}'
schemas["Customer_Center"]='{
    "name": "Customer_Center",
    "type": 2,
    "shardKeys": ["place"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0002",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Customer_Center",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "place": {"type": "number"},
                "firstName": {"type": "string"},
                "lastName": {"type": "string"},
                "gender": {"type": "string"},
                "birthday": {"type": "string"},
                "createDate": {"type": "string"},
                "location": {"type": "string"},
                "browserUsed": {"type": "string"}
            },
            "required": ["_key"]
        }
    }
}'

schemas["Customer_South"]='{
    "name": "Customer_South",
    "type": 2,
    "shardKeys": ["place"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0002",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Customer_South",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "place": {"type": "number"},
                "firstName": {"type": "string"},
                "lastName": {"type": "string"},
                "gender": {"type": "string"},
                "birthday": {"type": "string"},
                "createDate": {"type": "string"},
                "location": {"type": "string"},
                "browserUsed": {"type": "string"}
            },
            "required": ["_key"]
        }
    }
}'

schemas["Product"]='{
    "name": "Product",
    "type": 2,
    "leader": "DBServer0004",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Product",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "title": {"type": "string"},
                "price": {"type": "number"},
                "imgUrl": {"type": "string"},
                "productId": {"type": "string"},
                "brand": {"type": "string"}
            },
            "required": ["_key", "title", "price", "productId"]
        }
    }
}'

schemas["Product_Cheap"]='{
    "name": "Product_Cheap",
    "type": 2,
    "shardKeys": ["price"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0001",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Product_Cheap",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "title": {"type": "string"},
                "price": {"type": "number"},
                "imgUrl": {"type": "string"},
                "productId": {"type": "string"},
                "brand": {"type": "string"}
            },
            "required": ["_key", "title", "price", "productId"]
        }
    }
}'
schemas["Product_Expensive"]='{
    "name": "Product_Expensive",
    "type": 2,
    "shardKeys": ["price"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0002",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Product_Expensive",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "title": {"type": "string"},
                "price": {"type": "number"},
                "imgUrl": {"type": "string"},
                "productId": {"type": "string"},
                "brand": {"type": "string"}
            },
            "required": ["_key", "title", "price", "productId"]
        }
    }
}'

schemas["Order"]='{
    "name": "Order",
    "type": 2,
    "leader": "DBServer0004",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Order",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "PersonId": {"type": "string"},
                "OrderDate": {"type": "string"},
                "TotalPrice": {"type": "number"},
                "Orderline": {"type": "array"}
            },
            "required": ["_key", "PersonId", "OrderDate", "TotalPrice"]
        }
    }
}'
schemas["Order_Pre_Pandemic"]='{
    "name": "Order_Pre_Pandemic",
    "type": 2,
    "shardKeys": ["_key"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0003",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Order_Pre_Pandemic",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "PersonId": {"type": "string"},
                "OrderDate": {"type": "string"},
                "TotalPrice": {"type": "number"},
                "Orderline": {"type": "array"}
            },
            "required": ["_key", "PersonId", "OrderDate", "TotalPrice"]
        }
    }
}'
schemas["Order_Post_Pandemic"]='{
    "name": "Order_Post_Pandemic",
    "type": 2,
    "shardKeys": ["_key"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0003",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Order_Post_Pandemic",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "PersonId": {"type": "string"},
                "OrderDate": {"type": "string"},
                "TotalPrice": {"type": "number"},
                "Orderline": {"type": "array"}
            },
            "required": ["_key", "PersonId", "OrderDate", "TotalPrice"]
        }
    }
}'
schemas["Vendor"]='{
    "name": "Vendor",
    "type": 2,
    "leader": "DBServer0004",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Vendor",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "country": {"type": "string"},
                "industry": {"type": "string"}
            },
            "required": ["_key", "country", "industry"]
        }
    }
}'
schemas["Feedback"]='{
    "name": "Feedback",
    "type": 2,
    "leader": "DBServer0004",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Feedback",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "personId": {"type": "string"},
                "review": {"type": "string"}
            },
            "required": ["_key", "personId", "review"]
        }
    }
}'
schemas["Post"]='{
    "name": "Post",
    "type": 2,
    "leader": "DBServer0004",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Post",
        "rule": {
            "type": "object",
            "properties": {
                "_key": { "type": "string" },
                "imageFile": { "type": "string", "default": "" },
                "createDate": { "type": "string" },
                "location": { "type": "string" },
                "browserUsed": { "type": "string" },
                "content": { "type": "string" },
                "length": { "type": "string" }
            },
            "required": ["_key"]
        }
    }
}'
schemas["Post_Short"]='{
    "name": "Post_Short",
    "type": 2,
    "shardKeys": ["_key"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0001",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Post_Short",
        "rule": {
            "type": "object",
            "properties": {
                "_key": { "type": "string" },
                "content": { "type": "string" },
                "length": { "type": "number" },
                "browserUsed": { "type": "string" },
                "createDate": { "type": "string" },
                "imageFile": { "type": "string" }
            },
            "required": ["_key", "length"]
        }
    }
}'
schemas["Post_Medium"]='{
    "name": "Post_Medium",
    "type": 2,
    "shardKeys": ["_key"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0002",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Post_Medium",
        "rule": {
            "type": "object",
            "properties": {
                "_key": { "type": "string" },
                "content": { "type": "string" },
                "length": { "type": "number" },
                "browserUsed": { "type": "string" },
                "createDate": { "type": "string" },
                "imageFile": { "type": "string" }
            },
            "required": ["_key", "length"]
        }
    }
}'
schemas["Post_Long"]='{
    "name": "Post_Long",
    "type": 2,
    "shardKeys": ["_key"],
    "numberOfShards": 1,
    "replicationFactor": 1,
    "leader": "DBServer0003",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Post_Long",
        "rule": {
            "type": "object",
            "properties": {
                "_key": { "type": "string" },
                "content": { "type": "string" },
                "length": { "type": "number" },
                "browserUsed": { "type": "string" },
                "createDate": { "type": "string" },
                "imageFile": { "type": "string" }
            },
            "required": ["_key", "length"]
        }
    }
}'
schemas["Tag"]='{
    "name": "Tag",
    "type": 2,
    "leader": "DBServer0004",,
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Tag",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "title": {"type": "string"}
            },
            "required": ["_key"]
        }
    }
}'
schemas["Invoice"]='{
    "name": "Invoice",
    "type": 2,
    "leader": "DBServer0004",
    "schema": {
        "level": "none",
        "message": "Datos inválidos en Invoice",
        "rule": {
            "type": "object",
            "properties": {
                "_key": {"type": "string"},
                "OrderId": {"type": "string"},
                "TotalAmount": {"type": "number"},
                "IssuedDate": {"type": "string"}
            },
            "required": ["_key", "OrderId", "TotalAmount", "IssuedDate"]
        }
    }
}'

echo "📂 Creando colecciones con esquemas..."
for collection in "${!schemas[@]}"; do
    echo "➕ Creando colección '$collection' con esquema..."
    curl --silent --user "$USERNAME:$PASSWORD" --request POST \
        --header "Content-Type: application/json" \
        --data "${schemas[$collection]}" \
        "$COORDINATOR_URL/_db/$DB_NAME/_api/collection" | jq '.'
    echo "✅ Colección '$collection' creada con esquema."
done


# Crear relaciones (edges)
declare -A edges
edges["CustomerKnowsPerson"]='{"from": ["Customer"], "to": ["Person"]}'
edges["PersonHasInterestTag"]='{"from": ["Person"], "to": ["Tag"]}'
edges["PostHasCreatorPerson"]='{"from": ["Post"], "to": ["Person"]}'
edges["PostHasTag"]='{"from": ["Post"], "to": ["Tag"]}'


echo "📡 Creando relaciones (edges)..."
for edge in "${!edges[@]}"; do
    echo "➕ Creando relación '$edge'..."
    curl --silent --user "$USERNAME:$PASSWORD" --request POST \
        --header "Content-Type: application/json" \
        --data "{\"name\": \"$edge\", \"type\": 3, \"edge\": true}" \
        "$COORDINATOR_URL/_db/$DB_NAME/_api/collection" | jq '.'
    echo "✅ Relación '$edge' creada."
done

# 🛠️ **Creación del Grafo en ArangoDB**
echo "📡 Creando el grafo 'SocialNetwork' en ArangoDB..."
curl --silent --user "$USERNAME:$PASSWORD" --request POST \
    --header "Content-Type: application/json" \
    --data "{
        \"name\": \"SocialNetwork\",
        \"edgeDefinitions\": [
            {
                \"collection\": \"CustomerKnowsPerson\",
                \"from\": [\"Customer\"],
                \"to\": [\"Person\"]
            },
            {
                \"collection\": \"PersonHasInterestTag\",
                \"from\": [\"Person\"],
                \"to\": [\"Tag\"]
            },
            {
                \"collection\": \"PostHasCreatorPerson\",
                \"from\": [\"Post\"],
                \"to\": [\"Person\"]
            },
            {
                \"collection\": \"PostHasTag\",
                \"from\": [\"Post\"],
                \"to\": [\"Tag\"]
            }
        ]
    }" \
    "$COORDINATOR_URL/_db/$DB_NAME/_api/gharial"

echo "🎉 Configuración completada."
