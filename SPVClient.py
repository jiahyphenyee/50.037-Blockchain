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
            nodes = json.loads(data[1:])["nodes"]
            self.node.set_peers(nodes)
        elif msg_type == "h":  # new block header

            header_info = json.loads(data[1:])
            self.node.add_block_header(header_info)

        tcp_client.close()


class SPVClient(Node):
    def __init__(self, privkey, pubkey, address, listener=SPVCliListener):
        super().__init__(privkey, pubkey, address, listener)
        self.blk_headers_by_hash = {}

    @classmethod
    def new(cls, address):
        signing_key = ecdsa.SigningKey.generate()
        verifying_key = signing_key.get_verifying_key()
        privkey = signing_key
        pubkey = verifying_key
        return cls(privkey, pubkey, address)

    def add_blk_header(self, header_info):
        self.blk_headers_by_hash[header_info["blk_hash"]] = header_info["blk_header"]

    def get_blk_headers(self):
        """ Get headers for all blocks"""
        blk_headers = {}
        req = "x"
        replies = self.broadcast_request(req)
        reply = SPVClient._process_replies(replies)
        headers = json.loads(reply)["headers"]
        for blk_hash, header in headers.values():
            blk_headers[blk_hash] = header

        return blk_headers

    def make_transaction(self, receiver, amount, comment=""):
        """Create a new transaction"""
        if self.get_balance(stringify_key(self.pubkey)) >= amount:
            tx = Transaction.new(sender=self._keypair[1],
                                 receiver=receiver,
                                 amount=amount,
                                 comment="",
                                 key=self._keypair[0])
            tx_json = tx.serialize()
            print(f"{self.type} at {self.address} made a new transaction")
            msg = "t" + json.dumps({"tx_json": tx_json})
            self.broadcast_message(msg)
            return tx
        else:
            self.log("Not enough balance in your account!")

    def request_balance(self):
        """Request balance from network"""
        req = "m" + json.dumps({"identifier": stringify_key(self.pubkey)})
        replies = self.broadcast_request(req)
        return int(SPVClient._process_replies(replies))

    def verify_user_transaction(self, tx):
        """Verify that transaction is in blockchain"""
        tx_json = tx.serialize()
        req = "r" + json.dumps({"tx_json": tx_json})
        replies = self.broadcast_request(req)
        valid_reply = SPVClient._process_replies(replies)
        blk_hash = valid_reply["blk_hash"]
        proof = valid_reply["merkle_path"]
        last_blk_hash = valid_reply["last_blk_hash"]
        # Transaction not in blockchain
        if proof is None:
            return False

        if (blk_hash not in self.blk_headers_by_hash
                or last_blk_hash not in self.blk_headers_by_hash):
            return False
        blk_header = self.blk_headers_by_hash[blk_hash]
        if not verify_proof(tx, proof, blk_header["root"]):
            # Potential eclipse attack
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
        return json.loads(valid_reply)


if __name__ == "__main__":
    time.sleep(2)
    SPVClient.new(("localhost", int(sys.argv[1])))
    time.sleep(5)









