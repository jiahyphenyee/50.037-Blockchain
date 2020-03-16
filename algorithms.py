import hashlib
import json
import ecdsa

def hash(str):
    concat = str(hashlib.sha256(str.encode()).digest()) + str(hashlib.sha256(str.encode()).digest())
    return hashlib.sha256(concat).hexdigest()


'''def hash_d(dict):
    return hash1(json.dumps(dic))'''


def verify_sig(sig, msg, pubkey):
    ecdsa_pubkey = ecdsa.VerifyingKey.from_string(bytes.fromhex(pubkey))
    return ecdsa_pubkey.verify(bytes.fromhex(sig), msg.encode())


def sign(msg, privkey):
    ecdsa_privkey = ecdsa.SigningKey.from_string(bytes.fromhex(privkey))
    return ecdsa_privkey.sign(msg.encode()).hex()