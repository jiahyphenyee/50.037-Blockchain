import hashlib
import base58
import ecdsa
import datetime
import string
import random
import json
import base64

class MerkleTree:
    def __init__(self):
        self.tlist = [] # list of transactions
        self.tree = {}
        self.level = 0 # level of tree where root is at
    
    def add(self, t):
        # t: list of transactions forming the tree
        self.tree[0] = []
        
        for i in range(len(t)):
            self.tlist.append(t[i])
            self.tree[0].append(str(hashlib.sha256(t[i].encode()).digest()))
        
        print("done adding first layer")
        self.build()
        return self.tree
            
    def build(self):
        level = 1
        temp = self.tree[0]
        # Build tree computing new root
        while len(temp) > 1:
            hash_list = self.level_hash(temp)
            self.tree[level] = hash_list
            temp = hash_list
            level += 1
            
        self.level = level - 1
        print("tree successfully built")
        
        return self.tree 
        
        
    def level_hash(self, t):
        temp = []
        r = len(t)-1
        
        if len(t)%2 == 0:
            r = len(t)
        
        for i in range(r):
            if i%2 == 0:
                #h1 = str(hashlib.sha256(str(t[i]).encode()).digest()) # hash left
                #h2 = str(hashlib.sha256(str(t[i+1]).encode()).digest()) # hash right
                h1 = t[i]
                h2 = t[i+1]
                h3 = h1 + h2 # concat
                h3 = hashlib.sha256(str(h3).encode()).digest() # hash the concat
                temp.append(h3) 
                
            elif i%2 != 0:
                pass
            
        if len(t)%2 != 0:
            # if it is single last root
            #h3 = str(t[len(t)-1])
            h3 = hashlib.sha256(str(t[len(t)-1]).encode()).digest()
            temp.append(h3)
            
        return temp

    def get_proof(self, transaction):
        # Get membership proof for entry
        # return min no of nodes needed to compute root
        nodes = {}
        idx = self.tlist.index(transaction)
        
        if idx == len(self.tlist)-1:
            nodes[0] = ["", "N"]
        elif idx%2 == 0:
            #left
            nodes[0] = [self.tree[0][idx+1], "R"]
            
        else:
            #right
            nodes[0] = [self.tree[0][idx-1], "L"]
            
        level = 1
        idx = idx // 2
        
        while level != self.level:
            if idx%2 == 0:
                nodes[level] = [self.tree[level][idx+1], "R"]
            else:
                nodes[level] = [self.tree[level][idx-1], "L"]
            level += 1
            idx = idx//2  #get current index on next upper level
            
        return nodes
    
    def get_root(self):
        # Return the current root
        root = self.tree[self.level][0]
        return root

def verify_proof(transaction, proof, root):
    # Verify the proof for the entry transaction and given root. Returns boolean.
    level = 0
    c = str(hashlib.sha256(transaction.encode()).digest())
    
    while level in proof:
        if proof[level][1] == "R":
            c = c + proof[level][0]

        elif proof[level][1] == "L":
            c = proof[level][0] + c
        
        c = hashlib.sha256(str(c).encode()).digest() # hash the concat
        level += 1
    
    if c == root:
        return True
    
    return False


# mt = MerkleTree()
# mt.add(["1","2","3","4","5","6","7"])
# print(mt.tree)
# root = mt.get_root()
# proof = mt.get_proof("7")
# print(verify_proof("7", proof, root))

