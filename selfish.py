"""Evil Miner"""

import copy
import time
from block import Block
from transaction import Transaction
from miner import Miner, MinerListener
from blockchain import Blockchain
from algorithms import *

class SelfishMiner(Miner):

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

        self.badchain = Blockchain()
        new_block, prev_block = self.create_new_block(tx_collection)

        proof = self.proof_of_work(new_block)
        #self.blockchain.add_block(new_block, proof)
        self.badchain.add_block(new_block, proof, self.get_last_node().block)
        
        

        if new_block is not None:
            self.broadcast_blk(new_block)

        self.unconfirmed_transactions = []
        print(f"{self.type} at {self.address} created a block.")

        return new_block, prev_block