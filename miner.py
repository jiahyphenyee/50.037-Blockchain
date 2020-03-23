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
            if self.node.check_balance_and_nonce(transactions, blk.previous_hash):
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
            self.node.log(f"transaction = {tx_json}")
            proof, hash = self.node.get_transaction_proof(tx_json)
            self.node.log(f"blk_hash: {hash}")
            self.node.log(f"proof: {proof}")
            if proof is None:
                msg = "nil"
            else:
                msg = json.dumps({
                    "merkle_path": proof,
                    "blk_hash": str(hash)
                })
            tcp_client.sendall(msg.encode())
            self.node.log(f">>> Send proof to SPV")

        elif msg_type == "x":  # request for headers by spvclient
            self.node.log("======= Receive request for headers (SPV)")
            headers = self.node.get_blk_headers()
            msg = json.dumps({
                "headers": headers
            })
            tcp_client.sendall(msg.encode())
            self.node.log(">>> Send headers to SPV")

        elif msg_type == "c":  # request for nonce by spvclient
            self.node.log("======= Receive request for nonce (SPV)")
            identifier = json.loads(data[1:])["identifier"]
            msg = json.dumps(self.node.blockchain.get_nonce(identifier))
            tcp_client.sendall(msg.encode())
            self.node.log(f">>> Send nonce = {msg} to SPV")

        elif msg_type == "m":  # request for balance by spvclient
            self.node.log("======= Receive request for balance (SPV)")
            identifier = json.loads(data[1:])["identifier"]
            msg = json.dumps(self.node.get_balance(identifier))
            tcp_client.sendall(msg.encode())
            self.node.log(f">>> Send balance = {msg} to SPV")

        tcp_client.close()


