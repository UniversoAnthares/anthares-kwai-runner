#!/usr/bin/env python3
"""G4 authenticated, synthetic-user visual comparison against real plugins in isolated WP DB."""
import hashlib,json,os,pathlib,re,secrets,shlex,socket,subprocess,tempfile,threading,urllib.request
from playwright.sync_api import sync_playwright
HOST_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA7FQ2RBq0cii+VVCqcB90JxkJRPdurdrX1RGThhKtT2'
def bridge(token):
    req=urllib.request.Request('https://gitlab.com/api/v4/projects/87361776/variables?per_page=100',
          headers={'PRIVATE-TOKEN':token,'User-Agent':'anthares-g4-visual-isolated'})
    with urllib.request.urlopen(req,timeout=20) as r:rows=json.load(r)
    v={r.get('key'):r.get('value') for r in rows}
    if not all(v.get(k) for k in ('ANTHARES_QA_SSH_KEY','ANTHARES_QA_SSH_HOST','ANTHARES_QA_SSH_USER')):
        raise RuntimeError('SSH_BRIDGE_UNAVAILABLE')
    host=v['ANTHARES_QA_SSH_HOST'];user=v['ANTHARES_QA_SSH_USER']
    port=str(v.get('ANTHARES_QA_SSH_PORT') or '65002')
    if user!='u566597497' or port!='65002':raise RuntimeError('SSH_TARGET_UNEXPECTED')
    if {a[4][0] for a in socket.getaddrinfo(host,None,family=socket.AF_INET)}!={'195.35.39.110'}:
        raise RuntimeError('SSH_ADDRESS_UNEXPECTED')
    return v['ANTHARES_QA_SSH_KEY'],host,port,user
GENERATE=r"""
import pathlib,shlex,sys
source=pathlib.Path.home()/'domains/anthares.us/anthares-private-storage/studio-g6-review-20261116/anthares-studio/tests/integration/g5-runtime-isolated.sh'
if not source.is_file():raise RuntimeError('G5_RESTORE_RECIPE_NOT_FOUND')
script=source.read_text(encoding='utf8')
marker='echo "G5_ACF_DRY_RUN"'
if script.count(marker)!=1:raise RuntimeError('G5_RESTORE_RECIPE_CHANGED')
script=script.split(marker,1)[0]
script=script.replace('studio-g5-runtime-db-XXXXXXXX','studio-g4-visual-XXXXXXXX')
script=script.replace('SOCKET_DIR="$HOME/.anst-g5-runtime"', 'SOCKET_DIR="$HOME/.anst-g4-visual-JOB"')
script=script.replace('REPO="$(cd "$(dirname "$0")/../../.." && pwd)"','REPO="$PRIVATE/studio-g6-review-20261116"')
script=script.replace('ln -s "$REPO/anthares-studio" "$T/wp/wp-content/plugins/anthares-studio"',
                      'ln -s "$ROOT/wp-content/plugins/anthares-studio" "$T/wp/wp-content/plugins/anthares-studio"')
anchor="define('WP_DEBUG',false);"
if script.count(anchor)!=1:raise RuntimeError('WP_CONFIG_ANCHOR_CHANGED')
script=script.replace(anchor,anchor+"\ndefine('WP_HOME','http://127.0.0.1:PORT');\ndefine('WP_SITEURL','http://127.0.0.1:PORT');")
anchor2='cleanup(){\n rc=$?'
if script.count(anchor2)!=1:raise RuntimeError('CLEANUP_ANCHOR_CHANGED')
script=script.replace(anchor2,'cleanup(){\n rc=$?\n if test -n "$WEB_PID";then kill "$WEB_PID" 2>/dev/null || :;fi')
script=script.replace('PID=""','PID=""\nWEB_PID=""')
add=r'''
$PHP $WP --path="$T/wp" --skip-themes --no-color user create USERNAME EMAIL --role=administrator --user_pass=PASSWORD --porcelain >/dev/null
cat > "$T/wp/router.php" <<'ROUTER'
<?php
$path=urldecode(parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH));
if(is_file(__DIR__.'/'.$path))return false;
require __DIR__.'/index.php';
ROUTER
$PHP -S 127.0.0.1:PORT -t "$T/wp" "$T/wp/router.php" > "$T/web.log" 2>&1 &
WEB_PID=$!
for i in $(seq 1 12);do
 if curl --noproxy '*' -fsS --max-time 2 'http://127.0.0.1:PORT/wp-login.php' >/dev/null 2>&1;then break;fi
 sleep 1
done
if ! curl --noproxy '*' -fsS --max-time 3 'http://127.0.0.1:PORT/wp-login.php' >/dev/null 2>&1;then
 echo 'G4_HTTP_START_FAILED=1'
 echo "G4_HTTP_LOG_BYTES=$(wc -c < "$T/web.log")"
 curl --noproxy '*' -s -o /dev/null --max-time 3 'http://127.0.0.1:PORT/wp-login.php' || echo "G4_CURL_ERROR_CODE=$?"
 curl --noproxy '*' -sS -o /dev/null --max-time 3 -w 'G4_HTTP_CODE=%{http_code}\n' 'http://127.0.0.1:PORT/wp-login.php' || :
 if kill -0 "$WEB_PID" 2>/dev/null;then echo 'G4_WEB_PROCESS_ALIVE=1';else echo 'G4_WEB_PROCESS_ALIVE=0';fi
 if grep -qi 'Failed to listen' "$T/web.log";then echo 'G4_FAILED_TO_LISTEN=1';fi
 if grep -qi 'Fatal error' "$T/web.log";then echo 'G4_PHP_FATAL=1';fi
 if grep -qi 'Permission denied' "$T/web.log";then echo 'G4_LISTEN_PERMISSION_DENIED=1';fi
 exit 27
fi
echo 'G4_SERVER_READY=1'
echo "G4_STOP_FILE=$T/STOP"
for i in $(seq 1 240);do
 test -f "$T/STOP" && break
 sleep 1
done
echo 'G4_SERVER_FINISHED=1'
'''
job,port,username,email,password=JSON_ARGS
for x,y in [('JOB',job),('PORT',port),('USERNAME',shlex.quote(username)),('EMAIL',shlex.quote(email)),('PASSWORD',shlex.quote(password))]:
 script=script.replace(x,y)
 add=add.replace(x,y)
print(script+add)
"""
def main():
    if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':
        raise RuntimeError('WRONG_BRANCH')
    if os.getenv('GITHUB_EVENT_NAME')!='push':raise RuntimeError('WRONG_TRIGGER')
    job=os.environ['GITHUB_RUN_ID']
    port=27000+int(job)%2000
    password=secrets.token_urlsafe(24)
    username='g4qa'+str(job)
    key,host,sshport,user=bridge(os.environ['GITLAB_TOKEN'])
    with tempfile.TemporaryDirectory(prefix='studio-g4-visual-') as tmp:
        folder=pathlib.Path(tmp)
        k=folder/'key';k.write_text(key);k.chmod(0o600)
        known=folder/'hosts';known.write_text('anthares-studio-g4visual '+HOST_KEY+'\n')
        ssh=['ssh','-T','-i',str(k),'-p',sshport,'-o','BatchMode=yes','-o','IdentitiesOnly=yes',
             '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(known),
             '-o','HostKeyAlias=anthares-studio-g4visual','-o','ConnectTimeout=10',user+'@'+host]
        gen=GENERATE.replace('JSON_ARGS',repr([job,str(port),username,username+'@example.invalid',password]))
        generator=subprocess.run(ssh+['/opt/alt/python311/bin/python3.11 -'],
                                input=gen,text=True,capture_output=True,timeout=35)
        if generator.returncode:
            print('G4_GENERATOR_FAILED=1',flush=True)
            raise RuntimeError('G4_GENERATOR_FAILED')
        setup=generator.stdout
        if not setup.startswith('#!/usr/bin/env bash'):raise RuntimeError('G4_SETUP_INVALID')
        tunnel=['ssh','-T','-L',f'127.0.0.1:{port}:127.0.0.1:{port}']+ssh[1:]+['bash -s']
        proc=subprocess.Popen(tunnel,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              text=True,bufsize=1)
        output=[];errors=[];ready=threading.Event()
        def reader(stream,lines,flag=None):
            for line in stream:
                lines.append(line.rstrip())
                if flag and line.startswith('G4_SERVER_READY='):flag.set()
        threading.Thread(target=reader,args=(proc.stdout,output,ready),daemon=True).start()
        threading.Thread(target=reader,args=(proc.stderr,errors),daemon=True).start()
        marker=None
        try:
            proc.stdin.write(setup);proc.stdin.close()
            if not ready.wait(80):
                stages=[v for v in output if v.startswith(('G4_','G5_','G6_'))]
                print('G4_SETUP_STAGES='+','.join(stages[-12:])[:300],flush=True)
                last=(errors[-1] if errors else 'NO_STDERR')
                last=re.sub(r'(?i)password[^\\s]*|token[^\\s]*|secret[^\\s]*','[REDACTED]',last)
                last=re.sub(r'[^A-Za-z0-9 _.:=()\\[\\]/-]','_',last)[:180]
                print('G4_SETUP_FAILURE_LAST='+last,flush=True)
                print('G4_SSH_SUBPROCESS_EXIT='+str(proc.poll()),flush=True)
                raise RuntimeError('G4_ISOLATED_HTTP_NOT_READY')
            marker=next((v.split('=',1)[1] for v in output if v.startswith('G4_STOP_FILE=')),None)
            baseurl=f'http://127.0.0.1:{port}'
            with sync_playwright() as play:
                browser=play.chromium.launch(executable_path='/usr/bin/google-chrome',
                    headless=True,args=['--no-sandbox','--disable-gpu','--no-first-run'])
                try:
                    cases=[]
                    for width,height,label in [(1440,900,'desktop'),(390,844,'mobile')]:
                        context=browser.new_context(viewport={'width':width,'height':height})
                        page=context.new_page()
                        page.goto(baseurl+'/wp-login.php',wait_until='domcontentloaded',timeout=35000)
                        page.locator('#user_login').fill(username)
                        page.locator('#user_pass').fill(password)
                        page.locator('#wp-submit').click(timeout=15000)
                        page.wait_for_url(re.compile(r'wp-admin|profile\.php'),timeout=25000)
                        for mode in ['light','dark']:
                            widths=[]
                            for slug,keyname in [('estudio','anthares_estudio_theme_v1'),
                                                 ('studio','anthares_studio_theme_v1')]:
                                page.goto(baseurl+'/'+slug+'/',wait_until='domcontentloaded',timeout=35000)
                                page.evaluate('(x)=>localStorage.setItem(x.key,x.mode)',{'key':keyname,'mode':mode})
                                page.reload(wait_until='domcontentloaded',timeout=35000)
                                page.wait_for_selector('#anthares-estudio-root',timeout=25000)
                                page.wait_for_function("document.querySelector('#anthares-estudio-root')?.textContent?.length>25",timeout=22000)
                                status=page.evaluate("""() => {
                                    const el=document.querySelector('#anthares-estudio-root');
                                    const side=document.querySelector('#sidebar-primary');
                                    const title=document.querySelector('#page-titlebar');
                                    return {width:Math.round(el.getBoundingClientRect().width),
                                      side:side?getComputedStyle(side).display:'absent',
                                      title:title?getComputedStyle(title).display:'absent',
                                      appText:el.innerText.length,cls:document.body.className,
                                      overflow:document.documentElement.scrollWidth>innerWidth+30};
                                }""")
                                if status['side'] not in ('none','absent'):raise RuntimeError('G4_WIDGET_SIDEBAR_VISIBLE_'+slug)
                                if status['title'] not in ('none','absent'):raise RuntimeError('G4_WP_PAGE_TITLE_VISIBLE_'+slug)
                                if slug=='studio' and 'anst-studio-page' not in status['cls']:
                                    raise RuntimeError('G4_NEW_BODY_CSS_CLASS_MISSING')
                                if status['width']<width*.65:raise RuntimeError('G4_CONTENT_TOO_NARROW_'+slug)
                                picture=folder/('g4-'+label+'-'+mode+'-'+slug+'.png')
                                page.screenshot(path=str(picture),full_page=True,animations='disabled')
                                hashv=hashlib.sha256(picture.read_bytes()).hexdigest()
                                print('G4_SCREENSHOT='+label+'_'+mode+'_'+slug+' sha256='+hashv+' width='+str(status['width']),flush=True)
                                widths.append(status['width'])
                            ratio=widths[1]/max(1,widths[0])
                            if ratio<.89 or ratio>1.12:raise RuntimeError('G4_WIDTH_PARITY_'+label+'_'+mode)
                            cases.append((label,mode,round(ratio,3)))
                        context.close()
                    for case in cases:print('G4_CASE_PASS='+str(case),flush=True)
                    print('G4_VISUAL_BASELINE_PASS=1',flush=True)
                finally:browser.close()
        finally:
            if marker and re.fullmatch(r'.*/studio-g4-visual-[A-Za-z0-9]{8}/STOP',marker):
                subprocess.run(ssh+['touch '+shlex.quote(marker)],capture_output=True,text=True,timeout=15)
            try:proc.wait(timeout=20)
            except subprocess.TimeoutExpired:proc.terminate()
            if proc.poll() is None:proc.kill()
            print('G4_ISOLATED_CLEANUP_REQUESTED=1',flush=True)
if __name__=='__main__':
    main()
