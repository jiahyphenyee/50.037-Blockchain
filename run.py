import sys
import time
from miner import Miner
from selfish import SelfishMiner
from SPVClient import SPVClient
from addr_server import get_peers

def run_selfish_miner(addr):
    """
        Mines blocks without broadcasting. 
        Only publishes blocks when miner has mined 5 new blocks quietly.
    """
    miner = SelfishMiner.new(addr)
    while True:
        time.sleep(0.5)
        miner.mine()
        if miner.hidden_blocks == 5:
            break
    
    blocks = miner.hidden_chain.get_blks
    # broadcast last 5 blocks in the chain, starting from the 5th last block
    for i in range(-5, 0, 1):
        miner.broadcast_blk(blocks[i])
        time.sleep(1)
        

def run_miner(addr):
    miner = Miner.new(addr)
    while True:
        time.sleep(1)
        peer = miner.find_peer_by_type("SPVClient")
        if peer is not None:
            miner.make_transaction(peer["pubkey"])



def run_spv(addr):
    spv = SPVClient.new(addr)



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
