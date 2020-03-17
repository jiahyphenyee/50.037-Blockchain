import copy
import time
import sys
from block import Block
from transaction import Transaction
from miner import Miner, MinerListener
from blockchain import Blockchain

class SelfishMinerListener(MinerListener):
    # TODO implement message handling

class SelfishMiner(Miner):
    """Selfish Miner class"""

    def __init__(self, privkey, pubkey, address, listener=MinerListener):
        super().__init__(privkey, pubkey, address, listener=listener)
        self.hidden_chain = copy.deepcopy(self.blockchain)
        self.hidden_blocks = 0
    
    def get_longest_len(self, chain):
        """Get length of longest chain"""
        if chain == "public":
            return self.blockchain.last_node.block.blk_height
        else:
            return self.hidden_chain.last_node.block.blk_height


    def get_last_node(self):
            return self.hidden_chain.last_node

    def mine(self):
        """Blocks mined are not added to the public blockchain"""
        # if not self.check_final_balance(tx_collection):
        #     raise Exception("abnormal transactions!")
        #     return None

        new_block, prev_block = self.create_new_block(self.get_tx_pool())

        proof = self.proof_of_work(new_block)
        if proof is None:
            return None

        self.hidden_chain.add_block(new_block, proof, self.get_last_node())
        self.hidden_blocks += 1

        self.unconfirmed_transactions = []
        print(f"{self.type} at {self.address} created a block.")

        return new_block, prev_block

if __name__ == "__main__":
    """
        Mines blocks without broadcasting. 
        Only publishes blocks when miner has mined 5 new blocks quietly.
    """
    miner = SelfishMiner.new(("localhost", int(sys.argv[1])))
    time.sleep(5)

    # start mining
    while True:
        time.sleep(0.5)

        miner.mine()
        miner.get_own_balance()
        # stop mining
        # if miner.hidden_blocks == 3:
        #     break
        if miner.get_longest_len("public") < miner.get_longest_len("hidden"):
            break
    
    blocks = miner.hidden_chain.get_blks
    # broadcast last 5 blocks in the chain, starting from the 5th last block
    for i in range(-3, 0, 1):
        miner.broadcast_blk(blocks[i])
        time.sleep(1)