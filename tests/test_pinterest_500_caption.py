"""Pinterest Buffer must obey network's 500-character text limit."""
import unittest
from social_adapters.buffer_three_channels import pinterest_caption

class PinterestCaptionLimit(unittest.TestCase):
    def test_long_transcript_description_is_bounded(self):
        title="O Valor da Interpretação em A Metamorfose ● Universo Anthares"
        description="Neste corte o debate aborda aspectos da leitura crítica. "*25+" www.anthares.us"
        tags=["#Literatura","#Kafka","#Interpretação","#Filosofia"]
        caption=pinterest_caption(title,description,tags)
        self.assertLessEqual(len(caption),500)
        self.assertIn("www.anthares.us",caption)
        self.assertIn("#Kafka",caption)
        self.assertTrue(caption.startswith(title))
        self.assertNotIn("www.anthares.us www.anthares.us",caption)
    def test_short_description_keeps_everything(self):
        title="Kafka e o Sentido da Metamorfose ● Universo Anthares"
        caption=pinterest_caption(title,"Este trecho discute o problema da interpretação na literatura.",
                                  ["#Kafka","#Literatura"])
        self.assertIn("Este trecho discute",caption)
        self.assertIn("#Literatura",caption)
        self.assertIn("www.anthares.us",caption)
    def test_extreme_title_never_bypasses_network_limit(self):
        title="T"*68+" ● Universo Anthares"
        caption=pinterest_caption(title,"Um argumento específico "+("sobre literatura "*40),["#Literatura"])
        self.assertLessEqual(len(caption),500)
        self.assertIn("#Literatura",caption)
if __name__=="__main__":unittest.main()
