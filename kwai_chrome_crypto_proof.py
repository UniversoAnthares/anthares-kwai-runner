import base64,hashlib,json,os
from pathlib import Path
from cryptography.fernet import Fernet,InvalidToken
from playwright.async_api import async_playwright
import asyncio

ROOT=Path(".kwai-crypto-proof")
ROOT.mkdir(exist_ok=True)
CIPHER=ROOT/"synthetic.enc"
KEY=os.environ.get("KWAI_SESSION_KEY","")
def codec():
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(KEY.encode()).digest()))
async def main():
    assert KEY, "KWAI_SESSION_KEY is absent"
    mode=os.environ.get("PROOF_MODE","create")
    if mode=="create":
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True)
            ctx=await browser.new_context()
            await ctx.add_cookies([{"name":"synthetic_only","value":"not_a_real_kwai_cookie","url":"https://example.org"}])
            state=await ctx.storage_state()
            await browser.close()
        data=json.dumps(state,sort_keys=True).encode()
        CIPHER.write_bytes(codec().encrypt(data))
        print("CRYPTO_PROOF_CREATE="+json.dumps({"encrypted":True,"synthetic":True,"bytes":len(CIPHER.read_bytes())}))
    elif mode=="verify":
        assert CIPHER.exists(), "encrypted artifact missing on independent runner"
        ciphertext=CIPHER.read_bytes()
        plain=codec().decrypt(ciphertext)
        obj=json.loads(plain)
        assert any(c.get("name")=="synthetic_only" and c.get("value")=="not_a_real_kwai_cookie" for c in obj["cookies"])
        try:
            codec().decrypt(ciphertext[:-1]+bytes([ciphertext[-1]^1]))
            raise AssertionError("tampered ciphertext accepted")
        except InvalidToken:
            pass
        print("CRYPTO_PROOF_VERIFY="+json.dumps({"restored":True,"tamper_rejected":True,"synthetic":True}))
    else:
        raise ValueError("unknown proof mode")
asyncio.run(main())
