# AOI item fixo 17 — Codeberg retirado da autoridade operacional
STATUS: PROVEN
AREA: architecture/codeberg-retirement
DATE: 2026-10-28
RUN: read-only refs and native GitHub CI/Forgejo receipts
JOB: existing GitHub #123025502074 and #123145935173
COMMIT: operations source quarantine PR, merge SHA readback required
SUPERSEDES: 20261028-item17-codeberg-retirement-running.md
LEASE: ENCERRADO após integração e readback da branch principal.

BASELINE_PROVEN: GitHub é o primário canônico. PRs #1731/#1736/#1791/#1802/#1809 retiraram Codeberg dos roteamentos Git/CI, espelhamento, QA e despachos X/TikTok. GitLab permanece peer sob paridade; Forgejo Hostinger é redundância Git/CI não publicadora e não equivale a promoção social.
FAILED_AVOIDED: nenhum contato API com Codeberg suspenso, token/secret, publicação, reparação de estado UNCERTAIN, push GitLab sob revisão de segurança, habilitação de Forgejo Actions principal ou teste de publicação.
SUCCESS_SIGNAL: auditoria por SHA de **27/27** arquivos históricos `.forgejo/workflows`: gatilhos somente manuais (sem cron/push/workflow_run), **28/28** jobs explicitamente `if: false`; comparação Git nativa indica exatamente 27 workflows e arquivos de governança, sem alterações em publicadores/Neon/credenciais. No GitHub, 13/13 arquivos Codeberg-only de Actions têm `if: false`, nenhum fica com job elegível. A rotina WordPress Safe Mirror Fallback permanece ativa mas utiliza GitLab, não Codeberg. Duas funções históricas do QA/X definem URLs Codeberg, mas os caminhos `main()` ativos não as chamam.
TEST_VALIDITY: comparação de conteúdo integral, checagem local de triggers + guardas + CAS de branch, e leitura dos commits após PR. Nenhum novo teste produtivo, quota ou custo. Fonte de referência: SHA das políticas vivas em manifest v223433740e807a90.
INDEPENDENT_EVIDENCE: GitHub→Forgejo recuperação Git #40746611827, duas refs vazias legítimas e 13 restauráveis; QA GitHub-hosted P0 #40782057532/job #123145935173 com entrega e GET de comentário real; sandbox Forgejo QA run 243 com resultado terminal já documentado.
LIMITS: o Codeberg é inelegível e não mais primário. Habilitação de CI do Forgejo principal é separada (PR #1816, não promovida por esta alteração); publicadores TikTok/X e seus handoffs seguem itens 1,2,3,15; históricos GitLab divergentes seguem item 13. Endpoint read-only externo de espelho apresentou HTTP 503 em run posterior #40775387071; sua saúde e frescor permanecem critério do item 7 e não são prova de regressão ao Codeberg.
CONCLUSION: ITEM17=DONE quanto à aposentadoria operacional, com workflows antigos incapazes de reativação acidental.
