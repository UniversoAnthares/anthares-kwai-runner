#!/usr/bin/env python3
import re,sys,tempfile,pathlib
from datetime import datetime,timezone
case=sys.argv[1]; now=datetime(2026,10,6,2,30,tzinfo=timezone.utc)
fixtures={
"future-active":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T03:00:00Z\n"],
"expired-running":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T02:00:00Z\n"],
"superseded-future":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T03:00:00Z\n","STATUS: PROVEN\nLEASE_AREA: a\nLEASE_CLOSED: 2026-10-06T02:20:00Z\nSUPERSEDES: lease0.md\n"],
"closed-successor":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: 2026-10-06T03:00:00Z\n","STATUS: PROVEN\nLEASE_AREA: a\nLEASE_CLOSED: 2026-10-06T02:20:00Z\nSUPERSEDES: lease0.md\n"],
"malformed-expiry":["STATUS: RUNNING\nLEASE_AREA: a\nLEASE_EXPIRES: not-a-date\n"]}[case]
with tempfile.TemporaryDirectory() as td:
 ps=[]
 for i,t in enumerate(fixtures):
  p=pathlib.Path(td)/f"lease{i}.md";p.write_text(t);ps.append(p)
 superseded=set()
 for p in ps:
  t=p.read_text();m=re.search(r"(?m)^SUPERSEDES:\s*([^\n]+)",t)
  if m: superseded|={m.group(1).strip(),pathlib.Path(m.group(1).strip()).name}
 active=[];expired=[]
 for p in ps:
  t=p.read_text()
  if p.name in superseded: continue
  st=re.search(r"(?m)^STATUS:\s*([^\n]+)",t);ex=re.search(r"(?m)^LEASE_EXPIRES:\s*([^\s]+)",t)
  if not(st and ex) or st.group(1).strip().upper()!="RUNNING": continue
  try: dt=datetime.fromisoformat(ex.group(1).replace("Z","+00:00"))
  except ValueError: continue
  (active if dt>=now else expired).append(p.name)
 expect={"future-active":(1,0),"expired-running":(0,1),"superseded-future":(0,0),"closed-successor":(0,0),"malformed-expiry":(0,0)}[case]
 ok=(len(active),len(expired))==expect
 print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_"),active,expired)
 raise SystemExit(0 if ok else 1)
