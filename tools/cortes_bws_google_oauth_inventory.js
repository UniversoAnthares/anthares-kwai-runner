#!/usr/bin/env node
"use strict";
// Read-only Bitwarden Anthares Secrets inventory: never emit IDs, secret values,
// OAuth tokens, raw SDK responses, client credentials, or error messages.
const path = require("path");
const os = require("os");

async function main() {
  if (!process.env.BWS_ACCESS_TOKEN) {
    console.log("CORTES_BWS_BOOTSTRAP=UNAVAILABLE");
    return 2;
  }
  const sdk = require(path.join(process.env.RUNNER_TEMP || os.tmpdir(),
    "anthares-bws-sdk", "node_modules", "@bitwarden", "sdk-napi"));
  const client = new sdk.BitwardenClient({
    apiUrl: "https://api.bitwarden.com",
    identityUrl: "https://identity.bitwarden.com",
    userAgent: "anthares-cortes-readonly-inventory",
    deviceType: sdk.DeviceType.SDK
  });
  const unwrap = x => x?.data ?? x;
  const login = await client.auth().loginAccessToken(
    process.env.BWS_ACCESS_TOKEN, path.join(process.env.RUNNER_TEMP || os.tmpdir(), "cortes-bws-state"));
  if (login?.success === false) {
    console.log("CORTES_BWS_AUTH=FAIL");
    return 3;
  }
  console.log("CORTES_BWS_AUTH=PASS");
  const sample = unwrap(await client.secrets().get("6edd06b7-ce2e-4519-905f-b4e800e4fe1a"));
  if (!sample?.organizationId) {
    console.log("CORTES_BWS_SCOPE=UNKNOWN");
    return 4;
  }
  const result = unwrap(await client.secrets().list(sample.organizationId));
  const rows = Array.isArray(result?.data) ? result.data : Array.isArray(result) ? result : [];
  const keys = rows.filter(x => x && typeof x.key === "string");
  const candidates = keys.filter(x => /(?:GOOGLE|GDRIVE|DRIVE|RCLONE|OAUTH|YOUTUBE)/i.test(x.key));
  const targetProject = "a2e8f606-69c5-4d44-80d8-b4e800e279c6";
  const projectKeys = keys.filter(x => x.projectId === targetProject);
  console.log("CORTES_BWS_LIST=PASS");
  console.log("CORTES_BWS_POTENTIAL_GOOGLE_KEY_COUNT=" + candidates.length);
  console.log("CORTES_BWS_TARGET_PROJECT_VISIBLE_KEY_COUNT=" + projectKeys.length);
  for (const key of [
    "ANTHARES_CORTES_GDRIVE_CLIENT_ID",
    "ANTHARES_CORTES_GDRIVE_CLIENT_SECRET",
    "ANTHARES_CORTES_GDRIVE_PROFILE2",
    "ANTHARES_CORTES_GDRIVE_PROFILE3",
    "ANTHARES_CORTES_GDRIVE_PROFILE9"
  ]) {
    console.log("CORTES_BWS_" + key + "_PRESENT=" + keys.some(x => x.key === key));
  }
  console.log("CORTES_BWS_METADATA_ONLY=PASS");
  return 0;
}
main().then(code => process.exitCode=code).catch(err => {
  console.log("CORTES_BWS_INVENTORY_ERROR_KIND=" + (err?.constructor?.name || "Unknown"));
  process.exitCode=1;
});
