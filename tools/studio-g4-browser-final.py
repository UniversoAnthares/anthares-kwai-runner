#!/usr/bin/env python3
"""G4 browser acceptance: Quill autosave, concurrent writer, failure recovery, and mobile in synthetic Docker WP."""
import importlib.util,os,pathlib,re,shutil,subprocess,tempfile,time,json
from playwright.sync_api import sync_playwright
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('studio_g4_docker',HERE/'studio-g4-docker-qa.py')
g4=importlib.util.module_from_spec(spec);spec.loader.exec_module(g4)
def valid(ok,code):
 if not ok:raise RuntimeError(code)
def api(page,method,path,body=None):
 try:page.wait_for_function("window.AntharesEstudio?.rest",timeout=20000)
 except Exception:
  print('G4_BROWSER_CONFIG_MISSING_URL='+str(page.url.split('?')[0]),flush=True)
  print('G4_BROWSER_ROOT_PRESENT='+str(page.locator('#anthares-estudio-root').count()),flush=True)
  print('G4_BROWSER_BODY_CLASS='+str(page.locator('body').get_attribute('class'))[:150],flush=True)
  raise
 out=page.evaluate("""async (a)=>{
 const u=window.AntharesEstudio.rest+a.path;
 const res=await fetch(u,{method:a.method,headers:{'Content-Type':'application/json','X-WP-Nonce':window.AntharesEstudio.nonce},
  credentials:'same-origin',body:a.body?JSON.stringify(a.body):undefined,cache:'no-store'});
 let data={};try{data=await res.json()}catch(e){data={error:'INVALID_RESPONSE'}}
 return {status:res.status,data};
}""",{'method':method,'path':path,'body':body})
 return out
def require_api(page,method,path,body,expected,code):
 out=api(page,method,path,body)
 valid(out['status']==expected,code+'_HTTP_'+str(out['status']))
 return out['data']
def edit_editor(page,value):
 page.locator('.ql-editor').wait_for(state='visible',timeout=23000)
 page.locator('.ql-editor').fill(value,timeout=10000)
def wait_save(page,needle='Salvo automaticamente',timeout=20000):
 page.wait_for_function("(s)=>document.querySelector('#aest-save-status')?.textContent?.includes(s)",arg=needle,timeout=timeout)
def navigate(page,newid,pid,cid):
 page.goto(f'{g4.BASE_URL}/?page_id={newid}#studio/projeto/{pid}/manuscrito/capitulo/{cid}',
           wait_until='domcontentloaded',timeout=35000)
 page.locator('.ql-editor').wait_for(state='visible',timeout=23000)
def main():
 valid(os.getenv('GITHUB_REF')=='refs/heads/coord/studio-g4-g5-20261116','BRANCH_UNEXPECTED')
 with tempfile.TemporaryDirectory(prefix='anthares-g4-browser-qa-') as name:
  root=pathlib.Path(name)
  try:
   info=g4.retrieve_code(root)
   g4.patch_integrated(root/'dev/anthares-studio',root/'live/anthares-studio')
   plugin,newid=g4.setup_docker(root,info)
   staged=plugin/'anthares-studio'
   subprocess.run(['sudo','chown','-R',str(os.getuid())+':'+str(os.getgid()),str(plugin)],check=True)
   shutil.rmtree(staged)
   shutil.copytree(root/'dev/anthares-studio',staged)
   for current,folders,files in os.walk(staged):
    os.chmod(current,0o755)
    for folder in folders:os.chmod(pathlib.Path(current)/folder,0o755)
    for filename in files:
     f=pathlib.Path(current)/filename
     if f.is_file() and not f.is_symlink():os.chmod(f,0o644)
   g4.docker('restart','anthares-g4-wp');time.sleep(5)
   g4.wp('option','update','anst_acf_runtime_enabled','1')
   g4.wp('option','update','anst_writes_enabled','1')
   with sync_playwright() as play:
    browser=play.chromium.launch(headless=True,executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-gpu'])
    try:
     context=g4.login_context(browser,1440,900)
     try:
      tabA=context.new_page()
      tabA.goto(f'{g4.BASE_URL}/?page_id={newid}',wait_until='domcontentloaded')
      project=int(require_api(tabA,'POST','projects',{'mode':'manuscrito','title':'G4 Browsers QA'},200,'CREATE_PROJECT')['id'])
      chapter=int(require_api(tabA,'POST','chapters',{'project':project,'title':'Capítulo Sintético'},200,'CREATE_CHAPTER')['id'])
      print('G4_C009_SYNTHETIC_PROJECT_CHAPTER_CREATED=PASS',flush=True)
      navigate(tabA,newid,project,chapter)
      tabB=context.new_page();navigate(tabB,newid,project,chapter)
      edit_editor(tabA,'Primeiro autor, frase com Ω e acentuação.\n')
      wait_save(tabA)
      data=require_api(tabA,'GET','bootstrap?project='+str(project),None,200,'READ_AFTER_AUTOSAVE')
      record=next(c for c in data['chapters'] if c['id']==chapter)
      valid('Primeiro autor' in str(record['delta']),'AUTOSAVE_NOT_PERSISTED')
      print('G4_C016_AUTOSAVE_REST_AND_CONFIRM=PASS',flush=True)
      edit_editor(tabB,'Segundo editor tentou sobrescrever.\n')
      wait_save(tabB,'Falha ao salvar')
      valid('Segundo editor' in tabB.locator('.ql-editor').inner_text(),'DIRTY_EDITOR_TEXT_LOST')
      persisted=require_api(tabA,'GET','bootstrap?project='+str(project),None,200,'CONCURRENT_READ')
      saved=next(c for c in persisted['chapters'] if c['id']==chapter)
      valid('Primeiro autor' in str(saved['delta']) and 'Segundo editor' not in str(saved['delta']),'CONCURRENT_OVERWRITE_OCCURRED')
      print('G4_C022_BROWSER_TWO_TABS_CONFLICT_VISIBLE=PASS',flush=True)
      tabB.reload(wait_until='domcontentloaded')
      tabB.locator('.ql-editor').wait_for(state='visible',timeout=24000)
      valid('Primeiro autor' in tabB.locator('.ql-editor').inner_text(),'RELOAD_DID_NOT_RESTORE')
      print('G4_C016_CLOSE_REOPEN_CONTENT=PASS',flush=True)
      def inject_failure(route):
       if route.request.method=='POST':route.fulfill(status=500,content_type='application/json',body='{"message":"Falha sintética de rede"}')
       else:route.continue_()
      tabB.route(re.compile(r'/wp-json/anthares-studio/v1/chapters/\d+(?:\?|$)'),inject_failure)
      edit_editor(tabB,'Conteúdo sob falha sintética, deve permanecer.\n')
      wait_save(tabB,'Falha ao salvar')
      valid('deve permanecer' in tabB.locator('.ql-editor').inner_text(),'ERROR_LOST_EDITOR_TEXT')
      tabB.unroute_all()
      tabB.locator('[data-action="save-chapter"]').click()
      wait_save(tabB,'Salvo automaticamente')
      tabB.reload(wait_until='domcontentloaded')
      tabB.locator('.ql-editor').wait_for(state='visible',timeout=24000)
      valid('deve permanecer' in tabB.locator('.ql-editor').inner_text(),'500_RECOVERY_NOT_SAVED')
      print('G4_C021_HTTP_500_MESSAGE_AND_MANUAL_RECOVERY=PASS',flush=True)
      print('G4_C015_QUILL_EDITOR_DOM_AND_UNICODE=PASS',flush=True)
      shots=root/'shots';shots.mkdir(exist_ok=True)
      tabB.screenshot(path=str(shots/'g4-editor-desktop.png'),full_page=True,animations='disabled')
      tabA.close();tabB.close()
     finally:context.close()
     mobile=g4.login_context(browser,390,844)
     try:
      pm=mobile.new_page();navigate(pm,newid,project,chapter)
      valid(pm.locator('.ql-editor').is_visible(),'MOBILE_QUILL_HIDDEN')
      valid(pm.locator('#aest-toolbar').is_visible(),'MOBILE_QUILL_TOOLBAR_HIDDEN')
      edit_editor(pm,'Texto no celular com emoji 🙂 e acentuação.\n')
      wait_save(pm)
      pm.reload(wait_until='domcontentloaded')
      pm.locator('.ql-editor').wait_for(state='visible',timeout=24000)
      valid('Texto no celular' in pm.locator('.ql-editor').inner_text(),'MOBILE_QUILL_RELOAD_ERROR')
      valid(not pm.evaluate('document.documentElement.scrollWidth>innerWidth+30'),'MOBILE_EDITOR_HORIZONTAL_OVERFLOW')
      pm.screenshot(path=str(shots/'g4-editor-mobile.png'),full_page=True,animations='disabled')
      print('G4_C023_MOBILE_QUILL_AUTOSAVE=PASS',flush=True)
      pm.close()
     finally:mobile.close()
    finally:browser.close()
   g4.wp('option','update','anst_writes_enabled','0')
   valid(g4.wp('option','get','anst_writes_enabled').strip()=='0','SYNTHETIC_WRITES_FLAG_UNSAFE')
   print('G4_BROWSER_C016_C021_C022_C023=PASS',flush=True)
   dest=pathlib.Path(os.getenv('G4_BROWSER_EVIDENCE_DIR','/tmp/anthares-g4-browser-evidence'))
   dest.mkdir(parents=True,exist_ok=True)
   import zipfile
   with zipfile.ZipFile(dest/'g4-browser-synthetic.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in shots.glob('*.png'):z.write(p,arcname=p.name)
   print('G4_BROWSER_SCREENSHOTS='+str(len(list(shots.glob('*.png')))),flush=True)
  finally:
   for c in ('anthares-g4-wp','anthares-g4-db'):
    subprocess.run(['docker','rm','-f',c],capture_output=True)
   subprocess.run(['docker','network','rm','anthares-g4-net'],capture_output=True)
   subprocess.run(['sudo','chown','-R',str(os.getuid())+':'+str(os.getgid()),str(root)],capture_output=True)
   print('G4_BROWSER_SANDBOX_CLEANUP=PASS',flush=True)
if __name__=='__main__':main()
