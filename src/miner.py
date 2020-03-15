import copy
import random
import threading
import json
from src.block import Block
from Transactions import Transaction
from src.blockchain import Blockchain
from src.algorithms import *


from src.node import Node, Listener
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


"""
    As a full blockchain node:
        relies on network to receive updates about new blocks of transactions, 
        which then verifies and incorporates into its local copy of the blockchain.
    1. connect to peers
    2. construct a complete blockchain
      - for a brand-new node, it only knows one block, the genesis block, 
        which is statically embedded in the client software
      - starting from genesis block, the new node will have to download hundreds 
        of thousands of blocks to synchronize with the network
"""


class MinerListener(Listener):
    """Miner's Listener class"""

    def handle_client_data(self, data, client_sock):
        """Handle client data based on protocol indicator"""
        prot = data[0].lower()
        if prot == "n":
            # Sent by the central server when a new node joins
            peer = json.loads(data[1:])
            self._worker.add_peer(peer)
            client_sock.close()
        elif prot == "b":
            self._handle_block(data, client_sock)
        elif prot == "t":
            self._handle_transaction(data, client_sock)
        elif prot == "r":
            self._handle_transaction_proof(data, client_sock)
        elif prot == "x":
            self._handle_balance(data, client_sock)
        elif prot == "h":
            for header in self._worker.get_blk_headers:
                self.broadcast_message("h" + json.dumps(header))
        else:
            # either header or wrong message format
            client_sock.close()

    def _handle_block(self, data, client_sock):
        """Receive new block"""
        blk_json = json.loads(data[1:])["blk_json"]
        if client_sock:
            client_sock.close()
        # Stop mining if new block is received
        self._worker.stop_mine.set()
        self._worker.block_queue.put(blk_json)

    def _handle_transaction(self, data, client_sock):
        """Receive new transaction"""
        tx_json = json.loads(data[1:])["tx_json"]
        if client_sock:
            client_sock.close()
        if self._worker.all_tx_lock.acquire(False):
            self._worker.add_transaction(tx_json)
            self._worker.all_tx_lock.release()
        else:
            self._worker.tx_queue.put(tx_json)

    def _handle_transaction_proof(self, data, client_sock):
        """Process request for transaction proof"""
        tx_hash = json.loads(data[1:])["tx_hash"]
        tup = self._worker.get_transaction_proof(tx_hash)
        if tup is None:
            msg = json.dumps({
                "blk_hash": None,
                "proof": None,
                "last_blk_hash": None
            })
        else:
            msg = json.dumps({
                "blk_hash": tup[0],
                "proof": tup[1],
                "last_blk_hash": tup[2]
            })
        client_sock.sendall(msg.encode())
        client_sock.close()

    def _handle_balance(self, data, client_sock):
        pubkey = json.loads(data[1:])["identifier"]
        bal = self._worker.get_balance(pubkey)
        client_sock.sendall(str(bal).encode())
        client_sock.close()

