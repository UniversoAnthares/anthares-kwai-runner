import hashlib
import json
import os
import pathlib
import random
import tempfile
import time
import urllib.error
import urllib.request
import urllib.parse
from datetime import datetime, timezone

API = os.getenv("ANTHARES_VIDEO_ENDPOINT", "").rstrip("/")
SECRET = os.getenv("ANTHARES_VIDEO_SECRET", "")
RUNNER = os.getenv("RUNNER_NAME", "github-hosted")
RUN_ID = os.getenv("GITHUB_RUN_ID", "manual")
AUTO_QUEUE = os.getenv("ATD_AUTO_QUEUE", "").strip().lower() in {"1", "true", "yes", "on"}
AUTO_GATE_MAX_WAIT_SECONDS = max(
    0, int(os.getenv("ATD_KWAI_GATE_MAX_WAIT_SECONDS", "300") or 300)
)
LEDGER_PATH = pathlib.Path(
    os.getenv(
        "ATD_KWAI_PUBLISHED_LEDGER",
        r"D:\AntharesWork\kwai-publisher\kwai-published-ledger.json",
    )
)
HALT_PATH = pathlib.Path(
    os.getenv(
        "ATD_KWAI_AUTOMATION_HALT",
        r"D:\AntharesWork\kwai-publisher\KWAI_AUTOMATION_HALT.json",
    )
)
MAX_DEDUPE_SKIPS = 25
MAX_DAILY_PUBLISHES = 100
_RNG = random.SystemRandom()


def require_env():
    missing = []
    if not API:
        missing.append("ANTHARES_VIDEO_ENDPOINT")
    if not SECRET:
        missing.append("ANTHARES_VIDEO_SECRET")
    if missing:
        raise RuntimeError("Secrets ausentes: " + ", ".join(missing))


def api(path, method="GET", payload=None, timeout=60):
    require_env()
    headers = {"X-Anthares-Worker-Secret": SECRET}
    data = None
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:600]
        raise RuntimeError(f"{path}: HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{path}: falha de conexão: {exc.reason}") from exc
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path}: resposta do WordPress não é JSON.") from exc


def _empty_ledger():
    return {
        "version": 3,
        "last_published_at": 0,
        "next_publish_at": 0,
        "attempted": [],
        "published": [],
    }


def _load_ledger():
    if not LEDGER_PATH.exists():
        return _empty_ledger()
    try:
        data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"Ledger de publicações do Kwai está ilegível: {LEDGER_PATH}"
        ) from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Ledger de publicações do Kwai está inválido: {LEDGER_PATH}")
    data.setdefault("version", 3)
    data.setdefault("last_published_at", 0)
    data.setdefault("next_publish_at", 0)
    data.setdefault("attempted", [])
    data.setdefault("published", [])
    if not isinstance(data["attempted"], list) or not isinstance(data["published"], list):
        raise RuntimeError(f"Ledger de publicações do Kwai está inválido: {LEDGER_PATH}")
    return data


def _save_json_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _daily_published_count(ledger, now=None):
    now = int(now or time.time())
    today = datetime.fromtimestamp(now, tz=timezone.utc).date()
    count = 0
    for row in ledger.get("published", []):
        try:
            published_at = int(row.get("published_at") or 0)
            if published_at and datetime.fromtimestamp(published_at, tz=timezone.utc).date() == today:
                count += 1
        except (TypeError, ValueError, OverflowError):
            continue
    return count


def _daily_limit_open(ledger, now=None):
    count = _daily_published_count(ledger, now)
    if count >= MAX_DAILY_PUBLISHES:
        print(f"KWAI_DAILY_LIMIT reached={count} limit={MAX_DAILY_PUBLISHES}", flush=True)
        return False
    print(f"KWAI_DAILY_COUNT published={count} limit={MAX_DAILY_PUBLISHES}", flush=True)
    return True


def _next_publish_interval_seconds():
    # Sempre 6..11 minutos mais alguns segundos: nunca cai num minuto exato e
    # nunca ultrapassa 12 minutos.
    minutes = _RNG.randint(6, 11)
    seconds = _RNG.randint(7, 53)
    return minutes * 60 + seconds


def _item_hash(item):
    return (item.get("file_hash") or "").strip().lower()


