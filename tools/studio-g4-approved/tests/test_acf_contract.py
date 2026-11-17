from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
 'anst_projeto':set('_anst_start _anst_visibility _anst_topic _anst_premise _anst_logline _anst_storyline _anst_theme _anst_thesis _anst_tone _anst_summary _anst_events _anst_outline _anst_project_tone _anst_board_columns _anst_legacy_cards_imported _anst_unlock_v1 _anst_unlock_v2 _anst_elements_v1 _anst_elements_versions_v1 _anst_review_v1 _anst_source_id _anst_source_type _anst_source_sha256 _anst_cascade_project'.split()),
 'anst_nota':set('_anst_kind _anst_project _anst_source_id _anst_source_type _anst_source_sha256 _anst_cascade_project'.split()),
 'anst_capitulo':set('_anst_project _anst_delta _anst_import_sha _anst_pre_encoding_repair_backup _anst_pre_original_source_restore_20261113 _anst_structure_map_v1 _anst_versions_v1 _anst_source_id _anst_source_type _anst_source_sha256 _anst_cascade_project'.split()),
 'anst_cartao':set('_anst_project _anst_column _anst_rank _anst_color _anst_card_notes _anst_source_id _anst_source_type _anst_source_sha256 _anst_cascade_project'.split()),
}
class TestAcfContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.groups=[json.loads(x.read_text(encoding='utf8')) for x in (ROOT/'acf-json').glob('group_anst*.json')]
  cls.ledger=json.loads((ROOT/'docs/acf-core-migration-map.json').read_text(encoding='utf8'))
  cls.fields=[f for g in cls.groups for f in g['fields']]
 def test_group_count(self):
  self.assertEqual(len(self.groups),12);self.assertEqual(len(self.fields),40)
  self.assertEqual(self.ledger['fields'],40)
 def test_unique_names_and_keys(self):
  for a in ([g['key'] for g in self.groups],[f['key'] for f in self.fields],[f['name'] for f in self.fields]):self.assertEqual(len(a),len(set(a)))
 def test_offline(self):
  self.assertTrue(all(not g['active'] and g['show_in_rest']==0 for g in self.groups))
 def test_safe_names_and_types(self):
  fs={f['name']:f for f in self.fields}
  for f in self.fields:
   self.assertTrue(f['name'].startswith('studio_'))
   self.assertIn(f['type'],{'text','textarea','number','select','true_false','post_object'})
  for r in self.ledger['entries']:
   self.assertEqual(r['target_field_key'],fs[r['target_field_name']]['key'])
   self.assertNotEqual(r['legacy_key'],'_'+r['target_field_name'])
 def test_postmeta_coverage(self):
  for typ,keys in EXPECTED.items():
   actual={e['legacy_key'] for e in self.ledger['entries'] if e['post_type']==typ}
   self.assertEqual(actual,keys,typ)
 def test_quill_raw(self):
  f=next(f for f in self.fields if f['name']=='studio_chapter_delta_json')
  self.assertEqual((f['type'],f['new_lines'],f['maxlength']),('textarea','',0))
 def test_relations(self):
  for n in ('note_project_ref','card_project_ref','chapter_project_ref','cascade_project_ref'):
   f=next(f for f in self.fields if f['name']=='studio_'+n)
   self.assertEqual(f['post_type'],['anst_projeto'])
   self.assertEqual(f['return_format'],'id')
 def test_user_zoom(self):
  zoom=[e for e in self.ledger['entries'] if e['legacy_key']=='_anst_board_zoom_*']
  self.assertEqual(len(zoom),1);self.assertEqual(zoom[0]['legacy_storage'],'user')
if __name__=='__main__':unittest.main()
