import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const src=readFileSync(new URL("../src/northflank-owner-entry.js",import.meta.url),"utf8");

test("Manual drag requires the signed-in owner",()=>{
  assert.match(src,/ownerPath&&\!\(await ownerAuthorized\(request,env\)\)/);
  assert.match(src,/owner\/tiktok\/drag-mode/);
  assert.match(src,/owner\/tiktok\/drag-start/);
  assert.match(src,/owner\/tiktok\/drag-end/);
  assert.match(src,/interactive-browser\/drag/);
});
test("Manual drag is human-operated, checks bounds and sends two-point coordinates",()=>{
  assert.match(src,/Number\.isFinite\(x1\)/);
  assert.match(src,/x1<=1365/);
  assert.match(src,/y2<=768/);
  assert.match(src,/shot\.x/);
  assert.match(src,/shot\.y/);
  assert.match(src,/phase:"start"/);
  assert.match(src,/phase:"end"/);
  assert.match(src,/Arrastar na imagem/);
});