class Miner(Node):
    NORMAL = 0 # normal miner
    DS_MUTATE = 1 # starts to plant private chain for double spending
    DS_ATTACK = 2 # publish the withheld blocks to effect double spending

    def __init__(self, privkey, pubkey, address, listener=MinerListener):
        print(f"address: {address}")
        super().__init__(privkey, pubkey, address, listener)
        self.unconfirmed_transactions = []  # data yet to get into blockchain
        self.blockchain = Blockchain()
        self.my_unconfirmed_txn = list()   # all unconfirmed transactions sent by me
        self.copy_all_unconfirmed_txn = list()

        self.stop_mine = threading.Event()  # a indicator for whether to continue mining


        #attack
        self.mode = Miner.NORMAL
        # self.private_chain = None
        self.hidden_blocks_num = 0
        self.hidden_blocks = list()
        self.fork_block = None

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
        self.log(f"balance = {balance}")
        return balance

    """ inquiry """

    def get_transaction_proof(self, tx_json):
        """Get proof of transaction given transaction json"""
        # ask the blockchain to search each block to obtain possible proof from merkle tree
        proof, blk = self.blockchain.get_proof(tx_json)
        return proof, blk.hash

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
                                 key=self._keypair[0],
                                 nonce=self.blockchain.get_nonce(stringify_key(self.pubkey))+1+len(self.my_unconfirmed_txn))
            tx_json = tx.serialize()
            self.log(" Made a new transaction")
            self.my_unconfirmed_txn.append(tx_json)
            self.add_transaction(tx)
            msg = "t" + json.dumps({"tx_json": tx_json})
            self.broadcast_message(msg)
            return tx
        else:
            self.log("Not enough balance in your account!")

    def add_transaction(self, tx):
        """Add transaction to the pool of unconfirmed transactions and miner's own transaction list"""
        if not tx.validate():
            raise Exception("New transaction failed signature verification.")
        if not self.tx_resend_check(tx):
            raise Exception("New transaction failed resending check.")
        tx_json = tx.serialize()

        self.unconfirmed_transactions.append(tx_json)
        self.log(f"{len(self.unconfirmed_transactions)} number of unconfirmed transactions")

    def tx_resend_check(self, tx):
        nonce = self.blockchain.get_nonce(stringify_key(tx.sender))
        self.log(f"most recent nonce = {nonce} vs new nonce = {tx.nonce}")
        if tx.nonce <= nonce:
            self.log("New transaction failed resending check based on most updated chain.")
            return False
        else:
            self.log("New transaction passed resending check based on most updated chain.")
            return True





    """ Mining """
    def mine(self):
        if self.peers is None and self.stop_mine.is_set():
            return None

        self.log(f"mining on block height of {self.blockchain.last_node.block.blk_height} ....\n....\n")
        time.sleep(1)
        tx_collection = self.get_tx_pool()
        self.log(f"Number of unconfirmed transactions I'm mining on {len(self.get_tx_pool())}")

        if not self.check_balance_and_nonce(tx_collection, self.blockchain.last_node.block.hash):
            raise Exception("abnormal transactions!")
            return None

        new_block= self.create_new_block(tx_collection)
        proof = self.proof_of_work(new_block, self.stop_mine)
        if proof is None:
            return None

        self.log("prev_hash")
        self.blockchain.add(new_block, proof)
        for tx in tx_collection:
            self.unconfirmed_transactions.remove(tx)

        self.broadcast_blk(new_block, proof)
        self.log(" Mined a new block +$$$$$$$$")
        print("""
                    |---------|
                    |  block  |
                    |---------|
        """)
        self.blockchain.print()

        return new_block

    def get_tx_pool(self):
        if self.mode == Miner.DS_ATTACK:
            unconfirm = copy.deepcopy(self.copy_all_unconfirmed_txn)

            if len(self.my_unconfirmed_txn) != len(self.ds_txns):
                raise Exception("Double spend transactions wrongly replaced")

            unconfirm.extend(self.ds_txns)
            pool = [x for x in unconfirm if x not in self.my_unconfirmed_txn]

        else:
            pool = copy.deepcopy(self.unconfirmed_transactions)

        return pool

    def get_last_node(self):
        """returns last block of specified chain"""
        if self.mode == Miner.DS_ATTACK:
            if self.hidden_blocks_num == 0:
                return self.fork_block
            else:
                return self.hidden_blocks[self.hidden_blocks_num-1]
                
        else:
            return self.blockchain.last_node.block

    def create_new_block(self, tx_collection):
        last_node = self.get_last_node()

        new_block = Block(transactions=tx_collection,
                        timestamp=time.time(),
                        previous_hash=last_node.compute_hash(),
                        miner=self.pubkey)

        return new_block

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

    def check_balance_and_nonce(self, transactions, blk_hash):
        """
            Check balance state if transactions were applied.
            The balance of an account is checked to make sure it is larger than
            or equal to the spending transaction amount.
        """
        balance = self.blockchain.get_balance(blk_hash)
        tx_nonce = {}

        for tx_json in transactions:
            recv_tx = Transaction.deserialize(tx_json)
            # Sender must exist so if it doesn't, return false

            sender = stringify_key(recv_tx.sender)
            receiver = stringify_key(recv_tx.receiver)
            if sender not in balance:
                return False
            # checking if nonce run into conflict with previous nonce
            if sender not in tx_nonce:
                tx_nonce[sender] = []
            if recv_tx.nonce <= self.blockchain.get_nonce(sender, blk_hash):
                self.log("Detect conflicting nonce from transactions in chain!")
                return False
            elif recv_tx.nonce in tx_nonce[sender]:
                self.log("Detect conflicting nonce from transactions in collection")
                return False
            else:
                tx_nonce[sender].append(recv_tx.nonce)
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




    """DS Miner functions"""
    def get_longest_len(self, chain):
        """Get length of longest chain"""
        if chain == "public":
            return self.blockchain.last_node.block.blk_height
        else:
            # return self.private_chain.last_node.block.blk_height
            return self.fork_block.blk_height + self.hidden_blocks_num
            
    def setup_ds_attack(self):
        """Change miner to DS mode and take note of fork location"""
        self.mode = Miner.DS_MUTATE
        self.fork_block = self.get_last_node()
        # self.private_chain = copy.deepcopy(self.blockchain)
        self.copy_all_unconfirmed_txn = copy.deepcopy(self.unconfirmed_transactions)
        self.ds_txns = self.create_ds_txn()
        self.log("Ready for DS attack")
        
    def create_ds_txn(self):
        """replace DS miner's own unconfirmed transactions with new senders""" 
        ds_txns = list()

        if self.mode != Miner.DS_MUTATE:
            raise Exception("Honest miners cannot create double spend transactions")

        for tx_json in self.my_unconfirmed_txn:
            tx = Transaction.deserialize(tx_json)

            if tx.sender != self._keypair[1]:
                raise Exception("Sender is double spending on the wrong transaction")

            replacement_tx = Transaction.new(sender=self._keypair[1],
                                 receiver=self._keypair[1],
                                 amount=tx.amount,
                                 comment=tx.comment,
                                 key=self._keypair[0],
                                 nonce=tx.nonce)
            replacement_tx_json = replacement_tx.serialize()
            ds_txns.append(replacement_tx_json)

        return ds_txns

    def ds_mine(self):
        if self.mode == Miner.NORMAL:
            raise Exception("Normal Miner cannot double spend")

        
        else:
            self.mode = Miner.DS_ATTACK
            self.log(f"mining on block height of {self.blockchain.last_node.block.blk_height} ....\n....\n")
            
            tx_collection = self.get_tx_pool()
            # if not self.check_balance_and_nonce(tx_collection):
            #     raise Exception("abnormal transactions!")

            new_block = self.create_new_block(tx_collection)

            proof = self.proof_of_work(new_block, self.stop_mine)
            if proof is None:
                return None

            # self.private_chain.add_block(new_block, proof)
            self.hidden_blocks.append(new_block)
            self.hidden_blocks_num += 1

            for tx in tx_collection:
                if tx in self.copy_all_unconfirmed_txn:
                    self.copy_all_unconfirmed_txn.remove(tx)
                
            self.log(" Mined a new block +$$$$$$$$")
            print("""
                        |---------|
                        | dsblock |
                        |---------|
            """)
            self.blockchain.print()

        # if hidden chain is longer than public chain, no longer need to mine, just publish
        pub = self.get_longest_len("public")
        priv = self.get_longest_len("hidden")
        self.log(f"Checking if length of private chain {priv} > public chain {pub}")
        if self.get_longest_len("public") < self.get_longest_len("hidden"):
            self.ds_broadcast()
            return

        return new_block

    def ds_broadcast(self):
        if self.mode != Miner.DS_ATTACK:
            raise Exception("Miner is not in attacking mode")

        self.log("Starting DS chain Broadcast...")
        blocks = self.hidden_blocks
        count = 1

        for blk in blocks:
            self.log(f"Broadcasting block {count} out of {self.hidden_blocks_num}")
            self.blockchain.add_block(blk, blk.compute_hash())
            self.broadcast_blk(blk, blk.compute_hash())
            count += 1
            time.sleep(2)
        
        self.end_ds_attack()

    def end_ds_attack(self):
        self.log("Ended DS attack...")
        self.hidden_blocks_num = 0
        self.fork_block = None
        self.mode = Miner.NORMAL
        self.copy_all_unconfirmed_txn = list()



