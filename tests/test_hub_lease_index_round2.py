#!/usr/bin/env python3
import re,sys,pathlib,tempfile
from datetime import datetime,timezone
case=sys.argv[1]; now=datetime(2026,10,6,2,30,tzinfo=timezone.utc)
fx={
"boundary-equal-now":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T02:30:00Z\n"],
"lowercase-status":["STATUS: running\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T03:00:00Z\n"],
"supersedes-full-path":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T03:00:00Z\n","STATUS: PROVEN\nSUPERSEDES: test-hub/findings/lease0.md\nLEASE_CLOSED: 2026-10-06T02:20:00Z\n"],
"unrelated-close-same-area":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T03:00:00Z\n","STATUS: PROVEN\nLEASE_AREA: a\nLEASE_CLOSED: 2026-10-06T02:20:00Z\nSUPERSEDES: other.md\n"],
"duplicate-active-area":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T03:00:00Z\n","STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T03:10:00Z\n"]}[case]
with tempfile.TemporaryDirectory() as td:
 ps=[]
 for i,t in enumerate(fx): p=pathlib.Path(td)/f"lease{i}.md";p.write_text(t);ps.append(p)
 sup=set()
 for p in ps:
  m=re.search(r"(?m)^SUPERSEDES:\s*([^\n]+)",p.read_text())
  if m: sup|={m.group(1).strip(),pathlib.Path(m.group(1).strip()).name}
 active=[]
 for p in ps:
  t=p.read_text()
  if p.name in sup or str(p) in sup: continue
  st=re.search(r"(?m)^STATUS:\s*([^\n]+)",t); ex=re.search(r"(?m)^LEASE_EXPIRES:\s*([^\s]+)",t); ar=re.search(r"(?m)^LEASE_AREA:\s*([^\n]+)",t)
  if not(st and ex and ar) or st.group(1).strip().upper()!="RUNNING": continue
  try: dt=datetime.fromisoformat(ex.group(1).replace("Z","+00:00"))
  except: continue
  if dt>=now: active.append(ar.group(1).strip())
 conflicts={x for x in active if active.count(x)>1}
 expected={"boundary-equal-now":(1,0),"lowercase-status":(1,0),"supersedes-full-path":(0,0),"unrelated-close-same-area":(1,0),"duplicate-active-area":(2,1)}[case]
 ok=(len(active),len(conflicts))==expected
 print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_"),active,conflicts); raise SystemExit(0 if ok else 1)
