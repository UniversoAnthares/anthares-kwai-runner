import unittest
from anthares_publisher.editorial import (
    SUFFIX, require_strategic_master, prepare_publication_metadata, STRATEGIC_POLICY,
)
from social_adapters.buffer_three_channels import prepare

TITLE="Como Kafka apresenta a rejeição de Gregor Samsa"+SUFFIX
META={
    "segment_id":"g1:abcdefghijk:123:170",
    "source_id":"abcdefghijk",
    "title":TITLE,
    "description":"A transformação de Gregor Samsa em A metamorfose mostra como a família reage com vergonha à mudança e discute a identidade do personagem.",
    "keywords":["Kafka","Gregor Samsa","A metamorfose"],
    "hashtags":["#Kafka","#Metamorfose"],
    "editorial_policy":STRATEGIC_POLICY,
}
class StrategicPublicationTest(unittest.TestCase):
    def test_deny_any_unapproved_generic_clip(self):
        for removed in ("title","description","keywords","hashtags","editorial_policy"):
            data=dict(META)
            data.pop(removed)
            with self.subTest(field=removed), self.assertRaises(ValueError):
                require_strategic_master(data)
    def test_new_clip_keywords_and_tags_survive_adapters(self):
        data=prepare_publication_metadata(dict(META))
        self.assertTrue(data["title"].endswith(SUFFIX))
        self.assertIn("#Kafka",data["text"])
        self.assertIn("www.anthares.us",data["text"])
        entry=prepare({**META,"platform":"instagram","media_url":"https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_a.mp4","duration_seconds":47})
        self.assertIn("#Metamorfose",entry["caption"])
    def test_unrelated_non_cortes_text_remains_supported(self):
        info=prepare_publication_metadata({"title":"Resenha de Kafka"})
        self.assertEqual(info["title"],"Resenha de Kafka"+SUFFIX)
if __name__=="__main__": unittest.main()
