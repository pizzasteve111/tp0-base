Lo que tengo que hacer es que mi bash al ejecutarse me genere un compose nuevo con soporte para python, go e incluya los containers que instancio.

Al correr el bash, se me genera el nuevo yaml con esa config, luego le hago compose up a ese yaml nuevo.

DAR PERMISOS AL BASH => chmod +x generar-compose.sh

para construir las imagenes bien:
docker build -t client:latest -f client/Dockerfile .
docker build -t server:latest -f server/Dockerfile .

hacer cd ~/tp0-base para pullearse los cambios

despues en wsl cd /mnt/c/Users/juanc/tp0-tests,  source venv/bin/activate, REPO_PATH=/home/juanc/tp0-base make test
docker pull busybox para imagen que hace test

EJ2:
quiero que modificaciones en el config no me obliguen a reconstruir imagenes. Las configs deben vivir en el volumen del container.
. En el .sh le indico que quiero que los configs se carguen en el volumen del container

EJ3:
#contenedor temporal, el rm lo borra
MSG_RESPONSE=$(docker run --rm --network $NETWORK \
#se usa la imagen busybox que ya tiene netcat interno, entonces
#la comunicación sucede en el interior del compose
        busybox sh -c  "echo $MESSAGE | nc $SERVER_CONTAINER $PORT" | tr -d '\r\n')
#sh -c le pide a la shell que ejecute el siguiente comando ""

hago NETWORK=$(docker inspect $SERVER_CONTAINER \
    --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null)

porque lo que quiero es obtener toda la data del container,
me quedo con la network del container y uso esa para testear al echo


EJERCICIO 4:

Quiero que al mandar sigterm, termine gracefull. Osea que el server termine de responder sus mensajes sin aceptar nuevos y que el cliente cierre conexión.

Client tiene que tener un handle shutdown donde corta socket, server donde no acepta mas conns.
En el compose tiene que manejarse el comando SIGTERM y setear el tiempo que tienen.

EJERCICIO 5:
Ahora se simula la logica de una lotería.

Cliente es una quiniela, se levantan 5 clientes.
Sus variables de entorno son el de los campos de apuestas(nombres, numero etc).

Las variables de entorno que reciben representan a un usuario haciendo una apuesta. Los tests van a usar esto para simular apuestas que se hacen.
Client tiene que saber como interpretarlo.

SERVER:
tiene que poder recibir el bet de un client, leer los campos de la apuesta
y los almacena en las funciones ya dadas.

Protocolo:
Cuando client se triggerea por una env variable de una apuesta,
establece conexión con server.
Existe un tipo de dato BET_MESSAGE donde puede serializar los campos en
bytes y enviarlo por el canal, luego server sabe exactamente lo que recibe
asi que lo puede ir parseando y obteniendo el tipo de dato exacto que busca.

usamos send_all y recv_exact para evitar shor read/write.
Timeouts

Ejercicio 6:

antes el cliente mandaba una bet y cerraba conexion, ahora queremos mandar un chunk de bets.
Tiene que haber conexión persistente. Ni cliente ni servidor deben terminar conexión.

Cliente manda un conjunto de bets así solo recibe ack por batches y es mas eficiente.

En el config se instancia el tamaño del chunk,
cuando recibe una bet desde las env var, lo que hace es generar un vector
del tamaño dado por la config. En ese vector guardan las bets y de ahí

Las env var ahora tienen que ser configurables para cada uno de los usuarios.

se configura una cantidad maxima de apuestas.

Los archivos tienen que estar en el volumen así no se duplican en cada imagen.