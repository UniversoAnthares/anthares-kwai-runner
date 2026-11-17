#!/usr/bin/env python3
"""G4 screenshots on GitHub runner Docker WordPress, using code-only Hostinger tar.
Never exports production databases, accounts, cookies, or authored works.
"""
import hashlib, io, importlib.util, json, os, pathlib, re, shutil, socket, subprocess, tarfile, tempfile
from playwright.sync_api import sync_playwright

HERE=pathlib.Path(__file__).resolve().parent
helper=HERE/'studio-g5g6-isolated-qa.py'
spec=importlib.util.spec_from_file_location('anthares_g5_ssh',helper)
bridge_mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge_mod)
BASE_URL='http://127.0.0.1:19080'
PASS='Synthetic-Only-G4-2026!'
LOGIN='g4synthetic'
G6_HEAD='3efad7ad3b41e765132f625202daad88f8f2ee7d'
REMOTE=r"""
import io,json,os,pathlib,re,subprocess,sys,tarfile
home=pathlib.Path.home()
root=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
old=root/'wp-content/plugins/anthares-estudio'
live=root/'wp-content/plugins/anthares-studio'
dev=private/'studio-g6-review-20261116/anthares-studio'
acf=root/'wp-content/plugins/advanced-custom-fields'
def require(check,label):
 if not check:raise RuntimeError(label)
for folder in (old,live,dev,acf):
 require(folder.is_dir() and not folder.is_symlink(),'MISSING_SOURCE')
php='/opt/alt/php83/usr/bin/php'
command=[php,'-r',"require '"+str(root/'wp-load.php')+"';echo json_encode(['stylesheet'=>get_stylesheet(),'template'=>get_template()]);"]
res=subprocess.run(command,capture_output=True,text=True,timeout=45)
require(res.returncode==0,'WP_THEME_LOOKUP_FAILED')
match=re.search(r'\{"stylesheet":"([A-Za-z0-9_-]+)","template":"([A-Za-z0-9_-]+)"\}',res.stdout)
require(match is not None,'WP_THEME_NAMES_UNAVAILABLE')
names=list(dict.fromkeys(match.groups()))
theme_root=root/'wp-content/themes'
for name in names:
 require((theme_root/name).is_dir(),'THEME_FOLDER_MISSING')
# Stream whitelisted directories only: source code and styles, never wp-config, uploads, DB, user records or secrets.
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as z:
 for origin,arc in ((old,'legacy/anthares-estudio'),
                    (live,'live/anthares-studio'),
                    (dev,'dev/anthares-studio'),
                    (acf,'acf/advanced-custom-fields')):
  z.add(origin,arcname=arc,recursive=True,filter=lambda ti: None if (ti.name.endswith('/.git') or '/.git/' in ti.name or '/node_modules/' in ti.name or '/.env' in ti.name) else ti)
 for name in names:
  z.add(theme_root/name,arcname='themes/'+name,recursive=True,filter=lambda ti:None if '/.git/' in ti.name else ti)
 info=json.dumps({'stylesheet':names[0], 'template':names[-1], 'g6_source':'3efad7ad3b41e765132f625202daad88f8f2ee7d'}).encode()
 meta=tarfile.TarInfo('metadata.json');meta.size=len(info);z.addfile(meta,io.BytesIO(info))
"""

def check(ok,code):
 if not ok:raise RuntimeError(code)
def run(cmd,**kwargs):
 return subprocess.run(cmd,check=True,text=True,**kwargs)
def docker(*args):
 return run(['docker',*args],capture_output=True).stdout.strip()
def wp(*args):
 return docker('exec','-u','www-data','anthares-g4-wp','php','/tmp/wp-cli.phar','--path=/var/www/html','--skip-themes',*map(str,args))
def safe_extract(bundle,destination):
 destination.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(bundle),mode='r:gz') as t:
  members=t.getmembers()
  check(len(members)<15000,'BUNDLE_TOO_MANY_FILES')
  for m in members:
   check(not m.issym() and not m.islnk() and not m.isdev(),'BUNDLE_HAS_LINK_OR_DEVICE')
   check(not m.name.startswith('/') and '..' not in pathlib.PurePosixPath(m.name).parts,'BUNDLE_BAD_PATH')
  t.extractall(path=destination,filter='data')
 return json.loads((destination/'metadata.json').read_text())

def retrieve_code(root):
 key,host,port,user=bridge_mod.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='anthares-visual-ssh-') as folder:
  home=pathlib.Path(folder)
  keyfile=home/'key';keyfile.write_text(key);keyfile.chmod(0o600)
  hosts=home/'hosts';hosts.write_text('anthares-g4-docker '+bridge_mod.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(keyfile),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(hosts),
       '-o','HostKeyAlias=anthares-g4-docker','-o','ConnectTimeout=12',f'{user}@{host}',
       '/opt/alt/python311/bin/python3.11 -']
  result=subprocess.run(cmd,input=REMOTE.encode(),capture_output=True,timeout=100)
  check(result.returncode==0,'SSH_CODE_BUNDLE_FAILED')
  check(1000<len(result.stdout)<130_000_000,'BUNDLE_UNEXPECTED_SIZE')
  info=safe_extract(result.stdout,root)
  print('G4_CODE_ARCHIVE_BYTES='+str(len(result.stdout)),flush=True)
  print('G4_ACTIVE_THEME='+info['stylesheet'],flush=True)
  return info

def git_sha(content):
 return hashlib.sha1(b'blob '+str(len(content)).encode()+b'\x00'+content).hexdigest()

def patch_integrated(dev,original):
 # Four exact integration blobs already independently verified in run 44008570966.
 php=dev/'anthares-estudio.php'
 s=php.read_bytes().decode('utf8')
 before="""add_filter('body_class', function($classes){
 if(is_page('studio') && (!is_user_logged_in() || !anst_can_use()))$classes[]='aest-access-gate';
 return $classes;
});"""
 after="""add_filter('body_class', function($classes){
 if (is_page('studio')) {
  // Identidade visual estável e exclusiva do novo Studio.
  $classes[] = 'anst-studio-page';
  if (!is_user_logged_in() || !anst_can_use()) $classes[] = 'aest-access-gate';
 }
 return $classes;
});"""
 check(s.count(before)==1,'G6_BODY_FILTER_BASE_CHANGED')
 s=s.replace(before,after)
 anchor="function anst_trash_cleanup_enabled(){return (string)get_option('anst_trash_cleanup_enabled','0')==='1';}"
 guard="""
/** Preserva itens ANST da lixeira quando WordPress executa limpeza nativa. */
add_filter('pre_delete_post',static function($pre,$post,$force_delete){
 if($pre!==null)return $pre;
 if(!anst_trash_cleanup_enabled()&&doing_action('wp_scheduled_delete')&&
    $post instanceof WP_Post&&in_array($post->post_type,anst_trash_types(),true))return false;
 return $pre;
},10,3);"""
 check(s.count(anchor)==1,'G6_TRASH_GUARD_BASE_CHANGED')
 s=s.replace(anchor,anchor+'\n'+guard)
 approval="// A ativação do repositório ACF exige também anst_acf_runtime_enabled=1; OFF mantém o legado.\nif (!defined('ANST_ACF_RUNTIME_APPROVED')) { define('ANST_ACF_RUNTIME_APPROVED', true); }\n"
 header="if (!defined('ABSPATH')) { exit; }\n"
 check(s.count(header)==1,'APPROVAL_INSERTION_ANCHOR_CHANGED')
 s=s.replace(header,header+approval)
 for old,new in [
  ("$column=sanitize_key((string)$req->get_param('column'));","$column=sanitize_text_field((string)$req->get_param('column'));"),
  ("$col=sanitize_key((string)$req->get_param('column'));","$col=sanitize_text_field((string)$req->get_param('column'));"),
  ("anst_meta_update((int)$item['id'],'_anst_column',sanitize_key($item['column']));","anst_meta_update((int)$item['id'],'_anst_column',sanitize_text_field((string)$item['column']));"),
  ("$cols[]=['id'=>'col_'.wp_generate_password(8,false,false),'name'=>$name];","$cols[]=['id'=>'col_'.strtolower(wp_generate_password(8,false,false)),'name'=>$name];"),
 ]:
  check(s.count(old)==1,'G4_COLUMNS_PATCH_PRECONDITION_CHANGED')
  s=s.replace(old,new)
 php.write_bytes(s.encode())
 for name,count in [('estudio.css',509),('estudio-dark.css',216)]:
  path=dev/'assets'/name
  old=path.read_bytes()
  check(old.count(b'page-id-19344')==count,'G6_CSS_BASELINE_CHANGED')
  new=old.replace(b'page-id-19344',b'anst-studio-page')
  if name=='estudio.css':
   check(new.count(b'article#post-19344')==6,'G6_ARTICLE_SCOPE_CHANGED')
   new=new.replace(b'article#post-19344',b'article')
  path.write_bytes(new)
 # G4 contract discovery: unlock completion writes _anst_events, which requires its own ACF field.
 group=dev/'acf-json/group_anst02_v1.json'
 obj=json.loads(group.read_text(encoding='utf8'))
 check(len(obj['fields'])==9,'G4_ACF_02_OLD_COUNT_CHANGED')
 idx=next(i for i,x in enumerate(obj['fields']) if x['name']=='studio_summary')
 field={**obj['fields'][idx],'key':'field_anst02_events_v1','label':'events','name':'studio_events'}
 obj['fields'].insert(idx+1,field)
 obj['modified']=1794920700
 group.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 manifest=dev/'docs/acf-core-migration-map.json'
 ledger=json.loads(manifest.read_text(encoding='utf8'))
 check(ledger['fields']==39 and ledger['mappings']==51 and len(ledger['entries'])==51,'G4_ACF_MAP_OLD_COUNT_CHANGED')
 ix=next(i for i,x in enumerate(ledger['entries']) if x['legacy_key']=='_anst_summary' and x['post_type']=='anst_projeto')
 ledger['entries'].insert(ix+1,{'post_type':'anst_projeto','legacy_key':'_anst_events',
   'target_field_name':'studio_events','target_field_key':'field_anst02_events_v1',
   'legacy_storage':'postmeta','conversion':'preserve_raw_json_or_text','status':'OFFLINE_NOT_MIGRATED'})
 ledger['fields']=40
 ledger['mappings']=52
 manifest.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 for name,changes in [
   ('includes/acf/class-anst-acf-repository.php',[
      ("(int)($json['fields'] ?? 0) !== 39 || count($json['entries'] ?? []) !== 51",
       "(int)($json['fields'] ?? 0) !== 40 || count($json['entries'] ?? []) !== 52")]),
   ('includes/acf/class-anst-acf-migrator.php',[
      ('count($this->fields) !== 39','count($this->fields) !== 40'),
      ('count($this->mappings) !== 51','count($this->mappings) !== 52')]),
   ('tests/test_acf_contract.py',[
      ('_anst_tone _anst_summary _anst_outline','_anst_tone _anst_summary _anst_events _anst_outline'),
      ('len(self.fields),39','len(self.fields),40'),
      ("self.ledger['fields'],39","self.ledger['fields'],40")])
 ]:
  target=dev/name
  data=target.read_text(encoding='utf8')
  for old,new in changes:
   check(data.count(old)==1,'G4_ACF_CONTRACT_PATCH_CHANGED_'+name)
   data=data.replace(old,new)
  target.write_text(data,encoding='utf8')
 tests=dev/'tests/test_isolation.py'
 t=tests.read_text()
 for line in [
    "    'assets/estudio.css':'cc50278d75bc6a42d0c1bc6941e659b8372191266aef4760762189c06de973ee',\n",
    "    'assets/estudio-dark.css':'ad8d92fb38caf7afecc2409b3bcced8c0e63446b2a27776972b55dfface19a92',\n"]:
  check(t.count(line)==1,'G6_OLD_TEST_HASH_CHANGED')
  t=t.replace(line,'')
 name="    def test_all_visual_assets_remain_identical(self):"
 test="""    def test_new_studio_only_page_scoping(self):
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

    def test_unchanged_vendor_and_backups_remain_identical(self):"""
 check(t.count(name)==1,'G6_TEST_BASE_CHANGED')
 tests.write_text(t.replace(name,test))
 expected={
  'anthares-estudio.php':'5f5ba7189e14cee11b1bffc8d850152c48351a44',
  'assets/estudio.css':'a0238eb95b78da38b427b1da566463f611fcd37c',
  'assets/estudio-dark.css':'1afedf2d97abcbd8ccdbf78251bcf1f4c68fe6d9',
  'tests/test_isolation.py':'b3902ff5102bcb6fa6b94203985cc374406b1a82',
  'docs/acf-core-migration-map.json':'e4eed3976171510c2d4146eee04c38ed6ae2fc4f',
  'acf-json/group_anst02_v1.json':'e52490e072f6cb14e8f270f62962e178e39c8e77',
  'includes/acf/class-anst-acf-repository.php':'52075b6d0ce8906058ea24579c190a305e2f7ce6',
  'includes/acf/class-anst-acf-migrator.php':'286697cc7f2f9afcbcafcd8a52147aa9273f8602',
  'tests/test_acf_contract.py':'ec360933fada2050f1a83adbd48dd3f33937c309'
 }
 for name,sha in expected.items():
  check(git_sha((dev/name).read_bytes())==sha,'G6_INTEGRATION_HASH_MISMATCH_'+name)
 print('G6_INTEGRATION_BLOBS_MATCH=4',flush=True)

