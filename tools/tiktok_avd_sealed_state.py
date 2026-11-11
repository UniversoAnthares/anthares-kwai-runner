#!/usr/bin/env python3
"""Encrypt and restore portable Android AVD state (never use an unencrypted cache).

Works with the private existing ANTHARES_BROWSER_STATE_KEY. Each chunk is
individually AES-256-GCM-authenticated and a mandatory terminal record detects
truncation. Decryption is complete before extracting any state. No secret,
cookie, Google identity, Android screen or archive content is printed.
"""
import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

MAGIC=b"ANAVD2"
CHUNK=1024*1024
MAX_RECORD=CHUNK+16
PROFILE="tiktok-persist"
START=struct.Struct(">I")

def key(salt):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    value=os.environ.get("ANTHARES_BROWSER_STATE_KEY","").encode("utf-8")
    if len(value)<24:
        raise RuntimeError("ENCRYPTION_KEY_MISSING_OR_SHORT")
    return HKDF(algorithm=hashes.SHA256(),length=32,salt=salt,
                info=b"Anthares-TikTok-Android-AVD-v1").derive(value)

def check_root(root):
    root=Path(root)
    folder=root/"avd"/(PROFILE+".avd")
    ini=root/"avd"/(PROFILE+".ini")
    if not folder.is_dir() or not ini.is_file():
        raise RuntimeError("EXPECTED_AVD_PROFILE_MISSING")
    return root

def run(args):
    p=subprocess.run(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=900)
    if p.returncode:
        raise RuntimeError("AVD_TAR_FAILED")

def seal(root,output):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    root=check_root(root)
    with tempfile.TemporaryDirectory(prefix="anthares-avd-seal-") as td:
        compressed=Path(td)/"state.tar.zst"
        run(["tar","--zstd","-cf",str(compressed),"-C",str(root),
             "avd/"+PROFILE+".avd","avd/"+PROFILE+".ini"])
        salt=os.urandom(16);noncebase=os.urandom(8)
        header=MAGIC+salt+noncebase
        aead=AESGCM(key(salt))
        dst=Path(output)
        dst.parent.mkdir(parents=True,exist_ok=True)
        temp=dst.with_name(dst.name+".partial")
        with compressed.open("rb") as source,temp.open("wb") as dest:
            dest.write(header)
            seq=0
            while True:
                buf=source.read(CHUNK)
                if not buf:break
                if seq >= 0xFFFFFFFF:raise RuntimeError("TOO_MANY_CHUNKS")
                index=seq.to_bytes(4,"big")
                encrypted=aead.encrypt(noncebase+index,buf,header+index+b"D")
                dest.write(START.pack(len(encrypted)))
                dest.write(encrypted)
                seq+=1
            index=seq.to_bytes(4,"big")
            dest.write(START.pack(16))
            dest.write(aead.encrypt(noncebase+index,b"",header+index+b"E"))
        os.replace(temp,dst)
        print("TIKTOK_AVD_SEALED=1",flush=True)

def unseal(archive,root):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="anthares-avd-unseal-") as td:
        compressed=Path(td)/"state.tar.zst"
        with Path(archive).open("rb") as src,compressed.open("wb") as dest:
            header=src.read(len(MAGIC)+16+8)
            if len(header)!=30 or not header.startswith(MAGIC):
                raise RuntimeError("SEALED_HEADER_INVALID")
            salt=header[6:22];noncebase=header[22:30]
            aead=AESGCM(key(salt))
            seq=0
            while True:
                count_bytes=src.read(4)
                if len(count_bytes)!=4:raise RuntimeError("SEALED_TRUNCATED")
                count=START.unpack(count_bytes)[0]
                if count<16 or count>MAX_RECORD:raise RuntimeError("SEALED_RECORD_INVALID")
                ciphertext=src.read(count)
                if len(ciphertext)!=count:raise RuntimeError("SEALED_TRUNCATED")
                index=seq.to_bytes(4,"big")
                if count==16:
                    try:
                        clear=aead.decrypt(noncebase+index,ciphertext,header+index+b"E")
                    except InvalidTag:raise RuntimeError("SEALED_AUTHENTICATION_FAILED") from None
                    if clear or src.read(1):raise RuntimeError("SEALED_TRAILING_DATA")
                    break
                try:
                    clear=aead.decrypt(noncebase+index,ciphertext,header+index+b"D")
                except InvalidTag:raise RuntimeError("SEALED_AUTHENTICATION_FAILED") from None
                dest.write(clear)
                seq+=1
                if seq>=0xFFFFFFFF:raise RuntimeError("TOO_MANY_CHUNKS")
        # Validate exactly the expected portable AVD member structure.
        listed=subprocess.run(["tar","--zstd","-tf",str(compressed)],
                              capture_output=True,text=True,timeout=120)
        if listed.returncode:raise RuntimeError("SEALED_TAR_INVALID")
        prefix="avd/"+PROFILE+".avd/"
        expected_ini="avd/"+PROFILE+".ini"
        entries=[s.strip() for s in listed.stdout.splitlines() if s.strip()]
        if not entries or not expected_ini in entries:
            raise RuntimeError("SEALED_TAR_MEMBERS_INVALID")
        for member in entries:
            if member.startswith("/") or ".." in Path(member).parts or (
                member not in ("avd/"+PROFILE+".avd",expected_ini) and
                not member.startswith(prefix)):
                raise RuntimeError("SEALED_TAR_MEMBERS_INVALID")
        run(["tar","--zstd","--no-same-owner","--no-same-permissions",
             "-xf",str(compressed),"-C",str(root)])
        check_root(root)
        print("TIKTOK_AVD_RESTORED=1",flush=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["seal","restore"])
    parser.add_argument("--root",required=True)
    parser.add_argument("--archive",required=True)
    args=parser.parse_args()
    if args.mode=="seal":seal(args.root,args.archive)
    else:unseal(args.archive,args.root)

if __name__=="__main__":
    try:main()
    except Exception as e:
        reason=str(e)
        known=("ENCRYPTION_KEY_MISSING_OR_SHORT","EXPECTED_AVD_PROFILE_MISSING",
               "AVD_TAR_FAILED","TOO_MANY_CHUNKS","SEALED_HEADER_INVALID",
               "SEALED_TRUNCATED","SEALED_RECORD_INVALID",
               "SEALED_AUTHENTICATION_FAILED","SEALED_TRAILING_DATA",
               "SEALED_TAR_INVALID","SEALED_TAR_MEMBERS_INVALID")
        print("TIKTOK_AVD_ERROR="+(reason if reason in known else type(e).__name__.upper()),file=sys.stderr)
        sys.exit(1)
