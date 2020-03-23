# 50.037-Blockchain Project 1
### Notes
- the model we used here for SUTDCoin is Account/Balance model.

### Requirements for running demonstration
1. Have python3 installed
2. Have wxPython installed. 
   For Windows and Mac, please install using `pip install -U wxPython`

### Run GUI Demo
- After cloning/downloading this repo, open your terminal and cd to the root folder of this project
- `demo.sh` is our file for running the demo
- -m will set miner number
- -s will set SPV client number
- -f will set selfish miner number
- e.g. run `./demo.sh -m 2 -s 1` to start 2 miners and 1 spv client


#### 1. Miner Competition and Coin Creation
To simulate miner competition, we can run `./demo.sh -m 3` to create 3 miners.
- For each miner, click on `Join Network` button, this will register the miner at the Address server. They will also be receiving updates on network nodes that are listening and record the peers. You will see following message in their respective loggers.
```
Miner at ('localhost', 12348):  Join the network
Miner at ('localhost', 12348):  ======= Receive updates on network nodes
Miner at ('localhost', 12348):  Peers: []
```
- For each miner, clink on `Start Mining` button, this will set the miners mining for proof. Once a block is mined, you should see the following line somewhere in the logger of that miner that show you the proof and time spent on mining:
```
Miner at ('localhost', 12348):  Found proof = 00000522aaafc965668e4c0e5ae034c87a7720604c5762b91587890d5a78aeb1 < TARGET in 4.400625944137573 seconds
```
- The miner will then broadcast the block to its peers. The other miners will verify the proof and add the block to their own copy of chain. We can see the blockchain visualized as well every time when a new block is added. 
```
`- root
   `- hash: 00000522aaafc965668e4c0e5ae034c87a7720604c5762b91587890d5a78aeb1, number of transactions: 0
```

- Under the `Update Balance` button, the balance should be updated for the miner who successfully mined the block. If not, please press the `Update Balance` button to update.
- Sometimes Forking may happen if miners mine the block at the same time.
- For demostration purpose, mining event is only triggered once for one click. If a new block is mined or mining process stopped midway as others found a block, we need to manually press `Start Mining` button again to continue mining for another block

#### 2. Fork Resolution
Fork resolution is done by checking the nodes in the blockchain with no children, and then comparing which one has the longest chain. This is implemented in Blockchain under last_node property, which fetches the last block of the longest chain.
```
@property
    def last_node(self):
        """
        A quick pythonic way to retrieve the most recent block in the chain. Note that
        the chain will always consist of at least one block (i.e., genesis block)
        """
        return self.resolve()
```

#### 3. Miners and SPV Clients payments
To simulate Miner and SPV client payments, we can run `./demo.sh -m 2 -s 1` to create 2 miners and 1 spv client.
- Again, make them join the network to prove their existence and find other peers
- To be able to create transactions, we need to create coins first. So put the miners to mining.
- After a new block is mined and broadcasted, the spv client will receive new header as well. You might receive the following message. Press Get Headers Btn to sync headers with full blockchain node (miner here).
```
SPVClient at ('localhost', 22346):  Header with non-existing prev-hash. Do you want to request headers?
```
- Now let us pass some money from the miner to a spv client. In the `recipient` field, we use the port number of the spv client for simplicity. After we fill in the `amount`, we press  `Make A Transaction` to send the money. Note that the transaction is not confirmed yet. You should see that both miners receive a unconfirmed transaction. Every time a transaction is received, the miner will verify signature and nonce. (Checking nonce to prevent replay attack)
```
Miner at ('localhost', 12347):  ======= Receive new transaction from peer
Miner at ('localhost', 12347):  most recent nonce = 0 vs new nonce = 1
Miner at ('localhost', 12347):  New transaction passed resending check based on most updated chain.
Miner at ('localhost', 12347):  1 number of unconfirmed transactions
```
- If spv client request balance now, it will not see any increase in balance. So we will make the miners mine again to confirm this transaction. We will be able to see number of transactions in the new block mined.
```
`- root
   `- hash: 000004b55790d78dd21996a3ad9920e6af4bc8adc54017ea367bcde2765bb01d, number of transactions: 0
      `- hash: 00000e982f3bb572f3af7e0f215acc5f49b6264f85600620e377d6d5e1fc5c45, number of transactions: 1
```
- Now when spv client press Update Balance to request for balance, it will be updated.

#### 4. Transaction Verification and Resending Protection
- We will continue the Resending Protection demonstration from the previous one. To simply demonstration, we have made spv client to keep a list of interested transactions (all the transactions it has made to peers). To verify if a interested transaction is already in the blockchain we can choose the transaction and press verify to request proof from miner or press Resend to resend the transaction. To do this demo we will ask the spv clients to make a few transactions to the miners.
- If we verify a transaction that is already in the chain (that means miners has mined new blocks since you made transactions), you will see something below in spv's logger window.
```
SPVClient at ('localhost', 22346):  Requesting Proof from full blockchain node
SPVClient at ('localhost', 22346):  Transaction exit in the blockchain:)
```
- If we resend a transaction that is already in the chain, we will see the following in the miners' logger windows when they receive the new transaction
```
Miner at ('localhost', 12346):  New transaction failed resending check based on most updated chain.
```
- If we resend a transaction that is not in the chain (unconfirmed), it will be able to pass the check initially. But when miners try to mine new block with the gathered collection of transactions, you will see the following in the miners' logger windows
```
Miner at ('localhost', 12346):  Detect conflicting nonce from transactions in collection
```

#### 5. Double Spend Attack
- Run `./demo.sh -m 3` to create 3 miners. One of them will be Double Spend (DS).
- For each miner, `Join Network` to find peers in the network. Then `Start Mining` for all miners.
- Select `Start Mining` more than once or create transactions to create and transfer coins.
- When miners have sufficient coins to make transactions, create a few transactions. The chosen DS miner must create at least one transaction.
- Select `Start DS` to notify miner to conduct the attack. The miner will prepare the replacement transactions to be added to the forked block.
- `Start Mining` on all other miners besides the DS to validate the transactions.
- Then `DS Mine` by the DS miner. Each click mines 1 block. Repeat till the DS private chain is longer than the public chain.

The DS Miner will then broadcast the blocks to all other miners. The balance of DS miner should reflect that the previous transaction has been invalidated. He will also receive the rewards of the blocks he mined.

#### 6. Selfish Mining Attack
- Run `./demo.sh -m 1 -f 1` to create 1 miner and 1 selfish miner
- For each one, 'Join Network' to find peers in the network.
- Then we can slowly click mine on either the selfish miner or miner to work through the algorithm and see the broadcasting behaviour of the selfish miner when it has mined a block or when the other miner has mined a block



