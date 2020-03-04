import hashlib
import base58
import ecdsa
import datetime
import string
import random
import json
import base64

class Transaction:
    
    def __init__(self):
        pass
    
    @classmethod
    def new(cls, sender, receiver, amount, comment):
        cls.sender = sender
        cls.receiver = receiver
        cls.amount = amount
        cls.comment = comment
        cls.signature = ""
        
    def serialize(self):
        # Serializes object to CBOR or JSON string
        d = {}
        d["receiver"] = base64.encodebytes(self.receiver.to_string()).decode('ascii')
        d["sender"] =  base64.encodebytes(self.sender.to_string()).decode('ascii')
        d["amount"] = self.amount
        d["comment"] = self.comment
        return json.dumps(d)
        
    @classmethod
    def deserialize(cls, data):
        d = json.loads(data)
        d['sender'] = d['sender'].encode('ascii')
        d['receiver'] = d['receiver'].encode('ascii')
        obj = Transaction()
        obj.new(ecdsa.VerifyingKey.from_string(base64.decodebytes(d['sender'])), ecdsa.VerifyingKey.from_string(base64.decodebytes(d['receiver'])), d['amount'], d['comment'])
        return obj
    
    def sign(self, sk):
        serial = self.serialize()
        self.signature = sk.sign(serial.encode()) # can only sign byte-like object, not str
        
    def validate(self):
        # Validate transaction correctness ie verify signature
        val = self.sender.verify(self.signature, self.serialize().encode())
        return val
        
    def __eq__(self, other):
        if self.sender == other.sender and self.receiver == other.receiver and self.amount == other.amount and self.comment == other.comment:
            return True
        return False
        
# sk = ecdsa.SigningKey.generate()
# vk = sk.verifying_key

# rsk = ecdsa.SigningKey.generate()
# rvk = rsk.verifying_key

# t = Transaction()
# t.new(vk,rvk,10,'4')
# t.sign(sk)
# val = t.validate()
# print(val)

# t1 = t.serialize()
# t1d = t.deserialize(t1)
# print(t == t1d)