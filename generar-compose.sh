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
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
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

