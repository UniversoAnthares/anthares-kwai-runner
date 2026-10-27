import test from 'node:test';
import assert from 'node:assert/strict';
import { summarizeDrafts } from '../tools/cortes_pinterest_draft_audit.mjs';

const row = (id, text, duration, thumbnailSrc) =>
  ({id:'pinDraft-'+id, text, duration, thumbnailSrc});

test('empty inventory is safe and reports zero', () => {
  const result = summarizeDrafts([]);
  assert.equal(result.draft_count, 0);
  assert.equal(result.can_autodelete, false);
  assert.equal(result.can_autopublish, false);
});

test('different drafts remain distinct despite similar labels', () => {
  const rows = [
    row('3965574429086880832', '0:38\n25 dias até o vencimento', '0:38', 'https://i.pinimg.com/a.jpg'),
    row('3965585263409378240', '0:38\n25 dias até o vencimento', '0:38', 'https://i.pinimg.com/b.jpg'),
    row('3965595676994806592', '0:38\n25 dias até o vencimento', '0:38', 'https://i.pinimg.com/a.jpg'),
  ];
  const result = summarizeDrafts(rows);
  assert.equal(result.draft_count, 3);
  assert.equal(result.unique_thumbnails, 2);
  assert.equal(result.largest_thumbnail_group, 2);
  assert.equal(result.matching_display_groups, 1);
  assert.equal(result.untitled_drafts, 3);
  assert.equal(result.can_autodelete, false);
});

test('recognized editorial text does not authorize publication', () => {
  const result = summarizeDrafts([row('3965585263409378240',
    'A Metamorfose ● Universo Anthares','0:39','https://i.pinimg.com/a.jpg')]);
  assert.equal(result.titled_drafts,1);
  assert.equal(result.can_autopublish,false);
  assert.match(result.inventory_sha256,/^[a-f0-9]{64}$/);
});

test('invalid records and implausible counts fail closed', () => {
  assert.throws(()=>summarizeDrafts([row('bad','A','0:30','')]),/DRAFT_AUDIT_INVALID_DOM_DATA/);
  assert.throws(()=>summarizeDrafts(Array(101).fill(row('3965574429086880832','A','0:30',''))),
    /DRAFT_AUDIT_INVALID_DOM_DATA/);
});
