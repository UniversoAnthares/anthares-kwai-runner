import subprocess
exe = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
args = [exe,'--headless=new','--mute-audio','--disable-audio-output','--disable-notifications','--remote-debugging-address=127.0.0.1','--remote-debugging-port=9225',r'--user-data-dir=D:\AntharsWork\browser-profiles\AntharesMeta','--profile-directory=Default','--no-first-run','--no-default-browser-check','https://www.threads.com/']
subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW|subprocess.DETACHED_PROCESS, close_fds=True)
