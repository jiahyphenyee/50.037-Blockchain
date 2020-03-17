import time
import random
from ecdsa import SigningKey
from block import Block
from transaction import Transaction
from merkle_tree import *

TARGET = "ffffffffffffffff"
class Node:
    def __init__(self, previous, block=Block( [], 0, 0)):
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

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has blk_height 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block([], time.time(), "0")
        genesis_block.blk_height = 0
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
        block.nonce = 0

        computed_hash = block.compute_hash()
        # while not computed_hash.startswith('0' * Blockchain.difficulty):
        #     block.nonce += 1
        #     computed_hash = block.compute_hash()

        while not computed_hash < TARGET:
            block.nonce +=1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_block(self, block, proof, previous_block=None):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of a latest block
          in the chain match.
        """
        if previous_block is not None:
            for node in self.nodes:
                if node.block.__eq__(previous_block):
                    parent_node = node
                    break;
        else:
            parent_node = self.last_node
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
        if previous_block is None:
            self.last_nodes.remove(parent_node)
        self.last_nodes.append(current_node)
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

    def add(self, new_block, proof, previous_block=None):
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
        if previous_block is None:
            added = self.add_block(new_block, proof)
        else:
            added = self.add_block(new_block, proof, previous_block)

        return added

    def get_blks(self):
        blocks = list()
        last_node = self.last_node
        while last_node.block.hash != self.root.hash:
            blocks.append(last_node.block)
            last_node = last_node.previous
        blocks.append(last_node.block)
        return blocks

    def get_proof(self, transaction):
        #Transaction
        last_node = self.last_node
        while last_node.block.hash != self.root.hash and transaction not in last_node.block.transactions:
            last_node = last_node.previous
        proofs = last_node.block.merkle.get_proof(transaction)
        return proofs, last_node.block
    def get_balance(self):
        blocks = self.get_blks()
        dic = {}
        for block in blocks:
            if block.miner not in dic.keys():
                dic[block.miner.to_string()] = 100
            else:
                dic[block.miner.to_string()] += 100
            for transaction in block.transactions:
                tx = Transaction.deserialize(transaction)
                if tx.sender not in dic.keys():
                    dic[tx.sender.to] = -tx.amount
                else:
                    dic[tx.sender] -= tx.amount
                if tx.receiver not in dic.keys():
                    dic[tx.receiver] = tx.amount
                else:
                    dic[tx.receiver] += tx.amount
        return dic



if __name__ == "__main__":
    blockchain = Blockchain()
    print(blockchain.last_node.block,blockchain.last_node.block.blk_height)
    miner = SigningKey.generate()
    miner_public = miner.get_verifying_key()
    alice_private = SigningKey.generate()
    alice_public = alice_private.get_verifying_key()
    bob_private = SigningKey.generate()
    bob_public = bob_private.get_verifying_key()
    for j in range(2):
        transactions = list()
        # for i in range(random.randint(10,11)):
        for i in range(3):
            sk = SigningKey.generate()
            vk = sk.get_verifying_key()
            sk1 = SigningKey.generate()
            vk1 = sk1.get_verifying_key()
            t = Transaction.new(alice_public, bob_public, 4, 'r', alice_private)
            s = t.serialize()
            transactions.append(s)

        block = Block(transactions, time.time(), blockchain.last_node.block.hash)
        block.miner = miner_public
        proof = blockchain.proof_of_work(block)
        print(blockchain.add(block,proof))
        print(block, block.blk_height)
    screwedUpBlock = Block(transactions,time.time(), blockchain.root.hash)
    proof = blockchain.proof_of_work(screwedUpBlock)
    print(blockchain.add(screwedUpBlock, proof, blockchain.root))
    print(screwedUpBlock, screwedUpBlock.blk_height)
    for node in blockchain.last_nodes:
        print(node.block, node.block.blk_height)
    print(blockchain.get_blks())
    balance_addr = blockchain.get_balance()
    print(balance_addr)
    print(balance_addr[miner_public])
    print(balance_addr[alice_public])
    print(balance_addr[bob_public])
    # proofs, block = blockchain.get_proof(transactions[0])
    # print(verify_proof(transactions[0],proofs,block.merkle.get_root()))
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