def setup_docker(root,info):
 docker('network','create','anthares-g4-net')
 docker('run','-d','--name','anthares-g4-db','--network','anthares-g4-net',
        '-e','MARIADB_ROOT_PASSWORD=synthetic_root_123',
        '-e','MARIADB_DATABASE=wordpress','-e','MARIADB_USER=wordpress',
        '-e','MARIADB_PASSWORD=synthetic_db_123','mariadb:10.11')
 for i in range(35):
  z=subprocess.run(['docker','exec','anthares-g4-db','mariadb-admin','ping','-uroot',
                    '-psynthetic_root_123'],capture_output=True,text=True)
  if z.returncode==0:break
  import time;time.sleep(2)
 else:raise RuntimeError('DOCKER_MARIADB_NOT_READY')
 plugin_root=root/'mount/plugins';plugin_root.mkdir(parents=True,exist_ok=True)
 shutil.copytree(root/'legacy/anthares-estudio',plugin_root/'anthares-estudio')
 shutil.copytree(root/'live/anthares-studio',plugin_root/'anthares-studio')
 shutil.copytree(root/'acf/advanced-custom-fields',plugin_root/'advanced-custom-fields')
 # Hostinger may store private plugin files with 0700/0600 permissions.
 # Make ONLY the disposable, synthetic container copies web-readable.
 for sandbox_plugin in plugin_root.iterdir():
  for current,folders,files in os.walk(sandbox_plugin):
   os.chmod(current,0o755)
   for folder in folders:os.chmod(pathlib.Path(current)/folder,0o755)
   for file in files:
    p=pathlib.Path(current)/file
    if p.is_file() and not p.is_symlink():os.chmod(p,0o644)
 print('G4_SANDBOX_PLUGIN_READABLE=1',flush=True)
 themes=root/'themes'
 docker('run','-d','--name','anthares-g4-wp','--network','anthares-g4-net',
        '-p','127.0.0.1:19080:80',
        '-e','WORDPRESS_DB_HOST=anthares-g4-db:3306',
        '-e','WORDPRESS_DB_USER=wordpress',
        '-e','WORDPRESS_DB_PASSWORD=synthetic_db_123',
        '-e','WORDPRESS_DB_NAME=wordpress',
        '-v',str(plugin_root)+':/var/www/html/wp-content/plugins',
        '-v',str(themes)+':/var/www/html/wp-content/themes',
        'wordpress:php8.3-apache')
 # Copy wp-cli only into ephemeral docker. No package install on production.
 cli=root/'wp-cli.phar'
 cli.write_bytes(subprocess.run(
  ['curl','--fail','--silent','--show-error','--location',
   'https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar'],
  capture_output=True,check=True,timeout=70).stdout)
 docker('cp',str(cli),'anthares-g4-wp:/tmp/wp-cli.phar')
 import time
 for i in range(45):
  try:
   wp('core','version')
   break
  except subprocess.CalledProcessError:time.sleep(2)
 else:
  state=subprocess.run(['docker','inspect','--format={{.State.Status}}','anthares-g4-wp'],capture_output=True,text=True)
  logs=subprocess.run(['docker','logs','--tail','12','anthares-g4-wp'],capture_output=True,text=True)
  print('G4_WP_CONTAINER_STATUS='+state.stdout.strip(),flush=True)
  for line in (logs.stdout+'\n'+logs.stderr).splitlines()[-12:]:
   line=''.join(c if c.isalnum() or c in ' _:/.,()-' else '_' for c in line)[:150]
   print('G4_WP_CONTAINER_EVENT='+line,flush=True)
  raise RuntimeError('WORDPRESS_CONTAINER_NOT_READY')
 wp('core','install','--url='+BASE_URL,'--title=Estudio QA Isolado',
    '--admin_user='+LOGIN,'--admin_password='+PASS,'--admin_email=g4synthetic@example.invalid','--skip-email')
 # Production uses pretty REST paths; query-style REST URLs break the concatenated JS route base.
 wp('rewrite','structure','/%postname%/')
 wp('rewrite','flush','--hard')
 print('G4_PRETTY_REST_ROUTING=ENABLED',flush=True)
 for plugin_name in ('advanced-custom-fields','anthares-estudio','anthares-studio/anthares-estudio.php'):
  try:
   wp('plugin','activate',plugin_name)
   print('G4_PLUGIN_ACTIVE='+plugin_name,flush=True)
  except subprocess.CalledProcessError as e:
   print('G4_PLUGIN_ACTIVATION_FAILED='+plugin_name,flush=True)
   print('G4_SANDBOX_PLUGIN_MAIN_EXISTS='+str(int((plugin_root/'anthares-studio/anthares-estudio.php').is_file())),flush=True)
   print('G4_SANDBOX_PLUGIN_LIST='+wp('plugin','list','--field=name').replace('\n',',')[:300],flush=True)
   errors=(e.stderr or e.stdout or 'UNCLASSIFIED').splitlines()
   for line in errors[-8:]:
    clean=re.sub(r'[^A-Za-z0-9 _:/,().-]','_',line)[:175]
    print('G4_PLUGIN_DIAGNOSTIC='+clean,flush=True)
   raise
 active=info.get('stylesheet','')
 if active:
  try:
   wp('theme','activate',active)
   print('G4_THEME_ACTIVE='+active,flush=True)
  except subprocess.CalledProcessError:
   print('G4_THEME_FALLBACK=1',flush=True)
 oldid=int(wp('post','create','--post_type=page','--post_name=estudio',
                '--post_title=Estudio Antigo QA','--post_status=private',
                '--post_content=[anthares_estudio]','--porcelain'))
 newid=int(wp('post','create','--post_type=page','--post_name=studio',
                '--post_title=Estudio Novo QA','--post_status=private',
                '--post_content=[anthares_studio]','--porcelain'))
 wp('eval',"global $wpdb; $wpdb->query('UPDATE ' . $wpdb->posts . ' SET ID=19344 WHERE ID="+str(oldid)+"');")
 print('G4_OLD_PAGE_ID=19344 NEW_PAGE_ID='+str(newid),flush=True)
 wp('option','update','anst_writes_enabled','0')
 wp('option','update','anst_trash_cleanup_enabled','0')
 return plugin_root,newid

