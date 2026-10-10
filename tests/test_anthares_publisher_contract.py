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
    def test_rejects_untrusted_publication_urls(self):
        for url in ('http://www.kwai.com/v/1','https://kwai.com.evil.test/v/1','https://example.org/v/1','https://user@www.kwai.com/v/1'):
            with self.subTest(url=url),self.assertRaises(ValueError):
                validate_evidence(PublicationEvidence('kwai','lucasrosalem','v1',url),'kwai','lucasrosalem')
    def test_rejects_homepage_or_unrelated_post_id(self):
        for url in ('https://www.kwai.com/','https://www.kwai.com/v/other',
                    'https://www.kwai.com/v/v1234?video=v1','https://www.kwai.com/profile'):
            with self.subTest(url=url),self.assertRaises(ValueError):
                validate_evidence(PublicationEvidence('kwai','lucasrosalem','v1',url),'kwai','lucasrosalem')
    def test_evidence_must_match_target_account(self):
        validate_evidence(PublicationEvidence('kwai','lucasrosalem','v1','https://www.kwai.com/v/v1'),'kwai','lucasrosalem')
        with self.assertRaises(ValueError):
            validate_evidence(PublicationEvidence('kwai','other','v1','https://www.kwai.com/v/v1'),'kwai','lucasrosalem')

if __name__=='__main__':unittest.main()
