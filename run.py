import base64
import sys
import time
import ecdsa
from miner import Miner
from SPVClient import SPVClient
from addr_server import AddressServer



def run_miner(addr):
    miner = Miner.new(addr)
    while True:
        time.sleep(3)
        peer = miner.find_peer_by_type("SPVClient")

        if peer is not None:
            print(peer)
            peer_pubkey = peer["pubkey"]
            miner.make_transaction(peer_pubkey, 50)
        else:
            print("No peers in the network")



def run_spv(addr):
    spv = SPVClient.new(addr)
    while True:
        time.sleep(5)
        peer = spv.find_peer_by_type("Miner")




def main():
    """Main function"""
    print("Start simulation!")
    try:
        if sys.argv[1] == "server":
            AddressServer()
        elif sys.argv[1] == "miner":
            run_miner(("localhost", int(sys.argv[2])))
        elif sys.argv[1] == "spv":
            run_spv(("localhost", int(sys.argv[2])))
    except IndexError:
        print("Not enough arguments provided.")


if __name__ == '__main__':
    main()
