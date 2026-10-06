# Anthares Arsenal — inventário canônico

Atualizado: 2026-10-06 08:45 -04:00
Fonte de verdade experimental: `test-hub/README.md` + findings append-only.

Estados: PROVEN, PARTIAL, BLOCKED, NOT_STARTED, ABANDONED.

| Serviço | Estado | Acesso atual | ChatGPT direto | Remoto | Auth | Read | Write | Execute | Testado | Redundância | Bloqueio / próxima ação |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GitHub | PROVEN | conector ChatGPT | sim | n/a | OAuth/App | sim | sim | Actions | sim | GitLab/Codeberg pendentes | preservar |
| AI Commander | PARTIAL | MCP ChatGPT | sim | sim | pareamento | sim | sim | sim | probe atual encontrou contenção de arquivo | RDC/Mesh/WinRemote | repetir health após liberação do processo; sem reinstalar |
| Remote Desktop Commander | PARTIAL | MCP ChatGPT | sim | sim | pareamento | sim | sim | sim | dispositivo online; execução recusada por cota mensal | AI Commander | cota mensal esgotada |
| Render | PROVEN | conector ChatGPT | sim | n/a | OAuth | sim | sim | deploy/jobs | sim, workspace e serviços listados | GitHub executors | preservar |
| Gmail | PROVEN | conector ChatGPT instalado | sim | n/a | OAuth | sim | sim | ações mail | sim/conector disponível | Hostinger Mail | preservar |
| Google Drive | PROVEN | conector ChatGPT instalado | sim | n/a | OAuth | sim | sim | ações Drive | conector disponível | GitHub/files | preservar |
| Google Calendar | PROVEN | conector ChatGPT instalado | sim | n/a | OAuth | sim | sim | ações Calendar | conector disponível | — | preservar |
| Google Contacts | PROVEN | conector ChatGPT | sim | n/a | OAuth | sim | limitado | ações Contacts | conector disponível | — | preservar |
| Hostinger Mail | PROVEN | conector ChatGPT | sim | n/a | auth connector | sim | sim | mail | conector disponível | Gmail | preservar |
| Cloudflare control plane | PROVEN | Worker + Wrangler OAuth | indireto | cloud | OIDC/Wrangler OAuth | sim | deploy/admin via console autorizado | Worker | v16 + OIDC PROVEN | GitHub/Render failover parcial | falta conector ChatGPT direto; criar wrapper administrativo sem duplicar secrets |
| CircleCI | PARTIAL | CI externo existente | indireto | cloud | token/OAuth a validar | parcial | parcial | pipelines | evidências anteriores no hub; interface canônica ausente | GitHub Actions/GitLab CI futuro | criar API/MCP/wrapper para pipeline/job/log/artifact/cancel |
| WPVibe FileBridge | PROVEN | endpoint WordPress | indireto | produção | contrato próprio | sim | sim | n/a | read/write/expected_hash já provados no projeto | GitHub/SSH | consolidar contrato e teste de conflito/rollback no inventário |
| Kilo | PARTIAL | ferramenta no PC | via remoto | sim | local | sim | sim | sim | existência histórica; health atual impedido pela cota/contenção | Cline/Claude Code | wrapper start/status/execute/result/stop |
| Cline | PARTIAL | ferramenta no PC | via remoto | sim | local | sim | sim | sim | idem | Kilo/Claude Code | wrapper comum |
| Claude Code | PROVEN | ferramenta/agente já comprovado no arsenal | via remoto | sim | local/provider | sim | sim | sim | PROVEN prévio | Kilo/Cline | incluir no health comum |
| Chrome | PARTIAL | PC remoto | via remoto | sim | sessão local | sim | sim | automação | histórico funcional | APIs/MCP | wrapper comum |
| ADB/Android SDK | PARTIAL | CI/Android remoto + PC | indireto | sim/cloud | n/a | sim | sim | sim | Android API35/splits Kwai PROVEN | múltiplos substratos em avaliação | publicação Kwai ainda exige auth READY |
| Claude provider | PROVEN | arsenal | indireto | cloud | configurada | sim | sim | inferência | PROVEN informado/operacional | Grok/Perplexity/Gemini | health comum |
| Grok | PROVEN | arsenal | indireto | cloud | configurada | sim | sim | inferência | PROVEN existente | demais IAs | health comum |
| Perplexity | PROVEN | arsenal | indireto | cloud | configurada | sim | sim | inferência | PROVEN existente | demais IAs | health comum |
| Gemini | PROVEN | arsenal | indireto | cloud | configurada | sim | sim | inferência | PROVEN existente | demais IAs | health comum |
| Manus | NOT_STARTED | integração pendente | não | cloud | pendente | ? | ? | ? | não | demais IAs | localizar plugin/MCP/API e autenticar |
| Asaas | PARTIAL | WordPress/API | indireto | cloud | API segura no WP | sim | fluxo WP sim | pagamentos | fluxo funcional encerrado | — | avaliar somente administração direta |
| Telegram | PARTIAL | relay repo/Distribuidor | indireto | cloud | bot token | parcial | parcial | envio | implementação existe; prova canônica final pendente | — | fechar confirmação + dedupe |
| Kwai primary | PARTIAL | Android/CI publisher | indireto | cloud | sessão/login | parcial | publisher implementado | sim | safety PROVEN | Kwai secondary futuro | falta REAL_REMOTE_POST com identidade READY e ledger |
| TikTok primary | PARTIAL | Render + control plane | indireto | cloud | sessão central/OIDC | sim | publisher PROVEN | sim | publisher/media/OIDC PROVEN | GitHub fallback | falta REAL_REMOTE_POST independente + ledger |
| GitLab | NOT_STARTED | candidato | não | cloud | pendente | — | — | CI futuro | não | GitHub/Codeberg | conectar conta/repo e provar push+CI |
| Codeberg/Forgejo | NOT_STARTED | candidato | não | cloud | pendente | — | — | CI possível | não | GitHub/GitLab | conectar conta/repo e provar push |
| MeshCentral MCP | NOT_STARTED | candidato | não | remoto | pendente | — | — | — | não | AI Commander/RDC/WinRemote | instalar com TLS/auth e provar comando |
| WinRemote MCP | NOT_STARTED | candidato | não | remoto | pendente | — | — | — | não | AI Commander/RDC/Mesh | instalar e provar comando |
| Kwai secondary | NOT_STARTED | social nova | não | cloud | conta/sessão separada | — | — | — | não | Kwai primary | usar platform+account_id |
| Instagram | NOT_STARTED | social nova | plugin/API a conectar | cloud | pendente | — | — | — | não | Distribuidor | plugin discovery encontrou opções sociais; autenticação humana necessária |
| Threads | NOT_STARTED | social nova | plugin/API a conectar | cloud | pendente | — | — | — | não | Distribuidor | idem |
| X/Twitter | NOT_STARTED | social nova | plugin/API a conectar | cloud | pendente | — | — | — | não | Distribuidor | localizar caminho gratuito sustentável |

## Regras de integração

A unidade de destino social é `platform + account_id`. Credenciais, sessão, rate limit, circuit breaker, dedupe e ledger ficam isolados por conta.

Produção não depende permanentemente do PC. Ferramentas locais servem a desenvolvimento, recuperação e administração.

Secrets nunca entram neste inventário, findings, logs ou repositório. Health checks retornam somente estado e evidência sanitizada.

## Estados globais de health

`UP`: operação útil comprovada e health atual positivo.
`DEGRADED`: serviço utilizável com capacidade reduzida ou um caminho indisponível.
`DOWN`: health explícito falhou.
`AUTH_REQUIRED`: recurso existe e depende de autorização humana/credencial ausente.
`UNKNOWN`: ainda sem probe válido.
