import copy
import random
import sys
import time
from block import Block
from transaction import Transaction
from blockchain import Blockchain, TARGET
from algorithms import *
from node import Node, Listener

"""
Design and implement a Miner class realizing miner's functionalities. Then, implement a simple simulator with miners running Nakamoto consensus and making transactions:

    Adjust the TARGET (global and static) parameter, such that on average new blocks arrive every few (2-5) seconds.
    A miner who found a new block should be rewarded with 100 SUTDcoins.
    Introduce random transactions, such that miners (with coins) can send transactions to other miners.
    Make sure that coins cannot be double-spent.
        consider the addr:balance model and the UTXO model. What are pros and cons?
        do you need to modify (why, if so) the transaction format introduced in the first week? Hint: yes, you need.
    Extend the verification checks.
    Simulate miners competition..
"""


class MinerListener(Listener):
    """Miner's Listener class"""

    def handle_by_msg_type(self, data, tcp_client):
        """Handle client data based on msg_type"""
        msg_type = data[0].lower()
        if msg_type == "n":  # updates on network nodes
            self.node.log("======= Receive updates on network nodes")
            nodes = json.loads(data[1:])["nodes"]
            self.node.set_peers(nodes)

        elif msg_type == "b":  # new block
            self.node.log("======= Receive new block from peer")
            blk_json = json.loads(data[1:])["blk_json"]
            self.log(blk_json)
            # stop mining
            self.node.set_stop_mine(True)
            # verify it if all transactions inside the block are valid
            blk = Block.deserialize(blk_json)
            transactions = blk.transactions
            if self.node.check_final_balance(transactions):
                self.node.blockchain.add_block(blk)
                self.node.log("Added a new block received")
            else:
                self.node.log("Invalid transactions in the new block received!")

        elif msg_type == "t":  # new transaction
            self.node.log("======= Receive new transaction from peer")
            tx_json = json.loads(data[1:])["tx_json"]
            self.node.add_transaction(Transaction.deserialize(tx_json))

        elif msg_type == "r":  # request for transaction proof
            self.node.log("======= Receive request for transaction proof")
            tx_json = json.loads(data[1:])["tx_json"]
            proof = self.node.get_transaction_proof(Transaction.deserialize(tx_json))
            if proof is None:
                msg = "nil"
            else:
                msg = json.dumps({
                    "blk_hash": proof[0],
                    "merkle_path": proof[1],
                    "last_blk_hash": proof[3],

                })
            tcp_client.sendall(msg.encode())

        elif msg_type == "x":  # request for headers by spvclient
            self.node.log("======= Receive request for headers (SPV)")
            msg = json.dumps({
                "headers": self.node.get_blk_header()
            })
            tcp_client.sendall(msg.encode)

        tcp_client.close()


