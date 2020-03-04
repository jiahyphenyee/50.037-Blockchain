#!/usr/bin/env python

import hashlib
import base58
import ecdsa
import datetime
import time
import string
import random
import json
from Merkle import MerkleTree

class Block:
    
    def __init__(self, prev, transactions):
        self.transactions = transactions
        self.prev = prev #assume hashed
        self.timestamp = time.time()
        self.header = self.create_header()
        self.tree = {}
        self.create_merkle(transactions)
        
    def serialize(self):
        # Serializes object to CBOR or JSON string
        # serialize header to send to Blockchain     
        return json.dumps(self.header)
    
    def create_header(self):
        d = {}
        #d['prev_hash'] = hashlib.sha512(self.prev.encode()).digest()
        d['prev_hash'] = self.prev
        d['timestamp'] = int(self.timestamp * 1e6)
        d['nonce'] = '{0:05}'.format(random.randint(1, 100000)) #random int with fixed length 5 digits
        d['root'] = self.create_merkle(self.transactions)
        return d
        
    def create_merkle(self, transactions):
        mt = MerkleTree()
        mt.add(transactions)
        root = mt.get_root()
        self.tree = mt.tree
        return root
    



