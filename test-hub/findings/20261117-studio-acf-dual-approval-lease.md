# Escopo isolado — corrigir dupla autorização do ACF Studio
STATUS: RUNNING
AREA: anthares-studio/G5/safety-gate
DATE: 2026-11-17
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-acf-dual-approval-guard-20261117
SOURCE: anthares-wordpress PR #314 / integration/studio-g4-g5-g6-20261116 / HEAD 433631df89af6acbf47296b8114f1f0d5eebd9b5
PEER: GitLab branch integration/studio-g4-g5-g6-20261116 absent (404).
SCOPE: apenas anthares-studio/anthares-estudio.php e testes existentes de isolamento/fixture do ACF, em branch nova baseada na PR #314.
PROBLEM: o plugin define ANST_ACF_RUNTIME_APPROVED=true internamente; a autorização de implantação prevista exige aprovação externa independente de anst_acf_runtime_enabled=1.
PLAN: manter ANST_ACF_RUNTIME_APPROVED=false como padrão; aceitar true exclusivamente de configuração externa antes do carregamento; verificar estados OFF/ON e exigência de ambos os fatores.
BLOCK: sem alterações no plugin anthares-estudio, dados, CPTs, opções produtivas, flags de escrita, credenciais ou deploy; PR obrigatoriamente draft até G4/G5.
ROLLBACK: descartar branch/PR de código; nenhuma mutação produtiva autorizada por este lease.
EVIDENCE: PR de código e resultados QA serão registrados em finding append-only separado.
