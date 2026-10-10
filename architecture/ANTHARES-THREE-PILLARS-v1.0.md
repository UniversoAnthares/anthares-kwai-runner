# ANTHARES — CARTA ARQUITETURAL v1.0 (2026-10-10)

Status: BASELINE FIXA. Mudanças só por nova versão explícita, mantendo histórico e justificativa; não substituir silenciosamente este contrato.

## Três pilares permanentes

1. **Anthares Core** — orquestração, infraestrutura, planejamento, filas persistentes, heartbeat, leases, watchdog, recuperação, rastreabilidade, testes e supervisão de executores.
2. **Anthares Mobile** — operação de aplicativos Android, navegação por estados e evidências, autenticação legítima, cofre criptografado de sessões e verificação da identidade após reinicialização e nova execução.
3. **Anthares Publisher** — ingestão, cortes, deduplicação por origem/timecode, filas multirrede, publicação autorizada, reconciliação e confirmação independente por ID/URL.

## Restrições obrigatórias

- **Custo R$ 0:** nenhuma contratação, cartão, billing obrigatório ou uso pago não autorizado.
- **Reutilizar o arsenal:** GitHub Actions, GitLab CI/runners, Render, Cloudflare e demais conectores efetivamente autenticados, com verificação de capacidade antes de uso.
- **Operação sem PC pessoal:** produção, agendamento, execução, armazenamento, observabilidade e recuperação devem funcionar com o computador do proprietário desligado. Uso eventual do PC apenas para preparação autorizada, nunca como dependência de produção.
- **Mínima intervenção manual:** preferir automação legítima, credenciais de privilégio mínimo e sessões verificadas. Não contornar MFA, CAPTCHA ou controles de segurança da plataforma.
- **Evidência acima de aparência:** cache restaurado não prova login; clique não prova ação; job verde não prova publicação. Exigir conta identificada e ID/URL verificável.
- **Resiliência:** operações idempotentes, sem repetição de cortes, timeout explícito, backoff, fencing de leases, logs sem segredos e retomada após falha.
- **Sem promessas impossíveis:** gratuidade e autonomia dependem das quotas e interfaces reais dos provedores; registrar bloqueios externos com precisão.

## Ordem de construção

1. **Core mínimo:** manifesto de capacidades, registro persistente de tarefas e evidências, fila/lease, healthchecks, executor remoto gratuito e recuperação.
2. **Mobile mínimo:** diagnosticar UI real, login comprovado, persistência criptografada, restauração em duas execuções independentes.
3. **Publisher mínimo:** publicar um vídeo real, obter URL/ID, confirmar conta, evitar duplicação e repetir após reinicialização.
4. Ampliar os três pilares de forma incremental.

## Critérios de aceite

- Core: tarefa executada remotamente com PC desligado, falha detectada e retomada auditável sem duplicação.
- Mobile: identidade da conta correta verificada antes e depois de reinicialização e em execução independente; não expor credenciais.
- Publisher: publicação pública efetiva verificada por URL/ID e ledger de deduplicação, repetível sem intervenção quando permitido pela plataforma.

## Governança

Este documento é o contrato de arquitetura **v1.0**. Não remover nem fundir os três pilares. Mudanças devem ser propostas em documento versionado posterior, com motivação, compatibilidade e evidências. O commit SHA constitui referência auditável, mas imutabilidade forte depende de proteção de branch/tag e permissões GitHub.
