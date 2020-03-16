import copy
from block import Block
from transaction import Transaction
from blockchain import Blockchain
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

        if msg_type == "b":  # new block
            blk_json = json.loads(data[1:])["blk_json"]
            self.node.blockchain.setMinable(False)  # Stop mining
            self.node.blockchain.add_block(Block.deserialize(blk_json))

        elif msg_type == "t":  # new transaction
            tx_json = json.loads(data[1:])["tx_json"]
            self.node.blockchain.add_new_transaction(Transaction.deserialize(tx_json))

        elif msg_type == "r":  # request for transaction proof
            tx_hash = json.loads(data[1:])["tx_hash"]
            proof = self.node.get_transaction_proof(tx_hash)
            if proof is None:
                msg = "nil"
            else:
                msg = json.dumps({
                    "blk_hash": proof[0],
                    "merkle_path": proof[1],
                    "last_blk_hash": proof[3],

                })
            tcp_client.sendall(msg.encode())

        elif msg_type == "h":  # request for headers by spvclient
            msg = json.dumps({
                "headers": self.node.get_blk_header()
            })
            tcp_client.sendall(msg.encode)

        tcp_client.close()


class Miner(Node):

    def __init__(self, privkey, pubkey, address, listener=MinerListener):
        super().__init__(privkey, pubkey, address, listener)
        self.account_balance = {}
        # self.blockchain = Blockchain()

    @classmethod
    def new(cls, address):
        """Create new Miner instance"""
        signing_key = ecdsa.SigningKey.generate()
        verifying_key = signing_key.get_verifying_key()
        privkey = signing_key.to_string().hex()
        pubkey = verifying_key.to_string().hex()
        return cls(privkey, pubkey, address)

    def update(self):
        return

    """ inquiry """

    def get_transaction_proof(self, tx_hash):
        """Get proof of transaction given transaction hash"""
        # ask the blockchain to search each block to obtain possible proof from merkle tree
        proof = self.blockchain.get_proof(tx_hash)
        return proof

    def get_balance(self, identifier):
        """Get balance given identifier ie. pubkey"""
        self.update()
        if identifier not in self.account_balance:
            return 0
        return self.account_balance[identifier]

    def get_blk_headers(self, prev_hash):
        """Get headers of blocks that continues from prev_hash block. This method is to serve SPVClient"""
        blk_headers = {}
        for block in self.blockchain.get_blks(prev_hash):
            blk_headers[block.compute_hash()] = block.header

        return blk_headers

    """ Transactions """

    def make_transaction(self, receiver, amount, comment=""):
        """Create a new transaction"""
        tx = Transaction.new(self.privkey, self.pubkey, receiver, amount, comment)
        tx_json = tx.serialize()
        print(self.address, " made a new transaction")
        self.add_transaction(tx)
        msg = "t" + json.dumps({"tx_json": tx_json})
        self.broadcast_message(msg)
        return tx

    def add_transaction(self, transaction_json):
        """Add transaction to the pool of unconfirmed transactions"""
        transaction = Transaction.deserialize(transaction_json)
        if not transaction.validate():
            raise Exception("New transaction failed signature verification.")
        self.blockchain.add_new_transaction(transaction)

    """ Mining """

    def mine(self):
        # need to include this transaction so miner can obtain reward
        coinbase_tx = Transaction.new(
            sender=self.pubkey,
            receiver=self.pubkey,
            amount=100,
            comment="Coinbase",
            key=self.privkey,

        )
        # if not self.check_final_balance(self.blockchain.unconfirmed_transactions):
        #     return None

        block = self.blockchain.mine(coinbase_tx)

        if block is not None:
            blk_json = block.serialize()
            self.broadcast_message("b" + json.dumps({"blk_json": blk_json}))

        print(self.address, " created a block.")

        return block

    def check_final_balance(self, transactions):
        """
            Check balance state if transactions were applied.
            The balance of an account is checked to make sure it is larger than
            or equal to the spending transaction amount.
        """
        balance = copy.deepcopy(self._balance)
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
            if balance[recv_tx.sender] < 0 or balance[recv_tx.receiver] < 0:
                print("Negative balance can exist!")
                return False
        return True

    def test_connection(self):
        msg = "hello peer"
        self.broadcast_message(msg)





