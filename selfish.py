import copy
import time
from block import Block
from transaction import Transaction
from miner import Miner, MinerListener
from blockchain import Blockchain

class SelfishMiner(Miner):
    """Evil Miner class"""

    def __init__(self, privkey, pubkey, address, listener=MinerListener):
        super().__init__(privkey, pubkey, address, listener=listener)
        self.hidden_chain = copy.deepcopy(self.blockchain)
        self.hidden_blocks = 0

    def get_last_node(self):
            return self.hidden_chain.last_node

    def mine(self):
        """Blocks mined are not added to the public blockchain"""
        # need to include this transaction so miner can obtain reward
        coinbase_tx = Transaction.new(
            sender=self._keypair[0],
            receiver=self._keypair[1],
            amount=100,
            comment="Coinbase",
            key=self._keypair[0],

        )

        tx_collection = [coinbase_tx, self.get_tx_pool()]
        # if not self.check_final_balance(tx_collection):
        #     raise Exception("abnormal transactions!")
        #     return None

        new_block, prev_block = self.create_new_block(tx_collection)

        proof = self.proof_of_work(new_block)
        self.hidden_chain.add_block(new_block, proof, self.get_last_node())
        self.hidden_blocks += 1
        
        # if new_block is not None:
        #     self.broadcast_blk(new_block)

        self.unconfirmed_transactions = []
        print(f"{self.type} at {self.address} created a block.")

        return new_block, prev_block