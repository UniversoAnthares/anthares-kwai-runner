# AGENTE 05 — SpawnDroid: recuperação segura da autenticação (lease)
STATUS: RUNNING
AREA: session
DATE: 2026-11-14
RUN: none
JOB: agent05/spawndroid-auth-recovery-20261114
COMMIT: 5db0bf2ef1e0ed0f1cb930a563090415d686cd0e
SUPERSEDES: none

BASELINE_PROVEN: O SpawnDroid encerra/destrói os contêineres Android, sem persistência entre sessões. O cofre Kwai existente armazena dados criptografados, mas a restauração de autenticação entre Androids não está comprovada. Os publicadores atuais e o cloud_cutover.enabled=false permanecem intactos.
FAILED_AVOIDED: Não exportar dados privados do aplicativo, cookies ou chaves para contêineres novos; não automatizar MFA/OTP/CAPTCHA; não reexecutar postagens incertas nem consumir runners sem autorização.
SUCCESS_SIGNAL: novo gate independente testado em CI (duas contas, dois IDs de sessão, identidade exata, prazo, erros, quota, reconciliação), sem publicar ou alterar rota de produção.
FAILURE_SIGNAL: exposição de segredo, permissões cruzadas, publicação involuntária, ativação de cloud_cutover, testes com quota sem autorização ou conflito com Agentes 01–04.
TEST_VALIDITY: testes sintéticos são evidência de contrato, não prova de recuperação Android real.

## Escopo exclusivo de escrita
`tools/kwai_spawndroid_auth_recovery.py`, `tests/test_kwai_spawndroid_auth_recovery.py`, novo workflow dedicado de CI e documentação específica do Agente 05. Preservar os arquivos e workflows dos demais agentes. Mutação em branch isolada e PR draft; nenhuma mudança em produção.
