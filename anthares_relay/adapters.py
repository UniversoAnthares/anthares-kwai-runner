"""Strict adapter contract: no credentials, synthetic identity or guessed publication."""
from dataclasses import dataclass
from urllib.parse import urlsplit

@dataclass(frozen=True)
class IdentityProof:
    platform: str
    account: str
    authenticated: bool
    independently_verified: bool

    def valid_for(self, platform, account):
        return (self.platform == platform and self.account == account
                and self.authenticated is True
                and self.independently_verified is True)

@dataclass(frozen=True)
class PublicationProof:
    external_id: str
    public_url: str
    verified: bool

    def valid(self):
        if self.verified is not True or not isinstance(self.external_id,str) or not self.external_id:
            return False
        if not isinstance(self.public_url,str):
            return False
        parsed=urlsplit(self.public_url)
        return parsed.scheme=="https" and parsed.hostname in ("kwai.com","www.kwai.com","m.kwai.com","s.kwai.app")

class AuthenticatedAdapter:
    """Concrete implementation must use authorized remote platform integration."""
    platform="kwai"
    def identity(self):
        raise NotImplementedError("No authorized remote identity provider configured")
    def publish(self, video, identity):
        if not isinstance(identity,IdentityProof) or not identity.valid_for(self.platform,"lucasrosalem"):
            raise PermissionError("Kwai identity proof missing")
        raise NotImplementedError("No authorized Kwai publisher configured")
    def verify(self, external_id, public_url):
        raise NotImplementedError("Independent Kwai publication verification unavailable")
