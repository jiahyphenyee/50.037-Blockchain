
from merkle_tree import *
from transaction import *
from hashlib import sha256
import json
import random


class Block:
    def __init__(self, transactions, timestamp,previous_hash, miner):
        """
        Constructor for the `Block` class.
        :param transactions:  List of transactions.
        :param timestamp:     Time of generation of the block.
        :param previous_hash: Hash of the previous block in the chain which this block is part of.
        :PARAMS not included in intiliazation is hash
        """
        self.blk_height = 0
        self.merkle = MerkleTree(transactions) if len(transactions) != 0 else None
        self.transactions = transactions
        if self.merkle.__eq__(None):
            self.root = None
        else:
            self.root = self.merkle.get_root().hash
        self.timestamp = timestamp
        self.nonce = 0
        self.previous_hash = previous_hash # Adding the previous hash field
        self.hash = ""
        self.miner = miner

    @property
    def header(self):
        return {
            "prev_hash": self.previous_hash,
            "root": self.root, #hash of merkle
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }

    def serialize(self):
        # Serializes object to CBOR or JSON string
        dic = {}
        dic['header'] = self.header
        dic['transactions'] = self.transactions
        dic['blk_height'] = self.blk_height
        dic['hash'] = self.hash
        serialized = json.dumps(dic)
        return serialized

    @classmethod
    def deserialize(cls, data):
        # Instantiates/Deserializes object from CBOR or JSON string
        deserialized = json.loads(data)
        header = deserialized['header']
        block = Block(deserialized['blk_height'], deserialized['transactions'], header['timestamp'], header['prev_hash'])
        block.nonce = header['nonce']
        block.hash = deserialized['hash']
        return block


    def compute_hash(self):
        """
        Returns the hash of the block instance by first converting it
        into JSON string.
        """

        block_string = json.dumps(self.header)  # The string equivalent also considers the previous_hash field now
        return sha256(block_string.encode()).hexdigest()

    def __eq__(self, other):
        return self.nonce == other.nonce and self.root == other.root and self.timestamp == other.timestamp and self.previous_hash == other.previous_hash
