#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from anthares_publisher.contract import PublicationEvidence, validate_evidence
from anthares_publisher.ledger import confirm, connect, mark_attempt, reserve
from social_adapters.pinterest_browser import canonical_post_url, external_id_from_url, publish
from social_adapters.pinterest_strategy import build_strategy


class PinterestStrategyTests(unittest.TestCase):
    def test_character_content_routes_to_character_board(self):
        strategy = build_strategy("Como construir personagens com motivações fortes")
        self.assertEqual(strategy.board, "Construção de personagens")
        self.assertEqual(strategy.bucket, "education")
        self.assertEqual(strategy.weight, 0.70)
        self.assertLessEqual(len(strategy.title), 100)
        self.assertLessEqual(len(strategy.description), 800)

    def test_classics_routes_to_literature_bucket(self):
        strategy = build_strategy("O que Púchkin ensina sobre ritmo narrativo")
        self.assertEqual(strategy.board, "Literatura clássica")
        self.assertEqual(strategy.bucket, "literature")
        self.assertEqual(strategy.weight, 0.15)

    def test_anthares_routes_to_acquisition_bucket(self):
        strategy = build_strategy("Como publicar seu conto no Anthares e receber avaliação de texto")
        self.assertEqual(strategy.board, "Contos Anthares")
        self.assertEqual(strategy.bucket, "anthares")
        self.assertEqual(strategy.weight, 0.10)

    def test_explicit_overrides_are_respected_and_truncated(self):
        strategy = build_strategy(
            "caption",
            title="T" * 140,
            description="D" * 900,
            board="Pasta personalizada",
        )
        self.assertEqual(strategy.board, "Pasta personalizada")
        self.assertLessEqual(len(strategy.title), 100)
        self.assertLessEqual(len(strategy.description), 800)


class PinterestBrowserTests(unittest.TestCase):
    def test_pin_url_normalization_and_id(self):
        url = canonical_post_url("/pin/617415430169271912/?utm_source=x")
        self.assertEqual(url, "https://www.pinterest.com/pin/617415430169271912/")
        self.assertEqual(external_id_from_url(url), "617415430169271912")

    def test_evidence_accepts_pin_url(self):
        validate_evidence(
            PublicationEvidence(
                "pinterest",
                "lucas",
                "617415430169271912",
                "https://www.pinterest.com/pin/617415430169271912/",
            ),
            "pinterest",
            "lucas",
        )

    def test_evidence_rejects_non_pin_url(self):
        with self.assertRaises(ValueError):
            validate_evidence(
                PublicationEvidence("pinterest", "lucas", "123", "https://www.pinterest.com/lucas/"),
                "pinterest",
                "lucas",
            )

    def test_ledger_reserves_and_confirms_pinterest(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "state.sqlite3")
            row = reserve(db, "live-pin", 1000, 9000, "pinterest", "lucas", "c" * 64)
            self.assertTrue(mark_attempt(db, row["id"]))
            self.assertTrue(
                confirm(
                    db,
                    row["id"],
                    "617415430169271912",
                    "https://www.pinterest.com/pin/617415430169271912/",
                )
            )
            again = reserve(db, "live-pin", 1000, 9000, "pinterest", "lucas", "c" * 64)
            self.assertTrue(again["already_published"])

    def test_dry_run_returns_strategy_without_playwright(self):
        with tempfile.TemporaryDirectory() as td:
            video = Path(td) / "clip.mp4"
            video.write_bytes(b"synthetic-video")
            out = publish(
                video=str(video),
                caption="Como escrever diálogos naturais sem exposição artificial",
                account="lucas",
                profile=Path(td) / "profile",
                destination_url="https://anthares.us/como-escrever-dialogos",
                commit=False,
            )
            self.assertEqual(out["status"], "DRY_RUN")
            self.assertEqual(out["platform"], "pinterest")
            self.assertEqual(out["strategy"]["board"], "Técnicas de escrita")
            self.assertLessEqual(len(out["strategy"]["title"]), 100)
            self.assertLessEqual(len(out["strategy"]["description"]), 800)
            self.assertTrue(out["destination_url"].startswith("https://"))

    def test_destination_url_is_required_even_for_dry_run(self):
        with tempfile.TemporaryDirectory() as td:
            video = Path(td) / "clip.mp4"
            video.write_bytes(b"synthetic-video")
            with self.assertRaises(ValueError):
                publish(
                    video=str(video),
                    caption="teste",
                    account="lucas",
                    profile=Path(td) / "profile",
                    destination_url="",
                    commit=False,
                )


if __name__ == "__main__":
    unittest.main()
