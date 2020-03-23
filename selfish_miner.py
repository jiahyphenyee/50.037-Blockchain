# import copy
# import random
# import sys
# import time
# from block import Block
# from transaction import Transaction
# from blockchain import Blockchain, TARGET
# from algorithms import *
# from node import Node, Listener
# import threading
#
# """
# Design and implement a Miner class realizing miner's functionalities. Then, implement a simple simulator with miners running Nakamoto consensus and making transactions:
#
#     Adjust the TARGET (global and static) parameter, such that on average new blocks arrive every few (2-5) seconds.
#     A miner who found a new block should be rewarded with 100 SUTDcoins.
#     Introduce random transactions, such that miners (with coins) can send transactions to other miners.
#     Make sure that coins cannot be double-spent.
#         consider the addr:balance model and the UTXO model. What are pros and cons?
#         do you need to modify (why, if so) the transaction format introduced in the first week? Hint: yes, you need.
#     Extend the verification checks.
#     Simulate miners competition..
# """
#
#
# class SelfishMinerListener(Listener):
#     """Miner's Listener class"""
#
#     def handle_by_msg_type(self, data, tcp_client):
#         """Handle client data based on msg_type"""
#         msg_type = data[0].lower()
#         if msg_type == "n":  # updates on network nodes
#             self.node.log("======= Receive updates on network nodes")
#             nodes = json.loads(data[1:])["nodes"]
#             self.node.set_peers(nodes)
#
#         elif msg_type == "b":  # new block
#             self.node.log("======= Receive new block from peer")
#             blk_json = json.loads(data[1:])["blk_json"]
#             proof = json.loads(data[1:])["blk_proof"]
#             # stop mining
#             self.node.stop_mine.set()
#             # verify it if all transactions inside the block are valid
#             blk = Block.deserialize(blk_json)
#             transactions = blk.transactions
#             if self.node.check_final_balance(transactions):
#                 delta_previous = self.node.private_blockchain.length - self.node.blockchain.length
#                 success_add = self.node.blockchain.add(blk, proof)
#                 if delta_previous == 0:
#                     self.node.private_blockchain = copy.deepcopy(self.node.blockchain)
#                     self.node.privateBranchLen = 0
#                 elif delta_previous == 1:
#                     self.node.broadcast_blk(self.node.private_blockchain.last_node.block, self.node.private_blockchain.last_node.block.nonce)
#                 elif delta_previous == 2:
#                     previous_block = self.node.private_blockchain.last_node.previous.block
#                     last_block = self.node.private_blockchain.last_node.block
#                     self.node.broadcast_blk(previous_block,previous_block.nonce)
#                     self.node.broadcast_blk(last_block,last_block.nonce)
#                 else:
#                     last_node = self.node.private_blockchain.last_node
#                     for i in range(self.node.privateBranchLen):
#                         last_node = last_node.previous
#                     self.node.broadcast_blk(last_node.block, last_node.block.nonce)
#
#                 for tx in transactions:
#                     if tx in self.node.unconfirmed_transactions:
#                         self.node.unconfirmed_transactions.remove(tx)
#                 self.node.log(f"Added a new block received: {success_add} with {len(transactions)} transactions")
#                 self.node.blockchain.print()
#
#             else:
#                 self.node.log("Invalid transactions in the new block received! ")
#             self.node.stop_mine.clear()
#
#         elif msg_type == "t":  # new transaction
#             self.node.log("======= Receive new transaction from peer")
#             tx_json = json.loads(data[1:])["tx_json"]
#             self.node.add_transaction(Transaction.deserialize(tx_json))
#
#         elif msg_type == "r":  # request for transaction proof
#             self.node.log("======= Receive request for transaction proof")
#             tx_json = json.loads(data[1:])["tx_json"]
#             self.node.log(f"transaction = {tx_json}")
#             proof = self.node.get_transaction_proof(tx_json)
#             if proof is None:
#                 msg = "nil"
#             else:
#                 msg = json.dumps({
#                     "blk_hash": proof[0],
#                     "merkle_path": proof[1],
#                     "last_blk_hash": proof[3],
#
#                 })
#             tcp_client.sendall(msg.encode())
#             self.node.log(f">>> Send proof to SPV")
#
#         elif msg_type == "x":  # request for headers by spvclient
#             self.node.log("======= Receive request for headers (SPV)")
#             headers = self.node.get_blk_headers()
#             msg = json.dumps({
#                 "headers": headers
#             })
#             tcp_client.sendall(msg.encode())
#             self.node.log(">>> Send headers to SPV")
#
#         elif msg_type == "m":  # request for balance by spvclient
#             self.node.log("======= Receive request for balance (SPV)")
#             identifier = json.loads(data[1:])["identifier"]
#             msg = json.dumps(self.node.get_balance(identifier))
#             tcp_client.sendall(msg.encode())
#             self.node.log(f">>> Send balance = {msg} to SPV")
#
#         tcp_client.close()
#
#
# class SelfishMiner(Node):
#     NORMAL = 0  # normal miner
#     DS_MUTATE = 1  # starts to plant private chain for double spending
#     DS_ATTACK = 2  # publish the withheld blocks to effect double spending
#
#     def __init__(self, privkey, pubkey, address, listener=SelfishMinerListener):
#         print(f"address: {address}")
#         super().__init__(privkey, pubkey, address, listener)
#         self.unconfirmed_transactions = []  # data yet to get into blockchain
#         self.blockchain = Blockchain()
#         self.private_blockchain = Blockchain()
#         self.private_blocks = []
#         self.my_unconfirmed_txn = list()  # all unconfirmed transactions sent by me
#
#         self.stop_mine = threading.Event()  # a indicator for whether to continue mining
#         self.privateBranchLen = 0
#
#
#         # attack
#         self.mode = SelfishMiner.NORMAL
#         self.hidden_blocks = 0
#         self.fork_block = None
#
#     @classmethod
#     def new(cls, address):
#         """Create new Miner instance"""
#         signing_key = ecdsa.SigningKey.generate()
#         verifying_key = signing_key.get_verifying_key()
#         privkey = signing_key
#         pubkey = verifying_key
#         return cls(privkey, pubkey, address)
#
#     def get_own_balance(self):
#         balance = self.get_balance(stringify_key(self.pubkey))
#         # self.log(f"balance = {balance}")
#         return balance
#
#     """ inquiry """
#
#     def get_transaction_proof(self, tx_json):
#         """Get proof of transaction given transaction json"""
#         # ask the blockchain to search each block to obtain possible proof from merkle tree
#         proof = self.blockchain.get_proof(tx_json)
#         return proof
#
#     def get_balance(self, identifier):
#         """Get balance given identifier ie. pubkey"""
#         balance = self.blockchain.get_balance()
#         if identifier not in balance:
#             return 0
#         return balance[identifier]
#
#     def get_blk_headers(self):
#         """Get headers of blocks of the longest chain"""
#         blk_headers = {}
#         for block in self.blockchain.get_blks():
#             blk_headers[block.compute_hash()] = block.header
#
#         return blk_headers
#
#     """ Transactions """
#
#     def make_transaction(self, receiver, amount, comment=""):
#         """Create a new transaction"""
#         if self.get_balance(stringify_key(self.pubkey)) >= amount:
#             tx = Transaction.new(sender=self._keypair[1],
#                                  receiver=obtain_key_from_string(receiver),
#                                  amount=amount,
#                                  comment="",
#                                  key=self._keypair[0],
#                                  nonce=self.blockchain.get_nonce(stringify_key(self.pubkey)))
#             tx_json = tx.serialize()
#             self.log(" Made a new transaction")
#             self.my_unconfirmed_txn.append(tx_json)
#             self.add_transaction(tx)
#             msg = "t" + json.dumps({"tx_json": tx_json})
#             self.broadcast_message(msg)
#             return tx
#         else:
#             self.log("Not enough balance in your account!")
#
#     def add_transaction(self, tx):
#         """Add transaction to the pool of unconfirmed transactions and miner's own transaction list"""
#         if not tx.validate():
#             raise Exception("New transaction failed signature verification.")
#         tx_json = tx.serialize()
#
#         self.unconfirmed_transactions.append(tx_json)
#         self.log(f"{len(self.unconfirmed_transactions)} number of unconfirmed transactions")
#
#
#
#     def mine(self):
#         if self.peers is None and self.stop_mine.is_set():
#             return None
#
#         self.log(f"mining on block height of {self.blockchain.last_node.block.blk_height} ....\n....\n")
#         time.sleep(1)
#         tx_collection = self.get_tx_pool()
#
#         if not self.check_final_balance(tx_collection):
#             raise Exception("abnormal transactions!")
#             return None
#
#         new_block, prev_block = self.create_new_block(tx_collection)
#         proof = self.proof_of_work(new_block, self.stop_mine)
#         if proof is None:
#             return None
#
#         self.blockchain.add(new_block, proof)
#         for tx in tx_collection:
#             self.unconfirmed_transactions.remove(tx)
#             self.my_unconfirmed_txn.remove(tx)
#
#         self.broadcast_blk(new_block, proof)
#         self.log(" Mined a new block +$$$$$$$$")
#         print("""
#                     |---------|
#                     |  block  |
#                     |---------|
#         """)
#         self.blockchain.print()
#
#         return new_block, prev_block
#
#     def get_tx_pool(self):
#         if self.mode == SelfishMiner.DS_ATTACK:
#             all_unconfirmed = copy.deepcopy(self.unconfirmed_transactions)
#
#             if len(self.my_unconfirmed_txn) != len(self.ds_txns):
#                 raise Exception("Double spend transactions wrongly replaced")
#
#             pool = list(set(all_unconfirmed) - set(self.my_unconfirmed_txn)).append(self.ds_txns)
#         else:
#             pool = copy.deepcopy(self.unconfirmed_transactions)
#
#         return pool
#
#     def get_last_node(self):
#         return self.blockchain.last_node
#
#     def create_new_block(self, tx_collection):
#         last_node = self.get_last_node()
#
#         new_block = Block(transactions=tx_collection,
#                           timestamp=time.time(),
#                           previous_hash=last_node.block.hash,
#                           miner=self.pubkey)
#
#         return new_block, last_node.block
#
#     def broadcast_blk(self, new_blk, proof):
#         blk_json = new_blk.serialize()
#         self.broadcast_message("b" + json.dumps({"blk_json": blk_json,
#                                                  "blk_proof": proof}))
#         self.broadcast_message("h" + json.dumps({"blk_hash": new_blk.compute_hash(),
#                                                  "blk_header": new_blk.header
#                                                  }))
#
#     def proof_of_work(self, block, stop_mine):
#         """
#         Function that tries different values of the nonce to get a hash
#         that satisfies our difficulty criteria.
#         """
#         start = time.time()
#         computed_hash = block.compute_hash()
#
#         while not computed_hash < TARGET:
#             if self.stop_mine.is_set():
#                 # self.log("Stop Mining as others have found the block")
#                 return None
#             random.seed(time.time())
#             block.nonce = random.randint(0, 100000000)
#             computed_hash = block.compute_hash()
#
#         end = time.time()
#         self.log(f"Found proof = {computed_hash} < TARGET in {end - start} seconds")
#         return computed_hash
#
#     def check_final_balance(self, transactions):
#         """
#             Check balance state if transactions were applied.
#             The balance of an account is checked to make sure it is larger than
#             or equal to the spending transaction amount.
#         """
#         balance = self.blockchain.get_balance()
#
#         for tx_json in transactions:
#             recv_tx = Transaction.deserialize(tx_json)
#             # Sender must exist so if it doesn't, return false
#             sender = stringify_key(recv_tx.sender)
#             receiver = stringify_key(recv_tx.receiver)
#             if sender not in balance:
#                 return False
#             # Create new account for receiver if it doesn't exist
#             if receiver not in balance:
#                 balance[receiver] = 0
#             balance[sender] -= recv_tx.amount
#             balance[receiver] += recv_tx.amount
#             # Negative balance, return false
#             if balance[sender] < 0 or balance[receiver] < 0:
#                 print("Negative balance can exist!")
#                 return False
#         return True
#
#     """DS Miner functions"""
#
#     def get_longest_len(self, chain):
#         """Get length of longest chain"""
#         if chain == "public":
#             return self.blockchain.last_node.block.blk_height
#         else:
#             return self.fork_block.blk_height + len(self.hidden_blocks)
#
#     def setup_ds_attack(self):
#         """Change miner mode and take note of fork location"""
#         self.mode = SelfishMiner.DS_MUTATE
#         self.fork_block = self.get_last_node().block
#         self.ds_txns = self.create_ds_txn()
#         self.log("Ready for DS attack")
#
#     def create_ds_txn(self):
#         """replace DS miner's own unconfirmed transactions with new senders"""
#         ds_txns = list()
#
#         if self.mode != SelfishMiner.DS_MUTATE:
#             raise Exception("Honest miners cannot create double spend transactions")
#
#         for tx_json in self.my_unconfirmed_txn:
#             tx = Transaction.deserialize(tx_json)
#
#             if tx.sender != self._keypair[1]:
#                 raise Exception("Sender is double spending on the wrong transaction")
#
#             replacement_tx = Transaction.new(sender=self._keypair[1],
#                                              receiver=self._keypair[1],
#                                              amount=tx.amount,
#                                              comment=tx.comment,
#                                              key=self._keypair[0],
#                                              nonce=tx.nonce)
#
#             ds_txns.append(replacement_tx)
#         return ds_txns
#
#     def ds_mine(self):
#         if self.mode != SelfishMiner.DS_MUTATE:
#             raise Exception("Normal Miner cannot double spend")
#
#         # if hidden chain is longer than public chain, no longer need to mine, just publish
#         if self.get_longest_len("public") < self.get_longest_len("hidden"):
#             self.ds_broadcast()
#             return
#         else:
#             self.mode = SelfishMiner.DS_ATTACK
#             self.log(f"mining on block height of {self.blockchain.last_node.block.blk_height} ....\n....\n")
#
#             tx_collection = self.get_tx_pool()
#             if not self.check_final_balance(tx_collection):
#                 raise Exception("abnormal transactions!")
#
#             new_block, prev_block = self.create_new_block(tx_collection)
#             proof = self.proof_of_work(new_block, self.stop_mine)
#             if proof is None:
#                 return None
#
#             self.blockchain.add_block(new_block, proof, self.get_last_node().block)
#             self.hidden_blocks += 1
#
#             for tx in tx_collection:
#                 self.unconfirmed_transactions.remove(tx)
#                 self.my_unconfirmed_txn.remove(tx)
#
#             self.log(" Mined a new block +$$$$$$$$")
#             print("""
#                         |---------|
#                         | dsblock |
#                         |---------|
#             """)
#             self.blockchain.print()
#
#             return new_block, prev_block
#
#     def ds_broadcast(self):
#         if self.mode != SelfishMiner.DS_ATTACK:
#             raise Exception("Miner is not in attacking mode")
#
#         self.log("Starting DS chain braodcast")
#         blocks = miner.blockchain.get_blks()
#
#         for i in range(-self.hidden_blocks + 1, 0, 1):
#             self.broadcast_blk(blocks[i], blocks[i].hash)
#             time.sleep(1)
#
#         self.end_ds_attack()
#
#     def end_ds_attack(self):
#         self.log("Ended DS attack")
#         self.hidden_blocks = 0
#         self.fork_block = None
#         self.mode = SelfishMiner.NORMAL
#

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


