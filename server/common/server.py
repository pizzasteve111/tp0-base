import client_socket
import logging
import signal
import os
from common.utils import Bet, store_bets, load_bets, has_won
from multiprocessing import Pool, Manager, Lock

class Server:
    def __init__(self, port, listen_backlog,total_clients):
        manager=Manager()
        # Initialize server client_socket
        self._shutdown=False
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        self._server_client_socket = client_socket.client_socket(client_socket.AF_INET, client_socket.client_sock_STREAM)
        self._server_client_socket.bind(('', port))
        self._server_client_socket.listen(listen_backlog)
        self._clients_done=manager.Value("i",0)
        self._total_clients=total_clients
        
        #diccionario: clave Agency valor lista de Dnis ganadores
        self._winners_by_agency=manager.dict()
        self._client_sockets_by_agency=manager.dict()
        #en el compose se indica la cantidad de clients
        #se lo tiene que pasar a server ademas de client y de ahí lo saca

        self._lock=Lock()
        self._pool=Pool(processes=6)
        

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
        self._server_client_socket.close()

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
       
        while not self._shutdown:
            try:
                client_sock = self.__accept_new_connection()
                self._pool.apply_async(
                    handle_client_connection,
                    args=(
                        client_sock,
                        self._clients_done,
                        self._winners_by_agency,
                        self._lock,
                        self._total_clients
                    )
                )
            except OSError:
                break
        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        # while True:
        #     client_client_sock = self.__accept_new_connection()
        #     self.__handle_client_connection(client_client_sock)
    #asegura que hasta que no termine el salto de linea, no deja leer
    def __recv_line(self, client_sock):

        data = b''

        while not data.endswith(b'\n'):

            chunk = client_sock.recv(1024)

            if not chunk:
                break

            data += chunk

        return data.decode().strip()


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_client_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
#por fuera de clase así se puede picklear,usar datos compartidos entre procesos
#no depende de instancia.
def handle_client_connection(client_sock, clients_done, winners_dict, lock, total_clients):

        client_agency = None
        batch_count = 0
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
                        fields=payload.split(",")
                        bet = Bet(*fields)

                        client_agency = bet.agency
                        with lock:
                            store_bets([bet])

                        logging.info(
                            f'action: apuesta_almacenada | result: success | dni: {bet.GetDni()} | numero: {bet.GetNumber()}'
                        )
                        batch_count+=1
                    elif msg == "BATCH_END":
                        logging.info(f'action: apuesta_recibida | result: success | cantidad: {batch_count}')
                        batch_count = 0
                        client_sock.sendall(b"OK\n")
                    # -------- END --------
                    elif msg == "END":
                        with lock:
                            clients_done.value += 1

                            logging.info(
                                f'action: client_end | result: success | clients_done: {clients_done.value}'
                            )

                            if clients_done.value == total_clients:

                                winners = {}

                                for bet in load_bets():
                                    if has_won(bet):
                                        winners.setdefault(bet.agency, []).append(bet.document)

                                winners_dict.clear()
                                winners_dict.update(winners)

                                logging.info("action: sorteo | result: success")

                        return

                    # -------- GET_WINNERS --------
                    elif msg.startswith("GET|"):
                        agency_id = int(msg.split("|")[1])
                        with lock:
                            if clients_done.value < total_clients:
                                client_sock.sendall(b"WAIT\n")
                                continue

                            winners = winners_dict.get(agency_id, [])

                        for dni in winners:
                            client_sock.sendall(f"WIN|{dni}\n".encode())

                        client_sock.sendall(b"END\n")
                        return
        finally:
            client_sock.close()