"""A Server that provides a list of addresses of nodes"""

from concurrent.futures import ThreadPoolExecutor
import threading
import socket
import json

import algorithms


class DNSServer:

    HOST = "localhost"
    PORT = 6666

    def __init__(self):
        print("Starting DNS server..")
        self._addr_list = []

        # TCP socket configuration
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("localhost", DNSServer.PORT))
        self.socket.listen(5)
        threading.Thread(target=self.run).start()

    def run(self):
        while True:
            conn, _ = self.socket.accept()
            # Start new thread to handle client
            new_thread = threading.Thread(target=self.handle_client,
                                          args=[conn])
            print("New connection!")
            new_thread.start()

    def handle_client(self, tcpCliSock):
        """Handle receiving and sending"""
        data = tcpCliSock.recv(1024).decode()
        prot = data[0].lower()
        if prot == "a":
            # Receive a request for addresses
            msg = "a" + json.dumps(
                {"addresses": self._addr_list})
            tcpCliSock.sendall(msg.encode())
            tcpCliSock.close()
        elif prot == "n":
            node_address = json.loads(data[1:])
            node_address["address"] = tuple(node_address["address"])
            self.add_address(node_address)
            # Broadcast to the rest of the nodes
            self.broadcast_address(
                "n" + json.dumps(node_address))
            tcpCliSock.close()

    def add_address(self, address):
        """Add address to list if not already in list"""
        if address not in self._addr_list:
            self._addr_list.append(address)

    def broadcast_address(self, req):
        """Broadcast the new address to peers"""
        with ThreadPoolExecutor(max_workers=len(self.addresses)) as executor:
            for node in self.addresses:
                executor.submit(self._send_address,
                                req, node['address'])

    @staticmethod
    def _send_address(msg, address):
        """Send address to a single node"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(address)
            client.sendall(msg.encode())
        finally:
            client.close()

if __name__ == "__main__":
    DNSServer()