class SelfishMinerListener(Listener):
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
                delta_previous = self.node.private_blockchain.length - self.node.blockchain.length
                success_add = self.node.blockchain.add(blk, proof)
                if delta_previous == 0:
                    self.node.private_blockchain = copy.deepcopy(self.node.blockchain)
                    self.node.privateBranchLen = 0
                elif delta_previous == 1:
                    self.node.broadcast_blk(self.node.private_blockchain.last_node.block,
                                            self.node.private_blockchain.last_node.block.compute_hash())
                elif delta_previous == 2:

                    blks = self.node.private_blockchain.get_blks()
                    for i in range(self.node.privateBranchLen - 1, -1, -1):
                        self.node.broadcast_blk(blks[i],blk[i].compute_hash)
                else:
                    last_node = self.node.private_blockchain.last_node
                    for i in range(self.node.privateBranchLen):
                        last_node = last_node.previous
                    self.node.broadcast_blk(last_node.block, last_node.block.compute_hash())
                for tx in transactions:
                    if tx in self.node.unconfirmed_transactions:
                        self.node.unconfirmed_transactions.remove(tx)
                self.node.log(f"Added a new block received: {success_add} with {len(transactions)} transactions")
                self.node.blockchain.print()
                self.node.private_blockchain.print()
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


