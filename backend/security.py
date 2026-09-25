import hashlib, hmac, secrets


def hash_password(p):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(p.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return salt + ":" + digest


def verify_password(p, h):
    try:
        salt, digest = h.split(":")
        return hmac.compare_digest(
            hashlib.scrypt(p.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex(),
            digest,
        )
    except Exception:
        return False


def digest(v):
    return hashlib.sha256(v.encode()).hexdigest()