def _row_matches_item(row, item):
    if not isinstance(row, dict):
        return False
    provider = str(item.get("provider") or "")
    if str(row.get("provider") or "") != provider:
        return False
    queue_id = int(item.get("queue_id") or 0)
    file_hash = _item_hash(item)
    if queue_id and int(row.get("queue_id") or 0) == queue_id:
        return True
    if file_hash and str(row.get("file_hash") or "").lower() == file_hash:
        return True
    return False


def _duplicate_state(ledger, item):
    queue_id = int(item.get("queue_id") or 0)
    file_hash = _item_hash(item)
    for state in ("published", "attempted"):
        for row in ledger.get(state, []):
            if not _row_matches_item(row, item):
                continue
            if queue_id and int(row.get("queue_id") or 0) == queue_id:
                return state, f"queue_id={queue_id}"
            if file_hash and str(row.get("file_hash") or "").lower() == file_hash:
                return state, f"sha256={file_hash[:16]}"
    return "", ""


def _record_attempt(item):
    ledger = _load_ledger()
    state, _ = _duplicate_state(ledger, item)
    if state:
        return
    ledger["attempted"].append(
        {
            "provider": str(item.get("provider") or ""),
            "queue_id": int(item.get("queue_id") or 0),
            "file_hash": _item_hash(item),
            "attempted_at": int(time.time()),
            "run_id": RUN_ID,
        }
    )
    ledger["attempted"] = ledger["attempted"][-5000:]
    _save_json_atomic(LEDGER_PATH, ledger)


def _clear_attempt(item):
    ledger = _load_ledger()
    original = len(ledger.get("attempted", []))
    ledger["attempted"] = [
        row for row in ledger.get("attempted", []) if not _row_matches_item(row, item)
    ]
    if len(ledger["attempted"]) != original:
        _save_json_atomic(LEDGER_PATH, ledger)


def _record_published(item):
    ledger = _load_ledger()
    now = int(time.time())
    ledger["attempted"] = [
        row for row in ledger.get("attempted", []) if not _row_matches_item(row, item)
    ]
    already_published = any(
        _row_matches_item(row, item) for row in ledger.get("published", [])
    )
    if not already_published:
        ledger["published"].append(
            {
                "provider": str(item.get("provider") or ""),
                "queue_id": int(item.get("queue_id") or 0),
                "file_hash": _item_hash(item),
                "published_at": now,
                "run_id": RUN_ID,
            }
        )
        ledger["published"] = ledger["published"][-5000:]
    interval = _next_publish_interval_seconds()
    ledger["last_published_at"] = now
    ledger["next_publish_at"] = now + interval
    ledger["version"] = 3
    _save_json_atomic(LEDGER_PATH, ledger)
    print(
        f"KWAI_NEXT_PUBLISH_IN seconds={interval} next_publish_at={ledger['next_publish_at']}",
        flush=True,
    )


def _write_halt(item, error):
    payload = {
        "halted_at": int(time.time()),
        "provider": str(item.get("provider") or ""),
        "queue_id": int(item.get("queue_id") or 0),
        "run_id": RUN_ID,
        "reason": (error or "needs_human")[:1000],
    }
    _save_json_atomic(HALT_PATH, payload)
    print(f"KWAI_AUTO_HALTED queue_id={payload['queue_id']}", flush=True)


def _auto_gate_open():
    if not AUTO_QUEUE:
        return True
    if HALT_PATH.exists():
        print(f"KWAI_AUTO_HALTED halt_file={HALT_PATH}", flush=True)
        return False

    ledger = _load_ledger()
    if not _daily_limit_open(ledger):
        return False
    last = int(ledger.get("last_published_at") or 0)
    next_publish_at = int(ledger.get("next_publish_at") or 0)

    # Migração do ledger anterior: se já houve publicação, crie uma única janela
    # aleatória antes de permitir outra.
    if last and not next_publish_at:
        interval = _next_publish_interval_seconds()
        next_publish_at = last + interval
        ledger["next_publish_at"] = next_publish_at
        ledger["version"] = 3
        _save_json_atomic(LEDGER_PATH, ledger)

    if next_publish_at:
        remaining = next_publish_at - int(time.time())
        if remaining > AUTO_GATE_MAX_WAIT_SECONDS:
            print(f"KWAI_AUTO_RATE_LIMIT remaining_seconds={remaining}", flush=True)
            return False
        if remaining > 0:
            print(f"KWAI_AUTO_JITTER_WAIT seconds={remaining}", flush=True)
            time.sleep(remaining)
            if HALT_PATH.exists():
                print(f"KWAI_AUTO_HALTED halt_file={HALT_PATH}", flush=True)
                return False

    return True


def _result_payload(item, status, remote_id="", error="", retry_after=0):
    payload = {
        "provider": item["provider"],
        "queue_id": int(item["queue_id"]),
        "lock_token": item["lock_token"],
        "status": status,
        "remote_id": remote_id or "",
        "error": (error or "")[:4000],
    }
    if retry_after:
        payload["retry_after"] = int(retry_after)
    return payload


def claim(provider, queue_id=0, manual=True):
    auto_queue = bool(AUTO_QUEUE)
    if auto_queue and not _auto_gate_open():
        return None

    payload = {
        "provider": provider,
        "worker_id": f"github-{provider}-ui:{RUN_ID}",
        "manual": False if auto_queue else bool(manual),
    }
    if queue_id and not auto_queue:
        payload["queue_id"] = int(queue_id)

    for _ in range(MAX_DEDUPE_SKIPS):
        response = api("/publisher/claim", "POST", payload)
        item = response.get("item") if isinstance(response, dict) else None
        if not item:
            return None

        ledger = _load_ledger()
        state, duplicate = _duplicate_state(ledger, item)
        if not duplicate:
            # Grave a identidade antes de qualquer interação com o Kwai. Uma falha
            # controlada antes do clique em Publicar remove esta reserva via retry.
            # Se o processo/PC morrer em ponto ambíguo, a reserva permanece e impede
            # que o mesmo queue_id/SHA-256 seja publicado novamente às cegas.
            _record_attempt(item)
            return item

        if state == "attempted":
            message = (
                "Publicação anterior ficou em estado ambíguo; nova tentativa bloqueada "
                f"para impedir duplicação ({duplicate})."
            )
            api(
                "/publisher/result",
                "POST",
                _result_payload(item, "needs_human", error=message),
            )
            if auto_queue:
                _write_halt(item, message)
            print(
                f"KWAI_DUPLICATE_AMBIGUOUS_BLOCKED queue_id={item.get('queue_id')} reason={duplicate}",
                flush=True,
            )
            return None

        dedupe_id = _item_hash(item)[:16] or str(item.get("queue_id") or "")
        api(
            "/publisher/result",
            "POST",
            _result_payload(
                item,
                "published",
                remote_id=f"dedupe:{dedupe_id}",
                error=f"Ignorado pelo guard local: conteúdo já publicado ({duplicate}).",
            ),
        )
        print(
            f"KWAI_AUTO_DUPLICATE_SKIPPED queue_id={item.get('queue_id')} reason={duplicate}",
            flush=True,
        )

    raise RuntimeError(
        "Guard do Kwai encontrou 25 itens duplicados consecutivos; automação interrompida."
    )


def finish(item, status, remote_id="", error="", retry_after=0):
    response = api(
        "/publisher/result",
        "POST",
        _result_payload(item, status, remote_id, error, retry_after),
    )
    if status == "published":
        _record_published(item)
    elif status == "retry":
        # Falha conhecida antes do clique final: liberar somente este item para
        # uma futura tentativa. Estados ambíguos/needs_human continuam reservados.
        _clear_attempt(item)
    elif AUTO_QUEUE and status == "needs_human":
        _write_halt(item, error)
    return response


def download(item, directory=None):
    if directory is None:
        directory = tempfile.mkdtemp(prefix="anthares-publisher-")
    dest_dir = pathlib.Path(directory)
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = pathlib.Path(urllib.parse.urlparse(item["file_url"]).path).suffix or ".mp4"
    path = dest_dir / f"atd-{int(item['queue_id'])}{suffix}"

    request = urllib.request.Request(
        item["file_url"],
        headers={"User-Agent": "AntharesPublisher/1.0", "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    except Exception:
        if path.exists():
            path.unlink()
        raise

    if path.stat().st_size <= 0:
        raise RuntimeError("O arquivo baixado do WordPress está vazio.")

    expected = _item_hash(item)
    if expected:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest().lower()
        if actual != expected:
            path.unlink(missing_ok=True)
            raise RuntimeError("SHA-256 do arquivo não corresponde ao registro do WordPress.")

    return path