class Miner(Node):

    def __init__(self, privkey, pubkey, address, listener=MinerListener):
        print(f"address: {address}")
        super().__init__(privkey, pubkey, address, listener)
        self.unconfirmed_transactions = []  # data yet to get into blockchain
        self.blockchain = Blockchain()
        self._stop_mine = False  # a indicator for whether to continue mining


    @classmethod
    def new(cls, address):
        """Create new Miner instance"""
        signing_key = ecdsa.SigningKey.generate()
        verifying_key = signing_key.get_verifying_key()
        privkey = signing_key
        pubkey = verifying_key
        return cls(privkey, pubkey, address)

    def set_stop_mine(self, stop_mining):
        self._stop_mine = stop_mining
    """ inquiry """

    def get_transaction_proof(self, tx_hash):
        """Get proof of transaction given transaction hash"""
        # ask the blockchain to search each block to obtain possible proof from merkle tree
        proof = self.blockchain.get_proof(tx_hash)
        return proof

    def get_balance(self, identifier):
        """Get balance given identifier ie. pubkey"""
        balance = self.blockchain.get_balance()
        self.log(balance)
        if identifier not in balance:
            return 0
        return balance[identifier]

    def get_blk_headers(self):
        """Get headers of blocks of the longest chain"""
        blk_headers = {}
        for block in self.blockchain.get_blks():
            blk_headers[block.compute_hash()] = block.header

        return blk_headers

    """ Transactions """

    def make_transaction(self, receiver, amount, comment=""):
        """Create a new transaction"""
        tx = Transaction.new(sender=self._keypair[1],
                             receiver=obtain_key_from_string(receiver),
                             amount=amount,
                             comment="",
                             key=self._keypair[0])
        tx_json = tx.serialize()
        self.log(" Made a new transaction")
        self.add_transaction(tx)
        msg = "t" + json.dumps({"tx_json": tx_json})
        self.broadcast_message(msg)
        return tx

    def add_transaction(self, tx):
        """Add transaction to the pool of unconfirmed transactions"""
        if not tx.validate():
            raise Exception("New transaction failed signature verification.")
        self.unconfirmed_transactions.append(tx.serialize())
        self.log(f"{len(self.unconfirmed_transactions)} number of unconfirmed transactions")

    """ Mining """

    def mine(self):

        # if not self.check_final_balance(tx_collection):
        #     raise Exception("abnormal transactions!")
        #     return None

        new_block, prev_block = self.create_new_block(self.get_tx_pool())

        proof = self.proof_of_work(new_block)
        if proof is None:
            return None

        self.blockchain.add_block(new_block, proof)
        self.broadcast_blk(new_block)
        self.unconfirmed_transactions = []
        self.log(" Mined a new block +$$$$$$$$")
        self.set_stop_mine(False)

        return new_block, prev_block

    def get_tx_pool(self):
        return self.unconfirmed_transactions

    def get_last_node(self):
        return self.blockchain.last_node

    def create_new_block(self, tx_collection):
        last_node = self.get_last_node()

        new_block = Block(transactions=tx_collection,
                        timestamp=time.time(),
                        previous_hash=last_node.block.hash,
                        miner=self.pubkey)
        return new_block, last_node.block

    def broadcast_blk(self, new_blk):
        blk_json = new_blk.serialize()
        self.broadcast_message("b" + json.dumps({"blk_json": blk_json}))
        self.broadcast_message("h" + json.dumps({"blk_hash": new_blk.compute_hash(),
                                                 "blk_header": new_blk.header
                                                 }))

    def proof_of_work(self, block):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()

        while not computed_hash < TARGET:
            if self.stop_mine:
                return None
            block.nonce += 1
            computed_hash = block.compute_hash()
        self.log(f"Found proof = {computed_hash} < TARGET")
        return computed_hash

    def check_final_balance(self, transactions):
        """
            Check balance state if transactions were applied.
            The balance of an account is checked to make sure it is larger than
            or equal to the spending transaction amount.
        """
        balance = self.blockchain.get_balance

        for tx_json in transactions:
            recv_tx = Transaction.deserialize(tx_json)
            # Sender must exist so if it doesn't, return false
            if recv_tx.sender not in balance:
                return False
            # Create new account for receiver if it doesn't exist
            if recv_tx.receiver not in balance:
                balance[recv_tx.receiver] = 0
            balance[recv_tx.sender] -= recv_tx.amount
            balance[recv_tx.receiver] += recv_tx.amount
            # Negative balance, return false
            if balance[recv_tx.sender] < 0 or balance[recv_tx.receiver] < 0:
                print("Negative balance can exist!")
                return False
        return True

    def test_connection(self):
        msg = "peer"
        self.broadcast_message(msg)


def get_miner_balance(miner,identifier):
    balance = miner.get_balance(stringify_key(identifier))
    miner.log(f"balance = {balance}")


if __name__ == '__main__':
    miner = Miner.new(("localhost", int(sys.argv[1])))
    time.sleep(5)
    while True:
        time.sleep(5)
        peer = random.choice(miner.peers)

        if peer is None:
            print("No peers in the network")

        else:
            peer_pubkey = peer["pubkey"]
            miner.make_transaction(peer_pubkey, 1)
            get_miner_balance(miner, identifier=miner.pubkey)

        if len(miner.unconfirmed_transactions) > 5:
            miner.mine()
            get_miner_balance(miner, identifier=miner.pubkey)





