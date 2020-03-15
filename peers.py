"""
A fake DNS server that provides a list of address of
listening nodes on the network
"""

miners = [
    {
        "address": ("localhost", 6660),
        "pubkey": "nil"
      }
    ,
    {
        "address": ("localhost", 6661),
        "pubkey": "nil"
    }
    ,
    {
        "address": ("localhost", 6662),
        "pubkey": "nil"
    }

]
spvs = [
    {
        "address": ("localhost", 6667),
        "pubkey": "nil"
    },
    {
        "address": ("localhost", 6668),
        "pubkey": "nil"
    }
]


def get_peers(me):
    peers = []
    for miner in miners:
        if miner["address"] != me:
            peers.append(miner)
    for spv in spvs:
        if spv["address"] != me:
            peers.append(spv)

    return peers


if __name__ == '__main__':
    print(get_peers(("localhost", 6667)))






