#!/usr/bin/env python3
"""Evidence for one Pinterest cloud run. Read-only. Never emits raw logs or secrets."""
import json
import os
from pathlib import Path
import re
import sys

PIN=re.compile(r"CORTES_PINTEREST_CONFIRMED_URL=(https://www\.pinterest\.com/pin/[0-9]{10,25}/?)")
STATE=re.compile(r'\{[^\r\n]*"pinterest_cloud"\s*:\s*"[A-Z0-9_]+"[^\r\n]*\}')
REASON=re.compile(r"\b(?:PINTEREST_[A-Z0-9_]+|BUFFER_HTTP_[0-9]{3}|CORTES_QUEUE_[A-Z0-9_]+)\b")

def inspect(raw: str, *, event: str, run_id: str, conclusion: str) -> dict:
    unique=list(dict.fromkeys(PIN.findall(raw)))
    states=[]
    for match in STATE.finditer(raw):
        try:
            value=json.loads(match.group(0))
            if isinstance(value,dict):states.append(value)
        except ValueError:pass
    recent=states[-1] if states else {}
    declared=recent.get("posts_confirmed_this_run")
    consistent=(type(declared) is int and declared==len(unique))
    accepted=recent.get("pinterest_cloud")=="PASS"
    scheduled=recent.get("scheduled_action")=="SCHEDULED_IN_BUFFER"
    # URLs are printed by the cloud worker only after Buffer sent and Neon CAS.
    reconciled=unique if accepted and consistent else []
    if reconciled:result="PINS_RECONCILED"
    elif accepted and scheduled and consistent:result="SCHEDULED_NOT_PUBLISHED"
    elif recent.get("pinterest_cloud")=="BACKPRESSURE_BUFFER":result="WAITING_BUFFER_DELIVERY"
    elif recent.get("pinterest_cloud")=="COOLDOWN_HTTP_429":result="RATE_LIMIT_ISOLATED"
    elif accepted and consistent:result="PASS_NO_NEW_PIN"
    else:result="UNVERIFIED_OR_FAILED"
    return {
        "schema":1,
        "run_id":run_id if re.fullmatch(r"[0-9]{1,20}",run_id or "") else "unknown",
        "event":event if event in ("schedule","workflow_run","workflow_dispatch","push") else "unknown",
        "worker_conclusion":conclusion if conclusion in ("success","failure","cancelled") else "unknown",
        "result":result,
        "new_public_pins_verified_by_buffer_and_neon_cas":reconciled,
        "new_public_pin_count":len(reconciled),
        "buffer_schedule_accepted":scheduled,
        "buffer_pending_count":recent.get("buffer_pending_count") if type(recent.get("buffer_pending_count")) is int else None,
        "schedule_is_not_publication":True,
        "sent_count_matches_evidence":consistent,
        "board_500_fallback_recovered":("BUFFER_HTTP_500" in raw and accepted),
        "qa_failure_codes":sorted(set(REASON.findall(raw)))[:16],
        "independent_public_page_checked":False,
        "qa_auto_repair_verified":False,
        "independent_secondary_runner_verified":False
    }

def markdown(state:dict) -> str:
    labels={
        "PINS_RECONCILED":"PUBLICAÇÃO RECONCILIADA",
        "SCHEDULED_NOT_PUBLISHED":"SOMENTE AGENDAMENTO",
        "RATE_LIMIT_ISOLATED":"LIMITE DE API ISOLADO",
      "WAITING_BUFFER_DELIVERY":"AGENDAMENTOS BUFFER AGUARDANDO ENTREGA",
        "PASS_NO_NEW_PIN":"SEM NOVA PUBLICAÇÃO",
        "UNVERIFIED_OR_FAILED":"SEM EVIDÊNCIA SUFICIENTE"
    }
    lines=[
      "## Evidências — Pinterest",
      "",
      "- Resultado: **"+labels[state["result"]]+"**",
      "- Evento: "+state["event"]+"; run: "+state["run_id"],
      "- Novo agendamento aceito: **"+("sim" if state["buffer_schedule_accepted"] else "não")+"**",
      "- Pins enviados e reconciliados neste run: **"+str(state["new_public_pin_count"])+"**",
      "- Contagem de links consistente: **"+("sim" if state["sent_count_matches_evidence"] else "não")+"**",
      "- HTTP 500 recuperado: **"+("sim" if state["board_500_fallback_recovered"] else "não demonstrado")+"**",
      "- QA corrigiu erro automaticamente: **não demonstrado neste run**",
      "- Executor independente do GitHub: **não demonstrado neste run**",
      "",
      "**Um agendamento no Buffer não comprova publicação no Pinterest.**"
    ]
    if state["new_public_pin_count"]:
        lines+=["","### Links reconciliados"]+["- "+u for u in state["new_public_pins_verified_by_buffer_and_neon_cas"]]
    if state["qa_failure_codes"]:
        lines+=["","### Códigos seguros"]+["- "+v for v in state["qa_failure_codes"]]
    return "\n".join(lines)+"\n"

def main():
    f=Path(sys.argv[1]) if len(sys.argv)>1 else Path("/tmp/pinterest-run.log")
    raw=f.read_text(encoding="utf8",errors="replace") if f.is_file() else ""
    state=inspect(raw,event=os.getenv("GITHUB_EVENT_NAME","unknown"),
          run_id=os.getenv("GITHUB_RUN_ID","unknown"),
          conclusion=os.getenv("CORTES_WORKER_CONCLUSION","unknown"))
    dest=Path(os.getenv("PINTEREST_EVIDENCE_DIR","/tmp/pinterest-evidence"))
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"evidence.json").write_text(json.dumps(state,ensure_ascii=True,indent=2)+"\n",encoding="utf8")
    (dest/"evidence.md").write_text(markdown(state),encoding="utf8")
    path=os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path,"a",encoding="utf8") as f:f.write(markdown(state))
    print("PINTEREST_EVIDENCE_RESULT="+state["result"])
    print("PINTEREST_EVIDENCE_NEW_PUBLIC_PINS="+str(state["new_public_pin_count"]))
    print("PINTEREST_EVIDENCE_BUFFER_SCHEDULED="+str(state["buffer_schedule_accepted"]).lower())
    return 0
if __name__=="__main__":
    raise SystemExit(main())
