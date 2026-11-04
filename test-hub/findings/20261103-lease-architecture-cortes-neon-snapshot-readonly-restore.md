# Lease — recuperação de checkpoint Neon somente-leitura em executor remoto
STATUS: RUNNING
AREA: architecture
DATE: 2026-11-03
RUN: none
JOB: read-only-recovery-preparation
COMMIT: 3e56699d883835af71ac7ec8fd49a6a1a0fd6082
SUPERSEDES: none
LEASE_OWNER: ChatGPT / Reestruturação e Otimização / CORTES
LEASE_START_UTC: 2026-11-04T03:09:39.571Z
LEASE_EXPIRES_UTC: 2026-11-04T03:29:39.571Z
GOVERNANCE_MANIFEST: 223433740e807a90
SCOPE: preparar leitura e recuperação do snapshot existente cortes_media_ledger_snapshots por consulta SQL sem writer; compatibilidade com QA/cortes_short_resume_guard.py. Criar um módulo isolado e testes próprios em anthares-clipper sem alterar PR #229 ou #190, sem job ativo nem deploy.

## BASELINE_PROVEN
- Neon projeto atual mantém duas revisões inteiras do ledger, 15399 e 14688, com hash/tamanho conferidos e 68 segmentos incertos associados à revisão 15399.
- PR privada anthares-clipper #229 já prepara CAS com nova tabela head, ausente no Neon de produção: preservá-la sem overwrite.
- PR privada #190 envolve storage, Drive e executores ainda em QA; nenhum merge/alteração de mídia.
- CORTES reabastecimento Ubuntu já configurado no main com gate off; daily/resume ainda dependem de runner Windows.
- Custo adicional zero; ações exclusivamente read-only, teste sintético e PR draft. Nenhum runner GitHub/Hostinger será ativado sem quota verificada.

## SUCCESS_SIGNAL
- Função de recuperação usa tabela original, revision/digest pinados, chunks de bytes e SHA-256 local em memória; valida JSON, fonte, revisão e aborta em mismatch.
- QA sintética prova roundtrip e corrupção, sem acesso público nem segredos.
- Não cria cópia persistente ou backup em PC; o futuro executor remoto terá scratch efêmero e cleanup por finally.

## FAILURE_SIGNAL
- Tentativa de escrita em Neon, novo cron/job, secrets em git, leitura de arquivo alheio, quota paga, mudança no publisher, concorrência em PR ou execução no computador pessoal.

## VALIDITY
Lease autoriza apenas preparação isolada de código e registro de QA sem ativação. Terminar via finding. Deploy/integração de produção requer lease independente e quota comprovada.