class SelfishMiner(Node):

    NORMAL = 0  # normal miner
    DS_MUTATE = 1  # starts to plant private chain for double spending
    DS_ATTACK = 2  # publish the withheld blocks to effect double spending

    def __init__(self, privkey, pubkey, address, listener=SelfishMinerListener):
        print(f"address: {address}")
        super().__init__(privkey, pubkey, address, listener)
        self.unconfirmed_transactions = []  # data yet to get into blockchain
        self.blockchain = Blockchain()
        self.private_blockchain = Blockchain()
        self.my_unconfirmed_txn = list()  # all unconfirmed transactions sent by me

        self.stop_mine = threading.Event()  # a indicator for whether to continue mining
        self.privateBranchLen = 0

        # attack
        self.mode = SelfishMiner.NORMAL
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
                                 nonce=self.blockchain.get_nonce(stringify_key(self.pubkey)) + 1 + len(
                                     self.my_unconfirmed_txn))
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

        self.log(f"mining on block height of {self.private_blockchain.last_node.block.blk_height} ....\n....\n")
        time.sleep(1)
        tx_collection = self.get_tx_pool()

        if not self.check_final_balance(tx_collection):
            raise Exception("abnormal transactions!")
            return None

        new_block, prev_block = self.create_new_block(tx_collection)
        proof = self.proof_of_work(new_block, self.stop_mine)
        if proof is None:
            return None
        delta_previous = self.private_blockchain.length - self.blockchain.length
        self.private_blockchain.add(new_block, proof)

        for tx in tx_collection:
            self.unconfirmed_transactions.remove(tx)
            self.my_unconfirmed_txn.remove(tx)
        self.privateBranchLen += 1
        if (delta_previous ==0 and self.privateBranchLen ==2):
            broadcast_blks = self.private_blockchain.get_blks()
            for i in range(self.privateBranchLen - 1, -1, -1):
                self.broadcast_blk(broadcast_blks[i], broadcast_blks[i].compute_hash())
            self.privateBranchLen = 0
        # self.broadcast_blk(new_block, proof)
        self.log(" Mined a new block +$$$$$$$$")
        print("""
                    |---------|
                    |  block  |
                    |---------|
        """)
        self.blockchain.print()


        return new_block, prev_block
    """ Mining """

    #
    # def mine(self):
    #     if self.peers is None and self.stop_mine.is_set():
    #         return None
    #
    #     self.log(f"mining on block height of {self.blockchain.last_node.block.blk_height} ....\n....\n")
    #     time.sleep(1)
    #     tx_collection = self.get_tx_pool()
    #     self.log(f"Number of unconfirmed transactions I'm mining on {len(self.get_tx_pool())}")
    #
    #     if not self.check_final_balance(tx_collection):
    #         raise Exception("abnormal transactions!")
    #         return None
    #
    #     new_block = self.create_new_block(tx_collection)
    #     proof = self.proof_of_work(new_block, self.stop_mine)
    #     if proof is None:
    #         return None
    #
    #     self.log("prev_hash")
    #     self.blockchain.add(new_block, proof)
    #     for tx in tx_collection:
    #         self.unconfirmed_transactions.remove(tx)
    #
    #     self.broadcast_blk(new_block, proof)
    #     self.log(" Mined a new block +$$$$$$$$")
    #     print("""
    #                 |---------|
    #                 |   block  |
    #                 |---------|
    #     """)
    #     self.blockchain.print()
    #
    #     return new_block

    def get_tx_pool(self):
        if self.mode == SelfishMiner.DS_ATTACK:
            # all_unconfirmed = copy.deepcopy(self.unconfirmed_transactions)

            # if len(self.my_unconfirmed_txn) != len(self.ds_txns):
            #     raise Exception("Double spend transactions wrongly replaced")
            # self.log(f"****DEBUG IN DS****\nMy DS transactions is {len(self.ds_txns)}")
            # self.log(f"All unconfirmed transactions is {len(all_unconfirmed)}\n")
            # self.log(f"My unconfirmed transactions is {len(self.my_unconfirmed_txn)}")
            # self.log(f"Differnce {len(list(set(all_unconfirmed) - set(self.my_unconfirmed_txn)))}")

            # for x in all_unconfirmed:
            #     for y in self.my_unconfirmed_txn:
            #         if y == x:
            #             all_unconfirmed.remove(y)

            # pool = all_unconfirmed.append(self.ds_txns)
            # print(f"Length of final pool: {len(pool)}")
            pool = copy.deepcopy(self.ds_txns)
        else:
            pool = copy.deepcopy(self.unconfirmed_transactions)

        self.log(
            f"****DEBUG****\nCurrent no. of unconfirmed transaction pool is {len(pool)} for miner in mode: {self.mode}")
        return pool

    def get_last_node(self):
        """returns last block of specified chain"""
        if self.mode == SelfishMiner.DS_ATTACK:
            if self.hidden_blocks_num == 0:
                return self.fork_block
            else:
                return self.hidden_blocks[self.hidden_blocks_num - 1]

        else:
            return self.private_blockchain.last_node.block

    def create_new_block(self, tx_collection):
        last_node = self.get_last_node()

        new_block = Block(transactions=tx_collection,
                          timestamp=time.time(),
                          previous_hash=last_node.hash,
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

    """DS Miner functions"""

    def get_longest_len(self, chain):
        """Get length of longest chain"""
        if chain == "public":
            return self.blockchain.last_node.block.blk_height
        else:
            return self.private_chain.last_node.block.blk_height
            # return self.fork_node.block.blk_height + self.hidden_blocks_num

    def setup_ds_attack(self):
        """Change miner to DS mode and take note of fork location"""
        self.mode = SelfishMiner.DS_MUTATE
        self.log(f"Current miner mode is now {self.mode}")
        self.fork_block = self.get_last_node()
        self.private_chain = copy.deepcopy(self.blockchain)
        self.ds_txns = self.create_ds_txn()
        self.log("Ready for DS attack")

    def create_ds_txn(self):
        """replace DS miner's own unconfirmed transactions with new senders"""
        ds_txns = list()

        if self.mode != SelfishMiner.DS_MUTATE:
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

        self.log("Finished preparing double spend transactions")
        return ds_txns

    def ds_mine(self):
        if self.mode == SelfishMiner.NORMAL:
            self.log(f"Current Miner mode is not {self.DS_MUTATE}, it is {self.mode}")
            raise Exception("Normal Miner cannot double spend")

        # if hidden chain is longer than public chain, no longer need to mine, just publish
        pub = self.get_longest_len("public")
        priv = self.get_longest_len("hidden")
        self.log(f"Checking if my private chain, {priv} > public chain {pub}")
        if self.get_longest_len("public") < self.get_longest_len("hidden"):
            self.log("Hidden Chain is now longer than public blockchain")
            self.ds_broadcast()
            return
        else:
            self.mode = SelfishMiner.DS_ATTACK
            self.log(f"mining on block height of {self.blockchain.last_node.block.blk_height} ....\n....\n")

            tx_collection = self.get_tx_pool()
            if not self.check_final_balance(tx_collection):
                raise Exception("abnormal transactions!")

            new_block = self.create_new_block(tx_collection)

            proof = self.proof_of_work(new_block, self.stop_mine)
            if proof is None:
                return None

            self.private_chain.add_block(new_block, proof)
            self.hidden_blocks.append(new_block)
            self.hidden_blocks_num += 1

            for tx in tx_collection:
                if tx in self.unconfirmed_transactions:
                    self.unconfirmed_transactions.remove(tx)

            self.log(" Mined a new block +$$$$$$$$")
            print("""
                        |---------|
                        | dsblock |
                        |---------|
            """)
            self.blockchain.print()

            return new_block

    def ds_broadcast(self):
        if self.mode != SelfishMiner.DS_ATTACK:
            raise Exception("Miner is not in attacking mode")

        self.log("Starting DS chain braodcast")
        blocks = miner.private_chain.get_blks()

        for i in range(self.hidden_blocks_num - 1, 0, -1):
            self.log(f"Broadcasting block number {i} out of {self.hidden_blocks_num}")
            self.broadcast_blk(blocks[i], blocks[i].compute_hash())
            time.sleep(2)

        self.end_ds_attack()

    def end_ds_attack(self):
        self.log("Ended DS attack")
        self.hidden_blocks_num = 0
        self.fork_block = None
        self.mode = SelfishMiner.NORMAL


if __name__ == '__main__':
    miner = SelfishMiner.new(("localhost", int(sys.argv[1])))
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




