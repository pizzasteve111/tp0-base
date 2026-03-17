import socket
import logging
import signal
import os
from common.utils import Bet, store_bets, load_bets, has_won

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._shutdown=False
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._clients_done=0
        self._total_clients=0
        #diccionario: clave Agency valor lista de Dnis ganadores
        self._winners_by_agency={}
        #en el compose se indica la cantidad de clients
        #se lo tiene que pasar a server ademas de client y de ahí lo saca
        

    def __compute_winners(self):
        winners_by_agency = {}

        for bet in load_bets():
            if has_won(bet):
                agency = bet.agency
                winners_by_agency.setdefault(agency, []).append(bet.document)

        self._winners_by_agency = winners_by_agency

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

        client_agency = None

        try:
            buffer = b''

            while True:

                chunk = client_sock.recv(1024)
                if not chunk:
                    break

                buffer += chunk

                while b'\n' in buffer:

                    line, buffer = buffer.split(b'\n', 1)
                    msg = line.decode().strip()

                    if not msg:
                        continue

                    # -------- BET --------
                    if msg.startswith("BET|"):

                        payload = msg[len("BET|"):]
                        bet = self.__parse_bet(payload)

                        client_agency = bet.agency

                        store_bets([bet])

                        logging.info(
                            f'action: apuesta_almacenada | result: success | dni: {bet.GetDni()} | numero: {bet.GetNumber()}'
                        )

                    # -------- END --------
                    elif msg.startswith("END|"):

                        self._clients_done += 1

                        logging.info(
                            f'action: client_end | result: success | clients_done: {self._clients_done}'
                        )

                        if self._clients_done == self._total_clients:

                            self.__compute_winners()

                            logging.info("action: sorteo | result: success")

                        return

                    # -------- GET_WINNERS --------
                    elif msg.startswith("GET|"):

                        if self._clients_done < self._total_clients:
                            client_sock.sendall(b"WAIT\n")
                            continue

                        winners = self._winners_by_agency.get(client_agency, [])

                        for dni in winners:
                            client_sock.sendall(f"WIN|{dni}\n".encode())

                        client_sock.sendall(b"END\n")

        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        self._total_clients+=1
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
