#!/usr/bin/env python3
import sys
case=sys.argv[1]
leases={"supersedes-chain":[("a",1),("a",1),("a",0)],"case-sensitive-area":[("A",0),("a",0)],"three-way-conflict":[("a",0),("a",0),("a",0)],"closed-plus-active":[("a",1),("a",0)],"distinct-areas":[("a",0),("b",0),("c",0)]}[case]
active=[a for a,c in leases if not c]; conflicts={a for a in active if active.count(a)>1}
expect={"supersedes-chain":(1,0),"case-sensitive-area":(2,0),"three-way-conflict":(3,1),"closed-plus-active":(1,0),"distinct-areas":(3,0)}[case]
ok=(len(active),len(conflicts))==expect
print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_"),active,conflicts);raise SystemExit(0 if ok else 1)
