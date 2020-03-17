
from algorithms import *
from addr_server import *
from concurrent.futures import ThreadPoolExecutor
'''
All Nodes include the routing function to participate in the network.
All nodes validate and propagate transactions and blocks, and discover and maintain connections to peers.
For simplicity, we assume the address list of listening nodes are already available to each nodes
'''


class Node:

    ADDR_SERVER=("localhost", 6666)

    def __init__(self, privkey, pubkey, address, listener):
        self._keypair = (privkey, pubkey)
        self.address = address
        self.register_node()
        self.peers = []
        self.listener = listener(address, self)
        # start the listener thread to communicate with network users
        threading.Thread(target=self.listener.run).start()
        self.log_prefix = f"{self.type} at {self.address}: "
        self.log("Join the network")

    @property
    def pubkey(self):
        return self._keypair[1]

    @property
    def type(self):
        return self.__class__.__name__

    def log(self, msg):
        print(self.log_prefix, msg)

    def set_peers(self, peers):
        my_peers = []
        for peer in peers:
            if peer["address"] != self.address:
                my_peers.append(peer)
        self.peers = my_peers

    def register_node(self):
        msg = "n" + json.dumps({
            "type": self.type,  # Miner, SPVClient
            "address": self.address,
            "pubkey": stringify_key(self.pubkey)
        })
        self._send_message(msg, Node.ADDR_SERVER)

    def find_peer_by_type(self, node_type):

        for peer in self.peers:
            if peer["type"] == node_type:
                return peer
        return None

    def find_peer_by_pubkey(self, pubkey):
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
        if not self.peers:
            raise Exception("Not connected to network.")
        with ThreadPoolExecutor(max_workers=5) as executor:
            for peer in self.peers:
                executor.submit(Node._send_message, msg, tuple(peer['address']))

    def broadcast_request(self, req):
        """Broadcast the request to peers"""
        if not self.peers:
            raise Exception("Not connected to network.")
        executor = ThreadPoolExecutor(max_workers=5)
        futures = [
            executor.submit(Node._send_request, req, tuple(peer['address']))
            for peer in self.peers
        ]
        executor.shutdown(wait=True)
        replies = [future.result() for future in futures]
        return replies


class Listener:

    """Node listener thread to communicate with network users"""
    def __init__(self, server_addr, node):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(server_addr)
        self.socket.listen(5)
        self.node = node

    def run(self):
        """Accepting connection"""
        while True:
            conn, addr = self.socket.accept()
            # Start new thread to handle client
            new_thread = threading.Thread(target=self.handle_client, args=(conn,))

            new_thread.start()

    def handle_client(self, tcp_client):
        """Handle receiving and sending"""
        data = tcp_client.recv(8196).decode()
        self.handle_by_msg_type(data, tcp_client)

    def handle_by_msg_type(self, data, tcp_client):
        """To be overwritten when extending"""
        raise Exception("Override handle_by_type when extending "
                        + "from _NetNodeListener")


