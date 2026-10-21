"""Mandatory UTF-8/OEM mojibake blocking before remote social publication."""
import unittest

from anthares_publisher.unicode_gate import clean_publication_text, clean_metadata


class UnicodeGateTests(unittest.TestCase):
    def test_oem_console_corruption_is_repaired(self):
        self.assertEqual(clean_publication_text("AN├üLISE"), "ANÁLISE")
        self.assertEqual(clean_publication_text("ÔùÅ"), "●")
        self.assertEqual(clean_publication_text(
            "A Metamorfose [Kafka] - AN├üLISE | Trecho 157:14 ÔùÅ Universo Anthares"),
            "A Metamorfose [Kafka] - ANÁLISE | Trecho 157:14 ● Universo Anthares")

    def test_correct_text_is_unchanged(self):
        self.assertEqual(clean_publication_text("Ação ● Ficção – São Paulo"),
                         "Ação ● Ficção – São Paulo")

    def test_unrepairable_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "corrupt_blocked"):
            clean_publication_text("Ação �")
        with self.assertRaisesRegex(ValueError, "corrupt_blocked"):
            clean_publication_text("AN├üLISE �")

    def test_every_publication_text_field_repaired(self):
        damaged = "AN├üLISE ÔùÅ Universo Anthares"
        result = clean_metadata({
            "title": damaged, "caption": damaged, "description": damaged,
            "text": damaged, "hashtags": ["#AN├üLISE"], "alt_text": damaged})
        self.assertEqual(result["title"], "ANÁLISE ● Universo Anthares")
        self.assertEqual(result["hashtags"], ["#ANÁLISE"])
        self.assertTrue(all("├" not in str(v) for v in result.values()))


if __name__ == "__main__":
    unittest.main()
