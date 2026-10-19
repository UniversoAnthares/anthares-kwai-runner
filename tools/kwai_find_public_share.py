#!/usr/bin/env python3
"""Find a CORTES clip in the publisher's Kwai playlist and verify its share URL.

Read-only: navigates Kwai profile, copies a share URL, opens it and checks the
expected caption and the author's exact profile handle. Does not publish.
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import kwai_verify_public_post as proof

SERIAL=proof.SERIAL
URLS=re.compile(r"https://k\.kwai\.com/p/[A-Za-z0-9_-]+|https://www\.kwai\.com/@[A-Za-z0-9_.-]+/photo/[0-9]+")

def adb(*parts,timeout=40):
    return proof.adb(*parts,timeout=timeout)

def nodes():
    return proof.snapshot()

def text(node):
    return node.get("text","") or node.get("content-desc","")

def matchnode(items,label):
    target=proof.normal(label)
    return next((n for n in items if target and target in proof.normal(text(n)) and proof.center(n.get("bounds",""))),None)

def tap(n):
    pos=proof.center(n.get("bounds",""))
    if not pos:raise RuntimeError("missing_valid_ui_bounds")
    adb("shell","input","tap",str(pos[0]),str(pos[1]))
    time.sleep(1.6)

def kwai_profile():
    adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1")
    time.sleep(2)
    for attempt in range(3):
        current=nodes()
        if matchnode(current,"lucasrosalem") and any("Playlists" in text(n) for n in current):
            return current
        tab=next((n for n in current if proof.normal(text(n)) in ("perfil","profile")
                  and proof.center(n.get("bounds",""))),None)
        if not tab:raise RuntimeError("kwai_profile_tab_not_visible")
        tap(tab)
    raise RuntimeError("correct_kwai_profile_not_visible")

def playlist_items():
    current=kwai_profile()
    # A single source live is published into its own Kwai playlist; inspect
    # only the latest visible tile, not unrelated historical posts.
    candidates=[n for n in current if "LIVE" in text(n) and proof.center(n.get("bounds",""))]
    if not candidates:raise RuntimeError("source_playlist_tile_not_found")
    tap(candidates[-1])
    for _ in range(5):
        time.sleep(1.5)
        listing=nodes()
        if matchnode(listing,"episodio") or any("Episódio" in text(n) for n in listing):
            return listing
    raise RuntimeError("playlist_episodes_not_displayed")

def open_episode(title):
    listing=playlist_items()
    wanted=proof.normal(title)
    significant=" ".join(x for x in wanted.split() if x not in ("universo","anthares"))
    candidates=[]
    for node in listing:
        t=proof.normal(text(node))
        if len(significant)>=12 and significant in t and proof.center(node.get("bounds","")):
            candidates.append(node)
    if len(candidates)!=1:
        raise RuntimeError("playlist_episode_title_not_unique:"+str(len(candidates)))
    tap(candidates[0])
    current=nodes()
    if not matchnode(current,"Compartilhar"):
        raise RuntimeError("episode_share_not_available")
    return current

def copy_public_links(title):
    current=open_episode(title)
    share=[n for n in current if proof.normal(text(n))=="compartilhar" and proof.center(n.get("bounds",""))]
    if not share:raise RuntimeError("share_control_missing")
    tap(share[-1])
    current=nodes()
    copy=matchnode(current,"Copiar link")
    if not copy:raise RuntimeError("copy_link_control_missing")
    tap(copy)
    # Android's clipboard shell command is unavailable on this emulator.
    # Paste into Chrome's address field, then read only that field via UI dump.
    adb("shell","am","start","-a","android.intent.action.VIEW","-d","about:blank","-p","com.android.chrome")
    time.sleep(2)
    bar=next((n for n in nodes() if n.get("resource-id")=="com.android.chrome:id/url_bar"),None)
    if not bar:raise RuntimeError("clipboard_reader_address_bar_missing")
    tap(bar)
    adb("shell","input","keyevent","279")
    time.sleep(0.8)
    bar=next((n for n in nodes() if n.get("resource-id")=="com.android.chrome:id/url_bar"),None)
    value=bar.get("text","") if bar else ""
    urls=list(dict.fromkeys(URLS.findall(value)))
    if not urls:raise RuntimeError("share_clipboard_did_not_contain_public_link")
    return urls[:30]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--title",required=True)
    p.add_argument("--account",default="lucasrosalem")
    p.add_argument("--evidence-file",required=True)
    args=p.parse_args()
    if proof.normal(args.account)!="lucasrosalem":
        raise RuntimeError("wrong_expected_account")
    urls=copy_public_links(args.title)
    for link in urls:
        try:
            result=proof.verify(link,args.title,args.account,"Lucas Rosalem")
        except Exception as exc:
            print("CANDIDATE_REJECTED="+type(exc).__name__,flush=True)
            continue
        destination=pathlib.Path(args.evidence_file)
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print("KWAI_PUBLIC_LINK_CONFIRMED="+link,flush=True)
        return 0
    print("KWAI_PUBLIC_LINK_UNVERIFIED no matching video and author",flush=True)
    return 90

if __name__=="__main__":
    raise SystemExit(main())
