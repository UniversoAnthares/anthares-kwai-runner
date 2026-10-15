#!/usr/bin/env python3
from pathlib import Path
import re

p=Path(__file__).with_name('wrangler.toml')
s=p.read_text(encoding='utf-8')

def grab(key, default=''):
    m=re.search(r'^'+re.escape(key)+r'\s*=\s*"([^"]*)"\s*$',s,re.M)
    return m.group(1) if m else default

name=grab('name','anthares-ara-mcp')
account=grab('account_id','5c24be052e5144391f73a8e03491e88e')
main=grab('main','src/index.js')
compat=grab('compatibility_date','2026-10-01')

out=f'''name = "{name}"
account_id = "{account}"
main = "{main}"
compatibility_date = "{compat}"

[[send_email]]
name = "AUTH_EMAIL_SEND"
destination_address = "lucasyahn@gmail.com"

[vars]
AUTH_EMAIL_FROM = "noreply@anthares.us"
'''

for forbidden in ('durable_objects','GATEWAY_STATE','[[migrations]]','[[services]]'):
    if forbidden in out:
        raise SystemExit('forbidden stateless marker: '+forbidden)
for required in ('AUTH_EMAIL_SEND','lucasyahn@gmail.com','AUTH_EMAIL_FROM'):
    if required not in out:
        raise SystemExit('missing email marker: '+required)

p.write_text(out,encoding='utf-8')
print('ARA_STATELESS_WRANGLER_PATCH_OK=1')
