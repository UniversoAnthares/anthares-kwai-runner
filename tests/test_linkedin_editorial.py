import unittest
from anthares_publisher.linkedin_editorial import linkedin_caption, strategic_tags
from social_adapters.buffer_three_channels import prepare

class LinkedInEditorial(unittest.TestCase):
    def test_aristotle_context(self):
        text=linkedin_caption("Aristóteles e a ética","Uma reflexão filosófica sobre virtude.")
        self.assertIn("#Filosofia",text)
        self.assertIn("#UniversoAnthares",text)
        self.assertIn("www.anthares.us",text)
        self.assertTrue(text.splitlines()[0].endswith(" ● Universo Anthares"))

    def test_japanese_legend_tags(self):
        tags=strategic_tags("A mulher da boca rasgada", "Lenda japonesa da mitologia")
        self.assertIn("#Mitologia",tags)

    def test_retry_has_no_duplicate_brand_or_website(self):
        first=linkedin_caption("Kafka", "www.anthares.us #UniversoAnthares")
        again=linkedin_caption("Kafka ● Universo Anthares", "www.anthares.us #UniversoAnthares")
        self.assertEqual(first,again)
        self.assertEqual(again.count("www.anthares.us"),1)
        self.assertEqual(again.count("#UniversoAnthares"),1)

    def test_max_caption_length(self):
        out=linkedin_caption("Escritores e literatura","poesia " * 1600)
        self.assertLessEqual(len(out),2200)
        self.assertTrue(out.endswith("#UniversoAnthares #Literatura #Poesia"))

    def test_company_adapter_uses_editorial_copy(self):
        row={"platform":"linkedin","title":"Poemas e poetas","description":"Cultura e poesia",
             "media_url":"https://anthares.us/wp-content/uploads/2026/10/short.mp4",
             "duration_seconds":45}
        result=prepare(row)
        self.assertIn("#Poesia",result["caption"])
        self.assertIn("www.anthares.us",result["caption"])

if __name__=="__main__":unittest.main()
