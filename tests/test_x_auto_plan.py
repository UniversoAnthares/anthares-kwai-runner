import unittest
from tools.x_auto_plan import choose, plan

class XAutoPlanTests(unittest.TestCase):
    def request(self):
        words = []
        for i in range(1200):
            start = round(i * 0.65, 3)
            words.append({"id": i, "s": start, "e": round(start + .48, 3),
                          "t": "literatura." if i % 31 == 0 else "narrativa"})
        return {"kind": "X_MICROCUT_REQUEST_V1", "account": "lucasyahn",
                "output_policy": {"orientation": "horizontal", "aspect_ratio": "16:9",
                                  "source_class": "long_form"},
                "source": {"title": "Estudo de uma narrativa longa"}, "words": words}

    def test_auto_plan_selects_valid_long_segment(self):
        request = self.request()
        selected = plan(request)
        self.assertEqual(selected["kind"], "X_MICROCUT_PLAN_V1")
        self.assertTrue(0 <= selected["start_word_id"] < selected["end_word_id"])
        words = request["words"]
        a, b = selected["start_word_id"], selected["end_word_id"]
        self.assertTrue(520 <= words[b]["e"]-words[a]["s"] <= 760)
        self.assertTrue(0 < len(selected["caption"]) <= 240)

    def test_rejects_wrong_destination(self):
        request = self.request()
        request["account"] = "other"
        with self.assertRaisesRegex(ValueError, "CONTRACT"):
            plan(request)

    def test_rejects_insufficient_source(self):
        request = self.request()
        request["words"] = request["words"][:20]
        with self.assertRaisesRegex(ValueError, "TOO_SHORT"):
            plan(request)

if __name__ == "__main__":
    unittest.main()
