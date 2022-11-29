import socket
import threading

from mgylabs.utils import logger

log = logger.get_logger(__name__)

pool_sema = threading.BoundedSemaphore()


class IPCService:
    def __init__(self) -> None:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = None
        self.wait = []

    def set_port(self, port):
        self.port = port

    def run(self, callback, disconnect_callback):
        self.client_socket.connect(("localhost", self.port))

        log.info("Connected")

        while True:
            try:
                data = self.client_socket.recv(1024)

                if not data:
                    print("Disconnected")
                    break

                print("Received from the server", data.decode())

                if len(self.wait) == 0:
                    target = callback
                else:
                    target = self.wait.pop(0)

                threading.Thread(
                    target=target, args=(data.decode(),), daemon=True
                ).start()

            except ConnectionResetError:
                print("Disconnected")
                break

        self.client_socket.close()

        disconnect_callback()

    def wait_for_response(self, callback):
        self.wait.append(callback)

    def send(self, data: str):
        self.client_socket.send(data.encode())
        log.info(f"Send to server {data}")
