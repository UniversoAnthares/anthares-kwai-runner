"""Bounded input adapter for private import, never calls the Resend API.

Input is UTF-8 JSON array of [full_name, email], base64-encoded on stdin.
No source addresses, raw payload or emails are printed to stdout.
"""
import argparse
import base64
import json
import sys
from pastor_mailing_queue import PastoralQueue


def process(payload: bytes, db_path: str, source: str) -> dict:
    if len(payload) > 250_000:
        raise ValueError("batch input too large")
    raw = base64.b64decode(payload, validate=True)
    rows = json.loads(raw.decode("utf-8"))
    if not isinstance(rows, list) or len(rows) > 1000 or not all(
        isinstance(x, list) and len(x) == 2 and
        all(isinstance(v, str) and len(v) <= 350 for v in x)
        for x in rows
    ):
        raise ValueError("invalid source batch")
    return PastoralQueue(db_path).import_directory(rows, source)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--source", required=True)
    a = p.parse_args()
    result = process(sys.stdin.buffer.read(250_001),a.db,a.source)
    print(json.dumps(result,sort_keys=True))


if __name__ == "__main__":
    main()
