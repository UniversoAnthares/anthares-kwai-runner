import unittest
from anthares_publisher.contract import IdentityProof,PublicationEvidence,authorize,validate_evidence

class PublisherContractTests(unittest.TestCase):
    def test_verified_identity_authorizes_matching_account(self):
        p=IdentityProof('kwai','lucasrosalem','@lucasrosalem',True,'session-sha256')
        authorize(p,'kwai','lucasrosalem')
    def test_generic_or_wrong_identity_cannot_publish(self):
        with self.assertRaises(PermissionError):
            authorize(IdentityProof('kwai','lucasrosalem','other',True,'session'),'kwai','lucasrosalem')
        with self.assertRaises(PermissionError):
            authorize(IdentityProof('kwai','lucasrosalem','lucasrosalem',False,'session'),'kwai','lucasrosalem')
    def test_evidence_must_match_target_account(self):
        validate_evidence(PublicationEvidence('kwai','lucasrosalem','v1','https://www.kwai.com/v/v1'),'kwai','lucasrosalem')
        with self.assertRaises(ValueError):
            validate_evidence(PublicationEvidence('kwai','other','v1','https://www.kwai.com/v/v1'),'kwai','lucasrosalem')

if __name__=='__main__':unittest.main()
