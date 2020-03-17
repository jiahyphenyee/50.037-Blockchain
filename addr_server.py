"""
A fake address server that provides a list of address of
listening nodes on the network
"""
from concurrent.futures import ThreadPoolExecutor
import threading
import socket
import json


class AddressServer:

    HOST = "localhost"
    PORT = 6666

    def __init__(self):
        print(".......Starting Address Server........")
        self.nodes = []

        # TCP socket configuration
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("localhost", AddressServer.PORT))
        self.socket.listen(5)
        threading.Thread(target=self.run).start()

    def log(self, msg):
        print("~~~~~~ Address Server ~~~~~~ : ", msg)

    def run(self):
        while True:
            conn, _ = self.socket.accept()
            # Start new thread to handle client
            new_thread = threading.Thread(target=self.handle_client,
                                          args=(conn,))
            self.log("New connection!")
            new_thread.start()

    def handle_client(self, tcpCliSock):
        """Handle receiving and sending"""
        data = tcpCliSock.recv(1024).decode()
        msg_type = data[0].lower()
        if msg_type == "n":  # new node
            node = json.loads(data[1:])
            self.register(node)
            # Broadcast to the rest of the nodes
            self.broadcast_message("n" + json.dumps({"nodes": self.nodes}))
            tcpCliSock.close()

    def register(self, node):
        node_type = node["type"]
        node_address = node["address"]

        self.nodes.append(node)
        self.log(f" Registered new {node_type} : {node_address}")

        return True

    def broadcast_message(self, msg):
        """Broadcast the message to peers"""
        with ThreadPoolExecutor(max_workers=len(self.nodes)) as executor:
            for node in self.nodes:
                executor.submit(self._send_message, msg, tuple(node["address"]))

    @staticmethod
    def _send_message(msg, address):
        """Send address to a single node"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(address)
            client.sendall(msg.encode())
        finally:
            client.close()


if __name__ == '__main__':
    AddressServer()
