# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 15:48:35 2020

@author: user
"""
import hashlib
import json
import sys
import timeit
from ecdsa import SigningKey
from merkle_tree import *
import ecdsa
import base64
import random

def H(n, msg):
    m = hashlib.sha512(msg.encode('utf-8')).digest()
    return m[:n]


def collision(messages):
    hashes = {}
    for msg in messages:
        h = H(1, msg)
        if h in hashes.keys():
            return (msg, hashes[h])
        hashes[h] = msg
    return "no collision"


def collision(n):
    counter = 0
    hashes = {}
    start = timeit.timeit()
    while True:
        msg = str(counter)
        h = H(n, msg)
        if h in hashes.keys():
            end = timeit.timeit()
            print('time taken for collision: {}s'.format(end - start))
            return msg, hashes[h]
        hashes[h] = msg
        counter += 1


def preImage(image):
    start = timeit.timeit()
    counter = 0
    while True:
        msg = str(counter)
        h = H(1, msg)
        if h == image:
            end = timeit.timeit()
            print('time taken for preimage: {}s'.format(end - start))
            return msg
        counter += 1


class Transaction:
    def __init__(self, sender, receiver, amount, comment, nonce, signature=b""):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.comment = comment
        self.signature = signature
        self.nonce = nonce


    # Instantiates object from passed values

    @classmethod
    def new(cls, sender, receiver, amount, comment, key, nonce):
        # cls.sender = sender  # a public key of sender
        # cls.receiver = receiver  # a public key of receiver
        # cls.amount = amount  # transaction amount, an interger>0
        # cls.comment = comment  # arbitary text can be empty
        transaction = cls(sender, receiver, amount, comment, nonce)
        transaction.signature = transaction.sign(key)
        return transaction

    def serialize_sig(self):
        # Serializes object to CBOR or JSON string
        dic = {}
        dic['sender'] = base64.encodebytes(self.sender.to_string()).decode('ascii')
        dic['receiver'] = base64.encodebytes(self.receiver.to_string()).decode("ascii")
        dic['nonce'] = self.nonce
        dic['amount'] = self.amount
        dic['comment'] = self.comment
        serialized = json.dumps(dic)
        return serialized

    def serialize(self):
        # Serializes object to CBOR or JSON string
        dic = {}
        dic['sender'] = base64.encodebytes(self.sender.to_string()).decode('ascii')
        dic['receiver'] = base64.encodebytes(self.receiver.to_string()).decode("ascii")
        dic['nonce'] = self.nonce
        dic['amount'] = self.amount
        dic['comment'] = self.comment
        dic['signature'] = base64.encodebytes(self.signature).decode('ascii')
        serialized = json.dumps(dic)
        return serialized

    @classmethod
    def deserialize(cls, data):
        # Instantiates/Deserializes object from CBOR or JSON string
        deserialized = json.loads(data)
        deserialized['sender'] = deserialized['sender'].encode('ascii')
        deserialized['receiver'] = deserialized['receiver'].encode('ascii')
        deserialized['signature'] = deserialized['signature'].encode('ascii')
        trans = Transaction(ecdsa.VerifyingKey.from_string(base64.decodebytes(deserialized['sender'])),
                  ecdsa.VerifyingKey.from_string(base64.decodebytes(deserialized['receiver'])),
                  deserialized['amount'], deserialized['comment'], deserialized['nonce'], base64.decodebytes(deserialized['signature']))
        try:
            if trans.validate():
                return trans
        except ecdsa.keys.BadSignatureError:
            print("Oops!", sys.exc_info()[0], "occured.")
            return None

    def sign(self, sk):
        # Sign object with private key passed
        # That can be called within new()
        m = self.serialize_sig()
        return sk.sign(m.encode())

    def validate(self):
        # Validate transaction correctness ie verify signature
        # Can be called within from_json()
        # vk = self.sender.get_verifying_key()
        # vk.verify(self.signature, data.encode())
        return self.sender.verify(self.signature, self.serialize_sig().encode())

    def __eq__(self, other):
        # Check whether transactions are the same
        return self.signature == other.signature




if __name__ == "__main__":
    # m256 = hashlib.sha256(b"Blockchain Technology")
    # print(m256.digest())
    #
    # m512 = hashlib.sha512()
    # m512.update(b"Blockchain Technology")
    # print(m512.digest())
    #
    # m3_256 = hashlib.sha3_256()
    # m3_256.update(b"Blockchain Technology")
    # print(m3_256.digest())
    #
    # m3_512 = hashlib.sha3_512()
    # m3_512.update(b"Blockchain Technology")
    # print(m3_512.digest())
    #
    # print(b"\x00" * 2)
    # a = b"\x00"
    # print(preImage(a))
    # print(collision(4))
    # sk = SigningKey.generate()  # uses NIST192p
    # sk1 = SigningKey.generate()
    # vk = sk.verifying_key
    # signature = sk1.sign(b"message")
    # print(vk.verify(signature, b"message"))
    sk = SigningKey.generate()
    vk = sk.get_verifying_key()
    sk1 = SigningKey.generate()
    vk1 = sk1.get_verifying_key()
    t = Transaction.new(vk, vk1, 4, 'r', sk)
    print(t.validate())
    print(t.signature)
    s = t.serialize()
    t1 = t.deserialize(s)
    print(t1 == t)
    # transactions = list()
    # for i in range(random.randint(100,1000)):
    #     sk = SigningKey.generate()
    #     vk = sk.get_verifying_key()
    #     sk1 = SigningKey.generate()
    #     vk1 = sk1.get_verifying_key()
    #     t = Transaction.new(vk, vk1, 4, 'r', sk)
    #     s = t.serialize()
    #     transactions.append(s)
    # t = MerkleTree(transactions)
    # for i in range(10):
    #     j = random.randint(0,len(transactions))
    #     proofs = t.get_proof(transactions[j])
    #     print(verify_proof(MerkleTree.compute_hash(transactions[j]), proofs, t.get_root()))