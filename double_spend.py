import sys
import time
import json
import copy
import random
from miner import Miner, MinerListener
from SPVClient import SPVClient
from addr_server import get_peers

"""
    Bad Players: 
        DSMiner: The miner that support double spend
    victim:
        Vendor: the one who suffered from double spending
"""

class DSMiner(Miner):
    # NORMAL = 0 # a mode that runs the same as normal miner
    # MUTATE = 1 # a mode that start to plant private chain
    # ATTACK = 2 # a mode that publish the withheld blocks to effect double spending

    def __init__(self, privkey, pubkey, address):
        super().__init__(privkey, pubkey, address, listener=DSMinerlistener)
        #self.mode = DSMiner.NORMAL
        self.unwanted_tx = set() # a set of transactions that the DSClient wanna invalidate
        self.fork_block = None
        self.hidden_chain = None
        self.hidden_blocks = 0
        #self.withheld_blocks = [] # these blocks will not be published until attack fired

    """ Override mining functions """
    def get_longest_len(self, chain):
        """Get length of longest chain"""
        if chain == "public":
            return self.blockchain.last_node.block.blk_height
        else:
            return self.hidden_chain.last_node.block.blk_height

    def get_tx_pool(self):
        return self.unconfirmed_transactions-self.unwanted_tx

    def get_last_node(self):
        return self.hidden_chain.last_node

    def mine(self):
        new_block, prev_block = self.create_new_block(self.get_tx_pool())

        proof = self.proof_of_work(new_block)
        if proof is None:
            return None

        self.hidden_chain.add_block(new_block, proof, self.get_last_node())
        self.hidden_blocks += 1

        self.unconfirmed_transactions = []
        print(f"{self.type} at {self.address} created a block.")

        return new_block, prev_block

# def run_miner(addr):
#     miner = Miner.new(addr)
#     print("New miner")
#     miner.set_peers(get_peers(addr))
#     print(miner.peers)
#     while True:
#         time.sleep(1)
#         miner.test_connection()

# def run_spv(addr):
#     spv = SPVClient.new(addr)
#     spv.set_peers(get_peers(addr))

if __name__ == '__main__':
    miner = DSMiner.new(("localhost", int(sys.argv[1])))
    time.sleep(5)

    peer = random.choice(miner.peers)

    if peer is None or len(miner.unwanted_tx) > 0:
        print("No peer in the network")

    else:
        peer_pubkey = peer["pubkey"]
        miner.fork_block = miner.get_last_node().block
        # add own transaction
        tx = miner.make_transaction(peer_pubkey, 1)
        miner.unwanted_tx.add(tx)
        # create a hidden chain to mine on
        miner.hidden_chain = copy.deepcopy(miner.blockchain)
        miner.get_own_balance()

    # wait for a few more transactions
    while len(miner.unconfirmed_transactions) < 5:
        continue
    
    while True:
        # start mining
        miner.mine()
        miner.get_own_balance()

        # stop mining when hidden chain is longer than public chain
        if miner.get_longest_len("public") < miner.get_longest_len("hidden"):
            break

    blocks = miner.hidden_chain.get_blks

    # broadcast hidden blocks one by one
    for i in range(-miner.hidden_blocks, 0, 1):
        miner.broadcast_blk(blocks[i])
        time.sleep(1)
