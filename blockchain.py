import time
import random
from ecdsa import SigningKey
from block import Block
from transaction import Transaction
from merkle_tree import *
from algorithms import *
import copy
TARGET = "00000fffffffffff"

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
        # self.unconfirmed_transactions = []  # data yet to get into blockchain
        self.root = self.create_genesis_block()
        self.root_node = Node(None, self.root)
        self.last_nodes = []
        self.last_nodes.append(self.root_node)
        self.nodes = [self.root_node]
        # self.public_keys_nonce = {}

    @classmethod
    def new(cls, prev_blks):
        blockchain = cls()
        blks = []
        for i in range(len(prev_blks)):
            blk_str = prev_blks[i].serialize()
            block = Block.deserialize(blk_str)
            blks.append(block)
        blockchain.root = blks[-1]
        blockchain.root_node = Node(None, blockchain.root)
        blockchain.last_nodes = []
        blockchain.last_nodes.append(blockchain.root_node)
        blockchain.nodes = [blockchain.root_node]
        for i in range(-2, -len(blks) - 1, -1):
            blockchain.add(blks[i], blks[i].compute_hash())
        return blockchain

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has blk_height 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block([], 0, "0", None)
        genesis_block.blk_height = 0
        genesis_block.hash = genesis_block.compute_hash()
        return genesis_block
    @property
    def length(self):
        return self.last_node.block.blk_height

    @property
    def last_node(self):
        """
        A quick pythonic way to retrieve the most recent block in the chain. Note that
        the chain will always consist of at least one block (i.e., genesis block)
        """
        return self.resolve()

    def resolve(self):
        idx = -1
        last_node = None
        for node in self.last_nodes:
            if node.block.blk_height >= idx:
                idx = node.block.blk_height
                last_node = node
        return last_node

    def proof_of_work(self, block):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = random.randint(0,1000000000)

        computed_hash = block.compute_hash()
        # while not computed_hash.startswith('0' * Blockchain.difficulty):
        #     block.nonce += 1
        #     computed_hash = block.compute_hash()

        while not computed_hash < TARGET:
            block.nonce +=1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of a latest block
          in the chain match.
        """
        # if previous_block is not None:
        print(self.nodes)
        for node in self.nodes:

            print(node.block)
            if node.block.compute_hash() == block.previous_hash:
                parent_node = node
                break;
        # else:
        #     parent_node = self.last_node
        previous_hash = parent_node.block.hash
        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False
        block.blk_height = parent_node.block.blk_height + 1
        block.hash = proof
        current_node = Node(parent_node, block)
        parent_node.children.append(current_node)
        self.nodes.append(current_node)
        # if previous_block is None:
        #     self.last_nodes.remove(parent_node)
        for  node in self.last_nodes:
            if len(node.children) != 0:
                self.last_nodes.remove(node)
            # self.last_nodes.remove(parent_node)
        self.last_nodes.append(current_node)
        #
        # for transaction in block.transactions:
        #     tx = Transaction.deserialize(transaction)
        #     sender_string = stringify_key(tx.sender)
        #     if sender_string not in self.public_keys_nonce.keys():
        #         self.public_keys_nonce[sender_string] = 0
        #     else:
        #         self.public_keys_nonce[sender_string] += 1
        return True

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash < TARGET and
                block_hash == block.compute_hash())

    # def add_new_transaction(self, transaction):
    #     self.unconfirmed_transactions.append(transaction)

    def add(self, new_block, proof):
        """
        This function serves as an interface to add a new block
         to the blockchain after verifying the proof of work
         PARAMS:
         new_block: Block generated by miner
         proof: proof of work
         previous_block: Block to append to in blockchain
        """
        # if not self.unconfirmed_transactions:
        #     return False
        #
        # last_node = self.last_node
        #
        # new_block = Block(blk_height=last_node.block.blk_height + 1,
        #                   transactions=self.unconfirmed_transactions,
        #                   timestamp=time.time(),
        #                   previous_hash=last_node.block.hash)
        #
        # proof = self.proof_of_work(new_block)
        # if previous_block is None:
        for node in self.nodes:
            if new_block.compute_hash() == node.block.compute_hash():
                return False
        added = self.add_block(new_block, proof)
        # else:
        #     added = self.add_block(new_block, proof, previous_block)

        return added

    def get_blks(self, block_hash=None):

        blocks = list()
        if block_hash is None:
            last_node = self.last_node
        else:
            last_node = self.get_node_from_block_hash(block_hash)
        while last_node.block.hash != self.root.hash:
            blocks.append(last_node.block)
            last_node = last_node.previous
        blocks.append(last_node.block)
        return blocks

    def get_proof(self, transaction):
        # returns proofs of merkle tree and the block that the transaction is located in
        #Transaction
        last_node = self.last_node
        while last_node.block.hash != self.root.hash and transaction not in last_node.block.transactions:
            last_node = last_node.previous
        if last_node.block.hash == self.root.hash:
            return None, last_node.block
        proofs = last_node.block.merkle.get_proof(transaction)
        return proofs, last_node.block

    def get_nonce(self, public_key, block_hash=None):
        public_keys_nonce = {}
        blocks = self.get_blks(block_hash)
        for block in blocks:
            for transaction in block.transactions:
                tx = Transaction.deserialize(transaction)
                sender_string = stringify_key(tx.sender)
                if sender_string not in public_keys_nonce.keys():
                    public_keys_nonce[sender_string] = 0
                else:
                    public_keys_nonce[sender_string] += 1
        ## stringified public key
        if public_key not in public_keys_nonce.keys():
            return -1
        else:
            return public_keys_nonce[public_key]

    def get_node_from_block_hash(self, block_hash):
        for node in self.nodes:
            if node.block.compute_hash() == block_hash:
                return node
        return None

    def get_balance(self, block_hash=None):
        blocks = self.get_blks(block_hash)

        balance = {}
        for block in blocks:
            if block == self.root:
                continue
            miner_string = stringify_key(block.miner)
            if miner_string not in balance.keys():
                balance[miner_string] = 100
            else:
                balance[miner_string] += 100
            for transaction in block.transactions:
                tx = Transaction.deserialize(transaction)
                sender_string = stringify_key(tx.sender)
                if sender_string not in balance.keys():
                    balance[sender_string] = -tx.amount
                else:
                    balance[sender_string] -= tx.amount
                receiver_string = stringify_key(tx.receiver)
                if receiver_string not in balance.keys():
                    balance[receiver_string] = tx.amount
                else:
                    balance[receiver_string] += tx.amount
        return balance

    def print(self):
        pprint_tree(self.root_node)

def pprint_tree(node, file=None, _prefix="", _last=True):
    print(_prefix, "`- " if _last else "|- ", node.block, sep="", file=file)
    _prefix += "   " if _last else "|  "
    child_count = len(node.children)
    for i, child in enumerate(node.children):
        _last = i == (child_count - 1)
        pprint_tree(child, file, _prefix, _last)


if __name__ == "__main__":
    blockchain = Blockchain()
    print(blockchain.last_node.block,blockchain.last_node.block.blk_height)
    blockchain.print()
    miner = SigningKey.generate()
    miner_public = miner.get_verifying_key()
    alice_private = SigningKey.generate()
    alice_public = alice_private.get_verifying_key()
    bob_private = SigningKey.generate()
    bob_public = bob_private.get_verifying_key()
    for j in range(2):
        transactions = list()
        # for i in range(random.randint(10,11)):
        for i in range(2):
            sk = SigningKey.generate()
            vk = sk.get_verifying_key()
            sk1 = SigningKey.generate()
            vk1 = sk1.get_verifying_key()
            t = Transaction.new(alice_public, bob_public, 4, 'r',alice_private,blockchain.get_nonce(stringify_key(alice_public))+1)
            s = t.serialize()
            transactions.append(s)

        block = Block(transactions, time.time(), blockchain.last_node.block.hash,miner_public)
        proof = blockchain.proof_of_work(block)
        print(blockchain.add(block,proof))
        print(block, block.blk_height)
        blockchain.add(block,proof)
    # print(blockchain.get_blks())
    # print(blockchain.get_blks())
    # print(blockchain.public_keys_nonce)
    blockchain.print()
    print(blockchain.get_balance())
    # print(stringify_key(miner_public))
    # balance_addr = blockchain.get_balance()
    # print(balance_addr)
    # print(balance_addr[stringify_key(miner_public)])
    # print(balance_addr[stringify_key(alice_public)])
    # print(balance_addr[stringify_key(bob_public)])
    # print(s in blockchain.last_node.block.transactions)
    # print(blockchain.last_node.block.transactions)
    # # t = Transaction.new(alice_public, bob_public, 4, 'r', alice_private,
    # #                     blockchain.get_nonce(stringify_key(alice_public)) + 1)
    # # s = t.serialize()
    # proofs, block = blockchain.get_proof(s)
    # print(verify_proof(s, proofs, block.merkle.get_root().hash))
    blks = blockchain.get_blks()
    newChain = Blockchain.new(blks)

    screwedUpBlock = Block(transactions,time.time(), newChain.root.hash,miner_public)
    proof = newChain.proof_of_work(screwedUpBlock)
    print(newChain.add(screwedUpBlock, proof))
    # print(screwedUpBlock, screwedUpBlock.blk_height)
    # # for node in blockchain.last_nodes:
    # #     print(node.block, node.block.blk_height)
    newChain.print()
    blockchain.print()
    print(newChain.get_balance(screwedUpBlock.compute_hash()))
    print(blockchain.get_balance())
    print(newChain.get_nonce(stringify_key(alice_public),screwedUpBlock.compute_hash()))
    print(blockchain.get_nonce(stringify_key(alice_public)))
    # print(verify_proof(s, proofs, block.root))
    # print(block.root)
    # print(block.merkle.get_root().hash)
    # print(block.root == block.merkle.get_root().hash)
    # block = blockchain.last_node.block
    # print(block.previous_hash)
    # s = block.serialize()
    # b2 = Block.deserialize(s)
    # print(b2.__eq__(block))
    # proof = block.merkle.get_proof(transactions[0])
    # print(verify_proof(MerkleTree.compute_hash(transactions[0]), proof, block.merkle.get_root()))
    # proof = b2.merkle.get_proof(transactions[0])
    # print(verify_proof(MerkleTree.compute_hash(transactions[0]), proof, b2.merkle.get_root()))
    # print(b2.merkle.root.hash == block.merkle.root.hash)
    # print(block.hash)
    # print(b2.hash)
