// One-time, OIDC-limited reconciliation of three published Kwai cuts.
// The facts below were measured in a READ-ONLY GitHub runner (#43511361479)
// using public Kwai feed+CDN and WordPress source MP4. This module NEVER posts.
// Revoke the OIDC route once the three original records are confirmed.
const EXACT = Object.freeze({
  'kwai-cortes-cOhqEaY3-08-g1-cOhqEaY3-08-1983-2023': {
    account:'lucasrosalem', photo:'5200963257196327565',
    started:1794599393942, posted:1794599403839, generation:1,
    source:'https://anthares.us/wp-content/uploads/anthares-clips/2026/11/short_cOhqEaY3-08_g1_1983_2023.mp4',
    dispatch:'518658676f83aa49165b6f327004acc62eea94c2d9d5a984d48991069f2bc664',
    file:'feed9441ce09d0999cfd481a4cf266760999ac095bb02586427e4d65ede4d344',
    publicSha:'2194e054b9a384d253f17f7ef1c0b5a55d94910e274ac63786e9346a7c824824',
    sourceBytes:5165205, publicBytes:1828094, duration:34.4, initialStatus:'cancelled',
  },
  'kwai-cortes-A7BsgCe3-oo-g1-A7BsgCe3-oo-7595-7635': {
    account:'lucasrosalem', photo:'5236429103303004807',
    started:1794529424700, posted:1794529434243, generation:173,
    source:'https://anthares.us/wp-content/uploads/2026/10/short_A7BsgCe3-oo_g1_7595_7635.mp4',
    dispatch:'75f2c75e96d5a9696203281192198eb1d91d51ca55df4fe4d3f1a456987adf7d',
    file:'2e8b34222b40ba3d1f70d2c9e4eff5d8837d8b6d693d90f66ba4136d8fef27aa',
    publicSha:'4e9074f6f210ff5f2669ca9316f35dbf6a2664c3bd34d053c79439badf945b83',
    sourceBytes:5964639,publicBytes:2173887,duration:37.067,initialStatus:'uncertain',
  },
  'kwai-cortes-ua-217fddfeae7c0a86be66d8e8511e2916': {
    account:'universoanthares',photo:'5244028928629526188',
    started:1794534747829,posted:1794534757025,generation:1,
    source:'https://anthares.us/wp-content/uploads/2026/10/short_A7BsgCe3-oo_g1_7595_7635.mp4',
    dispatch:'75f2c75e96d5a9696203281192198eb1d91d51ca55df4fe4d3f1a456987adf7d',
    file:'2e8b34222b40ba3d1f70d2c9e4eff5d8837d8b6d693d90f66ba4136d8fef27aa',
    publicSha:'4e9074f6f210ff5f2669ca9316f35dbf6a2664c3bd34d053c79439badf945b83',
    sourceBytes:5964639,publicBytes:2173887,duration:37.067,initialStatus:'started',
  },
});
export const ONEOFF_WORKFLOW='kwai-three-verified-reconcile.yml';
export const ONEOFF_RECONCILED_KIND='kwai_three_public_sift_oidc_reconciled_v1';
export function validateOneoffKwaiPublicProof(body) {
  if(!body||typeof body!=='object'||Array.isArray(body))return null;
  const p=body.result;
  if(!p||typeof p!=='object'||Array.isArray(p))return null;
  const expected=EXACT[String(p.id||'')];
  if(!expected)return null;
  const target='kwai:'+expected.account,publicUrl='https://www.kwai.com/@'+expected.account+'/video/'+expected.photo;
  if(body.id!==p.id||body.target_key!==target||body.expected_account!==expected.account||
     p.account!==expected.account||p.photo_id!==expected.photo||p.public_url!==publicUrl||
     p.started_ms!==expected.started||p.posted_ms!==expected.posted||
     p.source_sha256!==expected.dispatch||p.ledger_media_hash_kind!=='dispatch_identity'||
     p.observed_source_file_sha256!==expected.file||
     p.public_media_sha256!==expected.publicSha||
     p.observed_source_file_bytes!==expected.sourceBytes||p.public_media_bytes!==expected.publicBytes||
     p.status!=='VERIFIED_PUBLIC_SOURCE_MEDIA_READONLY')return null;
  const m=p.proof;
  if(!m||m.matcher!=='sift_source_to_public_cdn_v1'||m.media_matched!==true||
     m.qualifying_distinct_frames!==6||!Array.isArray(m.best_source_frame_inliers)||
     m.best_source_frame_inliers.length!==6||
     m.best_source_frame_inliers.some(x=>!Number.isSafeInteger(x)||x<240||x>3000)||
     Math.abs(m.source_duration_seconds-expected.duration)>.05||
     Math.abs(m.public_duration_seconds-expected.duration)>.05||
     Math.abs(p.posted_ms-p.started_ms)>120000)return null;
  // Never trust role, status, URL, or lease numbers supplied by the client.
  return Object.freeze({id:p.id,target,account:expected.account,publicUrl,
      dispatch:expected.dispatch,source:expected.source,
      started:expected.started,posted:expected.posted,generation:expected.generation,
      initialStatus:expected.initialStatus,sourceSha:expected.file,publicSha:expected.publicSha,
      sourceBytes:expected.sourceBytes,publicBytes:expected.publicBytes,
      scores:[...m.best_source_frame_inliers],duration:expected.duration});
}
