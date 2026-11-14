import {fetchWithoutRedirects} from "./secure-fetch.mjs";

const BASE = 'https://anthares.us/forgejo';
const ALLOWED_FORGEJO_HOSTS = new Set(['anthares.us', 'forgejo.anthares.us']);
const MAX_B64_BYTES = 4 * 1024 * 1024;
const ALLOWED_REPOS = new Set(['anthares-admin/anthares-kwai-runner', 'anthares-admin/anthares-clipper', 'anthares-admin/anthares-wordpress']);
const ALLOWED_OWNERS = new Set(['anthares-admin']);
const REPO_MAX_LEN = 120;
const PATH_MAX_LEN = 240;
function base(env){ const b = String(env.FORGEJO_BASE_URL || BASE).replace(/\/+$/,''); const u = new URL(b); if (u.protocol !== 'https:') throw new Error('forgejo_base_url_invalid'); if (!ALLOWED_FORGEJO_HOSTS.has(u.hostname)) throw new Error('forgejo_base_host_not_allowed'); return u.origin + u.pathname; }
function token(env){ const t = String(env.FORGEJO_READ_TOKEN || '').trim(); if (!t) throw new Error('forgejo_read_token_missing'); return t; }
function safeHeaderValue(v){ return String(v||'').replace(/[\r\n]+/g, ' '); }
async function api(env, method, path) {
  validateEndpoint(path);
  const url = base(env) + path;
  const headers = { 'Accept': 'application/json', 'User-Agent': 'Anthares-Forgejo-Read-Bridge' };
  const t = token(env);
  if (t) headers.Authorization = 'token ' + safeHeaderValue(t);
  const r = await fetchWithoutRedirects(url, { method, headers, signal: AbortSignal.timeout(12000) });
  if (!r.ok) throw new Error('forgejo_request_failed');
  return r.json();
}
function validateRepo(v){ const s=String(v||'').trim(); if(!s||s.length>REPO_MAX_LEN||s.includes('..')||s.includes('//')||s.includes('\\')||/[\x00-\x1f]/.test(s)||s.includes('%')||s.includes(':')||s.startsWith('/')||s.endsWith('/')) throw new Error('invalid_repo'); if(!ALLOWED_REPOS.has(s)) throw new Error('repository_not_allowed'); return s; }
function validatePath(v){ const s=String(v||'').trim(); if(!s||s.length>PATH_MAX_LEN||s.startsWith('/')||s.startsWith('\\')||s.includes('\\')||/[\x00-\x1f]/.test(s)||s.includes('%')||s.includes(':')||s.includes('..')) throw new Error('invalid_path'); const segments=s.split('/'); if (segments.some(x=>!x || x==='.' || x==='..' || x==='.git')) throw new Error('path_traversal'); return s; }
function validateOwner(v){ const s=String(v||'').trim(); if(!s||!ALLOWED_OWNERS.has(s)) throw new Error('owner_not_allowed'); return s; }
const FORGEJO_ENDPOINT_RE = /^\/api\/v1\/(?:version|users\/[^/?]+\/repos(?:\?limit=\d+)?|repos\/[^/?]+\/[^/?]+\/(?:contents\/[^?]+(?:\?ref=[A-Za-z0-9._%-]+)?|actions\/runs(?:\/\d+)?(?:\/jobs)?(?:\?limit=\d+)?))$/;
function validateEndpoint(path){ if(!FORGEJO_ENDPOINT_RE.test(path)) throw new Error('forgejo_endpoint_not_allowed'); return path; }
function validateRunId(v){ const n=Number(v); if(!Number.isInteger(n)||n<=0||n>Number.MAX_SAFE_INTEGER) throw new Error('invalid_run_id'); return n; }
export const forgejoTools = [
  { name:'forgejo_version', description:'Read Forgejo server version.', inputSchema:{ type:'object', properties:{} }, scope:'forgejo.read' },
  { name:'forgejo_list_repos', description:'List Forgejo repositories for an owner.', inputSchema:{ type:'object', properties:{ owner:{ type:'string' } } }, scope:'forgejo.read' },
  { name:'forgejo_get_file', description:'Read a file from a Forgejo repository.', inputSchema:{ type:'object', properties:{ repo:{ type:'string' }, path:{ type:'string' }, ref:{ type:'string' } }, required:['repo','path'] }, scope:'forgejo.read' },
  { name:'forgejo_list_runs', description:'List Forgejo Actions runs for a repository.', inputSchema:{ type:'object', properties:{ repo:{ type:'string' }, limit:{ type:'integer', default:20 } }, required:['repo'] }, scope:'forgejo.read' },
  { name:'forgejo_get_run', description:'Get a Forgejo Actions run and its jobs.', inputSchema:{ type:'object', properties:{ repo:{ type:'string' }, run_id:{ type:'integer' } }, required:['repo','run_id'] }, scope:'forgejo.read' }
];
export async function callForgejoTool(env, name, args={}) {
  if (name === 'forgejo_version') return api(env, 'GET', '/api/v1/version');
  if (name === 'forgejo_list_repos') {
    const owner = validateOwner(args.owner || 'anthares-admin');
    return api(env, 'GET', '/api/v1/users/' + encodeURIComponent(owner) + '/repos?limit=50');
  }
  const repo = validateRepo(args.repo);
  const repoEnc = repo.split('/').map(encodeURIComponent).join('/');
  if (name === 'forgejo_get_file') {
    const path = validatePath(args.path);
    const ref = String(args.ref || 'main').replace(/[^A-Za-z0-9._-]/g, '');
    const data = await api(env, 'GET', '/api/v1/repos/' + repoEnc + '/contents/' + path.split('/').map(encodeURIComponent).join('/') + '?ref=' + encodeURIComponent(ref));
    if (data && data.content) {
      try { data.decoded = atob(String(data.content).replace(/\s/g,'')).slice(0, MAX_B64_BYTES); } catch {}
    }
    return data;
  }
  if (name === 'forgejo_list_runs') {
    const limit = Math.max(1, Math.min(Number(args.limit)||20, 50));
    return api(env, 'GET', '/api/v1/repos/' + repoEnc + '/actions/runs?limit=' + limit);
  }
  if (name === 'forgejo_get_run') {
    const requestedRun = validateRunId(args.run_id);
    // The web UI uses repository-local run numbers; the REST API uses
    // database run IDs. For example, UI run #1 has API id 567.
    const runsResponse = await api(env, 'GET', '/api/v1/repos/' + repoEnc + '/actions/runs?limit=50');
    const runs = Array.isArray(runsResponse.workflow_runs) ? runsResponse.workflow_runs : [];
    const target = '/actions/runs/' + requestedRun;
    const uiMatch = runs.find(item => {
      if (typeof item?.html_url !== 'string') return false;
      try { return new URL(item.html_url).pathname.endsWith(target); } catch { return false; }
    });
    const apiRunId = uiMatch ? validateRunId(uiMatch.id) : requestedRun;
    const run = await api(env, 'GET', '/api/v1/repos/' + repoEnc + '/actions/runs/' + apiRunId);
    let jobs = null;
    // Forgejo v15.0.9 can expose run metadata while lacking the REST
    // /runs/:id/jobs route; preserve this distinction for callers.
    try { jobs = await api(env, 'GET', '/api/v1/repos/' + repoEnc + '/actions/runs/' + apiRunId + '/jobs'); } catch {}
    return { run, jobs, ui_run_number: uiMatch ? requestedRun : null, api_run_id: apiRunId,
      jobs_status: jobs === null ? 'UNAVAILABLE' : 'AVAILABLE' };
  }
  throw new Error('unknown_forgejo_tool');
}
