#!/usr/bin/env bash



NETWORK=test-net
SERVER_CONTAINER=server
SERVER_IMAGE=server:latest
PORT=12345
MESSAGE="ping"
docker rm -f $SERVER_CONTAINER 2>/dev/null || true
docker network create $NETWORK >/dev/null 2>&1

docker run -d \
    --name $SERVER_CONTAINER \
    --network $NETWORK \
    $SERVER_IMAGE >/dev/null

sleep 5


MSG_RESPONSE=$(docker run --rm --network $NETWORK \
    busybox sh -c  "echo $MESSAGE | nc $SERVER_CONTAINER $PORT" | tr -d '\r\n')


if [ "$MSG_RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi