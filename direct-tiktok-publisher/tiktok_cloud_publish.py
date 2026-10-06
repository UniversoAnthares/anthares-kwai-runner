#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

from playwright.sync_api import sync_playwright

import tiktok_worker as tw
import tiktok_web_publish_v3 as v3

# v3 importa v2 e aplica os patches de modal/confirmação sobre o módulo principal.
t = v3.t
PLAN_PATH = Path(os.getenv("TIKTOK_YOUTUBE_PLAN", "tiktok-owned-plan.json"))
ARTIFACT_DIR = Path(os.getenv("ATD_ARTIFACT_DIR", "publisher-artifacts"))
HALT_PATH = Path(os.getenv("TIKTOK_AUTOMATION_HALT", ".state/TIKTOK_AUTOMATION_HALT.json"))
PUBLISH_EVIDENCE_PATH = Path(os.getenv("TIKTOK_PUBLISH_EVIDENCE", ".state/tiktok-last-publish.json"))
PUBLISHED_KEYS_PATH = Path(os.getenv("TIKTOK_PUBLISHED_KEYS", ".state/tiktok-published-keys.json"))
VIDEO_URL_RE = re.compile(r"https?://(?:www\.)?tiktok\.com/@[^/\s]+/video/(\d+)")

BLOCK_PATTERNS = (
    "temporarily blocked", "too many requests", "too many posts", "spam",
    "suspicious activity", "account warning", "account restriction", "restricted",
    "cannot post", "unable to post", "posting is unavailable",
    "try again later", "tente novamente mais tarde", "atividade suspeita",
    "conta restrita", "publicação bloqueada", "não foi possível publicar",
)

