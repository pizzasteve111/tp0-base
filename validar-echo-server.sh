#!/usr/bin/env bash



NETWORK=tp0_testing_net
SERVER_CONTAINER=server
PORT=12345
MESSAGE="ping"



MSG_RESPONSE=$(docker run --rm --network $NETWORK \
    busybox sh -c  "echo $MESSAGE | nc $SERVER_CONTAINER $PORT" | tr -d '\r\n')


if [ "$MSG_RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi