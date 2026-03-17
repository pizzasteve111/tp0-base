#!/usr/bin/env bash

COMPOSE_FILE=$1
TOTAL_CLIENTS=$2

if [ -z "$COMPOSE_FILE" ] || [ -z "$TOTAL_CLIENTS" ]; then
    
    exit 1
fi




cat > "$COMPOSE_FILE" <<EOF
version: "3"
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini

      
EOF

for i in $(seq 1 "$TOTAL_CLIENTS")
do
cat >> "$COMPOSE_FILE" <<EOF

  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
      - NOMBRE=${NOMBRE}
      - APELLIDO=${APELLIDO}
      - DOCUMENTO=${DOCUMENTO}
      - NACIMIENTO=${NACIMIENTO}
      - NUMERO=${NUMERO}
    depends_on:
      - server
    networks:
      - testing_net
    volumes:
      - ./data/dataset.zip:/dataset/dataset.zip
      - ./client/config.yaml:/config.yaml
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

