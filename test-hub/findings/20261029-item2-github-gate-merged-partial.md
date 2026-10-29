# Item fixo 2 — gate de handoff GitHub→Forgejo integrado; ativação produtiva pendente
STATUS: PARTIAL
AREA: tiktok/forgejo-producer-handoff
DATE: 2026-10-29 UTC
RUN: none (nenhuma execução produtiva Forgejo disparada)
JOB: none
COMMIT: d0f23dfefd0ca9178cd0a3b079b5e57d86b8e435 (clipper main)
SUPERSEDES: 20261029-item2-producer-handoff-gate-running.md
LEASE: ENCERRADO para alteração do workflow GitHub; nenhuma reserva sobre ativação Forgejo.

BASELINE_PROVEN: Forgejo WordPress preflight histórico #238 SUCCESS; Forgejo Clipper runs #1/#2/#3 foram canceladas na UI pelo titular. Github Clipper antes do ajuste tinha produtor com cron */5 e relay pós-rodada, ambos sem condição de handoff. Neon cortes_tiktok_publications: 538 registros (414 confirmed, 114 queued, 10 uncertain); 538 segment_id distintos; 12 entradas novas criadas entre 2026-10-29T12:28:26Z e 12:28:32Z. Nenhum campo de origem do executor no schema; as inserções não provam autoria.
IMPLEMENTED: PR UniversoAnthares/anthares-clipper #224 (merged, SHA d0f23dfefd0ca9178cd0a3b079b5e57d86b8e435). Arquivo .github/workflows/anthares-tiktok-owned-youtube.yml contém duas condições vars.CORTES_FORGEJO_PRODUCER_ENABLED != 'true', uma no job de enqueue e outra no relay. Ref principal e blob SHA 8a4ef9e495c5d9306f1b4d7bdeb0c39f9e9ff9eb validados após merge. Cron, runner Windows, OIDC, enqueuer e quotas mantidos. Gate ausente/false preserva produtor GitHub.
SUCCESS_SIGNAL_SOURCE: GitHub PR merged, readback de main, duas condições, execução anterior não desarmada. Nenhum teste produtivo gerado.
LIMITS: essa condição GitHub depende da variável de repositório GitHub. Variável homônima no Forgejo é independente. Leitura/mutação administrativa Forgejo anteriormente bloqueada por segurança; recusa preservada. Nenhuma ativação ou publicação Forgejo comprovada. Espelho Hostinger após o novo merge não foi confirmado porque a tentativa de SSH foi abortada.
NEXT_ESSENTIAL_GATES: (1) pelo canal administrativo autorizado, definir CORTES_FORGEJO_PRODUCER_ENABLED=true no GitHub, confirmar término terminal de runs antigos, (2) no Forgejo anthares-wordpress definir variável homônima true, (3) execução única e real de produtor com confirmação de ingress idempotente em Neon; rollback seguro para GitHub somente após assegurar fim da tentativa Forgejo. Preservar os 10 uncertain sem retry cego.
TEST_VALIDITY: prova de source e deduplicação estrutural do ledger, sem evidência de handoff ao vivo. ITEM2=PARTIAL.
COST: nenhuma quota, cobrança ou serviço novo.