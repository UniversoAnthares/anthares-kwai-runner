#!/usr/bin/env python3
"""QA against byte-matched G4+G5+G6 integration assembled in an owned isolated clone."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g5_transport',here/'studio-g5g6-isolated-qa.py')
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
REMOTE=r"""
import hashlib,pathlib,subprocess,tempfile,shutil,re,sys
home=pathlib.Path.home()
private=home/'domains/anthares.us/anthares-private-storage'
source=private/'studio-g6-review-20261116'
sha0='3efad7ad3b41e765132f625202daad88f8f2ee7d'
expected={
 'anthares-studio/anthares-estudio.php':'0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb',
 'anthares-studio/assets/estudio.css':'a0238eb95b78da38b427b1da566463f611fcd37c',
 'anthares-studio/assets/estudio-dark.css':'1afedf2d97abcbd8ccdbf78251bcf1f4c68fe6d9',
 'anthares-studio/tests/test_isolation.py':'b3902ff5102bcb6fa6b94203985cc374406b1a82',
}
def fail(cond,code):
 if not cond:raise RuntimeError(code)
def git_sha(path):
 data=path.read_bytes()
 return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\x00'+data).hexdigest()
def leftstrip_one_continuation(value):
 lines=value.split('\n')
 return '\n'.join([lines[0]]+[(part[1:] if part.startswith(' ') else part) for part in lines[1:]])
