
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
        # msg_type = data[0].lower()
        # if msg_type == "h":  # new block header
        #
        #     header_info = json.loads(data[1:])
        #     self.node.add_block_header(header_info)
        #
        # tcp_client.close()


class SPVClient(Node):
    def __init__(self, privkey, pubkey, address, listener=SPVCliListener):
        super().__init__(privkey, pubkey, address, listener)
        self.blk_headers_by_hash = self.get_blk_headers

    @classmethod
    def new(cls, address):
        signing_key = ecdsa.SigningKey.generate()
        verifying_key = signing_key.get_verifying_key()
        privkey = signing_key.to_string().hex()
        pubkey = verifying_key.to_string().hex()
        return cls(privkey, pubkey, address)

    def get_blk_headers(self, prev_hash=None):
        """ Get headers for all blocks"""
        blk_headers = {}
        req = "h" + json.dumps({"identifier": self.pubkey, "prev-hash": prev_hash})
        reply = self.broadcast_request(req)
        headers = json.loads(reply)["headers"]
        for blk_hash, header in headers.values():
            blk_headers[blk_hash] = header

        return blk_headers

    def make_transaction(self, receiver, amount, comment=""):
        """Create a new transaction"""
        tx = Transaction.new(self.pubkey, receiver, amount, comment, self.privkey)
        tx_json = tx.serialize()
        print(self.address, " made a new transaction")
        msg = "t" + json.dumps({"tx_json": tx_json})
        self.broadcast_message(msg)
        return tx

    def verify_user_transaction(self, tx_hash):
        """Verify that transaction is in blockchain"""
        req = "r" + json.dumps({"tx_hash": tx_hash})
        replies = self.broadcast_request(req)
        valid_reply = SPVClient._process_replies(replies)
        blk_hash = valid_reply["blk_hash"]
        proof = valid_reply["proof"]
        last_blk_hash = valid_reply["last_blk_hash"]
        # Transaction not in blockchain
        if proof is None:
            return False

        if (blk_hash not in self.blk_headers_by_hash
                or last_blk_hash not in self.blk_headers_by_hash):
            return False
        tx_json = self.transactions[tx_hash]
        blk_header = self.blk_headers_by_hash[blk_hash]
        if not verify_proof(tx_json, proof, blk_header["root"]):
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
    SPVClient.new(("localhost", 6666))






