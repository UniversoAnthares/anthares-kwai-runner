#!/usr/bin/env python3
"""Independent session vault. Authenticated encryption, no app-specific UI logic."""
import argparse,hashlib,hmac,json,os,secrets,sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
MAGIC="anthares.session.v1"
def derive(secret,salt):
    return hashlib.scrypt(secret.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32)
def encrypt(data,secret,identity):
    salt=secrets.token_bytes(16);nonce=secrets.token_bytes(12)
    header={"schema":MAGIC,"identity_hash":hashlib.sha256(identity.casefold().encode()).hexdigest(),"salt":salt.hex(),"nonce":nonce.hex()}
    aad=json.dumps(header,sort_keys=True,separators=(",",":")).encode()
    header["ciphertext"]=AESGCM(derive(secret,salt)).encrypt(nonce,data,aad).hex()
    return json.dumps(header,sort_keys=True).encode()
def decrypt(blob,secret,identity):
    h=json.loads(blob)
    if h.get("schema")!=MAGIC or not hmac.compare_digest(h["identity_hash"],hashlib.sha256(identity.casefold().encode()).hexdigest()):
        raise ValueError("identity or format mismatch")
    ciphertext=bytes.fromhex(h.pop("ciphertext"))
    aad=json.dumps(h,sort_keys=True,separators=(",",":")).encode()
    return AESGCM(derive(secret,bytes.fromhex(h["salt"]))).decrypt(bytes.fromhex(h["nonce"]),ciphertext,aad)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("seal","open"))
    p.add_argument("source");p.add_argument("destination")
    args=p.parse_args()
    secret=os.environ.get("KWAI_SESSION_VAULT_KEY","")
    identity=os.environ.get("KWAI_EXPECTED_ACCOUNT","")
    if len(secret)<24 or not identity:
        sys.exit("SESSION_VAULT_CONFIG_MISSING")
    data=Path(args.source).read_bytes()
    result=encrypt(data,secret,identity) if args.action=="seal" else decrypt(data,secret,identity)
    target=Path(args.destination)
    if target.exists():sys.exit("SESSION_VAULT_REFUSE_OVERWRITE")
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"wb") as out:out.write(result)
    print("SESSION_VAULT_"+("SEALED" if args.action=="seal" else "OPENED"))
if __name__=="__main__":main()
