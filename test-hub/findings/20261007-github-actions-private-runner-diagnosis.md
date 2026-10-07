# GitHub Actions — bloqueio de runners privados

STATUS: PROVEN
AREA: github-actions/private-runners
DATE: 2026-10-07

## Evidência
- `anthares-clipper`: runs 37606716603, 37636191986 e 37637735051 falharam antes de qualquer step observável; jobs sem runner atribuído.
- `anthares-wordpress`: run 37638290289 apresentou o mesmo padrão, antes de steps observáveis.
- `anthares-kwai-runner` (público): run 37561020721 executou com sucesso em runner GitHub-hosted.
- O workflow do Clipper já foi corrigido de actions/checkout@v7/setup-python@v7 para versões compatíveis v4/v5 e recebeu permissions: contents: read; o novo diagnóstico ainda falhou antes da execução.

## CONCLUSÃO
O bloqueio atual é de infraestrutura/uso do GitHub Actions para repositórios privados, não evidência de falha do código do Clipper ou WordPress.

## AÇÃO MANUAL
Verificar GitHub Billing & Licensing > Budgets and alerts / Actions. Se a cota estiver esgotada, liberar uso adicional configurando método de pagamento válido ou aumentando/removendo o orçamento que interrompe o uso. Depois repetir um workflow privado.

## PRÓXIMO TESTE
Após desbloqueio, executar novamente o workflow do Clipper e registrar o resultado neste Hub.