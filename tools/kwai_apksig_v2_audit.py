#!/usr/bin/env python3
"""Independent read-only APK Signature Scheme v2 integrity audit.

Uses the Android AOSP v2 structure/content-digest contract, not Google
apksigner. Does not change APK bytes, download files, launch Android,
authenticate accounts, or publish content.

Compatible with Hostinger Python 3.6 + cryptography 3.2.1.
https://source.android.com/docs/security/features/apksigning/v2
"""
from __future__ import print_function
import argparse
import hashlib
import hmac
import json
import os
import re
import struct
import sys
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, ec, rsa, dsa

V2_BLOCK_ID = 0x7109871A
APK_MAGIC = b"APK Sig Block 42"
EOCD_MAGIC = b"PK\x05\x06"
CHUNK_BYTES = 1048576
SIGNER_SHA256 = "bb8d2610b048bee8e9f96cd5456d8b8b5a0806d2a41dffdf744d2a8720e81047"
MAX_BLOCK = 32 * 1024 * 1024
SUPPORTED_ALGOS = {
    0x0101: ("sha256", "pss"),
    0x0102: ("sha512", "pss"),
    0x0103: ("sha256", "pkcs1"),
    0x0104: ("sha512", "pkcs1"),
    0x0201: ("sha256", "ecdsa"),
    0x0202: ("sha512", "ecdsa"),
    0x0301: ("sha256", "dsa"),
}


class ApkSigFailure(Exception):
    """Only sanitized validation failure codes are emitted."""


def u32(data, pos):
    if pos < 0 or pos + 4 > len(data):
        raise ApkSigFailure("TRUNCATED_U32")
    return struct.unpack_from("<I", data, pos)[0]


def u64(data, pos):
    if pos < 0 or pos + 8 > len(data):
        raise ApkSigFailure("TRUNCATED_U64")
    return struct.unpack_from("<Q", data, pos)[0]


def lp32(data, pos):
    length = u32(data, pos)
    start = pos + 4
    if length > len(data) - start:
        raise ApkSigFailure("LENGTH_PREFIX_OVERFLOW")
    return data[start:start + length], start + length


def entries_lp32(data):
    result = []
    pos = 0
    while pos < len(data):
        item, pos = lp32(data, pos)
        result.append(item)
    if pos != len(data):
        raise ApkSigFailure("TRAILING_LENGTH_DATA")
    return result


def locate_block(fp):
    fp.seek(0, os.SEEK_END)
    total = fp.tell()
    tail_count = min(total, 65535 + 22)
    fp.seek(total - tail_count)
    tail = fp.read(tail_count)
    eocd = -1
    for index in range(len(tail) - 22, -1, -1):
        if tail[index:index+4] != EOCD_MAGIC:
            continue
        if u32(tail[index+20:index+22] + b"\x00\x00", 0) == len(tail) - index - 22:
            eocd = total - tail_count + index
            break
    if eocd < 0:
        raise ApkSigFailure("ZIP_EOCD_NOT_FOUND")
    fp.seek(eocd + 16)
    cd_start = struct.unpack("<I", fp.read(4))[0]
    if cd_start == 0xFFFFFFFF or cd_start <= 24 or cd_start > eocd:
        raise ApkSigFailure("ZIP64_OR_CENTRAL_DIRECTORY_INVALID")
    fp.seek(cd_start - 24)
    footer = fp.read(24)
    size = u64(footer, 0)
    if footer[8:] != APK_MAGIC or size < 24 or size > MAX_BLOCK:
        raise ApkSigFailure("APK_SIGNING_BLOCK_NOT_FOUND")
    start = cd_start - (size + 8)
    if start < 0:
        raise ApkSigFailure("APK_SIGNING_BLOCK_OFFSET_INVALID")
    fp.seek(start)
    header_size = u64(fp.read(8), 0)
    if header_size != size:
        raise ApkSigFailure("APK_SIGNING_BLOCK_SIZE_MISMATCH")
    rest_len = size - 24
    fp.seek(start + 8)
    pairs = fp.read(rest_len)
    if len(pairs) != rest_len:
        raise ApkSigFailure("APK_SIGNING_BLOCK_TRUNCATED")
    fields = {}
    pos = 0
    while pos < len(pairs):
        n = u64(pairs, pos)
        pos += 8
        if n < 4 or n > len(pairs) - pos:
            raise ApkSigFailure("APK_SIGNING_PAIR_INVALID")
        field = u32(pairs, pos)
        if field in fields:
            raise ApkSigFailure("APK_SIGNING_PAIR_DUPLICATE")
        fields[field] = pairs[pos+4:pos+n]
        pos += n
    if V2_BLOCK_ID not in fields:
        raise ApkSigFailure("APK_V2_SIGNER_MISSING")
    fp.seek(eocd)
    eocd_bytes = fp.read(total-eocd)
    if len(eocd_bytes) < 22:
        raise ApkSigFailure("ZIP_EOCD_TRUNCATED")
    eocd_bytes = bytearray(eocd_bytes)
    eocd_bytes[16:20] = struct.pack("<I", start)
    return {
        "v2": fields[V2_BLOCK_ID], "block_start": start, "cd_start": cd_start,
        "eocd_start": eocd, "eocd_bytes": bytes(eocd_bytes), "bytes": total,
        "has_v3_block": 0xF05368C0 in fields,
    }


