import sys
import time
import json
import copy
import random
from miner import Miner, MinerListener
from SPVClient import SPVClient

"""
    Bad Players: 
        DSMiner: The miner that support double spend
    victim:
        Vendor: the one who suffered from double spending
"""

class DSMiner(Miner):
    NORMAL = 0 # a mode that runs the same as normal miner
    MUTATE = 1 # a mode that start to plant private chain
    ATTACK = 2 # a mode that publish the withheld blocks to effect double spending

    def __init__(self, privkey, pubkey, address, listener=MinerListener):
        super().__init__(privkey, pubkey, address, listener=listener)
        self.mode = DSMiner.NORMAL
        self.unwanted_tx = list() # a set of transactions that the DSClient wanna invalidate
        self.fork_block = None
        self.hidden_blocks = list()
        #self.withheld_blocks = [] # these blocks will not be published until attack fired

    """DS Miner functions"""
    def setup_ds_attack(self):
        self.fork_block = self.get_last_node().block
        self.log("Private Chain created, ready for DS attack")

    def get_longest_len(self, chain):
        """Get length of longest chain"""
        if chain == "public":
            return self.blockchain.last_node.block.blk_height
        else:
            return self.blockchain.fork_block.blk_height + len(self.hidden_blocks)

    """ Override mining functions """
    def get_tx_pool(self):
        final_tx_list = list(set(self.unconfirmed_transactions) - set(self.unwanted_tx))
        return final_tx_list

    def get_last_node(self):
        return self.hidden_chain.last_node

    """ Double Spending """ 
    def ds_mine(self):
        self.log(f"mining on block height of {self.blockchain.last_node.block.blk_height} ....")
        new_block, prev_block = self.create_new_block(self.get_tx_pool())

        proof = self.proof_of_work(new_block, self.stop_mine)
        if proof is None:
            return None

        self.hidden_chain.add_block(new_block, proof, self.get_last_node().block)
        self.hidden_blocks += 1

        self.unconfirmed_transactions = []
        self.log(" Mined a new block +$$$$$$$$")
        print("""
                    |---------|
                    | dsblock |
                    |---------|
        """)

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
    time.sleep(10)

    peer = random.choice(miner.peers)

    if peer is None or len(miner.unwanted_tx) > 0:
        print("No peer in the network")

    else:
        peer_pubkey = peer["pubkey"]
        # add own transaction
        tx = miner.make_transaction(peer_pubkey, 1)
        miner.unwanted_tx.append(tx)
        miner.log("Starting Double Spend attack")
        # create a hidden chain to mine on
        miner.hidden_chain = copy.deepcopy(miner.blockchain)
        miner.fork_block = miner.get_last_node().block
        miner.get_own_balance()

    time.sleep(5)
    # wait for a few more transactions
    # while len(miner.unconfirmed_transactions) < 5:
    #     continue
    
        # TODO: Check that my transaction has been added to the original chain?

    while True:
        # start mining
        miner.mine()
        miner.get_own_balance()

        # stop mining when hidden chain is longer than public chain
        if miner.get_longest_len("public") < miner.get_longest_len("hidden"):
            break

    blocks = miner.hidden_chain.get_blks()

    # broadcast hidden blocks one by one
    miner.log("Starting Double Spend Broadcast")
    for i in range(-miner.hidden_blocks + 1, 0, 1):
        miner.broadcast_blk(blocks[i], blocks[i].hash)
        time.sleep(1)
