import sys
import time
import json
from miner import Miner, MinerListener
from SPVClient import SPVClient
from peers import get_peers

"""
    Bad Players: 
        DSMiner: The miner that support double spend
    victim:
        Vendor: the one who suffered from double spending
"""
class DSMinerlistener(MinerListener):


class DSMiner(Miner):
    NORMAL = 0 # a mode that runs the same as normal miner
    MUTATE = 1 # a mode that start to plant private chain
    ATTACK = 2 # a mode that publish the withheld blocks to effect double spending

    def __init__(self, privkey, pubkey, address):
        super().__init__(privkey, pubkey, address, listener=DSMinerlistener)
        self.mode = DSMiner.NORMAL
        self.unwanted_tx = set() # a set of transactions that the DSClient wanna invalidate
        self.fork_block = None
        self.withheld_blocks = [] # these blocks will not be published until attack fired
        self.pubchain_count = 0

    """ Override mining functions """
    def get_tx_pool(self):
        return self.unconfirmed_transactions-self.unwanted_tx

    def broadcast_blk(self,new_blk):
        if self.mode == DSMiner.NORMAL:
            blk_json = new_blk.serialize()
            self.broadcast_message("b" + json.dumps({"blk_json": blk_json}))
        elif self.mode == DSMiner.MUTATE:
            blk_json = new_blk.serialize




def run_miner(addr):
    miner = Miner.new(addr)
    print("New miner")
    miner.set_peers(get_peers(addr))
    print(miner.peers)
    while True:
        time.sleep(1)
        miner.test_connection()

def run_spv(addr):
    spv = SPVClient.new(addr)
    spv.set_peers(get_peers(addr))


def main():
    """Main function"""
    print("Start simulation!")
    try:
        if sys.argv[1] == "miner":
            run_miner(("localhost", int(sys.argv[2])))
        elif sys.argv[1] == "spv":
            run_spv(("localhost", int(sys.argv[2])))
    except IndexError:
        print("Not enough arguments provided.")


if __name__ == '__main__':
    main()
