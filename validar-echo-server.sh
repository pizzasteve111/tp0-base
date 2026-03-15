#!/usr/bin/env bash




SERVER_CONTAINER=server
PORT=12345
MESSAGE="ping"

NETWORK=$(docker inspect $SERVER_CONTAINER \
    --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null)

if [ -z "$NETWORK" ]; then
    echo "action: test_echo_server | result: fail"
    exit 0
fi

MSG_RESPONSE=$(docker run --rm --network $NETWORK \
    busybox sh -c  "echo $MESSAGE | nc $SERVER_CONTAINER $PORT" | tr -d '\r\n')


if [ "$MSG_RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi