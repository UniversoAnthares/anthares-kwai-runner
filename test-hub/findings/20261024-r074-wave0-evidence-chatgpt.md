# R07.4 Onda 0 — execução prática e pendências verificadas
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-24
JOB: R07.4-WAVE0-01-09-20261024
LEASE_OWNER: chatgpt-wave0-20261024
COMMIT: anthares-kwai-runner main 1b7b146db05b0c6b1d45cba5e7cc55dacf08c162
SUPERSEDES: none
SCOPE: somente inspeção, instalação de dependência psutil sob SYSTEM, smoke do guard; sem deploy, publicação, acesso a secrets, filas alteradas ou jobs inciertos reenviados.
REVIEW: https://docs.google.com/document/d/1SkjpRPJYLe9n_9SDOA4s-RibN8Pb_hm6-ukS6pbV7aQ/edit (R07.5) e https://docs.google.com/document/d/1EQQYr7wszBb8WzateaqDZNxrrWmnuIt31YO4LpGWmKU/edit (Anexo AE)

## Governança
policy.preflight validado pela execução Anthares Remote e2146d1e4bec9d674edd549f82138a1a. Versão 2e28d54043d6bad1; hashes rules d747d7172dc4d869a768a3800111ff0b9148a0dc619be970a96ca392d9f782d0, indice 577572e173222404f7f1923b90062690c3a677d8ce0082433fbe8a2f33523343 e PROMPT-MESTRE.md a867c767f1253cdc2db18dd6fea71e4013c77d1507a2eae8017e5e6cde38080d. AUD-02 permanece concluído PRs governance #2/#3, audit 218 repositórios/0 falhas.

## AUD-01 / ISO-01
GitHub org list por consulta autenticada: 14 repositórios. Vercel list_projects: 12 numa equipe. Neon list_projects: 2 projetos nesta conexão (ARA HA e enciclopédia; não prova ausência de Neon CORTES em outra credencial). Windows: 355 scheduled tasks, 104 nominalmente relacionadas a Anthares/CORTES/redes. Código: 110 workflows anthares-clipper, 500 workflows anthares-kwai-runner; nomes por rede são indícios, não identidade operacional. Fontes de Cloudflare/Hostinger, contas externas, faturamento, papéis SQL e inventário de produtores ainda não exaustivos. Owner cross-network não certificado. Ambos PARCIAL.

## GOV-14
ci/network_scope_guard.py e .github/workflows/network-scope-guard.yml existem; usam BASE confiável pull_request_target, mas execução é self-hosted Windows e required-check externo/identidades negativas não comprovados. Clone de staging antigo não continha test_network_scope_guard.py (0 testes executados; FAIL, não PASS). PARCIAL.

## OPS-02 — recuperação concreta
Anthares Remote f2876dffe67c87c06d8c376938a4a0bd instalou psutil==6.1.1 via pip --user no Python 3.12.10 do SYSTEM, corrigindo ModuleNotFoundError no console remoto. Guard sha256 7eb3c7eda4cf9d77a6fce3ab60604537dea8e80fc71a0e4c90bfa851284013f5. Smoke real run_owned_command echo WINDOW_GUARD_TEST_OK, job 2a71aecdfb910a349a058c3dee949c08; sweep 0 lease/0 remaining, CDP checked=2, errors=[]; negative tests g.test_noninteractive_guard_20261022: EXPECTED_DENIALS=2, job 883da9c04cfb7e60e5be78d1bda0d409. Task Scheduler "Anthares Agent Window Lifecycle Guard" taskUser Lucas, Interactive, Hidden=true, LastTaskResult=0, distinto da instalação psutil sob SYSTEM. De 86 tarefas nominais Ready/Running, 77 possuem marcadores guard/silent/hidden; 9 sem marcador explícito (entre elas Threads SYSTEM e tarefas temporárias), ainda requerem auditoria de escopo e efeitos antes de ajustar. PENDENTE→PARCIAL, não concluído. Não se encerraram processos pessoais.

## CI-13
GitHub Actions real success run 40125470133 (2026-10-24 19h28 UTC), outros flows publicados successful. GitLab CI pipeline 2985001474: seis jobs failed exclusivamente por ci_quota_exceeded. CI GitLab fica no catálogo, temporariamente ineligível; GitLab Git/Issues permanecem. AppVeyor/Harness/Northflank precisam de prova atual por capability. PARCIAL.

## QA-01
Prova HTTP GET anônima em anthares.us/, /author/balduino/, /desafios-de-escrita/: os três status 200, latências 1,56-1,93 s, nenhuma ocorrência literal dos dois controles privados de vitrine ou do repasse pesquisado. Não comprova testes autenticados por role, checkout fictício, plugin runtime nem ausência de outros dados. Repo inclui tests/security-profile-vitrine-privacy.php, offline; QA Manifest Premerge GitHub run 40120105413 falhou e tentativa de logs por conector devolveu 404 BlobNotFound. PENDENTE→PARCIAL.

## MEDIA-01
F1 30min Ready, result 0, status idle_no_eligible_media. zero MP4 em runner-media/output e shorts; master real histórico previamente armazenado/restaurado 2×, sem prova automática de novo master. PARCIAL.

## DOC-01
Checklist R07.5 e Plano CORTES Anexo AE atualizados. Histórico e IDs 01–34 preservados; trabalho contínuo, PARCIAL.

## Estado final R07.5
01 AUD-01 PARCIAL; 02 AUD-02 CONCLUÍDO; 03 GOV-14 PARCIAL; 04 CORTES-ISO-01 PARCIAL; 05 DOC-01 PARCIAL; 06 MEDIA-01 PARCIAL; 07 OPS-02 PARCIAL; 08 CI-13 PARCIAL; 09 QA-01 PARCIAL.
Global 34: 1 concluído, 14 parciais, 18 pendentes, 1 bloqueado. Não executar produção ou contornar recusas para elevar estados artificialmente. Limites de homologação constam dos anexos; sem alterações em tokens, publicadores, banco ou filas.
