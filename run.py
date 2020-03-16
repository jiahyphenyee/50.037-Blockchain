import sys
import time
from miner import Miner
from SPVClient import SPVClient
from addr_server import get_peers

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
