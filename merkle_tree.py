import hashlib


class MerkleNode():
    def __init__(self,hash,leftChild = None, rightChild = None, isLeaf = False, isLeft = False):
        self.hash = hash
        self.parent = None
        self.isLeft = isLeft
        self.isLeaf = isLeaf
        self.leftChild = leftChild
        self.rightChild = rightChild


class MerkleTree():
    def __init__(self, transactions = list()):
        self.leaves = list()
        self.add(transactions)
        self.root = self.build(self.leaves)

    def add(self, transactions):
        # Add entries to tree
        leaves = list()
        i = 0
        for transaction in transactions:

            leaves.append(MerkleNode(MerkleTree.compute_hash(transaction), isLeaf=True))
        self.leaves = leaves

    def build(self, leaves):
        # Build tree computing new root
        num_leaves = len(leaves)
        if num_leaves == 1:
            return leaves[0]

        parents = []

        i = 0
        while i < num_leaves:
            left_child = leaves[i]
            left_child.isLeft = True
            right_child = leaves[i + 1] if i + 1 < num_leaves else left_child

            parents.append(self.create_parent(left_child, right_child))

            i += 2

        return self.build(parents)

    def create_parent(self,leftchild,rightchild):
        parent = MerkleNode(self.compute_hash(leftchild.hash + rightchild.hash),leftchild,rightchild)
        leftchild.parent = parent
        rightchild.parent = parent

        # print("Left child: {}, Right child: {}, Parent: {}".format(
        #     leftchild.hash, rightchild.hash, parent.hash))
        return parent

    def get_proof(self, entry):
        # Get membership proof for entry
        entryHash = self.compute_hash(entry)
        proofs = list()
        idx = -1
        for i in range(len(self.leaves)):
            if entryHash == self.leaves[i].hash:
                idx = i
                break
        if idx == -1:
            return proofs

        parent = self.leaves[idx].parent
        if parent is None:
            return [self.leaves[idx]]
        if parent.leftChild.hash == self.leaves[idx].hash:
            proofs.append(parent.rightChild)
        else:
            proofs.append(parent.leftChild)

        while parent != self.root:
            newParent = parent.parent
            if newParent.leftChild.hash == parent.hash:
                proofs.append(newParent.rightChild)
            else:
                proofs.append(newParent.leftChild)
            parent = newParent

        return proofs

    def get_root(self):
        # Return the current root
        return self.root

    @staticmethod
    def compute_hash(data):
        data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()


def verify_proof(entry, proofs, root):
    # Verify the proof for the entry and given root. Returns boolean.
    entry = MerkleTree.compute_hash(entry)
    if len(proofs) == 0:
        return False
    if len(proofs) == 1:
        return entry == proofs[0].hash and entry == root.hash
    for proof in proofs:
        if proof.isLeft:
            hash = MerkleTree.compute_hash(proof.hash + entry)
        else:
            hash = MerkleTree.compute_hash(entry + proof.hash)
        if hash != proof.parent.hash:
            return False
        entry = hash
    if entry != root.hash:
        return False
    return True
