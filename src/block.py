
from .transaction import MerkleTree
from hashlib import sha256
import json
import random

class Block:
    def __init__(self, blk_height, transactions, timestamp, previous_hash,):
        """
        Constructor for the `Block` class.
        :param index:         Unique ID of the block.
        :param transactions:  List of transactions.
        :param timestamp:     Time of generation of the block.
        :param previous_hash: Hash of the previous block in the chain which this block is part of.
        """
        self.blk_height = blk_height
        self.root = MerkleTree(transactions) if len(transactions) != 0 else None
        if self.merkle.__eq__(None):
            self.transactions = None
        else:
            self.transactions = self.merkle.get_root().hash
        self.timestamp = timestamp
        self.previous_hash = previous_hash # Adding the previous hash field

    @property
    def header(self):
        return {
            "prev_hash": self.previous_hash,
            "root": self.root,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }

    def compute_hash(self):
        """
        Returns the hash of the block instance by first converting it
        into JSON string.
        """

        block_string = json.dumps(self.header)  # The string equivalent also considers the previous_hash field now
        return sha256(block_string.encode()).hexdigest()

    def __eq__(self, other):
        return self.index == other.index and self.transactions == other.transactions and self.timestamp == other.timestamp and self.previous_hash == other.previous_hash
