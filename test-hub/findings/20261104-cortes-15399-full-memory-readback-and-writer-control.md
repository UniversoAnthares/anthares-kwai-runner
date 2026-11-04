# CORTES / AOI-21 — recuperação integral do snapshot, auditoria do controle de escritor
STATUS: PARTIAL
AREA: architecture
DATE: 2026-11-04
RUN: none (Neon SQL SELECT / execução JS isolada em memória)
JOB: full-memory-readback-no-production-executor
COMMIT: 52987aed165f3682ef6c5f5ec0774b76bad94893
SUPERSEDES: 20261104-lease-architecture-cortes-15399-memory-readback.md
LEASE_CLOSED_UTC: 2026-11-04T03:44:02.865Z
GOVERNANCE_MANIFEST: 223433740e807a90
ITEMS: [AOI-21]
PRODUCTION_STATUS: UNCHANGED
COST_ADDED: 0

## Resultado terminal PROVEN — conteúdo recuperado integralmente fora do PC
- Uma única consulta Neon SELECT em `public.cortes_media_ledger_snapshots`, fixada por `revision=15399`, `source_bytes=2932006` e `sha256_hex=cc5d1a188b53f6f1780f392097b73ea0ac78758b632dd6205e9890ad37d2206a`, retornou payload Base64 integral.
- Conteúdo foi decodificado em memória em executor isolado de código, fora do PC e de GitHub Actions. Os 2.932.006 bytes foram reconstruídos, e SHA-256 independente em JavaScript teve correspondência EXATA com digest da base. Implementação SHA-256 passou auto-teste público conhecido para `abc`.
- UTF-8 e JSON interpretados integralmente; `version=1`, `revision=15399`, cinco fontes e 649 registros de segmento. Nenhum arquivo de mídia ou checkpoint persistente criado; dados sensíveis não foram publicados em relatório.
- Já existente em Clipper main o leitor Python `qa/cortes_neon_snapshot_restore_readonly.py` (commit 52987aed165f3682ef6c5f5ec0774b76bad94893), com nove testes sintéticos de QA aprovados no histórico e SQL de leitura por blocos validada diretamente no Neon. Nesta rodada NÃO foi executada a CLI original dentro de GitHub Actions por não existir quota e credencial com autorização verificadas. Não atribuir o teste JS ao executor do GitHub.
- A versão mais recente do Neon ainda é revision 15399, a segunda 14688; duas revisões SHA íntegras.

## Controle observado em produção — PROVEN parcialmente
- Tabela de snapshots: PRIMARY KEY pelo digest SHA-256; CHECK exige hash calculado dos bytes; CHECK de revisão não negativa e tamanho 1..16.000.000. Há dois snapshots, revisões distintas e hashes distintos.
- Fila Kwai `kwai:lucasrosalem`: 456 `confirmed`, 68 `uncertain`, zero leases ativos; zero intervalos de origem repetidos, zero IDs remotos repetidos, gerações existentes positivas. Os 68 têm `publication_started_at`, nenhum possui recibo/remote_id; os 456 confirmados incluem três com `remote_id` ausente.
- Não houve operações de publicação, atualização de status, reserva de quota, aquisição de lease ou tentativa de gravar no banco.
- Um SELECT em `pg_locks` não mostrou escritor ativo naquele instante. Isto é uma observação pontual, sem comprovar exclusividade permanente do escritor.

## Controle de escritor único — ainda UNVERIFIED / sem implantação
- Esquema `cortes_cloud` ausente; tabela `cortes_short_ledger_head` ausente; papel `cortes_short_ledger_writer` ausente; índice único por revisão de CAS também ausente. A migração destes mecanismos está na PR privada Clipper #229, ainda DRAFT, e depende de proprietário autorizado, lease de writer, pré-requisitos de produção, quota/rollback e teste separado.
- A tabela de snapshots atual é imutável por conteúdo e íntegra, porém não confere sozinha compare-and-swap/fencing e single-writer. O estado de código e os testes da PR #229 são READY_FOR_REVIEW, não DEPLOYED nem PRODUCTION_PROVEN.
- Um SELECT agregado adicional recebeu recusa de segurança do provedor (`DENIED_PENDING_REVIEW`); não houve repetição, substituição de ferramenta, nem acesso por caminho alternativo. As consultas independentes e autorizadas apresentadas aqui foram concluídas sem efeitos colaterais.

## Condições restantes
1. **Restauração no executor final:** executar CLI Python real com role Neon restrita, scratch efêmero e quota gratuita comprovada; verificar log da recuperação dos 2.932.006 bytes e descarte final do scratch.
2. **Escritor único:** revisar PR #229, instalar/validar CAS, role e fencing com lease, SHA atual, provas de negação e rollback, sob autorização de produção. Nenhum componente novo foi implantado hoje.
3. **Kwai:** obter prova de cada vídeo na conta correta e reconciliar os 68 UNCERTAIN e três confirmados sem ID. Bloquear reenvios incertos.
4. **CORTES:** migrar `daily` e `resume` após cobertura real de masters, quota de executor, source lock e coordenação do escritor único. O refill Ubuntu permanece com execução bloqueada.

## Classificação
PROVEN: recuperação integral em memória fora do PC e SHA independente; integridade dos snapshots; invariantes de unicidade/leases disponíveis.
DEPLOYED (inativo): leitor Python de QA no repositório.
UNVERIFIED: execução da CLI no GitHub-hosted; writer CAS/single-writer produtivo; posts Kwai; migração integral.
RECONCILE_REQUIRED: 68 publicações Kwai.
Nenhuma despesa nova, mídia publicada, credencial alterada, segredo exposto ou job disparado.
