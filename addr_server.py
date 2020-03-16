"""
A fake DNS server that provides a list of address of
listening nodes on the network
"""

nodes = []


def register(my_node):
    nodes.append({
        "type": my_node.type,  # Miner, SPVClient
        "address": my_node.address,
        "pubkey": my_node.pubkey
    })
    print(f" Registered new node of type {my_node.type} : {my_node.address}")


def get_peers(my_node):
    my_peers = []
    for node in nodes:
        if node["address"] != my_node.address:
            my_peers.append(node)

    return my_peers









