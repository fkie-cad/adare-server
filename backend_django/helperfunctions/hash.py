import hashlib

def hash_file_sha256(filecontent: bytes):
    h = hashlib.sha256()
    h.update(filecontent)
    return h.hexdigest()

def combine_hashes(hashes: list):
    h = hashlib.sha256()
    for hash in hashes:
        h.update(hash.encode())
    return h.hexdigest()