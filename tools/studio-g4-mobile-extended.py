#!/usr/bin/env python3
"""G4 C008 / C023 browser extensions: scroll restoration, mobile modal and card/column drag; synthetic-only."""
import importlib.util,os,pathlib,re,shutil,subprocess,tempfile,time,zipfile
from playwright.sync_api import sync_playwright
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('studio_g4_docker',HERE/'studio-g4-docker-qa.py')
g4=importlib.util.module_from_spec(spec);spec.loader.exec_module(g4)
spec2=importlib.util.spec_from_file_location('studio_g4_browser',HERE/'studio-g4-browser-final.py')
br=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(br)
def check(v,code):
 if not v:raise RuntimeError(code)
def save_codes(container):
 for current,folders,files in os.walk(container):
  os.chmod(current,0o755)
  for folder in folders:os.chmod(pathlib.Path(current)/folder,0o755)
  for filename in files:
   f=pathlib.Path(current)/filename
   if f.is_file() and not f.is_symlink():os.chmod(f,0o644)
def project_context(browser,newid):
 context=g4.login_context(browser,390,844)
 page=context.new_page()
 page.goto(f'{g4.BASE_URL}/?page_id={newid}',wait_until='domcontentloaded')
 page.wait_for_function("window.AntharesEstudio?.rest",timeout=16000)
 return context,page
def show_mural(page,newid,project):
 page.goto(f'{g4.BASE_URL}/?page_id={newid}#studio/projeto/{project}/planejamento',
           wait_until='domcontentloaded',timeout=25000)
 page.locator('.aest-mural').wait_for(state='visible',timeout=16000)
 page.locator('.aest-mural-card').first.wait_for(state='visible',timeout=16000)