def record(page):
 return page.evaluate("""() => {
 const e=document.querySelector('#anthares-estudio-root');
 const side=document.querySelector('#sidebar-primary');
 const title=document.querySelector('#page-titlebar');
 const b=e?e.getBoundingClientRect():{x:0,y:0,width:0,height:0};
 return {
   root:!!e, x:b.x,width:b.width,height:b.height,
   text:e?.innerText?.length||0,
   sidebar:side?getComputedStyle(side).display:'absent',
   title:title?getComputedStyle(title).display:'absent',
   body:document.body.className,
   error:document.querySelector('.aest-error')?.innerText||'',
   overflow:document.documentElement.scrollWidth>window.innerWidth+30
 };
}""")

def render_pair(context,root,stage,theme,viewport,phase,newid):
 page=context.new_page()
 label=viewport
 vals=[]
 try:
  for slug,pid in [('estudio',19344),('studio',newid)]:
   page.goto(BASE_URL+'/?page_id='+str(pid),wait_until='domcontentloaded',timeout=35000)
   page.evaluate("(a)=>{localStorage.setItem(a.key,a.mode)}",
     {'key':'anthares_estudio_theme_v1' if slug=='estudio' else 'anthares_studio_theme_v1','mode':theme})
   page.reload(wait_until='domcontentloaded',timeout=35000)
   try:page.locator('#anthares-estudio-root').wait_for(state='visible',timeout=22000)
   except Exception:raise RuntimeError('G4_APP_ROOT_MISSING_'+phase+'_'+slug)
   page.wait_for_timeout(350)
   v=record(page)
   check(v['text']>30,'G4_EMPTY_APP_'+slug)
   if stage!='zero':
    check('Projeto Sintetico' in page.locator('#anthares-estudio-root').inner_text(),'G4_PROJECT_INVISIBLE_'+stage+'_'+slug)
   if phase=='live' and slug=='studio':
    check('anst-studio-page' in v['body'],'G4_NEW_SCOPE_MISSING')
   check(v['sidebar'] in ('none','absent'),'G4_WIDGET_SIDEBAR_VISIBLE_'+slug)
   check(v['title'] in ('none','absent'),'G4_PAGE_TITLE_VISIBLE_'+slug)
   check(not v['overflow'],'G4_HORIZONTAL_OVERFLOW_'+slug+'_'+label)
   check(v['width']>90,'G4_APP_TOO_NARROW_'+slug)
   shot=root/('shots/'+phase+'-'+stage+'-'+label+'-'+theme+'-'+slug+'.png')
   shot.parent.mkdir(parents=True,exist_ok=True)
   page.screenshot(path=str(shot),full_page=True,animations='disabled')
   vals.append(v)
  ratio=vals[1]['width']/vals[0]['width']
  print('G4_PAIR='+phase+'_'+stage+'_'+label+'_'+theme+
        ' width_ratio='+str(round(ratio,3))+
        ' legacy='+str(round(vals[0]['width']))+' studio='+str(round(vals[1]['width'])),flush=True)
  check(.86<=ratio<=1.14,'G4_WIDTH_PARITY_FAILED_'+label+'_'+stage)
  return vals
 finally:page.close()

