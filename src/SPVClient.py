import copy
import json
import threading
import sys
import time
import random
import os.path
import ecdsa
import algorithms

from src.node import Node, Listener
from .block import Block
from .merkle_tree import verify_proof
from src.transaction import Transaction

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

    def handle_client_data(self, data, client_sock):
        """Handle client data based on protocol indicator"""
        prot = data[0].lower()
        if prot == "n":
            # Sent by the central server when a new node joins
            address = json.loads(data[1:])
            # print(f"{self._worker.name} added a node to their network.")
            self._worker.add_peer(address)
            client_sock.close()
        elif prot == "h":
            # Receive new block header
            block_header = json.loads(data[1:])
            client_sock.close()
            self._worker.add_block_header(block_header)
        elif prot == "t":
            # Receive new transaction
            tx_json = json.loads(data[1:])["tx_json"]
            client_sock.close()
            self._worker.add_transaction(tx_json)
        elif prot in "rx":
            # Receive request for transaction proof or balance
            # Send "spv" back so client can exclude this reply
            client_sock.sendall("spv".encode())
            client_sock.close()
        else:
            client_sock.close()


class SPVClient(Node):
    def __init__(self, privkey, pubkey, address, listener=SPVCliListener):
        super().__init__(privkey, pubkey, address, listener)
        self.transactions = {}
        genesis = Block.get_genesis()
        genesis_hash = algorithms.hash(genesis.header)
        self.blk_headers_by_hash = {genesis_hash: genesis.header}

    @classmethod
    def new(cls, address):
        signing_key = ecdsa.SigningKey.generate()
        verifying_key = signing_key.get_verifying_key()
        privkey = signing_key.to_string().hex()
        pubkey = verifying_key.to_string().hex()
        return cls(privkey, pubkey, address)


    def get_blk_headers(self):
        req = "x" + json.dumps({"identifier": self.pubkey})
        replies = self.broadcast_request(req)
        return int(SPVClient._process_replies(replies))
        return copy.deepcopy(list(self.blk_headers_by_hash.values()))


    def make_transaction(self, receiver, amount, comment=""):
        """Create a new transaction"""
        trans = Transaction.new(self.pubkey, receiver, amount, comment, self.privkey)
        tx_json = trans.to_json()
        msg = "t" + json.dumps({"tx_json": tx_json})
        self.broadcast_message(msg)
        return trans

    def add_transaction(self, tx_json):
        """Add transaction to the pool of transactions"""
        recv_tx = Transaction.from_json(tx_json)
        if not recv_tx.verify():
            raise Exception("New transaction failed signature verification.")
        if self.pubkey not in [recv_tx.sender, recv_tx.receiver]:
            # Transaction does not concern us, discard it
            return
        tx_hash = algo.hash1(tx_json)
        self._trans_lock.acquire()
        try:
            self.transactions[tx_hash] = tx_json
        finally:
            self._trans_lock.release()

    def add_block_header(self, header):
        """Add block header to dictionary"""
        header_hash = algorithms.hash(header)
        if header_hash >= Block.TARGET:
            raise Exception("Invalid block header hash.")
        self._blkheader_lock.acquire()
        try:
            if header["prev_hash"] not in self.blk_headers_by_hash:
                raise Exception("Previous block does not exist.")
            self.blk_headers_by_hash[header_hash] = header
        finally:
            self._blkheader_lock.release()

    def request_balance(self):
        """Request balance from network"""
        req = "x" + json.dumps({"identifier": self.pubkey})
        replies = self.broadcast_request(req)
        return int(SPVClient._process_replies(replies))

    def verify_transaction_proof(self, tx_hash):
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
        # Assume majority reply is not lying and that two hash checks
        # are sufficient (may not be true IRL)
        self._blkheader_lock.acquire()
        self._trans_lock.acquire()
        try:
            if (blk_hash not in self.blk_headers_by_hash
                    or last_blk_hash not in self.blk_headers_by_hash):
                return False
            tx_json = self.transactions[tx_hash]
            blk_header = self.blk_headers_by_hash[blk_hash]
            if not verify_proof(tx_json, proof, blk_header["root"]):
                # Potential eclipse attack
                raise Exception("Transaction proof verification failed.")
        finally:
            self._blkheader_lock.release()
            self._trans_lock.release()
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


def spv_main_send_transaction(spv):
    """Used in main to send one transaction"""
    balance = spv.request_balance()
    if balance > 10:
        peer_index = random.randint(0, len(spv.peers) - 1)
        chosen_peer = spv.peers[peer_index]
        created_tx = spv.create_transaction(chosen_peer["pubkey"], 10)
        tx_json = created_tx.to_json()
        tx_hash = algo.hash1(tx_json)
        print(f"SPV {spv.name} sent {tx_hash} to {chosen_peer['pubkey']}")


def spv_main_verify_tx(spv):
    """Used in main to verify transaction proof"""
    transactions = spv.transactions
    if transactions:
        i = random.randint(0, len(transactions) - 1)
        tx_hash = algo.hash1(transactions[i])
        tx_in_bc = spv.verify_transaction_proof(tx_hash)
        print(f"SPV {spv.name} check {tx_hash} in blockchain: {tx_in_bc}")




def main():
    """Main function"""
    spv = SPVClient.new(("127.0.0.1", int(sys.argv[1])))
    spv.startup()
    while not os.path.exists("mine_lock"):
        time.sleep(0.5)
    while True:
        # Request transaction proof
        spv_main_verify_tx(spv)
        time.sleep(1)
        # Create new transaction
        spv_main_send_transaction(spv)
        time.sleep(8)


if __name__ == "__main__":
    main()
        





