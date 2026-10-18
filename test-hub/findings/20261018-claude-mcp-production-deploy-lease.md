# Claude MCP Cloudflare canary deployment
STATUS: RUNNING
AREA: ara-mcp-claude-deploy
DATE: 2026-10-18
START_UTC: 2026-10-18T21:42:16.405Z
EXPIRES_UTC: 2026-10-18T22:07:16.405Z
BASELINE_PROVEN: PR #162 head c4133032b21415b88ad3534cc9592d6b860019bc; Node suite 11/11, Wrangler dry-run valid. Cloudflare existing deployment 3b2a566b-ca6d-4b04-958d-3453ae4caad2. GitHub main 2c377274da79e3638897877bcf95eac5db8254d9; GitLab peer index.js 273d1af68ee486ee0291d6c1fa0f025a270020f9.
FAILED_AVOIDED: preserve active ChatGPT MCP credentials and OAuth endpoints; no GitHub token values in logs; no blind CI or unbounded remote shell.
SCOPE: guarded anthares-ara-mcp deploy from exact PR head with existing encrypted production secrets, read-only health/OAuth/unauth negative tests, rollback on regression. No unrelated changes or reboot.
SUCCESS_SIGNAL: new Cloudflare deployed version, /health 200, OAuth metadata 200, unauth MCP 401, Claude client oauth requests satisfy restrictions.
FAILURE_SIGNAL: denied auth, degraded production endpoints, loss of existing secrets; rollback to version 3b2a566b-ca6d-4b04-958d-3453ae4caad2.
TEST_VALIDITY: compare remote head and peer source before deploy; no claim owner Claude OAuth approval until it happens. 
