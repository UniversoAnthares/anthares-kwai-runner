# Agent04 — lease de diagnóstico isolado do Kwai Lite
STATUS: RUNNING
AREA: kwai-lite-readiness
DATE: 2026-11-14
OWNER: agent04-chatgpt
LEASE_SCOPE: leitura e documentação da integridade APK / inventário SpawnDroid para kwai.lite.video e @lucasrosalem
LEASE_EXPIRES: 30 minutos após criação
BASELINE_GITHUB_HEAD: 5db0bf2ef1e0ed0f1cb930a563090415d686cd0e
PEER_GITLAB: UniversoAnthares/anthares-kwai-runner main defasado; sem reconciliação ou espelhamento

BASELINE_PROVEN: extração ADB do aplicativo instalado no Android próprio, 18 APKs e manifesto SHA-256; adaptadores SpawnDroid existentes exclusivos de com.kwai.video; histórico Kwai já contém publicações verificadas em ambas as contas, sem prova de execução SpawnDroid.
FAILED_AVOIDED: não empacotar splits sob outra assinatura, não iniciar demo no lugar de Kwai Lite, não alterar Neon, filas ou publicadores, não ocupar runner compartilhado de AG01/02/03.
SUCCESS_SIGNAL: auditoria somente leitura de arquivos SHA-256, assinatura Android v2/v3 e identidade instalada; listagem autenticada de artefatos e sessões SpawnDroid; finding de encerramento com aptidão ou bloqueio verificável.
FAILURE_SIGNAL: hash/certificado divergente, pacote inesperado, autenticação de workspace ausente, pacote universal legítimo indisponível ou runner concorrente.
TEST_VALIDITY: nenhuma sessão criada por esta tarefa; as APIs autenticadas são consultadas somente por GET; certificado é extraído do APK Signing Block, sem alegar verificação integral da assinatura.
PUBLICATION_ATTEMPTED: false
COST_ADDITIONAL_BRL: 0
