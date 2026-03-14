#!/bin/bash



COMPOSE_FILE=${1:-}
TOTAL_CLIENTS=${2:-}

# Si están vacíos los parámetros, mostrar uso y salir
if [ -z "$COMPOSE_FILE" ] || [ -z "$TOTAL_CLIENTS" ]; then
    
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    
    exit 2
fi

echo "hay $TOTAL_CLIENTS clientes levantados "

# El nombre del servicio en docker-compose es 'client' según el repo
docker compose -f "$COMPOSE_FILE" up --build --scale client="$TOTAL_CLIENTS"