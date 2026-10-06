"""Safe campaign preparation layer. It cannot send email."""
import csv, io, re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List
from email_queue import Queue, normalize_email

EMAIL_RE=re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@dataclass
class ContactProfile:
    email: str
    name: str = ""
    segments: List[str] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)

class ContactBook:
    def __init__(self, queue: Queue):
        self.queue=queue
        self.profiles: Dict[str,ContactProfile]={}

    def import_csv(self, data: str, source: str) -> dict:
        stats={"rows":0,"accepted":0,"invalid":0,"duplicates":0}
        for row in csv.DictReader(io.StringIO(data)):
            stats["rows"]+=1
            email=normalize_email(row.get("email",""))
            if not EMAIL_RE.match(email):
                stats["invalid"]+=1; continue
            existed=email in self.profiles
            p=self.profiles.setdefault(email,ContactProfile(email=email))
            if row.get("name") and not p.name: p.name=row["name"].strip()
            segments=[x.strip().lower() for x in row.get("segments","").split("|") if x.strip()]
            for s in segments:
                if s not in p.segments: p.segments.append(s)
            if source not in p.provenance: p.provenance.append(source)
            self.queue.upsert_contact(email,source)
            stats["duplicates" if existed else "accepted"]+=1
        return stats

    def segment(self, name: str) -> List[ContactProfile]:
        key=name.strip().lower()
        return [p for p in self.profiles.values() if key in p.segments and p.email not in self.queue.suppression]

class Template:
    def __init__(self, subject: str, body: str):
        self.subject=subject; self.body=body
    def render(self, contact: ContactProfile, unsubscribe_url: str) -> tuple[str,str]:
        values={"name":contact.name or "","email":contact.email,"unsubscribe_url":unsubscribe_url}
        def fill(text):
            for k,v in values.items(): text=text.replace("{{"+k+"}}",v)
            return text
        body=fill(self.body)
        if unsubscribe_url not in body:
            raise ValueError("template must contain unsubscribe URL")
        return fill(self.subject),body

def report(queue: Queue, campaign_id: str) -> dict:
    out={}
    for d in queue.deliveries.values():
        if d.campaign_id==campaign_id: out[d.status]=out.get(d.status,0)+1
    return out