class Miner:
    MAX_TX = 10

    def __init__(self, privkey, pubkey, address, listener=MinerListener):
        super().__init__(privkey, pubkey, address, listener)
        self._balance = {}
        self._all_transactions = set()
        self._blockchain = Blockchain()
        # locks
        self.blockchain_lock = threading.RLock()
        self.transaction_all_lock = threading.RLock
        self.transaction_added_lock = threading.RLock()
        self.balance_lock = threading.RLock()
        self.stop_mine = threading.Event()

    @classmethod
    def new(cls, ip_address):
        """Create new Miner instance"""
        signing_key = ecdsa.SigningKey.generate()
        verifying_key = signing_key.get_verifying_key()
        privkey = signing_key.to_string().hex()
        pubkey = verifying_key.to_string().hex()
        return cls(privkey, pubkey, ip_address)

    @property
    def all_transactions(self):
        """Copy of all transactions"""
        # self._update()
        with self.transaction_all_lock:
            tx_copy = copy.deepcopy(self._all_transactions)
        return tx_copy

    """ ====================================================
        ===================== Inquiry ======================
        ===================================================="""

    def get_transaction_proof(self, tx_hash):
        """Get proof of transaction given transaction hash"""
        self._update()
        with self.blockchain_lock:
            last_blk = self._blockchain.resolve()
            res = self._blockchain.get_transaction_proof_in_fork(
                tx_hash, last_blk)
        if res is None:
            return None
        last_blk_hash = hash(last_blk.header)
        return res[0], res[1], last_blk_hash

    def get_balance(self, identifier):
        """Get balance given identifier ie. pubkey"""
        self._update()
        with self.balance_lock:
            if identifier not in self._balance:
                return 0
            return self._balance[identifier]

    def get_blk_headers(self):
        return self._blockchain.get


    """ ====================================================
        =================== Transaction ====================
        ===================================================="""

    def create_transaction(self, receiver, amount, comment=""):
        """Create a new transaction"""
        new_transaction = Transaction.new(self.privkey, self.pubkey, receiver, amount, comment)
        transaction_json = new_transaction.to_json()
        self.add_transaction(transaction_json)
        self.broadcast_message(json.dumps({"tx_json": transaction_json}))
        return new_transaction

    def add_transaction(self, transaction_json):
        """Add transaction to the pool of transactions"""
        transaction = Transaction.from_json(transaction_json)
        if not transaction.verify():
            raise Exception("New transaction failed signature verification.")
        with self.all_tx_lock:
            if transaction_json in self._all_transactions:
                print(f"{self.name} - Transaction already exist in pool.")
                return
            self._all_transactions.add(transaction_json)

    """ ====================================================
        ====================== MINING ======================
        ===================================================="""

    def mine(self, prev_hash=None):
        # get the block
        prev_blk = None if prev_hash is None else self._blockchain.hash_block_map[prev_hash]
        last_blk = self._update(prev_blk)
        pending_tx = self._get_tx_pool()
        tx_collection = self._collect_transactions(pending_tx)
        block = self._mine_new_block(last_blk.header, tx_collection)
        if block is not None:
            blk_json = block.to_json()

            # Add block to blockchain (thread safe)
            block = Block.from_json(blk_json)
            with self.blockchain_lock:
                self._blockchain.add(block)
            print(f"{self.__class__.__name__} {self.name} created a block.")

            # Broadcast block and the header.
            self._broadcast_block(block)
            # Remove gathered transactions from pool and them to added pile
            with self.added_tx_lock:
                self._added_transactions |= set(tx_collection)
        self._update()
        return block

    def _mine_new_block(self, last_blk_hdr, gathered_tx):
        # Mine new block
        # TODO: specify the hash used
        prev_hash = hash(last_blk_hdr)
        block = Block.new(prev_hash, gathered_tx, self.stop_mine)
        if block is None:
            # Mining stopped because a new block is received
            return None
        return block

    def _collect_transactions(self, tx_pool):
        # Get a set of random transactions from pending transactions
        self.transaction_all_lock.acquire()
        self.transaction_added_lock.acquire()
        try:
            # Put in coinbase transaction
            coinbase_tx = Transaction.new(
                self.privkey,
                self.pubkey,
                self.pubkey,
                Block.REWARD,  # 100 SUTD Coins
                "Coinbase"
            )
            tx_collection = [coinbase_tx.to_json()]
            # No transactions to process, return coinbase transaction only
            if not tx_pool:
                return tx_collection
            num_tx = min(Miner.MAX_NUM_TX, len(tx_pool))
            while True:
                if num_tx <= 0:
                    return tx_collection
                # choose randomly from the pool transactions
                trans_sample = random.sample(tx_pool, num_tx)
                num_tx -= 1
                if self._check_transactions_balance(trans_sample):
                    break
            tx_collection.extend(trans_sample)
        finally:
            self.transaction_added_lock.release()
            self.transaction_all_lock.release()
        return tx_collection

    def _check_transactions_balance(self, transactions):
        """Check balance state if transactions were applied"""
        self.balance_lock.acquire()
        try:
            balance = copy.deepcopy(self._balance)
        finally:
            self.balance_lock.release()
        for tx_json in transactions:
            recv_tx = Transaction.from_json(tx_json)
            # Sender must exist so if it doesn't, return false
            if recv_tx.sender not in balance:
                return False
            # Create new account for receiver if it doesn't exist
            if recv_tx.receiver not in balance:
                balance[recv_tx.receiver] = 0
            balance[recv_tx.sender] -= recv_tx.amount
            balance[recv_tx.receiver] += recv_tx.amount
            # Negative balance, return false
            if balance[recv_tx.sender] < 0 \
                    or balance[recv_tx.receiver] < 0:
                return False
        return True

    def _broadcast_block(self, block):
        # b is only taken by miners while h is taken by spv_clients
        blk_json = block.to_json()
        self.broadcast_message("b" + json.dumps({"blk_json": blk_json}))
        self.broadcast_message("h" + json.dumps(block.header))

    """ ====================================================
        ====================== Update ======================
        ===================================================="""

    def _update(self, last_blk=None):
        """Update miner's blockchain, balance state and transactions"""
        self._clear_queue()
        self.blockchain_lock.acquire()
        self.transaction_added_lock.acquire()
        self.balance_lock.acquire()
        try:
            # Resolve blockchain to get last block
            if last_blk is None:
                last_blk = self._blockchain.resolve()
            # TODO:Update added transactions with transactions in blockchain
            #blockchain_tx = self._blockchain.get_transactions_by_fork(last_blk)
            #self._added_transactions = set(blockchain_tx)
            # TODO:Update balance state with latest
            #self._balance = self._blockchain.get_balance_by_fork(last_blk)
        finally:
            self.blockchain_lock.release()
            self.transaction_added_lock.release()
            self.balance_lock.release()
        self.stop_mine.clear()
        return last_blk
