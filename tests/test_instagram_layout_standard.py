"""CORTES 9:16 standard layout: verified panel counts and safe fallback."""
import unittest
from tools import cortes_instagram_layout_standard as layout

class StandardLayoutTests(unittest.TestCase):
    def test_one_person_and_unverified_faces_use_single_full_frame(self):
        self.assertEqual(layout.lanes_from_centres([(0.4,0.5)]),1)
        self.assertEqual(layout.lanes_from_centres([(0.1,0.5),(0.3,0.6)]),1)
        self.assertEqual(layout.lanes_from_centres([]),1)
        self.assertEqual(layout.lanes_from_centres([(0,0)]*5),1)

    def test_two_real_distinct_left_right_lanes_stack(self):
        self.assertEqual(layout.lanes_from_centres([(0.25,0.4),(0.76,0.4)]),2)
        self.assertIn('vstack=inputs=2',layout.layout_filter(2))
        self.assertIn('crop=720:540',layout.layout_filter(2))

    def test_three_presenters_three_vertical_panels(self):
        self.assertEqual(layout.lanes_from_centres([(0.15,0.5),(0.48,0.5),(0.83,0.5)]),3)
        self.assertIn('vstack=inputs=3',layout.layout_filter(3))
        self.assertIn('crop=720:360',layout.layout_filter(3))

    def test_four_presenters_two_by_two_grid(self):
        self.assertEqual(layout.lanes_from_centres([
            (0.25,0.25),(0.75,0.25),(0.25,0.75),(0.75,0.75)]),4)
        self.assertIn('hstack=inputs=2',layout.layout_filter(4))
        self.assertIn('vstack=inputs=2',layout.layout_filter(4))
        self.assertEqual(layout.lanes_from_centres([(0.25,0.25)]*4),1)

    def test_all_templates_preserve_canonical_geometry_and_title_layer(self):
        for count in (1,2,3,4):
            f=layout.layout_filter(count)
            self.assertIn('pad=720:1280:0:150',f)
            self.assertIn('[canvas][1:v]overlay=0:0',f)
            self.assertIn('format=yuv420p[v]',f)
            self.assertEqual((layout.WIDTH,layout.HEIGHT,layout.HEADER,layout.BODY,layout.FOOTER),
                             (720,1280,150,1080,50))

if __name__=="__main__":
    unittest.main()
