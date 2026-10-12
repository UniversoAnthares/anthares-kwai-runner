#!/usr/bin/env python3
"""Compatibility adapter for the proven Kwai semantic login route.

The old state machine accumulated brittle Home/Profile heuristics. Run
38304923738 proved the stable Android 35 path is install -> Home -> Me ->
native login chooser. Keep the old public contract for callers while routing
all new work through that proven implementation.
"""
import os
import subprocess
import sys

MODE=os.environ.get('KWAI_LOGIN_MODE','plain')
SETTLE=os.environ.get('KWAI_LOGIN_SETTLE','3')
REPORT='kwai-home-login-state.txt'

ROUTE_MAP={
    'plain':'me_direct',
    'relaunch-before-login':'me_retry',
    'pregrant-notification':'me_direct',
    'allow-permissions':'me_direct',
    'allow-then-retry':'me_retry',
    'deny-then-retry':'me_retry',
    'network-wait':'me_direct',
    'profile-fallback':'profile_content',
    'dismiss-guide':'me_direct',
    'relaunch-after-login':'me_retry',
}
NETWORK_MAP={
    'network-wait':'network_wait',
}

def emit(line):
    print(line,flush=True)
    with open(REPORT,'a',encoding='utf-8') as f:
        f.write(line+'\n')

open(REPORT,'w').close()

# Preserve the old contract: this adapter is still responsible for making sure
# the verified split APK set is installed and the app has been launched.
install=subprocess.run(['bash','kwai_vault_install.sh'],stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,text=True,timeout=300)
print(install.stdout,end='')
if install.returncode!=0:
    emit('FAIL_INSTALL_OR_INITIAL_LAUNCH='+str(install.returncode))
    raise SystemExit(install.returncode)

env=os.environ.copy()
env['KWAI_ROUTE']=ROUTE_MAP.get(MODE,'me_direct')
env['KWAI_NETWORK']=NETWORK_MAP.get(MODE,'baseline')
env['KWAI_SETTLE']=SETTLE
emit('SEMANTIC_ADAPTER_ROUTE='+env['KWAI_ROUTE'])
emit('SEMANTIC_ADAPTER_NETWORK='+env['KWAI_NETWORK'])

probe=subprocess.run(['python3','tools/kwai_semantic_login_route_probe.py'],
                     env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     text=True,timeout=240)
print(probe.stdout,end='')
if probe.returncode==0:
    emit('KWAI_HOME_LOGIN_SURFACE=PASS')
    raise SystemExit(0)

emit('KWAI_HOME_LOGIN_SURFACE=FAIL')
emit('SEMANTIC_ADAPTER_RC='+str(probe.returncode))
raise SystemExit(probe.returncode)
