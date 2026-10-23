"""Read a TinyFish API key protected with Windows DPAPI for the current account.

GitHub/Unix workers use TINYFISH_API_KEY from their deployment secret store.
This module never prints, persists, or logs decrypted credentials.
"""
from __future__ import annotations

import base64
import ctypes
import os
import pathlib
import sys


DEFAULT_STORE = pathlib.Path(r"D:\AntharsWork\secure\tinyfish\api-key.dpapi")


def read_current_user_key() -> str:
    if sys.platform != "win32":
        return ""
    path = pathlib.Path(os.getenv("ANTHARES_TINYFISH_KEY_FILE") or DEFAULT_STORE)
    try:
        ciphertext = base64.b64decode(path.read_text(encoding="ascii").strip(), validate=True)
        if not 16 <= len(ciphertext) <= 8192:
            return ""
        class DataBlob(ctypes.Structure):
            _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]
        buffer = ctypes.create_string_buffer(ciphertext)
        input_blob = DataBlob(len(ciphertext), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
        output_blob = DataBlob()
        crypt = ctypes.WinDLL("crypt32", use_last_error=True)
        crypt.CryptUnprotectData.argtypes = [
            ctypes.POINTER(DataBlob), ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong,
            ctypes.POINTER(DataBlob),
        ]
        crypt.CryptUnprotectData.restype = ctypes.c_int
        if not crypt.CryptUnprotectData(ctypes.byref(input_blob), None, None,
                                         None, None, 0, ctypes.byref(output_blob)):
            return ""
        try:
            plain = ctypes.string_at(output_blob.pbData, output_blob.cbData)
            return plain.decode("utf-8")
        finally:
            ctypes.windll.kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))
    except (OSError, ValueError, UnicodeError):
        return ""
