/** Codeberg Forgejo Actions dispatch adapter. No credentials, claims, or publication logic here.
 * The caller MUST hold the shared Neon first-winner fence and independently prove
 * original TERMINAL + NOT_APPLIED before invoking dispatch().
 * An ambiguous HTTP response is terminal for this attempt: never blind-retry.
 */
const API = "https://codeberg.org/api/v1";
const ALLOWED = new Set(["avs-d1-live-homologation.yml"]);
const HEX = /^[0-9a-f]{40}$/i;
const REF = /^[A-Za-z0-9._/-]+$/;
export function validateIntent(x) {
  if (!x || x.repository !== "UniversoAnthares/anthares-video-studio" ||
      !ALLOWED.has(x.workflow) || x.ref !== "main" || !HEX.test(x.sha || "") ||
      !/^[A-Za-z0-9:_-]{8,128}$/.test(x.attemptId || "") ||
      x.nonpublishing !== true || x.originalTerminal !== true ||
      x.sideEffects !== "NOT_APPLIED" || x.fenceWon !== true ||
      x.independentQuotaHealthy !== true)
    throw Error("CODEBERG_DISPATCH_GUARD_REJECTED");
  return Object.freeze({...x});
}
function url(x, suffix) {
  return API + "/repos/" + x.repository + "/actions/" + suffix;
}
async function responseJson(res) {
  if (!res.ok) throw Error("CODEBERG_READBACK_HTTP_" + res.status);
  return res.json();
}
export async function dispatchCodeberg({intent, token, fetcher = fetch, receipt}) {
  const x = validateIntent(intent);
  if (!token || token.length < 12) throw Error("CODEBERG_TOKEN_MISSING");
  if (typeof receipt !== "function") throw Error("DURABLE_RECEIPT_REQUIRED");
  const headers = { Authorization: "token " + token, Accept: "application/json" };
  // Pin the actual main commit immediately before dispatch; never dispatch if it moved.
  const branch = await responseJson(await fetcher(API + "/repos/" + x.repository + "/branches/main",
      {headers, signal: AbortSignal.timeout(8000)}));
  if (branch.commit?.id !== x.sha) throw Error("CODEBERG_HEAD_MISMATCH");
  // Persist DISPATCH_INTENT before network mutation; caller must atomically fence on attempt ID.
  if (await receipt({attemptId:x.attemptId, status:"DISPATCH_INTENT", sha:x.sha}) !== true)
    throw Error("FENCE_RECEIPT_REJECTED");
  let res;
  try {
    res = await fetcher(url(x,"workflows/" + x.workflow + "/dispatches"),
      {method:"POST",headers:{...headers,"Content-Type":"application/json"},
       body:JSON.stringify({ref:x.ref,inputs:{publish:"false",smoke:"true"}}),
       signal:AbortSignal.timeout(10000)});
  } catch {
    await receipt({attemptId:x.attemptId,status:"DISPATCH_UNCERTAIN",sha:x.sha});
    return {state:"DISPATCH_UNCERTAIN",retryAllowed:false};
  }
  if (![200,201,202,204].includes(res.status)) {
    await receipt({attemptId:x.attemptId,status:"DISPATCH_UNCERTAIN",sha:x.sha});
    return {state:"DISPATCH_UNCERTAIN",httpStatus:res.status,retryAllowed:false};
  }
  await receipt({attemptId:x.attemptId,status:"DISPATCH_ACCEPTED",sha:x.sha});
  return {state:"DISPATCH_ACCEPTED",retryAllowed:false,sha:x.sha};
}
export async function readCodebergRun({repository, runId, token, fetcher=fetch}) {
  if (repository!=="UniversoAnthares/anthares-video-studio" ||
      !/^[1-9][0-9]{0,16}$/.test(String(runId)) || !token || token.length < 12)
    throw Error("CODEBERG_READBACK_GUARD_REJECTED");
  const data = await responseJson(await fetcher(API+"/repos/"+repository+"/actions/runs/"+runId,
    {headers:{Authorization:"token "+token,Accept:"application/json"},signal:AbortSignal.timeout(8000)}));
  return {id:data.id,status:data.status,conclusion:data.conclusion,
          sha:data.head_sha ?? data.sha,htmlUrl:data.html_url};
}
export function verifyReadback(run, expectedSha) {
  if (!HEX.test(expectedSha||"") || run.sha!==expectedSha ||
      !["success","failure","cancelled","skipped","timed_out"].includes(run.conclusion))
    return {state:"UNVERIFIED"};
  return {state:run.conclusion==="success"?"SUCCESS":"FAILED",runId:run.id};
}
