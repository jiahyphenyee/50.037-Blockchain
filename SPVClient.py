import sys
import time

from algorithms import *
from node import Node, Listener
from merkle_tree import verify_proof
from transaction import Transaction

'''
Design and implement an SPVClient class. SPV clients should implement a simple SPV logic, i.e., they should:

    have their key pairs associated
    be able to receive block headers (not full blocks)
    be able to receive transactions (with their presence proofs) and verify them
    be able to send transactions

Integrate your implementation with your simulator from the previous exercise. Test your implementation.
'''


class SPVCliListener(Listener):
    """SPV client's Listener class"""

    def handle_by_msg_type(self, data, tcp_client):
        """Handle client data based on msg_type"""
        msg_type = data[0].lower()
        if msg_type == "n":  # updates on network nodes
            self.node.log("======= Receive updates on network nodes")
            nodes = json.loads(data[1:])["nodes"]
            self.node.set_peers(nodes)
        elif msg_type == "h":  # new block header
            self.node.log("======= Receive new header from peer")
            header_info = json.loads(data[1:])
            self.node.add_blk_header(header_info)


        tcp_client.close()


class SPVClient(Node):
    def __init__(self, privkey, pubkey, address, listener=SPVCliListener):
        super().__init__(privkey, pubkey, address, listener)
        self.blk_headers_by_hash = {}
        self.balance = 0
        self.interested_txn = []
        self.my_unconfirmed_txn = []

    @classmethod
    def new(cls, address):
        signing_key = ecdsa.SigningKey.generate()
        verifying_key = signing_key.get_verifying_key()
        privkey = signing_key
        pubkey = verifying_key
        return cls(privkey, pubkey, address)

    def add_blk_header(self, header_info):
        header = header_info["blk_header"]
        if header["prev_hash"] in self.blk_headers_by_hash:
            blk_hash = header_info["blk_hash"]
            self.blk_headers_by_hash[blk_hash] = header
            self.log(f"New Header hash: {blk_hash}")
        else:
            self.log("Header with non-existing prev-hash. Do you want to request headers?")

    def get_blk_headers(self):
        """ Get headers for all blocks"""
        self.log("Requesting for block headers from full node")
        blk_headers = {}
        req = "x"
        replies = self.broadcast_request(req)
        reply = SPVClient._process_replies(replies)
        headers = reply["headers"]
        self.log("====== Received headers from peers: {headers}")
        for blk_hash, header in headers.items():
            blk_headers[blk_hash] = header
        self.blk_headers_by_hash = blk_headers
        self.log(f"current headers: {self.blk_headers_by_hash}")

    def make_transaction(self, receiver, amount, comment=""):
        """Create a new transaction"""
        self.update_my_transactions()

        if self.balance >= amount:
            tx = Transaction.new(sender=self._keypair[1],
                                 receiver=obtain_key_from_string(receiver),
                                 amount=amount,
                                 comment="",
                                 key=self._keypair[0],
                                 nonce=self.request_nonce()+1+len(self.my_unconfirmed_txn))
            tx_json = tx.serialize()
            self.log("Made a new transaction")
            self.log(tx_json)
            msg = "t" + json.dumps({"tx_json": tx_json})
            self.interested_txn.append(tx_json)
            self.my_unconfirmed_txn.append(tx_json)
            self.broadcast_message(msg)

            return tx
        else:
            self.log("Not enough balance in your account!")

    def request_nonce(self):
        """Request nonce from network"""
        self.log(f"Requesting nonce from full node..")
        req = "c" + json.dumps({"identifier": stringify_key(self.pubkey)})
        replies = self.broadcast_request(req)
        reply = float(SPVClient._process_replies(replies))
        self.log(f"Get Nonce = {reply}")
        return reply

    def request_balance(self):
        """Request balance from network"""
        self.log(f"Requesting Balance from full node..")
        req = "m" + json.dumps({"identifier": stringify_key(self.pubkey)})
        replies = self.broadcast_request(req)
        reply = float(SPVClient._process_replies(replies))
        self.balance = reply
        self.log(f"Get Balance = {reply}")
        return reply

    def update_my_transactions(self):
        for tx_json in self.my_unconfirmed_txn:
            if self.verify_user_transaction(tx_json):
                self.my_unconfirmed_txn.remove(tx_json)

    def verify_user_transaction(self, tx_json):
        """Verify that transaction is in blockchain"""
        self.log(f"Requesting Proof from full blockchain node")
        req = "r" + json.dumps({"tx_json": tx_json})
        replies = self.broadcast_request(req)
        valid_reply = SPVClient._process_replies(replies)
        if valid_reply is None:
            return False
        blk_hash = valid_reply["blk_hash"]
        proof = valid_reply["merkle_path"]
        # Transaction not in blockchain
        if proof is None:
            self.log(f"No Proof Found!")
            return False

        if blk_hash not in self.blk_headers_by_hash:
            self.log(f"Block Hash Not Found!")
            return False
        blk_header = self.blk_headers_by_hash[blk_hash]
        if not verify_proof(Transaction.deserialize(tx_json), proof, blk_header["root"]):
            # Potential eclipse attack
            self.log("Transaction proof verification failed.")
            raise Exception("Transaction proof verification failed.")
        return True

    # STATIC METHODS

    @staticmethod
    def _process_replies(replies):
        """Process the replies from sending requests"""
        replies = [rep for rep in replies if rep.lower() != "spv"]
        if not replies:
            raise Exception("No miner replies for request.")
        # Assume majority reply is valid
        valid_reply = max(replies, key=replies.count)
        print(f"valid reply: {valid_reply}")

        if valid_reply != "nil":
            return json.loads(valid_reply)
        else:
            print(f"No Valid Reply")
            return None


if __name__ == "__main__":
    time.sleep(2)
    SPVClient.new(("localhost", int(sys.argv[1])))
    time.sleep(5)