def run_rest_matrix(root):
    fixture=HERE/'studio-g4-c001-c025-runtime-fixture.php'
    check(fixture.is_file(),'G4_REST_FIXTURE_MISSING')
    docker('cp',str(fixture),'anthares-g4-wp:/tmp/studio-g4-c001-c025-runtime-fixture.php')
    lint=docker('exec','anthares-g4-wp','php','-l','/tmp/studio-g4-c001-c025-runtime-fixture.php')
    check('No syntax errors' in lint,'G4_REST_FIXTURE_PHP_LINT')
    for mode in ('OFF','ON'):
        wp('option','update','anst_writes_enabled','0')
        wp('option','update','anst_acf_runtime_enabled','0' if mode=='OFF' else '1')
        command=['docker','exec','-e','G4_FIXTURE_MODE='+mode,'-u','www-data',
                 'anthares-g4-wp','php','/tmp/wp-cli.phar','--path=/var/www/html',
                 '--skip-themes','eval-file','/tmp/studio-g4-c001-c025-runtime-fixture.php']
        result=subprocess.run(command,capture_output=True,text=True,timeout=95)
        for line in result.stdout.splitlines():
            if line.startswith('G4_'):print(line,flush=True)
        if result.returncode:
            for n,line in enumerate((result.stderr.strip().splitlines() or ['NO_STDERR'])[:9]):
                safe=re.sub(r'[^A-Za-z0-9 /:()_.=-]','_',line)[:210]
                print('G4_REST_MATRIX_ERROR_'+str(n)+'_MODE='+mode+' '+safe,flush=True)
            raise RuntimeError('G4_REST_MATRIX_FAILED_'+mode)
        check('G4_SYNTHETIC_REST_MATRIX_'+mode+'=PASS' in result.stdout,
              'G4_REST_MATRIX_SUCCESS_MARKER_MISSING_'+mode)
    check(wp('option','get','anst_writes_enabled').strip()=='0','G4_SANDBOX_WRITES_LEFT_OPEN')
    print('G4_REST_MATRIX_BOTH_ACF_MODES_PASS=1',flush=True)

