import io,json,unittest
from unittest.mock import patch
from tools import cortes_pinterest_metadata_qa as qa

class QAHeadlineResilience(unittest.TestCase):
 def test_llm_without_hashtags_derives_contextual_hashtags(self):
  text=("Interpretações diferentes de uma obra não tornam automaticamente o livro bom. "
        "Discordar de um crítico não significa que alguém esteja errado. ")*3
  value={"title":"Por que uma interpretação não salva um livro ruim",
         "keywords":["interpretação literária","valor estético","discordância crítica","livro ruim"],
         "hashtags":[]}
  response=io.BytesIO(json.dumps({"response":json.dumps(value,ensure_ascii=False)}).encode())
  with patch.object(qa.urllib.request,"urlopen",return_value=response):
   meta=qa.strategic_metadata(text,"A Metamorfose [Kafka] - ANÁLISE (LIVE)",
                               "g1:fOmihuHUT1M:1727:1763")
  self.assertGreaterEqual(len(meta["hashtags"]),2)
  self.assertTrue(all(tag.startswith("#") for tag in meta["hashtags"]))
  self.assertNotEqual(meta["title"],"A Metamorfose [Kafka] - ANÁLISE (LIVE)")
  self.assertEqual(meta["editorial_policy"],"anthares_editorial_transcript_v2")
 def test_qwen_string_keywords_uses_grounded_fallback(self):
  excerpt=("Interpretações possíveis não salvam um livro ruim. "
           "Gosto pessoal e valor estético são conceitos diferentes. ")*5
  response={"title":"O que distingue gostar de uma obra e julgar sua qualidade",
            "keywords":"interpretações possíveis, valor estético",
            "hashtags":""}
  with patch.object(qa.urllib.request,"urlopen",
       return_value=io.BytesIO(json.dumps({"response":json.dumps(response)}).encode())):
   value=qa.strategic_metadata(excerpt,
       "A Metamorfose [Kafka] - ANÁLISE (LIVE)", "g1:fOmihuHUT1M:1727:1763")
  self.assertGreaterEqual(len(value["keywords"]),3)
  self.assertGreaterEqual(len(value["hashtags"]),2)
  self.assertIn("www.anthares.us",value["description"])

 def test_worker_guard_context(self):
  with qa.single_worker_guard() as acquired:
   self.assertTrue(acquired)
   with qa.single_worker_guard() as another:
    self.assertFalse(another)

if __name__=="__main__":unittest.main()
