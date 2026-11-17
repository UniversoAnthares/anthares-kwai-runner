# Studio G5 - CPTs internos com interface administrativa restrita

STATUS: PARTIAL
AREA: anthares-studio/g5/private-cpt-admin
DATE: 2026-11-17
JOB: studio-g5-private-cpt-admin-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/317
COMMIT: d6697afb74a11d09eb1589cdd84085867279e0b7
SUPERSEDES: test-hub/findings/20261117-studio-g5-private-cpt-admin-running.md

## Objetivo
Implementar a parte de G5 que exige administração de registros WordPress com CPTs privados e capacidades exclusivas de administradores, preservando o plugin legado e o bloqueio ACF até G4.

## Resultado
- PR #317 (DRAFT) criada em branch isolada, derivada da PR #316, sem mudanças em produção.
- Quatro CPTs anst_* passam a declarar show_ui=true, permanecendo public=false, publicly_queryable=false e show_in_rest=false.
- As capacidades primitivas edit_posts, edit_others_posts, edit_private_posts, edit_published_posts, publish_posts, read_private_posts, create_posts, delete_posts, delete_others_posts, delete_private_posts e delete_published_posts são mapeadas para manage_options, com map_meta_cap=true.
- Regressão adicionada ao test_acf_contract.py, arquivo existente.
- PHP 8.4: lint do bloco modificado PASS. Simulação de register_post_type: 4 CPTs e 64 asserções PASS.
- QA inventário Hostinger da cópia disponível: 665/665 PASS; nenhum caminho auditável novo na PR #317.

## Limites e próximo gate
- Teste WordPress real com permissões e PHP lint integral do checkout da PR #317 ainda faltam.
- Permanece bloqueado qualquer deploy/merge/ativação ACF por dependências G4, QA e coordenação com PRs #315/#316.
- Plugin original intacto e nenhuma escrita em dados reais nesta tarefa.
- Não repetir testes de escrita remota negados sem alteração causal ou autorização explícita da plataforma.

## Encerramento
Lease particular G5 privado/CPT admin concluído no escopo de implementação isolada; homologação da funcionalidade classificada PARTIAL.
