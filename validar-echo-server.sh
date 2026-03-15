#!/usr/bin/env bash



NETWORK=test-net
SERVER_CONTAINER=server
SERVER_IMAGE=server:latest
PORT=12345
MESSAGE="ping"

docker network create $NETWORK >/dev/null 2>&1

docker run -d \
    --name $SERVER_CONTAINER \
    --network $NETWORK \
    $SERVER_IMAGE >/dev/null

sleep 5

#contenedor temporal, el rm lo borra
MSG_RESPONSE=$(docker run --rm --network $NETWORK \
#se usa la imagen busybox que ya tiene netcat interno, entonces
#la comunicación sucede en el interior del compose
        busybox sh -c  "$MESSAGE | nc $SERVER_CONTAINER $PORT" | tr -d '\r\n')
#sh -c le pide a la shell que ejecute el siguiente comando ""

if [ "$MSG_RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi