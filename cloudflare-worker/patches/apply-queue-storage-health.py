"""Apply after v17/v18 migrations; preserve their queue and auth fencing."""
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'src' / 'index.js'
s = p.read_text(encoding='utf-8-sig')
if "from './queue_storage_health.js'" in s:
    print('QUEUE_STORAGE_HEALTH_ALREADY_APPLIED=1')
    raise SystemExit(0)
start = '  for(const raw of this.sql.exec("SELECT id,payload,account_id FROM jobs").toArray()){'
end = '\n  }\n'
assert s.count(start) == 1, 'account migration anchor changed'
a = s.index(start)
b = s.index(end, a) + len(end)
s = s[:a] + '  migrateLegacyTargetAccounts(this.sql);\n' + s[b:]
assert s.count('export default {') == 1
s = s.replace('export default {', 'const worker = {', 1)
s = "import {migrateLegacyTargetAccounts, storageQuotaResponse} from './queue_storage_health.js';\n" + s
s += '''
export default {...worker, async fetch(request, env) {
  try { return await worker.fetch(request, env); }
  catch (error) {
    const quota = storageQuotaResponse(error);
    if (quota) return quota;
    throw error;
  }
}};
'''
p.write_text(s, encoding='utf-8')
print('QUEUE_STORAGE_HEALTH_APPLIED=1')