def read_v2_signer(raw):
    sd, p = lp32(raw, 0)
    signatures, p = lp32(raw, p)
    public_key, p = lp32(raw, p)
    if p != len(raw):
        raise ApkSigFailure("APK_SIGNER_TRAILING_BYTES")
    digests_blob, q = lp32(sd, 0)
    certs_blob, q = lp32(sd, q)
    extras, q = lp32(sd, q)
    if not certs_blob:
        raise ApkSigFailure("APK_SIGNER_CERTIFICATE_MISSING")
    # Some Google Play-delivered splits append one zero uint32. This suffix
    # remains inside the signed byte sequence; signature verification below
    # covers every byte, including the suffix. apksigner is still the final
    # Android-compatibility authority.
    if q != len(sd) and sd[q:] != b"\x00\x00\x00\x00":
        raise ApkSigFailure("APK_SIGNED_DATA_UNSUPPORTED_TRAILER")
    digests = {}
    for item in entries_lp32(digests_blob):
        if len(item) < 8:
            raise ApkSigFailure("APK_SIGNER_DIGEST_INVALID")
        algo = u32(item, 0)
        value, end = lp32(item, 4)
        if end != len(item) or algo in digests:
            raise ApkSigFailure("APK_SIGNER_DIGEST_INVALID")
        digests[algo] = value
    signed = {}
    for item in entries_lp32(signatures):
        if len(item) < 8:
            raise ApkSigFailure("APK_SIGNER_SIGNATURE_INVALID")
        algo = u32(item, 0)
        value, end = lp32(item, 4)
        if end != len(item) or algo in signed:
            raise ApkSigFailure("APK_SIGNER_SIGNATURE_INVALID")
        signed[algo] = value
    certs = entries_lp32(certs_blob)
    if not certs or len(certs[0]) > 8192:
        raise ApkSigFailure("APK_CERTIFICATE_INVALID")
    return {
        "data": sd, "digests": digests, "signatures": signed,
        "spki": public_key, "certificate": certs[0],
    }


def check_signer(signer, expected_cert):
    certificate = x509.load_der_x509_certificate(
        signer["certificate"], default_backend())
    fingerprint = certificate.fingerprint(hashes.SHA256()).hex()
    if not hmac.compare_digest(fingerprint, expected_cert):
        raise ApkSigFailure("APK_PUBLISHER_CERTIFICATE_MISMATCH")
    pub = certificate.public_key()
    spki = pub.public_bytes(serialization.Encoding.DER,
                            serialization.PublicFormat.SubjectPublicKeyInfo)
    if not hmac.compare_digest(spki, signer["spki"]):
        raise ApkSigFailure("APK_PUBLIC_KEY_MISMATCH")
    candidates = set(signer["digests"]).intersection(signer["signatures"])
    preference = (0x0102, 0x0104, 0x0202, 0x0101, 0x0103, 0x0201, 0x0301)
    for algo in preference:
        if algo not in candidates or algo not in SUPPORTED_ALGOS:
            continue
        hash_name, method = SUPPORTED_ALGOS[algo]
        algorithm = hashes.SHA512() if hash_name == "sha512" else hashes.SHA256()
        signature = signer["signatures"][algo]
        try:
            if method == "pss" and isinstance(pub, rsa.RSAPublicKey):
                pub.verify(signature, signer["data"],
                           padding.PSS(mgf=padding.MGF1(algorithm),
                                       salt_length=algorithm.digest_size), algorithm)
            elif method == "pkcs1" and isinstance(pub, rsa.RSAPublicKey):
                pub.verify(signature, signer["data"], padding.PKCS1v15(), algorithm)
            elif method == "ecdsa" and isinstance(pub, ec.EllipticCurvePublicKey):
                pub.verify(signature, signer["data"], ec.ECDSA(algorithm))
            elif method == "dsa" and isinstance(pub, dsa.DSAPublicKey):
                pub.verify(signature, signer["data"], algorithm)
            else:
                raise ApkSigFailure("APK_SIGNATURE_KEY_TYPE_MISMATCH")
        except ApkSigFailure:
            raise
        except Exception:
            raise ApkSigFailure("APK_V2_DIGITAL_SIGNATURE_INVALID") from None
        expected_digest = signer["digests"][algo]
        if len(expected_digest) != algorithm.digest_size:
            raise ApkSigFailure("APK_CONTENT_DIGEST_LENGTH_INVALID")
        return hash_name, expected_digest, algo, fingerprint
    raise ApkSigFailure("APK_V2_SIGNATURE_ALGORITHM_UNSUPPORTED")