def _halt_if_platform_block(page, reason="") -> None:
    try:
        body = page.locator("body").inner_text(timeout=3000).lower()
    except Exception:
        body = ""
    hit = next((p for p in BLOCK_PATTERNS if p in body), None)
    if not hit:
        return
    HALT_PATH.parent.mkdir(parents=True, exist_ok=True)
    HALT_PATH.write_text(json.dumps({
        "halted_at": int(time.time()),
        "reason": reason or "platform_block_signal",
        "signal": hit,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    raise RuntimeError(f"TikTok sinalizou bloqueio/restrição; automação interrompida: {hit}")


def _caption(plan: dict) -> str:
    source = " ".join(str(plan.get("source_title") or "").split()).strip()
    segment = " ".join(str(plan.get("title") or "").split()).strip()
    summary = " ".join(str(plan.get("summary") or plan.get("resumo_curto") or "").split()).strip()
    def clean(value: str) -> str:
        value = value.replace("�", "")
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return " ".join(value.split()).strip(" .,-")
    source, segment, summary = clean(source), clean(segment), clean(summary)
    generic_sources = {"new anthares", "anthares", "live", "stream", "livestream"}
    meaningful = len(segment) >= 12 and sum(1 for w in segment.split() if len(w) >= 3) >= 3
    raw = segment if meaningful else source
    if not raw or raw.casefold() in generic_sources:
        raw = summary[:100] if len(summary) >= 12 else "Literatura e escrita"
    if len(raw) > 100:
        raw = raw[:97].rsplit(" ", 1)[0] + "..."
    topic=(raw+" "+summary+" "+source).casefold()
    tags=["#literatura","#escrita"]
    thematic=[
        (("personagem","personagens","protagonista"),"#personagens"),
        (("dialogo","dialogos"),"#dialogos"),
        (("narrador","ponto de vista","foco narrativo"),"#narrativa"),
        (("cena","cenas"),"#cenaliteraria"),
        (("conto","contos"),"#contos"),
        (("romance","romances"),"#romance"),
        (("poesia","poema","verso"),"#poesia"),
        (("fantasia","fantastico"),"#fantasia"),
        (("terror","horror","lovecraft"),"#terror"),
        (("classico","classicos"),"#classicos"),
        (("storytelling","historia","histórias"),"#storytelling"),
    ]
    for keys,tag in thematic:
        if any(k in topic for k in keys) and tag not in tags:
            tags.append(tag)
        if len(tags)>=5: break
    if "#escritores" not in tags: tags.append("#escritores")
    return raw+" "+" ".join(tags[:5])

def _fill_caption(page, caption: str) -> None:
    selectors = [
        '[contenteditable="true"][data-e2e*="caption"]',
        '[contenteditable="true"]',
        'textarea[placeholder*="descr"]',
        'textarea[placeholder*="caption"]',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=800):
                loc.click()
                loc.fill(caption)
                print(f"TIKTOK_CAPTION={caption}", flush=True)
                return
        except Exception:
            pass
    raise RuntimeError("Campo de legenda/título do TikTok não foi localizado.")


def _new_profile_candidates(before_ids: set[str], inventory: list[dict]) -> list[dict]:
    unique = {}
    for item in inventory or []:
        video_id = str((item or {}).get("id") or "").strip()
        if not video_id or video_id in before_ids:
            continue
        unique[video_id] = {
            "id": video_id,
            "url": str((item or {}).get("url") or "").strip(),
            "text": str((item or {}).get("text") or "")[:500],
        }
    return list(unique.values())


def main() -> None:
    if not PLAN_PATH.is_file():
        raise RuntimeError(f"Plano do job não existe: {PLAN_PATH}")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    # The one-off failover proof has already been published. It is permanently
    # non-publishable now; this guard is inside the publisher so every caller
    # fails closed even if a workflow is accidentally re-run with publish=true.
    segment_id=str(plan.get("segment_id") or "").strip()
    account=os.getenv("EXPECTED_TIKTOK_USERNAME","").strip().lstrip("@").casefold()
    if segment_id == "cloud-failover-test":
        raise RuntimeError("Prova cloud-failover-test encerrada; republicação bloqueada.")
    if not segment_id or not account:
        raise RuntimeError("Publicação bloqueada: conta ou segment_id ausente.")
    publish_key=account+"::"+segment_id
    try:
        published_keys=json.loads(PUBLISHED_KEYS_PATH.read_text(encoding="utf-8")) if PUBLISHED_KEYS_PATH.exists() else {}
    except Exception as exc:
        raise RuntimeError("Registro redundante de deduplicação ilegível; publicação bloqueada.") from exc
    if publish_key in published_keys:
        raise RuntimeError("Publicação duplicada bloqueada pelo registro redundante: "+publish_key)
    media_path = Path(str(plan.get("media_path") or "")).resolve()
    if not media_path.is_file() or media_path.stat().st_size <= 0:
        raise RuntimeError(f"Arquivo de mídia do job não existe: {media_path}")
    media_hash = hashlib.sha256(media_path.read_bytes()).hexdigest()
    for prior_key, prior in published_keys.items():
        if isinstance(prior, dict) and prior.get("account") == account and prior.get("media_sha256") == media_hash:
            raise RuntimeError("Publicação duplicada bloqueada pelo hash do vídeo: "+str(prior_key))

    before_inventory = tw.inventory_profile_videos(account)
    before_ids = {str(item.get("id") or "").strip() for item in before_inventory if str(item.get("id") or "").strip()}
    print(f"TIKTOK_PROFILE_BASELINE count={len(before_ids)}", flush=True)

    state = tw.storage_state()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu",
                "--disable-extensions", "--disable-background-networking",
                "--disable-component-update", "--disable-default-apps",
                "--disable-features=Translate,MediaRouter,OptimizationHints",
                "--disable-sync", "--metrics-recording-only", "--no-first-run",
                "--no-zygote", "--renderer-process-limit=1",
            ],
        )
        context = browser.new_context(
            storage_state=state,
            viewport={"width": 1440, "height": 1000},
            locale="pt-BR",
        )
        page = context.new_page()
        try:
            file_input = t.open_upload(page, context)
            t.screenshot(page, "tiktok-owned-upload-page.png")
            file_input.set_input_files(str(media_path))
            post_button = t.wait_upload_ready(page)
            t.handle_auto_checks_modal(page)
            _fill_caption(page, _caption(plan))
            t.screenshot(page, "tiktok-owned-upload-ready.png")

            privacy = t.set_public_visibility(page)
            if privacy is False:
                raise RuntimeError(
                    "A interface do TikTok não apresenta publicação pública para esta conta."
                )

            post_button = t.enabled_post_button(page) or post_button
            before = str(page.url)
            post_button.click(timeout=30000)
            time.sleep(2)
            _halt_if_platform_block(page, "after_post_click")
            confirmed = t.wait_confirmation(page, before)
            _halt_if_platform_block(page, "confirmation_check")
            t.screenshot(page, "tiktok-owned-after-post.png")
            if not confirmed:
                raise RuntimeError(
                    "O clique em Publicar foi executado, mas faltou confirmação inequívoca; "
                    "o ledger permanecerá em attempted para impedir repetição automática."
                )

            verified_post = None
            for verify_attempt in range(1, 4):
                post_inventory = tw.inventory_profile_videos(account)
                candidates = _new_profile_candidates(before_ids, post_inventory)
                print(
                    f"TIKTOK_PROFILE_VERIFY attempt={verify_attempt} new_candidates={len(candidates)}",
                    flush=True,
                )
                if len(candidates) == 1:
                    verified_post = candidates[0]
                    break
                if len(candidates) > 1:
                    raise RuntimeError(
                        "Publicação possivelmente ocorreu, porém o perfil apresenta múltiplos vídeos novos; "
                        "reconciliação manual/central é obrigatória antes de qualquer retry."
                    )
                if verify_attempt < 3:
                    time.sleep(5)
            if not verified_post:
                raise RuntimeError(
                    "A interface confirmou publicação, porém nenhum vídeo novo inequívoco apareceu no perfil; "
                    "o job deve permanecer UNCERTAIN até reconciliação."
                )

            evidence_id = str(verified_post.get("id") or "").strip()
            evidence_url = str(verified_post.get("url") or "").strip()
            if not evidence_id:
                raise RuntimeError("Verificação de perfil retornou vídeo sem ID; reconciliação obrigatória.")
            page_match = VIDEO_URL_RE.search(str(page.url))
            if page_match and page_match.group(1) != evidence_id:
                raise RuntimeError(
                    "ID pós-publicação da interface diverge do único vídeo novo do perfil; "
                    "o job deve permanecer UNCERTAIN até reconciliação."
                )
            evidence = {
                "confirmed_at": int(time.time()),
                "account": os.getenv("EXPECTED_TIKTOK_USERNAME", ""),
                "segment_id": str(plan.get("segment_id") or ""),
                "source_id": str(plan.get("source_id") or ""),
                "caption": _caption(plan),
                "remote_url": evidence_url,
                "remote_id": evidence_id,
                "confirmation": "profile_new_post",
                "ui_confirmation": "ui_success",
                "confirmed": True,
            }
            PUBLISH_EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
            PUBLISH_EVIDENCE_PATH.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            PUBLISHED_KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
            published_keys[publish_key]={
                "confirmed_at": evidence["confirmed_at"],
                "remote_id": evidence_id,
                "segment_id": segment_id,
                "account": account,
                "media_sha256": media_hash,
            }
            tmp=PUBLISHED_KEYS_PATH.with_suffix(PUBLISHED_KEYS_PATH.suffix+".tmp")
            tmp.write_text(json.dumps(published_keys,ensure_ascii=False,indent=2),encoding="utf-8")
            os.replace(tmp,PUBLISHED_KEYS_PATH)
            print(
                "TIKTOK_OWNED_PUBLISH=OK "
                f"segment={plan.get('segment_id', '')} source={plan.get('source_id', '')} "
                f"remote_id={evidence_id}",
                flush=True,
            )
            try:
                from render_session import persist_session_state
                if persist_session_state(context.storage_state()):
                    print("TIKTOK_SESSION_PERSIST=OK", flush=True)
            except Exception as exc:
                print(f"TIKTOK_SESSION_PERSIST=SKIPPED {type(exc).__name__}", flush=True)
        except Exception:
            try:
                t.screenshot(page, "tiktok-owned-error.png")
            except Exception:
                pass
            raise
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    print("Anthares TikTok Owned YouTube Publisher", flush=True)
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr, flush=True)
        raise