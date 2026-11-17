#!/usr/bin/env python3
"""Readonly code drift probe relative to G6/G5 approved plugin; emits bounded sanitized diff."""
import importlib.util,os,pathlib,subprocess,tempfile
p=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('bridge',p/'studio-g5g6-isolated-qa.py')
b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
REMOTE=r"""
import difflib,hashlib,pathlib,subprocess,re
home=pathlib.Path.home();private=home/'domains/anthares.us/anthares-private-storage'
source=private/'studio-g6-review-20261116/anthares-studio/anthares-estudio.php'
live=home/'domains/anthares.us/public_html/wp-content/plugins/anthares-studio/anthares-estudio.php'
def blob(s):return hashlib.sha1(b'blob '+str(len(s)).encode()+b'\0'+s).hexdigest()
def need(b,label):
 if not b:raise RuntimeError(label)
expected=source.read_text(encoding='utf8')
old="""add_filter('body_class', function($classes){
 if(is_page('studio') && (!is_user_logged_in() || !anst_can_use()))$classes[]='aest-access-gate';
 return $classes;
});"""
new="""add_filter('body_class', function($classes){
 if (is_page('studio')) {
  // Identidade visual estável e exclusiva do novo Studio.
  $classes[] = 'anst-studio-page';
  if (!is_user_logged_in() || !anst_can_use()) $classes[] = 'aest-access-gate';
 }
 return $classes;
});"""
need(expected.count(old)==1,'SOURCE_BODY_CHANGED')
expected=expected.replace(old,new)
anchor="function anst_trash_cleanup_enabled(){return (string)get_option('anst_trash_cleanup_enabled','0')==='1';}"
guard="""
/** Preserva itens ANST da lixeira quando WordPress executa limpeza nativa. */
add_filter('pre_delete_post',static function($pre,$post,$force_delete){
 if($pre!==null)return $pre;
 if(!anst_trash_cleanup_enabled()&&doing_action('wp_scheduled_delete')&&
    $post instanceof WP_Post&&in_array($post->post_type,anst_trash_types(),true))return false;
 return $pre;
},10,3);"""
need(expected.count(anchor)==1,'SOURCE_GUARD_CHANGED')
expected=expected.replace(anchor,anchor+'\n'+guard)
need(blob(expected.encode())=='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb','INTEGRATED_SOURCE_UNEXPECTED')
actual=live.read_text(encoding='utf8')
print('G5_DRIFT_LIVE_BLOB='+blob(actual.encode()),flush=True)
print('G5_DRIFT_LIVE_SHA256='+hashlib.sha256(actual.encode()).hexdigest(),flush=True)
print('G5_DRIFT_SOURCE_LINES='+str(len(expected.splitlines())),flush=True)
print('G5_DRIFT_LIVE_LINES='+str(len(actual.splitlines())),flush=True)
before=expected.splitlines();after=actual.splitlines()
changes=[(tag,i,j,k,l) for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes() if tag!='equal']
print('G5_DRIFT_HUNKS='+str(len(changes)),flush=True)
for idx,(tag,i,j,k,l) in enumerate(changes[:16]):
 print('G5_DRIFT_HUNK_'+str(idx)+'='+tag+' expected_'+str(i+1)+'_'+str(j)+' live_'+str(k+1)+'_'+str(l),flush=True)
 for prefix,arr in [('REMOVED',before[i:j]),('ADDED',after[k:l])]:
  for n,line in enumerate(arr[:6]):
   if re.search(r'(?i)(password|private_key|token|authorization|secret)',line):
    line='[REDACTED]'
   line=re.sub(r'[^A-Za-z0-9 .:_=/$|(){};?!+\-\[\]#\"\\x27]','_',line).strip()[:175]
   print('G5_DRIFT_'+prefix+'_'+str(idx)+'_'+str(n)+'='+line,flush=True)
print('G5_DRIFT_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('BRANCH')
 key,host,port,user=b.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='g5-drift-') as t:
  d=pathlib.Path(t);k=d/'key';k.write_text(key);k.chmod(0o600)
  h=d/'hosts';h.write_text('anthares-g5-drift '+b.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5-drift','-o','ConnectTimeout=10',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=90)
  for line in r.stdout.splitlines():
   if line.startswith('G5_DRIFT_'):print(line,flush=True)
  if r.returncode:
   last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G5_DRIFT_ERROR='+''.join(c if c.isalnum() or c in ' _:.-' else '_' for c in last)[:120],flush=True)
   raise RuntimeError('DRIFT_PROBE_FAILED')
  if 'G5_DRIFT_PROVEN=1' not in r.stdout:raise RuntimeError('DRIFT_PROOF_MISSING')
if __name__=='__main__':main()
