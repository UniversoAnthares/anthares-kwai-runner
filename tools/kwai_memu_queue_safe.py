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
    def verify_after_post(self, before):
        # Never accept navigation, toast or elapsed time as post confirmation.
        # Account and profile evidence must both be positive. An intermittent
        # UI read/login timeout is retryable without another publication click.
        deadline = time.monotonic() + self.cfg.verify_timeout
        last_error = ''
        while time.monotonic() < deadline:
            try:
                self.verify_identity()
                after = self.profile_fingerprints('99-queue-profile-proof', cold=False)
                if ku.profile_grid_changed(before, after):
                    self.after_fingerprints = after
                    return True, 'memu-exact-identity-new-profile-card'
                last_error = 'profile-grid-unchanged'
            except ku.HumanVerification:
                raise
            except (ku.KwaiUpError, OSError) as exc:
                last_error = ku.safe_token(str(exc), 'read-only-profile-check-failed')
                print('KWAI_VERIFY_RETRY_SAFE=' + last_error, flush=True)
            time.sleep(5)
        return False, 'memu-profile-confirmation-missing:' + last_error


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
        save_proof(path, {'state':'verified','publication_attempted':True,'job_id':cfg.job_id,
            'verification_evidence':'memu-exact-identity-new-profile-card',
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
