"""Provider-neutral campaign queue core. No network providers are implemented here."""
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Dict, List

TERMINAL_SUPPRESS = {"BOUNCED_HARD", "COMPLAINED", "UNSUBSCRIBED"}

def normalize_email(value: str) -> str:
    return value.strip().lower()

@dataclass
class Contact:
    email: str
    sources: List[str] = field(default_factory=list)
    suppressed: bool = False

@dataclass
class Campaign:
    campaign_id: str
    approved: bool = False
    recipient_set_approved: bool = False
    daily_cap: int = 100

@dataclass
class Delivery:
    campaign_id: str
    email: str
    provider: str
    status: str = "QUEUED"
    attempts: int = 0
    dedupe_key: str = ""

class Queue:
    def __init__(self):
        self.contacts: Dict[str, Contact] = {}
        self.deliveries: Dict[str, Delivery] = {}
        self.suppression = set()

    def upsert_contact(self, email: str, source: str) -> Contact:
        key = normalize_email(email)
        c = self.contacts.setdefault(key, Contact(key))
        if source and source not in c.sources:
            c.sources.append(source)
        return c

    def suppress(self, email: str, reason: str) -> None:
        key = normalize_email(email)
        self.suppression.add(key)
        if key in self.contacts:
            self.contacts[key].suppressed = True

    def enqueue(self, campaign: Campaign, email: str, provider: str) -> Delivery:
        if not (campaign.approved and campaign.recipient_set_approved):
            raise PermissionError("campaign and recipient set require explicit approval")
        key = normalize_email(email)
        if key in self.suppression or self.contacts.get(key, Contact(key)).suppressed:
            raise PermissionError("suppressed recipient")
        dedupe = sha256(f"{campaign.campaign_id}|{key}|{provider}".encode()).hexdigest()
        if dedupe in self.deliveries:
            return self.deliveries[dedupe]
        d = Delivery(campaign.campaign_id, key, provider, dedupe_key=dedupe)
        self.deliveries[dedupe] = d
        return d

    def lease_batch(self, campaign: Campaign, provider: str, already_sent_today: int = 0) -> List[Delivery]:
        remaining = max(0, campaign.daily_cap - already_sent_today)
        out = []
        for d in self.deliveries.values():
            if len(out) >= remaining:
                break
            if d.campaign_id != campaign.campaign_id or d.provider != provider or d.status != "QUEUED":
                continue
            if d.email in self.suppression:
                d.status = "SUPPRESSED"
                continue
            d.status = "LEASED"
            out.append(d)
        return out

    def record_result(self, delivery: Delivery, result: str) -> None:
        delivery.attempts += 1
        delivery.status = result
        if result in TERMINAL_SUPPRESS:
            self.suppress(delivery.email, result)