head=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=10).strip()
fail(head==sha0,'G6_SOURCE_HEAD_CHANGED')
T=pathlib.Path(tempfile.mkdtemp(prefix='studio-g4-g5-g6-integrated-',dir=private))
try:
 repo=T/'code'
 p=subprocess.run(['git','clone','--quiet','--no-hardlinks','--local',str(source),str(repo)],
                  capture_output=True,text=True,timeout=30)
 fail(p.returncode==0,'G6_CLEAN_CLONE_FAILED')
 p=subprocess.run(['git','-C',str(repo),'checkout','--quiet','--detach',sha0],capture_output=True,text=True,timeout=15)
 fail(p.returncode==0,'G6_CHECKOUT_FAILED')
 php=repo/'anthares-studio/anthares-estudio.php'
 code=php.read_text(encoding='utf-8')
 bodyOld='''add_filter('body_class', function($classes){
  if(is_page('studio') && (!is_user_logged_in() || !anst_can_use()))$classes[]='aest-access-gate';
  return $classes;
});'''
 bodyNew='''add_filter('body_class', function($classes){
 if (is_page('studio')) {
  // Identidade visual estável e exclusiva do novo Studio.
  $classes[] = 'anst-studio-page';
  if (!is_user_logged_in() || !anst_can_use()) $classes[] = 'aest-access-gate';
 }
 return $classes;
});'''
 bodyOld=leftstrip_one_continuation(bodyOld)
 fail(code.count(bodyOld)==1,'G6_BODY_OLD_SCOPE_MISMATCH')
 code=code.replace(bodyOld,bodyNew)
 anchor="function anst_trash_cleanup_enabled(){return (string)get_option('anst_trash_cleanup_enabled','0')==='1';}"
 guard='''
/** Preserva itens ANST da lixeira quando WordPress executa limpeza nativa. */
add_filter('pre_delete_post',static function($pre,$post,$force_delete){
 if($pre!==null)return $pre;
 if(!anst_trash_cleanup_enabled()&&doing_action('wp_scheduled_delete')&&
    $post instanceof WP_Post&&in_array($post->post_type,anst_trash_types(),true))return false;
 return $pre;
},10,3);'''
 fail(code.count(anchor)==1 and "add_filter('pre_delete_post'" not in code,'TRASH_GUARD_SOURCE_CHANGED')
 code=code.replace(anchor,anchor+'\n'+guard)
 php.write_text(code,encoding='utf-8')
 for name,count in [('estudio.css',509),('estudio-dark.css',216)]:
  p=repo/'anthares-studio/assets'/name
  text=p.read_text(encoding='utf-8')
  fail(text.count('page-id-19344')==count,'CSS_BASELINE_CHANGED_'+name)
  text=text.replace('page-id-19344','anst-studio-page')
  if name=='estudio.css':
   fail(text.count('article#post-19344')==6,'ARTICLE_SELECTOR_COUNT_CHANGED')
   text=text.replace('article#post-19344','article')
  p.write_text(text,encoding='utf-8')
 tests=repo/'anthares-studio/tests/test_isolation.py'
 t=tests.read_text(encoding='utf-8')
 remove=[
 "    'assets/estudio.css':'cc50278d75bc6a42d0c1bc6941e659b8372191266aef4760762189c06de973ee',\n",
 "    'assets/estudio-dark.css':'ad8d92fb38caf7afecc2409b3bcced8c0e63446b2a27776972b55dfface19a92',\n"]
 for snippet in remove:
  fail(t.count(snippet)==1,'HASH_TEST_SOURCE_CHANGED')
  t=t.replace(snippet,'')
 old='    def test_all_visual_assets_remain_identical(self):'
 new='''    def test_new_studio_only_page_scoping(self):
        self.assertIn("$classes[] = 'anst-studio-page';", PHP)
        for name, count in [('assets/estudio.css', 509), ('assets/estudio-dark.css', 216)]:
            content=(ROOT/name).read_text(encoding='utf8')
            with self.subTest(name=name):
                self.assertNotIn('page-id-19344',content)
                self.assertNotIn('post-19344',content)
                self.assertEqual(content.count('anst-studio-page'), count)
        css=(ROOT/'assets/estudio.css').read_text(encoding='utf8')
        self.assertIn('body.anst-studio-page #sidebar-primary',css)
        self.assertIn('body.anst-studio-page #page-titlebar',css)
        self.assertIn('body.anst-studio-page #main.content-area',css)
        self.assertIn("add_filter('pre_delete_post'",PHP)
        self.assertIn("add_filter('wp_untrash_post_status'",PHP)

    def test_unchanged_vendor_and_backups_remain_identical(self):'''
 fail(t.count(old)==1,'TEST_CASE_SOURCE_CHANGED')
 tests.write_text(t.replace(old,new),encoding='utf-8')
 for rel,sha in expected.items():
  actual=git_sha(repo/rel)
  if actual!=sha:
   print('INTEGRATED_BLOB_MISMATCH='+rel.replace('/','_'),flush=True)
  fail(actual==sha,'INTEGRATION_NOT_BYTE_EXACT')
 print('INTEGRATION_SOURCE_MATCH=4_OF_4_GITHUB_BLOBS',flush=True)
 lint=subprocess.run(['/opt/alt/php83/usr/bin/php','-l',str(php)],capture_output=True,text=True,timeout=15)
 fail(lint.returncode==0,'INTEGRATED_PHP_LINT_FAILED')
 print('INTEGRATED_PHP_LINT=PASS',flush=True)
 unit=subprocess.run(['/opt/alt/python311/bin/python3.11','-m','unittest','discover','-s',str(repo/'anthares-studio/tests'),'-p','test*.py'],
                     cwd=repo,capture_output=True,text=True,timeout=75)
 if unit.returncode:
  print('INTEGRATED_UNIT_FAILURE='+re.sub('[^A-Za-z0-9 _.-]','_',unit.stderr.splitlines()[-1])[:90],flush=True)
 fail(unit.returncode==0,'INTEGRATED_UNIT_TEST_FAILED')
 matched=re.search(r'Ran (\d+) tests',unit.stderr)
 print('INTEGRATED_UNIT_TESTS_PASS='+str(matched.group(1) if matched else 'unknown'),flush=True)
 qa=subprocess.run(['/opt/alt/python311/bin/python3.11','qa/manifest-coverage-preflight.py','--check'],
                   cwd=repo,capture_output=True,text=True,timeout=45)
 fail(qa.returncode==0,'INTEGRATED_QA_MANIFEST_FAILED')
 print('INTEGRATED_MANIFEST=PASS',flush=True)
 g5=repo/'anthares-studio/tests/integration/g5-runtime-isolated.sh'
 print('INTEGRATED_G5_RUNTIME_STARTED=1',flush=True)
 run=subprocess.run(['bash',str(g5)],cwd=repo,capture_output=True,text=True,timeout=260)
 for ln in run.stdout.splitlines():
  if ln.startswith(('G5_ACF_APPLY','G5_RUNTIME_FLAG','G5_RUNTIME_FIXTURE_PASS','G5_LEGACY_OFF','G5_ACF_RUNTIME_INTEGRATION_PASS')):
   print('INTEGRATED_G5_EVENT='+ln[:95],flush=True)
 fail(run.returncode==0 and 'G5_ACF_RUNTIME_INTEGRATION_PASS' in run.stdout,'INTEGRATED_G5_RUNTIME_FAILED')
 print('INTEGRATED_G5_RUNTIME_PASS=1',flush=True)
 print('INTEGRATED_G4_G5_G6_SOURCE_TESTED=1',flush=True)
finally:
 shutil.rmtree(T,ignore_errors=True)
 print('INTEGRATED_QA_PRIVATE_CLEANUP=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 key,host,port,user=transport.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g4g5-merged-') as tmp:
  k=pathlib.Path(tmp)/'key';k.write_text(key);k.chmod(0o600)
  hosts=pathlib.Path(tmp)/'hosts';hosts.write_text('anthares-g4g5-merge '+transport.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(hosts),
       '-o','HostKeyAlias=anthares-g4g5-merge','-o','ConnectTimeout=12',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  p=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=310)
  for line in p.stdout.splitlines():
   if line.startswith(('INTEGRATION_','INTEGRATED_')):print(line,flush=True)
  if p.returncode:
   tail=(p.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('INTEGRATED_QA_ERROR='+''.join(c if c.isalnum() or c in ' _:-' else '_' for c in tail)[:120],flush=True)
   raise RuntimeError('INTEGRATED_QA_REMOTE_FAILED')
  if 'INTEGRATED_G4_G5_G6_SOURCE_TESTED=1' not in p.stdout:raise RuntimeError('EXPECTED_PROOF_MISSING')
if __name__=='__main__':
 main()
