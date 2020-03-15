from monsterurl import get_monster
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
'''
All Nodes include the routing function to participate in the network.
All nodes validate and propagate transactions and blocks, and discover and maintain connections to peers.
For simplicity, we assume the address list of listening nodes are already available to each nodes
'''


class Node:
    def __init__(self, privkey, pubkey, address, listener):
        self._keypair = (privkey, pubkey)
        self.address = address
        self.peers = []
        self.listener = listener(address, self)
        # start the listener thread to communicate with network users
        threading.Thread(target=self._listener.run).start()
        self.run()
        print(" New node running on address: ", self.address)

    def set_peers(self, peers):
        """We will use this to set all available peers at once"""
        self.peers = peers

    def find_peer_by_pubkey(self, pubkey):
        """Find peer with particular pubkey"""
        for peer in self.peers:
            if peer["pubkey"] == pubkey:
                return peer
        return None

    """Uni-cast communication"""
    @staticmethod
    def _send_request(req, address):
        """Send request to a single node"""
        try:
            cliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliSock.connect(address)
            cliSock.sendall(req.encode())
            reply = cliSock.recv(8196).decode()
        finally:
            cliSock.close()
        return reply

    @staticmethod
    def _send_message(msg, address):
        """Send transaction to a single node"""
        try:
            cliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliSock.connect(address)
            cliSock.sendall(msg.encode())
        finally:
            cliSock.close()

    """Broad-cast communication"""

    def broadcast_message(self, msg):
        """Broadcast the message to peers"""
        # Assume that peers are all nodes in the network
        # (of course, not practical IRL since its not scalable)
        if not self._peers:
            raise Exception("Not connected to network.")
        with ThreadPoolExecutor(max_workers=5) as executor:
            for peer in self._peers:
                executor.submit(Node._send_message, msg, peer['address'])

    def broadcast_request(self, req):
        """Broadcast the request to peers"""
        if not self._peers:
            raise Exception("Not connected to network.")
        executor = ThreadPoolExecutor(max_workers=5)
        futures = [
            executor.submit(Node._send_request, req, peer['address'])
            for peer in self._peers
        ]
        executor.shutdown(wait=True)
        replies = [future.result() for future in futures]
        return replies


class Listener:

    """Node listener thread to communicate with network users"""
    def __init__(self, server_addr):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(server_addr)
        self.socket.listen(5)

    def run(self):
        """Accepting connection"""
        while True:
            conn, addr = self.socket.accept()
            # Start new thread to handle client
            new_thread = threading.Thread(self.handle_client, [conn])
            print("New Connection from:", addr)
            new_thread.start()

    def handle_client(self, tcpCliSock):
        """Handle receiving and sending"""
        data = tcpCliSock.recv(8196).decode()
        self.handle_client_data(data, tcpCliSock)

    def handle_client_data(self, data, tcpCliSock):
        """To be overwritten when extending"""
        raise Exception("Override handle_client_data when extending "
                        + "from _NetNodeListener")


if __name__ == "__main__":
    pass
