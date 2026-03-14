#!/bin/bash

COMPOSE_FILE=${1:-}
TOTAL_CLIENTS=${2:-}

# Si están vacíos los parámetros, mostrar uso y salir
if [ -z "$COMPOSE_FILE" ] || [ -z "$TOTAL_CLIENTS" ]; then
    
    exit 1
fi


echo "hay $TOTAL_CLIENTS clientes levantados "

#las <> indican la dirección, con cat. Osea todo va a parar al output file
cat > "$COMPOSE_FILE" <<EOF
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
EOF

#levanto un container por cada uno de los N clientes,
for ((i=1;i<=TOTAL_CLIENTS;i++))
do
cat >> "$COMPOSE_FILE" <<EOF

  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
      - CLI_LOG_LEVEL=DEBUG
    depends_on:
      - server
    networks:
      - testing_net
EOF
done

cat >> "$COMPOSE_FILE" <<EOF

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF

##entonces con esto hago que se me genere el compose.yaml con todas estas configuraciones que le pido
