"""Queue adapter for the existing full-Kwai publisher with durable post proof.

PREPARE is reversible. COMMIT is called only after the central STARTED fence.
Unlike the legacy local-test adapter, success requires identity and a new profile
card, and writes the same proof contract consumed by the central acknowledgement.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('memu_existing_safe', ROOT/'kwai-up'/'kwai_up_safe.py')
safe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(safe)
ku = safe.ku


def proof_path(job):
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', job)[-100:]
    return ROOT/'.state'/'kwai-native-cortes'/(name+'.json')


def save_proof(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


class QueuePublisher(safe.SafePublisher):
    @staticmethod
    def _caption_key(value):
        return ''.join(c for c in ku.unicodedata.normalize('NFKD',value).casefold() if c.isalnum())

    def prepare(self):
        # Never force-stop a possibly still uploading Kwai process, even before
        # a new job; read-only navigation and the fenced queue remain mandatory.
        if self.probe()!=0:return 20
        self.verify_identity(force_stop=False)
        return ku.Publisher.prepare(self)

    def profile_fingerprints(self,stage,cold):
        # Preserve running Kwai. Fingerprints are only diagnostic screenshots.
        fingerprints=super().profile_fingerprints(stage,False)
        if stage=='20-before':
            self.profile_before_url=self.capture_first_profile_post(require_caption=False)
            print('KWAI_BASELINE_PUBLIC_POST_CAPTURED=1',flush=True)
        return fingerprints

    def capture_first_profile_post(self,require_caption):
        """Read exact video title and public share URL from the first profile card."""
        nodes=self.dump('98-profile-before-select')
        if not safe.account_pattern(self.expected_account()).search(ku.text_blob(nodes).casefold()):
            raise ku.KwaiUpError('post-link-account-mismatch')
        thumbs=[n for n in nodes if n.get('resource-id')==ku.PROFILE_THUMB_ID and ku.center(n.get('bounds',''))]
        if not thumbs:raise ku.KwaiUpError('post-link-profile-card-missing')
        thumbs.sort(key=lambda n:ku.bounds_tuple(n.get('bounds','')) or (9999,9999,9999,9999))
        self.tap_node(thumbs[0],2)
        share=None
        wanted=self._caption_key(self.cfg.caption)[:55] if require_caption else ''
        for attempt in range(8):
            detail=self.dump('98-post-detail',screenshot=False)
            blob=ku.text_blob(detail)
            share=next((n for n in detail if n.get('text','').casefold()=='compartilhar' and ku.center(n.get('bounds',''))),None)
            if share and (not require_caption or (len(wanted)>=25 and wanted in self._caption_key(blob))):
                break
            if attempt==7:
                raise ku.KwaiUpError('post-link-exact-caption-not-visible' if require_caption else 'post-link-share-not-visible')
            time.sleep(2)
        self.tap_node(share,2)
        menu=self.dump('98-post-share-menu',screenshot=False)
        copy=next((n for n in menu if 'copiar link' in n.get('text','').casefold() and ku.center(n.get('bounds',''))),None)
        if not copy:raise ku.KwaiUpError('post-link-copy-command-missing')
        self.tap_node(copy,1)
        self.adb.run('shell','am','start','-a','android.intent.action.VIEW','-d','about:blank','-p','com.android.chrome',timeout=35)
        time.sleep(2)
        bar=None
        for attempt in range(6):
            browser=self.dump('98-browser-clipboard',screenshot=False)
            bar=next((n for n in browser if n.get('resource-id')=='com.android.chrome:id/url_bar' and ku.center(n.get('bounds',''))),None)
            if bar:break
            time.sleep(1)
        if not bar:raise ku.KwaiUpError('post-link-chrome-address-bar-missing')
        self.tap_node(bar,1)
        self.adb.run('shell','input','keyevent','279')
        time.sleep(1)
        browser=self.dump('98-browser-url-proof',screenshot=False)
        bar=next((n for n in browser if n.get('resource-id')=='com.android.chrome:id/url_bar'),None)
        match=re.search(r'https?://k[.]kwai[.]com/p/[A-Za-z0-9_-]+',(bar or {}).get('text',''))
        if not match:raise ku.KwaiUpError('post-link-public-url-missing')
        return match.group(0)

    def verify_after_post(self,before):
        """Post proof is exact caption + different public URL on verified account."""
        proof=self.load_ready()
        baseline=str(proof.get('profile_before_url') or '')
        if not re.fullmatch(r'https?://k[.]kwai[.]com/p/[A-Za-z0-9_-]+',baseline):
            raise ku.KwaiUpError('post-link-baseline-required')
        # Do not restart Kwai while the upload is still finishing.
        time.sleep(25)
        deadline=time.monotonic()+max(90,self.cfg.verify_timeout)
        last_error='not-verified'
        while time.monotonic()<deadline:
            try:
                self.verify_identity(force_stop=False)
                self.after_fingerprints=self.profile_fingerprints('99-queue-profile-proof',cold=False)
                url=self.capture_first_profile_post(require_caption=True)
                if url==baseline:
                    last_error='same-public-url-as-before'
                else:
                    self.public_url=url
                    print('KWAI_NEW_POST_PUBLIC_URL='+url,flush=True)
                    return True,'memu-exact-caption-new-public-url'
            except ku.HumanVerification:raise
            except (ku.KwaiUpError,OSError) as exc:
                last_error=ku.safe_token(str(exc),'read-only-public-url-proof-failed')
                print('KWAI_VERIFY_RETRY_SAFE='+last_error,flush=True)
            time.sleep(6)
        return False,'memu-post-not-proven:'+last_error



def main():
    mode = sys.argv[1] if len(sys.argv)>1 else ''
    if mode not in ('prepare', 'commit', 'verify'): return 64
    cfg = ku.Config.from_env(mode)
    path = proof_path(cfg.job_id)
    old = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if old.get('publication_attempted') and mode != 'verify':
        print('KWAI_UP_STATE=UNCERTAIN DEDUPE_GUARD=1', flush=True)
        return 90
    pub = QueuePublisher(cfg)
    if mode == 'prepare':
        result = pub.prepare()
        if result: return result
        baseline=getattr(pub,'profile_before_url',None)
        if not baseline:
            raise ku.KwaiUpError('post-link-baseline-capture-required')
        ready=json.loads(pub.ready_file.read_text(encoding='utf-8'))
        ready['profile_before_url']=baseline
        pub.ready_file.write_text(json.dumps(ready,ensure_ascii=False,indent=2),encoding='utf-8')
        nodes = pub.dump('22-caption-proof')
        field = ku.find_id(nodes, ku.EDITOR_ID) or next((n for n in nodes if n.get('resource-id')==ku.EDITOR_ID), {})
        if ' '.join(field.get('text','').split()) != ' '.join(cfg.caption[:150].split()):
            raise ku.KwaiUpError('caption-proof-mismatch')
        return 0
    if mode == 'commit':
        # Verify ready/media identity before recording the irreversible attempt.
        pub.load_ready()
        save_proof(path, {'state':'publication_attempted','publication_attempted':True,'job_id':cfg.job_id})
        result = pub.commit()
    else:
        result = pub.verify()
    if result == 0:
        url=str(getattr(pub,'public_url','') or '')
        if not re.fullmatch(r'https://k[.]kwai[.]com/p/[A-Za-z0-9_-]+',url):
            raise ku.KwaiUpError('public-link-required-for-verified-post')
        # This is the same durable proof consumed by queue.evidence().
        # Atomic write happens before marking the job verified.
        save_proof(cfg.artifacts/'public-link-proof.json',{
            'ok':True,'expected_account':pub.expected_account().lstrip('@').lower(),
            'public_url':url,'caption':cfg.caption,'job_id':cfg.job_id,
            'kind':'kwai_exact_account_caption_distinct_url',
            'timestamp':int(time.time())})
        save_proof(path, {'state':'verified','publication_attempted':True,'job_id':cfg.job_id,
            'verification_evidence':'memu-exact-caption-new-public-url', 'public_url':getattr(pub,'public_url',None),
            'profile_verification':{'account':pub.expected_account().lstrip('@').lower(),
                'caption':cfg.caption,'post_time':str(int(time.time())),
                'fingerprints':pub.after_fingerprints,
                'screenshot':str(cfg.artifacts/'99-queue-profile-proof.png')}})
    return result


if __name__ == '__main__':
    try: raise SystemExit(main())
    except ku.KwaiUpError as error:
        print('KWAI_UP_STATE=FAILED_SAFE REASON='+ku.safe_token(str(error)), flush=True)
        raise SystemExit(70)
