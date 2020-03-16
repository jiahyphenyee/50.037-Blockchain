import sys
import time
from miner import Miner
from SPVClient import SPVClient
from peers import get_peers


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
