import logging
import socket
import threading

log = logging.getLogger(__name__)

pool_sema = threading.BoundedSemaphore()


class IPCService:
    def __init__(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port = None
        self.wait = []

    def set_port(self, port):
        self.port = port

    def run(self, callback, disconnect_callback):
        self.server_socket.bind(("localhost", self.port))
        self.server_socket.listen()

        log.info(f"listen {self.port}...")
        self.client_socket, self.addr = self.server_socket.accept()

        log.info("Connected by %s", self.addr)

        while True:
            try:
                data = self.client_socket.recv(1024)

                if not data:
                    print("Disconnected by " + self.addr[0], ":", self.addr[1])
                    break

                print("Received from " + self.addr[0], ":", self.addr[1], data.decode())

                if len(self.wait) == 0:
                    target = callback
                else:
                    target = self.wait.pop(0)

                threading.Thread(
                    target=target, args=(data.decode(),), daemon=True
                ).start()

            except ConnectionResetError:
                print("Disconnected by " + self.addr[0], ":", self.addr[1])
                break

        self.client_socket.close()

        disconnect_callback()

    def wait_for_response(self, callback):
        self.wait.append(callback)

    def send(self, data: str):
        self.client_socket.send(data.encode())
