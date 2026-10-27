#!/usr/bin/env node
// Read-only inventory of existing Pinterest drafts through the authenticated,
// pre-existing Chrome CDP target. Never create, navigate, close or click tabs.
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const LOOPBACK = 'http://127.0.0.1:9226';
const EDITOR_PATH = '/pin-creation-tool/';
const sha = value => createHash('sha256').update(String(value)).digest('hex');
const normalize = text => String(text || '').replace(/\s+/g, ' ').trim();

export function summarizeDrafts(rows) {
  if (!Array.isArray(rows) || rows.length > 100 || rows.some(
    r => !r || !/^pinDraft-[0-9]{5,25}$/.test(String(r.id || ''))
  )) throw Error('DRAFT_AUDIT_INVALID_DOM_DATA');
  const sources = new Map(), composites = new Map();
  let titlesPresent = 0;
  for (const row of rows) {
    const thumb = sha(row.thumbnailSrc || '');
    const text = normalize(row.text);
    const duration = String(row.duration || '').slice(0, 12);
    if (text.includes('● Universo Anthares')) titlesPresent++;
    sources.set(thumb, (sources.get(thumb) || 0) + 1);
    const key = sha(thumb + '|' + duration + '|' + text);
    composites.set(key, (composites.get(key) || 0) + 1);
  }
  return {
    status: 'READ_ONLY_RECONCILIATION_REQUIRED',
    draft_count: rows.length,
    titled_drafts: titlesPresent,
    untitled_drafts: rows.length - titlesPresent,
    unique_thumbnails: sources.size,
    largest_thumbnail_group: Math.max(0, ...sources.values()),
    matching_display_groups: [...composites.values()].filter(v => v > 1).length,
    // Thumbnail/text coincidences are never proof of duplicate media.
    can_autodelete: false,
    can_autopublish: false,
    inventory_sha256: sha(rows.map(r => String(r.id) + ':' +
      sha(r.thumbnailSrc || '') + ':' + normalize(r.text)).sort().join('\n'))
  };
}

function domReadOnly() {
  if (location.hostname !== 'br.pinterest.com' ||
      location.pathname !== '/pin-creation-tool/') {
    throw Error('DRAFT_AUDIT_UNEXPECTED_PAGE');
  }
  return [...document.querySelectorAll('[data-test-id^="pinDraft-"]')].map(e => ({
    id: e.getAttribute('data-test-id'),
    duration: (e.innerText || '').trim().split('\n')[0],
    text: (e.innerText || '').slice(0, 300),
    thumbnailSrc: e.querySelector('img')?.currentSrc || e.querySelector('img')?.src || ''
  }));
}

async function audit() {
  const response = await fetch(LOOPBACK + '/json/list', {signal: AbortSignal.timeout(5500)});
  if (!response.ok) throw Error('DRAFT_AUDIT_CDP_UNAVAILABLE');
  const targets = await response.json();
  const target = targets.find(item => {
    if (item.type !== 'page' || !item.webSocketDebuggerUrl) return false;
    try {
      const u = new URL(item.url);
      return u.hostname === 'br.pinterest.com' && u.pathname === EDITOR_PATH;
    } catch {return false;}
  });
  if (!target) throw Error('DRAFT_AUDIT_EDITOR_NOT_OPEN');
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  try {
    await new Promise((ok, bad) => {
      const timeout = setTimeout(() => bad(Error('DRAFT_AUDIT_SOCKET_TIMEOUT')), 10000);
      ws.onopen = () => {clearTimeout(timeout);ok();};
      ws.onerror = () => {clearTimeout(timeout);bad(Error('DRAFT_AUDIT_SOCKET_FAILED'));};
    });
    const rows = await new Promise((ok, bad) => {
      const timer = setTimeout(() => bad(Error('DRAFT_AUDIT_RPC_TIMEOUT')), 12000);
      ws.onmessage = event => {
        let response;
        try {response = JSON.parse(event.data);} catch {return;}
        if (response.id !== 1) return;
        clearTimeout(timer);
        if (response.error || response.result?.exceptionDetails ||
            !Array.isArray(response.result?.result?.value)) {
          bad(Error('DRAFT_AUDIT_EVALUATION_FAILED')); return;
        }
        ok(response.result.result.value);
      };
      ws.send(JSON.stringify({id: 1, method: 'Runtime.evaluate', params: {
        expression: '(' + domReadOnly.toString() + ')()',
        returnByValue: true, awaitPromise: false, userGesture: false
      }}));
    });
    return summarizeDrafts(rows);
  } finally {
    // Close only the audit WebSocket connection, never the shared Chrome tab.
    try {ws.close();} catch {}
  }
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  audit().then(data => {console.log(JSON.stringify(data));}).catch(error => {
    const code = /^DRAFT_AUDIT_[A-Z_]+$/.test(error.message)
      ? error.message : 'DRAFT_AUDIT_UNAVAILABLE';
    console.log(JSON.stringify({status: code, can_autodelete: false, can_autopublish: false}));
    process.exitCode = 2;
  });
}
