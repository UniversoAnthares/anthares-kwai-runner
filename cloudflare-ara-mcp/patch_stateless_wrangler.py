#!/usr/bin/env python3
from pathlib import Path

p=Path(__file__).with_name('wrangler.toml')
s=p.read_text(encoding='utf-8')
head=[]
for line in s.splitlines():
    if line.startswith('[[durable_objects.bindings]]') or line.startswith('[[migrations]]') or line.startswith('[[services]]'):
        break
    head.append(line)
base='\n'.join(head).rstrip()+"\n"
required=['name = "anthares-ara-mcp"','main = "src/index.js"','compatibility_date = "2026-10-01"']
for item in required:
    if item not in base:
        raise SystemExit('missing wrangler marker: '+item)
p.write_text(base,encoding='utf-8')
print('ARA_STATELESS_WRANGLER_PATCH_OK=1')
