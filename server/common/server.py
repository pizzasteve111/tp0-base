import socket
import logging
import signal
import os
from threading import Thread, Lock, Condition
from common.utils import Bet, store_bets, load_bets, has_won

class Server:
    def __init__(self, port, listen_backlog,total_clients):
        # Initialize server client_socket
        self._shutdown=False
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._clients_done=0
        self._total_clients=total_clients
        
        #diccionario: clave Agency valor lista de Dnis ganadores
        self._winners_by_agency={}
        self._client_sockets_by_agency={}
        #en el compose se indica la cantidad de clients
        #se lo tiene que pasar a server ademas de client y de ahí lo saca
        self._winners_computed=False
        self._condition= Condition()
        

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
            raise ValueError("")

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
                t = Thread(target=self.__handle_client_connection, args=(client_sock,))
                t.daemon = True
                t.start()
            except OSError:
                break
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
       

        
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
#por fuera de clase así se puede picklear,usar datos compartidos entre procesos
#no depende de instancia.
    def __handle_client_connection(self, client_sock):
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

                        if msg.startswith("BET|"):
                            payload = msg[len("BET|"):]
                            bet = self.__parse_bet(payload)
                            client_agency = bet.agency
                            with self._condition:
                                store_bets([bet])
                            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.GetDni()} | numero: {bet.GetNumber()}')
                            batch_count += 1

                        elif msg == "BATCH_END":
                            logging.info(f'action: apuesta_recibida | result: success | cantidad: {batch_count}')
                            batch_count = 0
                            client_sock.sendall(b"OK\n")

                        elif msg == "END":
                            with self._condition:
                                self._clients_done += 1
                                logging.info(f'action: client_end | result: success | clients_done: {self._clients_done}')
                                if self._clients_done == self._total_clients:
                                    self._winners_computed=True
                                    self.__compute_winners()
                                    logging.info("action: sorteo | result: success")
                                    # que la condition me triggeree todas las conexiones dormidas
                                    self._condition.notify_all()
                                else:
                                    #si no esta el flag, que esperen
                                    self._condition.wait_for(lambda: self._winners_computed)
                            agency_id = client_agency
                            winners = list(self._winners_by_agency.get(agency_id, []))
                            for dni in winners:
                                client_sock.sendall(f"WIN|{dni}\n".encode())
                            client_sock.sendall(b"END\n")
                            return
            finally:
                client_sock.close()