import copy
import random
import sys
import time
from block import Block
from transaction import Transaction
from blockchain import Blockchain, TARGET
from algorithms import *
from node import Node, Listener
import threading

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
            proof = json.loads(data[1:])["blk_proof"]
            # stop mining
            self.node.stop_mine.set()
            # verify it if all transactions inside the block are valid
            blk = Block.deserialize(blk_json)
            transactions = blk.transactions
            if self.node.check_final_balance(transactions):
                success_add = self.node.blockchain.add(blk, proof)
                for tx in transactions:
                    if tx in self.node.unconfirmed_transactions:
                        self.node.unconfirmed_transactions.remove(tx)
                self.node.log(f"Added a new block received: {success_add} with {len(transactions)} transactions")
                self.node.blockchain.print()

            else:
                self.node.log("Invalid transactions in the new block received! ")
            self.node.stop_mine.clear()

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
            headers = self.node.get_blk_headers()
            msg = json.dumps({
                "headers": headers
            })
            tcp_client.sendall(msg.encode())
            self.node.log(">>> send headers to SPV")

        elif msg_type == "m":  # request for balance by spvclient
            self.node.log("======= Receive request for balance (SPV)")
            identifier = json.loads(data[1:])["identifier"]
            msg = json.dumps(self.node.get_balance(identifier))
            tcp_client.sendall(msg.encode())
            self.node.log(f">>> send balance = {msg} to SPV")

        tcp_client.close()


class Miner(Node):

    def __init__(self, privkey, pubkey, address, listener=MinerListener):
        print(f"address: {address}")
        super().__init__(privkey, pubkey, address, listener)
        self.unconfirmed_transactions = []  # data yet to get into blockchain
        self.blockchain = Blockchain()


        #locks
        self.chain_lock = threading.RLock()
        self.tx_lock = threading.RLock()
        self.stop_mine = threading.Event()  # a indicator for whether to continue mining


    @classmethod
    def new(cls, address):
        """Create new Miner instance"""
        signing_key = ecdsa.SigningKey.generate()
        verifying_key = signing_key.get_verifying_key()
        privkey = signing_key
        pubkey = verifying_key
        return cls(privkey, pubkey, address)

    def get_own_balance(self):
        balance = self.get_balance(stringify_key(self.pubkey))
        #self.log(f"balance = {balance}")
        return balance

    """ inquiry """

    def get_transaction_proof(self, tx_hash):
        """Get proof of transaction given transaction hash"""
        # ask the blockchain to search each block to obtain possible proof from merkle tree
        proof = self.blockchain.get_proof(tx_hash)
        return proof

    def get_balance(self, identifier):
        """Get balance given identifier ie. pubkey"""
        balance = self.blockchain.get_balance()
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
        if self.get_balance(stringify_key(self.pubkey)) >= amount:
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
        else:
            self.log("Not enough balance in your account!")

    def add_transaction(self, tx):
        """Add transaction to the pool of unconfirmed transactions"""
        if not tx.validate():
            raise Exception("New transaction failed signature verification.")
        tx_json = tx.serialize()

        self.unconfirmed_transactions.append(tx_json)
        self.log(f"{len(self.unconfirmed_transactions)} number of unconfirmed transactions")

    """ Mining """
    def mine(self):
        if self.peers is None and self.stop_mine.is_set():
            return None

        self.log(f"mining on block height of {self.blockchain.last_node.block.blk_height} ....\n....\n")
        time.sleep(1)
        tx_collection = self.get_tx_pool()

        if not self.check_final_balance(tx_collection):
            raise Exception("abnormal transactions!")
            return None

        new_block, prev_block = self.create_new_block(tx_collection)
        proof = self.proof_of_work(new_block, self.stop_mine)
        if proof is None:
            return None

        self.blockchain.add(new_block, proof)
        for tx in tx_collection:
            self.unconfirmed_transactions.remove(tx)

        self.broadcast_blk(new_block, proof)
        self.log(" Mined a new block +$$$$$$$$")
        print("""
                    |---------|
                    |   block   |
                    |---------|
        """)
        self.blockchain.print()

        return new_block, prev_block

    def get_tx_pool(self):
        pool = copy.deepcopy(self.unconfirmed_transactions)
        return pool

    def get_last_node(self):
        return self.blockchain.last_node

    def create_new_block(self, tx_collection):
        last_node = self.get_last_node()

        new_block = Block(transactions=tx_collection,
                        timestamp=time.time(),
                        previous_hash=last_node.block.hash,
                        miner=self.pubkey)

        return new_block, last_node.block

    def broadcast_blk(self, new_blk, proof):
        blk_json = new_blk.serialize()
        self.broadcast_message("b" + json.dumps({"blk_json": blk_json,
                                                 "blk_proof": proof}))
        self.broadcast_message("h" + json.dumps({"blk_hash": new_blk.compute_hash(),
                                                 "blk_header": new_blk.header
                                                 }))

    def proof_of_work(self, block, stop_mine):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies our difficulty criteria.
        """
        start = time.time()
        computed_hash = block.compute_hash()

        while not computed_hash < TARGET:
            if self.stop_mine.is_set():
                # self.log("Stop Mining as others have found the block")
                return None
            random.seed(time.time())
            block.nonce = random.randint(0, 100000000)
            computed_hash = block.compute_hash()

        end = time.time()
        self.log(f"Found proof = {computed_hash} < TARGET in {end - start} seconds")
        return computed_hash

    def check_final_balance(self, transactions):
        """
            Check balance state if transactions were applied.
            The balance of an account is checked to make sure it is larger than
            or equal to the spending transaction amount.
        """
        balance = self.blockchain.get_balance()

        for tx_json in transactions:
            recv_tx = Transaction.deserialize(tx_json)
            # Sender must exist so if it doesn't, return false
            sender = stringify_key(recv_tx.sender)
            receiver = stringify_key(recv_tx.receiver)
            if sender not in balance:
                return False
            # Create new account for receiver if it doesn't exist
            if receiver not in balance:
                balance[receiver] = 0
            balance[sender] -= recv_tx.amount
            balance[receiver] += recv_tx.amount
            # Negative balance, return false
            if balance[sender] < 0 or balance[receiver] < 0:
                print("Negative balance can exist!")
                return False
        return True






if __name__ == '__main__':
    miner = Miner.new(("localhost", int(sys.argv[1])))
    time.sleep(5)
    while True:
        time.sleep(2)
        peer = random.choice(miner.peers)

        # make transaction

        if peer is None:
            print("No peers known")

        else:

            miner.mine()
            miner.get_own_balance()

            # peer = random.choice(miner.find_peer_by_type("SPVClient"))
            # peer_pubkey = peer["pubkey"]
            # miner.make_transaction(peer_pubkey, 1)