def main():
 check(os.getenv('GITHUB_REF')=='refs/heads/coord/studio-g4-g5-20261116','WRONG_BRANCH')
 with tempfile.TemporaryDirectory(prefix='studio-g4-mobile-extended-') as n:
  root=pathlib.Path(n)
  try:
   info=g4.retrieve_code(root)
   g4.patch_integrated(root/'dev/anthares-studio',root/'live/anthares-studio')
   plugin,newid=g4.setup_docker(root,info)
   target=plugin/'anthares-studio'
   subprocess.run(['sudo','chown','-R',str(os.getuid())+':'+str(os.getgid()),str(plugin)],check=True)
   shutil.rmtree(target)
   shutil.copytree(root/'dev/anthares-studio',target)
   save_codes(target)
   g4.docker('restart','anthares-g4-wp')
   time.sleep(5)
   g4.wp('option','update','anst_acf_runtime_enabled','1')
   g4.wp('option','update','anst_writes_enabled','1')
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/google-chrome',
      args=['--no-sandbox','--disable-gpu','--disable-background-networking'])
    try:
     ctx,page=project_context(browser,newid)
     try:
      out=br.require_api(page,'POST','projects',{'mode':'sem-ideia','title':'G4 Mural Mobile Sintetico'},200,'MURAL_PROJECT')
      project=int(out['id'])
      out=br.require_api(page,'POST','cards',{'project':project,'column':'soltas','text':'Cartão G4 arrastável sintético'},200,'MURAL_CARD')
      cid=int(out['id'])
      show_mural(page,newid,project)
      page.locator(f'[data-card-id="{cid}"] .aest-card-content').click()
      dialog=page.locator('.aest-card-notes-dialog[role=dialog]')
      dialog.wait_for(state='visible',timeout=13000)
      check(dialog.get_attribute('aria-modal')=='true','MOBILE_DIALOG_ARIA')
      dialog.locator('#aest-card-notes-text').fill('Observações salvas no modal mobile.')
      dialog.locator('button[type=submit]').click()
      page.wait_for_function("""id=>!document.querySelector('.aest-card-notes-overlay') ||
         document.querySelector('.aest-card-notes-overlay #aest-card-notes-status')?.textContent?.includes('salv')""",
         arg=cid,timeout=14000)
      d=br.require_api(page,'GET','bootstrap?project='+str(project),None,200,'MOBILE_MODAL_PERSIST')
      card=next(c for c in d['cards'] if c['id']==cid)
      check('Observações salvas no modal mobile' in card['notes'],'MOBILE_MODAL_LOST_NOTES')
      print('G4_C023_MOBILE_CARD_MODAL_PERSISTENCE=PASS',flush=True)
      page.locator('.aest-card-notes-overlay').count() and page.locator('[data-action="card-notes-close"]').click()
      show_mural(page,newid,project)
      source=page.locator(f'.aest-mural-card[data-card-id="{cid}"]')
      destination=page.locator('.aest-mural-drop[data-column="trama"]')
      source.drag_to(destination,force=True,timeout=14000)
      page.wait_for_timeout(700)
      out=br.require_api(page,'GET','bootstrap?project='+str(project),None,200,'MOBILE_DRAG_PERSIST')
      card=next(c for c in out['cards'] if c['id']==cid)
      check(card['column']=='trama','MOBILE_DRAG_NOT_SAVED')
      print('G4_C023_VIEWPORT_390_HTML5_CARD_DRAG=PASS',flush=True)
      # C008: scroll restoration using a dense project route and browser history.
      page.goto(f'{g4.BASE_URL}/?page_id={newid}#studio/projeto/{project}/planejamento',
                wait_until='domcontentloaded')
      page.locator('.aest-mural').wait_for(state='visible')
      maxscroll=page.evaluate("document.documentElement.scrollHeight-window.innerHeight")
      if maxscroll<100:
       print('G4_C008_SCROLL_CONTENT_TOO_SHORT=1',flush=True)
      else:
       y=min(180,maxscroll-20)
       page.evaluate("(target)=>window.scrollTo(0,target)",y)
       page.wait_for_timeout(150)
       original=page.evaluate('Math.round(window.scrollY)')
       page.locator('.aest-group-tabs button[data-tab="pesquisa"]').click()
       page.wait_for_function("location.hash.includes('/pesquisa')",timeout=9000)
       page.go_back(wait_until='domcontentloaded')
       page.wait_for_function("location.hash.includes('/planejamento')",timeout=9000)
       page.wait_for_timeout(650)
       restored=page.evaluate('Math.round(window.scrollY)')
       check(abs(restored-original)<45,'G4_C008_SCROLL_HISTORY_DELTA_'+str(abs(restored-original)))
       print('G4_C008_SCROLL_HISTORY_RESTORATION=PASS',flush=True)
      page.screenshot(path=str(root/'g4-mobile-modal-drag-scroll.png'),animations='disabled',full_page=True)
      print('G4_EXTENDED_BROWSER_PASS=1',flush=True)
     finally:ctx.close()
    finally:browser.close()
   g4.wp('option','update','anst_writes_enabled','0')
   destination=pathlib.Path(os.getenv('G4_MOBILE_EVIDENCE_DIR','/tmp/studio-g4-mobile-evidence'))
   destination.mkdir(parents=True,exist_ok=True)
   shutil.copy2(root/'g4-mobile-modal-drag-scroll.png',destination/'g4-mobile-modal-drag-scroll.png')
   print('G4_EXTENDED_SYNTHETIC_EVIDENCE=1',flush=True)
  finally:
   for name in ('anthares-g4-wp','anthares-g4-db'):
    subprocess.run(['docker','rm','-f',name],capture_output=True)
   subprocess.run(['docker','network','rm','anthares-g4-net'],capture_output=True)
   subprocess.run(['sudo','chown','-R',str(os.getuid())+':'+str(os.getgid()),str(root)],capture_output=True)
   print('G4_EXTENDED_DOCKER_CLEANUP=PASS',flush=True)
if __name__=='__main__':main()
