import time
from block import Block

class Node:
    def __init__(self, previous, block=Block):
        self.block = block
        self.children = []  # the pointer initially points to nothing
        self.previous = previous


class Blockchain:
    difficulty = 5

    def __init__(self):
        """
        Constructor for the `Blockchain` class.
        """
        self.unconfirmed_transactions = []  # data yet to get into blockchain
        self.root = self.create_genesis_block()
        self.root_node = Node(None, self.root)
        self.last_nodes = []
        self.last_nodes.append(self.root_node)

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        return genesis_block

    @property
    def last_node(self):
        """
        A quick pythonic way to retrieve the most recent block in the chain. Note that
        the chain will always consist of at least one block (i.e., genesis block)
        """
        return self.resolve()

    def resolve(self):
        idx = 0
        last_node = None
        for node in self.last_nodes:
            if node.block.index >= idx:
                idx = node.block.index
                last_node = node.block
        return last_node

    def proof_of_work(self, block):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_block(self, block, proof, previous_block):

        """
                A function that adds the block to the chain after verification.
                Verification includes:
                * Checking if the proof is valid.
                * The previous_hash referred in the block and the hash of a latest block
                  in the chain match.
                """

        for node in self.last_nodes:
            if node.block.__eq__(previous_block):
                parent_node = node
                break;

        previous_hash = parent_node.block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof

        current_node = Node(parent_node, block)
        parent_node.children.append(current_node)
        self.last_nodes.append(current_node)
        for node in self.last_nodes:
            if len(node.children) != 0 :
                self.last_nodes.remove(node)
        return True

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of a latest block
          in the chain match.
        """
        parent_node = self.last_node
        previous_hash = parent_node.block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        current_node = Node(self.last_node,block)
        parent_node.children.append(current_node)
        self.last_nodes.remove(parent_node)
        self.last_nodes.append(current_node)
        return True

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out proof of work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_node = self.last_node

        new_block = Block(index=last_node.block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_node.block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index

