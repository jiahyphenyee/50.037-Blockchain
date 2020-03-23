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
#### 5. 51% Attack
- Install mongodb server community edition from [here](https://www.mongodb.com/download-center/community)
- create a new database called `isit_database_mongo`
- make sure mongo server is running on port:27017
- run `mongod` in any shell
- create an admin user with username: `isit_database_mongo` password: `password`

for the API, go [here](https://docs.mongodb.com/manual/reference/method/)
To GET data from the database
- import `from common.util import mongo`
- use the syntax: `mongo.db.<collection name>.<mongo function>` e.g. `mongo.db.logs.find({})

#### 6. Selfish Mining Attack
- Install MySQL server version 5.7.27 from [here](https://dev.mysql.com/downloads/windows/installer/5.7.html)
- Create the followint table in existing database:
```
CREATE TABLE IF NOT EXISTS `kindle_reviews` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `asin` VARCHAR(255) NOT NULL,
  `helpful` VARCHAR(255) NOT NULL,
  `overall` INT(11) NOT NULL,
  `reviewText` TEXT NOT NULL,
  `reviewTime` VARCHAR(255) NOT NULL,
  `reviewerID` VARCHAR(255) NOT NULL,
  `reviewerName` VARCHAR(255) NOT NULL,
  `summary` VARCHAR(255) NOT NULL,
  `unixReviewTime` INT(11) NOT NULL,
  PRIMARY KEY (`id`));

```


