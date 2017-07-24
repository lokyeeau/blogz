import hashlib

def make_pw_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()  # return a string that represents the hashed password as a result of running the PW through the sha256 system

def check_pw_hash(password, hash):
    if make_pw_hash(password) == hash:
        return True
    else: return False