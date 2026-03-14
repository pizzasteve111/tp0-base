Lo que tengo que hacer es que mi bash al ejecutarse me genere un compose nuevo con soporte para python, go e incluya los containers que instancio.

Al correr el bash, se me genera el nuevo yaml con esa config, luego le hago compose up a ese yaml nuevo.

DAR PERMISOS AL BASH => chmod +x generar-compose.sh

para construir las imagenes bien:
docker build -t client:latest -f client/Dockerfile .
docker build -t server:latest -f server/Dockerfile .

despues en wsl cd /mnt/c/Users/juanc/tp0-tests,  source venv/bin/activate, REPO_PATH=/mnt/c/Users/juanc/tp0/tp0-base make test

EJ2:
quiero que modificaciones en el config no me obliguen a reconstruir imagenes. Las configs deben vivir en el volumen del container.
. En el .sh le indico que quiero que los configs se carguen en el volumen del container