const BASE = 'https://anthares.us/forgejo';
function base(env){ return String(env.FORGEJO_BASE_URL || BASE).replace(/\/+$/,''); }
function token(env){ return String(env.FORGEJO_TOKEN || env.FORGEJO_READ_TOKEN || '').trim(); }
async function api(env, method, path) {
  const url = base(env) + path;
  const headers = { 'Accept': 'application/json', 'User-Agent': 'Anthares-Forgejo-Read-Bridge' };
  const t = token(env);
  if (t) headers.Authorization = 'token ' + t;
  const r = await fetch(url, { method, headers });
  if (!r.ok) throw new Error('forgejo_http_' + r.status);
  return r.json();
}
function validateRepo(v){ const s=String(v||'').trim(); if(!s||s.includes('..')||s.includes('//')) throw new Error('invalid_repo'); return s; }
function validatePath(v){ const s=String(v||'').trim(); if(!s||s.startsWith('/')||s.includes('..')) throw new Error('invalid_path'); return s; }
export const forgejoTools = [
  { name:'forgejo_version', description:'Read Forgejo server version.', inputSchema:{ type:'object', properties:{} }, scope:'forgejo.read' },
  { name:'forgejo_list_repos', description:'List Forgejo repositories for an owner (default anthares-admin).', inputSchema:{ type:'object', properties:{ owner:{ type:'string' } } }, scope:'forgejo.read' },
  { name:'forgejo_get_file', description:'Read a file from a Forgejo repository.', inputSchema:{ type:'object', properties:{ repo:{ type:'string' }, path:{ type:'string' }, ref:{ type:'string' } }, required:['repo','path'] }, scope:'forgejo.read' },
  { name:'forgejo_list_runs', description:'List Forgejo Actions runs for a repository.', inputSchema:{ type:'object', properties:{ repo:{ type:'string' }, limit:{ type:'integer', default:20 } }, required:['repo'] }, scope:'forgejo.read' },
  { name:'forgejo_get_run', description:'Get a Forgejo Actions run and its jobs.', inputSchema:{ type:'object', properties:{ repo:{ type:'string' }, run_id:{ type:'integer' } }, required:['repo','run_id'] }, scope:'forgejo.read' }
];
export async function callForgejoTool(env, name, args={}) {
  if (name === 'forgejo_version') return api(env, 'GET', '/api/v1/version');
  if (name === 'forgejo_list_repos') {
    const owner = String(args.owner || 'anthares-admin');
    return api(env, 'GET', '/api/v1/users/' + encodeURIComponent(owner) + '/repos?limit=50');
  }
  const repo = validateRepo(args.repo);
  if (name === 'forgejo_get_file') {
    const path = validatePath(args.path);
    const ref = String(args.ref || 'main');
    const data = await api(env, 'GET', '/api/v1/repos/' + repo + '/contents/' + encodeURIComponent(path) + '?ref=' + encodeURIComponent(ref));
    if (data && data.content) {
      try { data.decoded = atob(String(data.content).replace(/\s/g,'')); } catch {}
    }
    return data;
  }
  if (name === 'forgejo_list_runs') {
    const limit = Math.max(1, Math.min(Number(args.limit)||20, 50));
    return api(env, 'GET', '/api/v1/repos/' + repo + '/actions/runs?limit=' + limit);
  }
  if (name === 'forgejo_get_run') {
    const runId = Number(args.run_id);
    const run = await api(env, 'GET', '/api/v1/repos/' + repo + '/actions/runs/' + runId);
    let jobs = null;
    try { jobs = await api(env, 'GET', '/api/v1/repos/' + repo + '/actions/runs/' + runId + '/jobs'); } catch {}
    return { run, jobs };
  }
  throw new Error('unknown_forgejo_tool');
}
