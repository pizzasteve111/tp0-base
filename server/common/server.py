import socket
import logging
import signal
from common.utils import Bet, store_bets, load_bets

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._shutdown=False
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    #si llamo a cerrar el server, que no acepte mas conns.
    def handle_shutdown(self, signum, frame):
        logging.info("action: shutdown | result: in_progress")
        self._shutdown = True
        self._server_socket.close()

    def __parse_bet(self, msg: str) -> Bet:
        fields = msg.split(',')

        if len(fields) != 6:
            raise ValueError("Invalid bet format")

        agency, first_name, last_name, document, birthdate, number = fields

        return Bet(
            agency,
            first_name,
            last_name,
            document,
            birthdate,
            number
        )
    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        while not self._shutdown:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
            except OSError:
                break
        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        # while True:
        #     client_sock = self.__accept_new_connection()
        #     self.__handle_client_connection(client_sock)
    #asegura que hasta que no termine el salto de linea, no deja leer
    def __recv_line(self, sock):

        data = b''

        while not data.endswith(b'\n'):

            chunk = sock.recv(1024)

            if not chunk:
                break

            data += chunk

        return data.decode().strip()
    def __handle_client_connection(self, client_sock):

        try:

            buffer = b''

            while True:

                chunk = client_sock.recv(1024)

                # conexión cerrada por el cliente
                if not chunk:
                    break

                buffer += chunk

                # procesar todas las bets completas en el buffer
                while b'\n' in buffer:

                    line, buffer = buffer.split(b'\n', 1)

                    msg = line.decode().strip()

                    if not msg:
                        continue

                    bet = self.__parse_bet(msg)

                    dni = bet.GetDni()
                    bet_number = bet.GetNumber()

                    store_bets([bet])

                    logging.info(
                        f'action: apuesta_almacenada | result: success | dni: {dni} | numero: {bet_number}'
                    )

                # ACK del batch recibido
                client_sock.sendall(b"OK\n")

        except OSError as e:

            logging.error(
                f"action: process_bet | result: fail | error: {e}"
            )

        finally:

            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