def login_context(browser,width,height):
 context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
 p=context.new_page()
 p.goto(BASE_URL+'/wp-login.php',wait_until='domcontentloaded',timeout=35000)
 p.locator('#user_login').fill(LOGIN)
 p.locator('#user_pass').fill(PASS)
 p.locator('#wp-submit').click()
 p.wait_for_url(re.compile(r'wp-admin|profile\.php'),timeout=30000)
 p.close()
 return context

def main():
 check(os.getenv('GITHUB_REF')=='refs/heads/coord/studio-g4-g5-20261116','WRONG_BRANCH')
 with tempfile.TemporaryDirectory(prefix='anthares-g4-docker-') as name:
  root=pathlib.Path(name)
  try:
   info=retrieve_code(root)
   patch_integrated(root/'dev/anthares-studio',root/'live/anthares-studio')
   plugin,newid=setup_docker(root,info)
   if os.getenv('G4_REST_FAST')=='1':
    staged=plugin/'anthares-studio'
    subprocess.run(['sudo','chown','-R',str(os.getuid())+':'+str(os.getgid()),str(plugin)],check=True)
    shutil.rmtree(staged)
    shutil.copytree(root/'dev/anthares-studio',staged)
    for current,folders,files in os.walk(staged):
     os.chmod(current,0o755)
     for folder in folders:os.chmod(pathlib.Path(current)/folder,0o755)
     for filename in files:
      pth=pathlib.Path(current)/filename
      if pth.is_file() and not pth.is_symlink():os.chmod(pth,0o644)
    docker('restart','anthares-g4-wp')
    import time;time.sleep(6)
    run_rest_matrix(root)
    print('G4_REST_FAST_PROVEN=1',flush=True)
    return
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/google-chrome',
      args=['--no-sandbox','--disable-gpu','--disable-background-networking'])
    try:
     for state in ('zero','one','many'):
      if state!='zero':
       for kind in ('aest_projeto','anst_projeto'):
        wp('post','create','--post_type='+kind,'--post_author=1','--post_status=publish',
           '--post_title=Projeto Sintetico '+state+' '+kind,'--porcelain')
      for width,height,label in ((1440,900,'desktop'),(390,844,'mobile')):
       context=login_context(browser,width,height)
       try:
        for theme in ('light','dark'):
         render_pair(context,root,state,theme,label,'live',newid)
       finally:context.close()
     print('G4_VISUAL_BASELINE_PASS=1',flush=True)
     # Replace only the ephemeral container-mounted new Studio. PHP worker is restarted.
     staged=plugin/'anthares-studio'
     # The WordPress container may have changed ownership of its writable volume.
     # Restore ownership only inside this job's private temporary plugin directory.
     subprocess.run(['sudo','chown','-R',str(os.getuid())+':'+str(os.getgid()),str(plugin)],check=True)
     shutil.rmtree(staged)
     shutil.copytree(root/'dev/anthares-studio',staged)
     for current,folders,files in os.walk(staged):
      os.chmod(current,0o755)
      for folder in folders:os.chmod(pathlib.Path(current)/folder,0o755)
      for filename in files:
       pth=pathlib.Path(current)/filename
       if pth.is_file() and not pth.is_symlink():os.chmod(pth,0o644)
     docker('restart','anthares-g4-wp')
     import time;time.sleep(8)
     run_rest_matrix(root)
     context=login_context(browser,1440,900)
     try:
      page=context.new_page()
      page.goto(BASE_URL+'/?page_id='+str(newid)+'#studio/inicio',wait_until='domcontentloaded')
      page.locator('#anthares-estudio-root').wait_for(state='visible',timeout=25000)
      nav=page.locator('aside.aest-nav').inner_text()
      for name in ('Início','Meus projetos','Banco de ideias','Curso de Escrita','Ajuda'):
       check(name in nav,'G6_NAV_MISSING_'+name)
      pids=wp('post','list','--post_type=anst_projeto','--post_status=publish','--field=ID').splitlines()
      check(len(pids)>=1,'G6_SYNTHETIC_PROJECT_MISSING')
      page.goto(BASE_URL+'/?page_id='+str(newid)+'#studio/projetos',wait_until='domcontentloaded')
      try:
       page.locator('.aest-project-tile-open').first.wait_for(state='visible',timeout=18000)
       page.locator('.aest-project-tile-open').first.click()
       page.locator('.aest-group-tabs').wait_for(state='visible',timeout=14000)
      except Exception:
       print('G6_ROUTE_DEBUG_HASH='+str(page.evaluate('location.hash')),flush=True)
       print('G6_ROUTE_DEBUG_TILES='+str(page.locator('.aest-project-tile-open').count()),flush=True)
       print('G6_ROUTE_DEBUG_GROUPS='+str(page.locator('.aest-group-tabs').count()),flush=True)
       raise
      buttons=page.locator('.aest-group-tabs button')
      check(buttons.count()==7,'G6_SEVEN_GROUPS_MISSING')
      print('G6_NAV_VISUAL_5_AND_7=PASS',flush=True)
      page.screenshot(path=str(root/'shots/g6-five-seven-desktop.png'),full_page=True)
      for slug in ('pesquisa','planejamento','manuscrito','analises','revisao','publicacao','visao'):
       btn=page.locator('.aest-group-tabs button[data-tab="'+slug+'"]')
       btn.click(timeout=9000)
       page.wait_for_function("(tab)=>location.hash.includes('/'+tab)",arg=slug,timeout=12000)
       check(btn.get_attribute('aria-selected')=='true','G6_ACTIVE_GROUP_WRONG_'+slug)
      # C008: a URL de projeto e o estado ativo sobrevivem ao reload e history back/forward.
      page.locator('.aest-group-tabs button[data-tab="pesquisa"]').click()
      page.wait_for_function("location.hash.includes('/pesquisa')",timeout=12000)
      page.reload(wait_until='domcontentloaded')
      page.locator('.aest-group-tabs button[data-tab="pesquisa"][aria-selected="true"]').wait_for(timeout=16000)
      page.locator('.aest-group-tabs button[data-tab="analises"]').click()
      page.wait_for_function("location.hash.includes('/analises')",timeout=12000)
      page.go_back(wait_until='domcontentloaded')
      page.wait_for_function("location.hash.includes('/pesquisa')",timeout=16000)
      page.go_forward(wait_until='domcontentloaded')
      page.wait_for_function("location.hash.includes('/analises')",timeout=16000)
      print('G4_C008_G6_DEEP_LINK_HISTORY=PASS',flush=True)
      page.close()
     finally:context.close()
     mobile=login_context(browser,390,844)
     try:
      pg=mobile.new_page()
      pg.goto(BASE_URL+'/?page_id='+str(newid)+'#studio/projetos',wait_until='domcontentloaded')
      pg.locator('.aest-project-tile-open').first.wait_for(timeout=18000)
      pg.locator('.aest-project-tile-open').first.click()
      pg.locator('.aest-group-tabs').wait_for(timeout=18000)
      check(pg.locator('.aest-group-tabs button').count()==7,'G6_MOBILE_GROUP_COUNT')
      pg.locator('.aest-group-tabs button[data-tab="manuscrito"]').click()
      pg.locator('.aest-group-tabs button[data-tab="manuscrito"][aria-selected="true"]').wait_for(timeout=16000)
      check(not pg.evaluate("document.documentElement.scrollWidth>innerWidth+30"),'G6_MOBILE_OVERFLOW')
      pg.screenshot(path=str(root/'shots/g6-seven-mobile.png'),full_page=True)
      pg.close()
      print('G4_C023_G6_MOBILE_NAV=PASS',flush=True)
     finally:mobile.close()
     anonymous=browser.new_context()
     try:
      pg=anonymous.new_page()
      resp=pg.goto(BASE_URL+'/?page_id='+str(newid),wait_until='domcontentloaded',timeout=18000)
      check(resp.status in (403,404),'G4_C025_PRIVATE_PAGE_EXPOSED')
      check('Projeto Sintetico' not in pg.locator('body').inner_text(),'G4_C025_PRIVATE_TEXT_EXPOSED')
      response=pg.goto(BASE_URL+'/wp-json/anthares-studio/v1/bootstrap',
                       wait_until='domcontentloaded',timeout=18000)
      check(response.status in (401,403),'G4_C025_REST_UNAUTH_EXPOSED')
      pg.close()
      print('G4_C025_PRIVATE_REST_UNAUTH=PASS',flush=True)
     finally:anonymous.close()
    finally:browser.close()
   print('G4_G6_VISUAL_SANDBOX_PASS=1',flush=True)
   archive=root/'evidence.zip'
   import zipfile
   with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as f:
    for file in (root/'shots').glob('*.png'):f.write(file,arcname=file.name)
   destination=pathlib.Path(os.environ.get('G4_EVIDENCE_DIR','/tmp/anthares-g4-evidence'))
   destination.mkdir(parents=True,exist_ok=True)
   shutil.copy2(archive,destination/'g4-g6-screenshots.zip')
   print('G4_EVIDENCE_SCREENSHOT_COUNT='+str(len(list((root/'shots').glob('*.png')))),flush=True)
  finally:
   subprocess.run(['docker','rm','-f','anthares-g4-wp'],capture_output=True)
   subprocess.run(['docker','rm','-f','anthares-g4-db'],capture_output=True)
   subprocess.run(['docker','network','rm','anthares-g4-net'],capture_output=True)
   subprocess.run(['sudo','chown','-R',str(os.getuid())+':'+str(os.getgid()),str(root)],capture_output=True)
   print('G4_DOCKER_CLEANUP=PASS',flush=True)

if __name__=='__main__':
 main()