def chunked_content_digest(fp, block, hash_name):
    chunks = []
    def update_chunk(chunk):
        h = hashlib.new(hash_name)
        h.update(b"\xa5")
        h.update(struct.pack("<I", len(chunk)))
        h.update(chunk)
        chunks.append(h.digest())
    def read_section(offset, length):
        fp.seek(offset)
        remaining = length
        while remaining:
            n = min(CHUNK_BYTES, remaining)
            chunk = fp.read(n)
            if len(chunk) != n:
                raise ApkSigFailure("APK_CONTENT_READ_TRUNCATED")
            update_chunk(chunk)
            remaining -= n
    read_section(0, block["block_start"])
    read_section(block["cd_start"], block["eocd_start"]-block["cd_start"])
    # EOCD section includes the adjusted central-directory offset.
    eocd = block["eocd_bytes"]
    for off in range(0, len(eocd), CHUNK_BYTES):
        update_chunk(eocd[off:off+CHUNK_BYTES])
    root = hashlib.new(hash_name)
    root.update(b"\x5a")
    root.update(struct.pack("<I", len(chunks)))
    for value in chunks:
        root.update(value)
    return root.digest()


def audit_apk(path, original_sha, cert=SIGNER_SHA256):
    file = Path(path)
    if not file.is_file() or not file.name.endswith(".apk") or file.is_symlink():
        raise ApkSigFailure("APK_FILE_UNAVAILABLE")
    expected = str(original_sha).lower()
    if not re.match(r"^[0-9a-f]{64}$", expected):
        raise ApkSigFailure("APK_REFERENCE_HASH_INVALID")
    sha = hashlib.sha256()
    with file.open("rb") as fp:
        for chunk in iter(lambda: fp.read(4*1024*1024), b""):
            sha.update(chunk)
    if not hmac.compare_digest(sha.hexdigest(), expected):
        raise ApkSigFailure("APK_SOURCE_SHA256_MISMATCH")
    with file.open("rb") as fp:
        block = locate_block(fp)
        signers_blob, pos = lp32(block["v2"], 0)
        if pos != len(block["v2"]):
            raise ApkSigFailure("APK_V2_EXTRA_BYTES")
        raw_signers = entries_lp32(signers_blob)
        if len(raw_signers) != 1:
            raise ApkSigFailure("APK_SIGNER_COUNT_UNEXPECTED")
        signer = read_v2_signer(raw_signers[0])
        name, expected_digest, algo, fingerprint = check_signer(signer, cert)
        actual_digest = chunked_content_digest(fp, block, name)
        if not hmac.compare_digest(actual_digest, expected_digest):
            raise ApkSigFailure("APK_V2_CONTENT_DIGEST_MISMATCH")
    return {
        "filename": file.name, "size": file.stat().st_size,
        "sha256": expected, "cert_sha256": fingerprint,
        "v2_signature_valid": True, "v2_content_digest_valid": True,
        "signature_algorithm": hex(algo),
        "has_v3_block": block["has_v3_block"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--min-files", type=int, default=1)
    args = parser.parse_args()
    try:
        doc = json.loads(Path(args.manifest).read_text("utf-8-sig"))
        package = doc.get("package")
        if package not in ("com.kwai.video", "kwai.lite.video"):
            raise ApkSigFailure("UNEXPECTED_APK_PACKAGE")
        items = doc.get("files")
        if not isinstance(items, list) or not items:
            raise ApkSigFailure("MANIFEST_MISSING_FILES")
        count = 0
        for entry in items:
            if not isinstance(entry, dict):
                raise ApkSigFailure("MANIFEST_ENTRY_INVALID")
            name = entry.get("name")
            if not isinstance(name, str) or not re.match(r"^(base|split_[a-zA-Z0-9_.-]+)\.apk$", name):
                raise ApkSigFailure("MANIFEST_APK_NAME_INVALID")
            record = audit_apk(Path(args.folder)/name, entry.get("sha256"))
            if record["size"] != entry.get("bytes"):
                raise ApkSigFailure("MANIFEST_APK_SIZE_MISMATCH")
            count += 1
            print("APK_V2_PROVEN=" + name + ":SHA256_CERT_CONTENT_OK")
        if count < args.min_files:
            raise ApkSigFailure("REQUIRED_APK_COUNT_NOT_VERIFIED")
        print("APK_V2_TOTAL_VALIDATED=" + str(count))
        print("SPAWNDROID_INSTALL_MULTIPLE_APKS=NOT_RUN")
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 0
    except (ApkSigFailure, IOError, ValueError) as exc:
        msg = str(exc) if isinstance(exc, ApkSigFailure) else "AUDIT_IO_OR_JSON_FAILED"
        print("APK_V2_AUDIT_BLOCKED=" + msg)
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 25


if __name__ == "__main__":
    sys.exit(main())
