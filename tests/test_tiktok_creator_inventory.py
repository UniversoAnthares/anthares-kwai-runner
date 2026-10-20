import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"direct-tiktok-publisher"))
import tiktok_creator_inventory as inv

class CreatorStudioInventoryTest(unittest.TestCase):
    def test_marker_matched_only_in_record_it_belongs_to(self):
        target="7698574965993458964"
        other="7698574965993458965"
        data={"ItemModule":{
            target:{"id":target,"desc":"Corte literário #anthares32aabbc011"},
            other:{"id":other,"desc":"Sem marcador"},
        }}
        found=inv.collect_posts(data)
        self.assertIn(target,found)
        self.assertEqual(found[target]["id"],target)
        self.assertIn("#anthares32aabbc011",found[target]["text"])
        self.assertNotIn("#anthares32aabbc011",found[other]["text"])

    def test_no_free_floating_marker_attributed_to_another_video(self):
        data={"items":[
            {"id":"7698574965993458964","desc":"Vídeo original"},
            {"caption":"#anthares32aabbc011"},
        ]}
        posts=inv.collect_posts(data)
        self.assertNotIn("#anthares32aabbc011",posts["7698574965993458964"]["text"])

    def test_bad_ids_and_no_caption_ignored(self):
        doc={"items":[{"id":"ABC","desc":"#anthares32aabbc011"},
                      {"id":"7698574965993458964","desc":""}]}
        self.assertEqual(inv.collect_posts(doc),{})

if __name__=="__main__":
    unittest.main()
