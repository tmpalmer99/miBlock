import hashlib

def get_hash(address):
    hash = hashlib.sha1(address.encode()).hexdigest()
    return int(hash, 16)