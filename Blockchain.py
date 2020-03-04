import hashlib
import base58
import ecdsa
import datetime
import time
import string
import random
import json
from Merkle import MerkleTree

class Blockchain:
    def __init__(self, target):
        self.chain = []  # key = serialized header of parent block, value = serialized header of next block
        self.current_block = ""   #current block header (hashed)
        self.genesis()
        self.current_chain_idx = 0
        self.target = target
        self.timestamp = 0
        self.merkle = MerkleTree()
    
    def genesis(self):
        # create genesis block
        d = {}
        # genesis merkle tree has no transactions
        self.merkle.add([])

        d['prev_hash'] = hashlib.sha512(str(0).encode()).digest()
        d['timestamp'] = int(self.timestamp * 1e6)
        d['nonce'] = '{0:05}'.format(random.randint(1, 100000)) #random int with fixed length 5 digits
        d['root'] = self.merkle.get_root()
        
        header_gen = json.dumps(d)
        
        self.chain.append(hashlib.sha512(str(header_gen).encode()).digest())   #add hashed header to chain
        self.current_block = hashlib.sha512(str(header_gen).encode()).digest()
        
        return self.current_block
        
    def add(self, block, transactions):
        # every few seconds a block should be added
        # immediately resolve fork after adding block

        if self.validate(block, transactions):
            # add block to chain
            self.chain[self.current_chain_idx].append(block)
        return self.chain
    
        
    def deserialize(self, block):
        # deserialize block header received from miner
        return json.loads(block)
        

    def validate(self, block, transactions):
        
        header = self.deserialize(block)
        
        #PoW, h(current_header) < TARGET
        hblock = hashlib.sha512(str(block).encode()).digest()
        if hblock >= self.target:
            return False
        
        #check root
        mt = MerkleTree()
        mt.add(transactions)
        root = mt.get_root()
        if root != header['root']:
            return False
        
        #previous header, fork
        if header['prev_hash'] != self.current_block:
            longest_chain = self.resolve()
            self.current_block = longest_chain[-1]
            self.current_chain_idx = self.chain.index(longest_chain) # or get from resolve()
            # TODO: how to find where the fork happened
            return False
        
        # check timestamp rules?
        
        return True
        
    def resolve(self):
        # duplicate if there is a fork
        # check which is the longest chain NOW
        # set the current block header to the main chain
        # do not delete a shorter chain
        
        # can implement a counter of the length of then chain
        return []



TARGET = '{0:05}'.format(random.randint(1, 100000))
