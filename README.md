# 50.037-Blockchain Project 1

### Requirements for running demonstration
1. Have python3 installed
2. Have wxPython installed. 
   For Windows and Mac, please install using `pip install -U wxPython`

### Run GUI Demo
- After cloning/downloading this repo, open your terminal and cd to the root folder of this project
- `demo.sh` is our file for running the demo
- -m will Set miner number
- -s will Set SPV client number
- e.g. run `./demo.sh -m 2 -s 1` to start 2 miners and 1 spv client


#### 1. Miner Competition and Coin Creation
To simulate miner competition, we can run `./demo.sh -m 3` to create 3 miners.
- For each miner, click on Join Network button, this will register the miner at the Address server. They will also be receiving updates on network nodes that are listening and record the peers. You will see following message in their respective loggers.
```
Miner at ('localhost', 12348):  Join the network
Miner at ('localhost', 12348):  ======= Receive updates on network nodes
Miner at ('localhost', 12348):  Peers: []
```
- For each miner, clink on Start Mining button, this will set the miners mining for proof. Once a block is mined, you should see the following line somewhere in the logger of that miner that show you the proof and time spent on mining:
```
Miner at ('localhost', 12348):  Found proof = 00000522aaafc965668e4c0e5ae034c87a7720604c5762b91587890d5a78aeb1 < TARGET in 4.400625944137573 seconds
```
- The miner will then broadcast the block to its peers. The other miners will verify the proof and add the block to their own copy of chain. We can see the blockchain visualized as well every time when a new block is added. 
```
`- root
   `- hash: 00000522aaafc965668e4c0e5ae034c87a7720604c5762b91587890d5a78aeb1, number of transactions: 0
```

- Under the Update Balance button, the balance should be updated for the miner who successfully mined the block. If not, please press the Update Balance button to update.
- Sometimes Forking may happen if miners mine the block at the same time.
- For demostration purpose, mining event is only triggered once for one click. If a new block is mined or mining process stopped midway as others found a block, we need to manually press Start Mine button again to continue mining for another block

#### 2. Fork Resolution


#### 3. Miners and SPV Clients payments
To simulate Miner and SPV client payments, we can run `./demo.sh -m 2 -s 1` to create 2 miners and 1 spv client.
- Again, make them join the network to prove their existence and find other peers
- To be able to create transactions, we need to create coins first. So put the miners to mining.
- After the miners

#### 4. Transaction Resending Protection

#### 5. Double Spend Attack
- Run `./demo.sh -m 2` to create 3 miners. One of them will be Double Spend (DS).
- For each miner, `Join Network` to find peers in the network. Then `Start Mining` for all miners.
- Select `Start Mining` more than once or create transactions to create and transfer coins.
- When miners have sufficient coins to make transactions, create a few transactions. The chosen DS miner must create at least one transaction.
- Select `Start DS` to notify miner to conduct the attack. The miner will prepare the replacement transactions to be added to the forked block.
- `Start Mining` on all other miners besides the DS to validate the transactions.
- Then `DS Mine` by the DS miner. Each click mines 1 block. Repeat till the DS private chain is longer than the public chain.

The DS Miner will then broadcast the blocks to all other miners. The balance of DS miner should reflect that the previous transaction has been invalidated. He will also receive the rewards of the blocks he mined.

#### 6. Selfish Mining Attack



