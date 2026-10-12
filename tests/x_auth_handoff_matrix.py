import json, os, sys, time

CASE=int(os.environ['CASE'])

# Synthetic-only auth-state transport tests. Never contains real X credentials.

def valid_state():
    return {
        'cookies':[
            {'name':'auth_token','value':'dummy','domain':'.x.com','path':'/','expires':time.time()+3600,'httpOnly':True,'secure':True,'sameSite':'Lax'},
            {'name':'ct0','value':'dummycsrf','domain':'.x.com','path':'/','expires':time.time()+3600,'httpOnly':False,'secure':True,'sameSite':'Lax'},
        ],
        'origins':[{'origin':'https://x.com','localStorage':[]}]
    }

def parse(raw):
    data=json.loads(raw)
    if not isinstance(data,dict) or not isinstance(data.get('cookies'),list):
        raise RuntimeError('invalid X storage state')
    return data

def lint(data):
    issues=[]
    cookies=data.get('cookies',[])
    if not cookies: issues.append('no_cookies')
    names={c.get('name') for c in cookies if isinstance(c,dict)}
    if 'auth_token' not in names: issues.append('missing_auth_token')
    if 'ct0' not in names: issues.append('missing_ct0')
    for c in cookies:
        if not isinstance(c,dict): issues.append('cookie_not_object'); continue
        if not c.get('name'): issues.append('missing_name')
        if c.get('domain') not in ('.x.com','x.com','.twitter.com','twitter.com'): issues.append('wrong_domain')
        if c.get('secure') is not True: issues.append('not_secure')
        exp=c.get('expires')
        if isinstance(exp,(int,float)) and exp>0 and exp<time.time(): issues.append('expired')
        ss=c.get('sameSite')
        if ss not in (None,'Lax','Strict','None'): issues.append('bad_samesite')
    return sorted(set(issues))

s=valid_state(); expectation='pass'; expected_issue=None

if CASE==1: raw=json.dumps(s)
elif CASE==2: raw=json.dumps(s,separators=(',',':'))
elif CASE==3: raw='  '+json.dumps(s)+'  '
elif CASE==4: raw=json.dumps({'cookies':s['cookies']})
elif CASE==5: raw=json.dumps({'cookies':s['cookies'],'origins':[]})
elif CASE==6: s['cookies'][0]['domain']='x.com'; raw=json.dumps(s)
elif CASE==7: s['cookies'][1]['domain']='x.com'; raw=json.dumps(s)
elif CASE==8: s['cookies'][0]['sameSite']='None'; raw=json.dumps(s)
elif CASE==9: s['cookies'][1]['sameSite']='Strict'; raw=json.dumps(s)
elif CASE==10: s['cookies'][0].pop('expires'); raw=json.dumps(s)
elif CASE==11: raw=''; expectation='reject_parse'
elif CASE==12: raw='null'; expectation='reject_parse'
elif CASE==13: raw='[]'; expectation='reject_parse'
elif CASE==14: raw='{}'; expectation='reject_parse'
elif CASE==15: raw='{"cookies":null}'; expectation='reject_parse'
elif CASE==16: raw='{"cookies":{}}'; expectation='reject_parse'
elif CASE==17: raw='{bad json'; expectation='reject_parse'
elif CASE==18: raw=json.dumps({'cookies':[]}); expected_issue='no_cookies'
elif CASE==19: s['cookies']=s['cookies'][1:]; raw=json.dumps(s); expected_issue='missing_auth_token'
elif CASE==20: s['cookies']=s['cookies'][:1]; raw=json.dumps(s); expected_issue='missing_ct0'
elif CASE==21: s['cookies'][0]['domain']='example.com'; raw=json.dumps(s); expected_issue='wrong_domain'
elif CASE==22: s['cookies'][0]['secure']=False; raw=json.dumps(s); expected_issue='not_secure'
elif CASE==23: s['cookies'][0]['expires']=time.time()-1; raw=json.dumps(s); expected_issue='expired'
elif CASE==24: s['cookies'][0]['sameSite']='Bogus'; raw=json.dumps(s); expected_issue='bad_samesite'
elif CASE==25: s['cookies'][0].pop('name'); raw=json.dumps(s); expected_issue='missing_name'
elif CASE==26: s['cookies'].append('oops'); raw=json.dumps(s); expected_issue='cookie_not_object'
elif CASE==27: s['origins']=[{'origin':'https://x.com','localStorage':[{'name':'k','value':'v'}]}]; raw=json.dumps(s)
elif CASE==28: s['origins']=[{'origin':'https://twitter.com','localStorage':[]}]; raw=json.dumps(s)
elif CASE==29: s['cookies'][0]['path']=''; raw=json.dumps(s)
elif CASE==30: s['cookies'][0]['httpOnly']=False; raw=json.dumps(s)
elif CASE==31: s['cookies'][0]['expires']=-1; raw=json.dumps(s)
elif CASE==32: s['cookies'][0]['value']=''; raw=json.dumps(s)
elif CASE==33: s['cookies'][0]['value']='x'*4096; raw=json.dumps(s)
elif CASE==34: raw=json.dumps(s).replace('"cookies"','"cookies"',1)+'\n'
elif CASE==35: raw='\ufeff'+json.dumps(s); expectation='reject_parse'
elif CASE==36: s['cookies'][0]['domain']='.twitter.com'; raw=json.dumps(s)
elif CASE==37: s['cookies'][1]['domain']='twitter.com'; raw=json.dumps(s)
elif CASE==38: s['cookies'][0]['sameSite']=None; raw=json.dumps(s)
elif CASE==39: s['cookies'][0]['expires']=0; raw=json.dumps(s)
elif CASE==40: s['cookies'].append(dict(s['cookies'][0])); raw=json.dumps(s)
else: raise SystemExit('bad case')

try:
    data=parse(raw)
    parsed=True
except Exception as e:
    parsed=False
    err=type(e).__name__+': '+str(e)

if expectation=='reject_parse':
    ok=not parsed
    print(json.dumps({'case':CASE,'ok':ok,'expected':'reject_parse','error':None if parsed else err}))
    raise SystemExit(0 if ok else 1)

if not parsed:
    print(json.dumps({'case':CASE,'ok':False,'unexpected_parse_error':err}))
    raise SystemExit(1)

issues=lint(data)
if expected_issue:
    ok=expected_issue in issues
else:
    ok=True

print(json.dumps({'case':CASE,'ok':ok,'issues':issues,'expected_issue':expected_issue}))
raise SystemExit(0 if ok else 1)
