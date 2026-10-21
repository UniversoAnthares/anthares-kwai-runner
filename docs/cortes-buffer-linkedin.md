# CORTES → LinkedIn: todos os cortes curtos da rodada no próprio dia

STATUS: BUFFER_CHANNEL_VERIFIED / CLOUD_WORKER_READY / SAME_DAY_DELIVERY_NOT_PROVEN
DATE: 2026-10-20

## Objetivo
Publicar cortes curtos na página corporativa do LinkedIn **Universo Anthares** via integração autorizada do Buffer, sem aguardar a aprovação da Community Management API do app próprio. A permissão para a página é obtida pelo OAuth do próprio Buffer, não por login automatizado do LinkedIn. Destino corporativo existente: https://www.linkedin.com/company/145345334/ .

## Pré-requisitos externos
1. Acessar https://publish.buffer.com/settings/channels na sessão do proprietário e conectar **LinkedIn Page Universo Anthares** (não o perfil pessoal). Fazer a autorização OAuth no LinkedIn pelo perfil Super Admin da página. Canal Buffer conectado e confirmado: `6ad8a372778b240e2f799c72`.
2. Acessar https://publish.buffer.com/settings/api , criar chave da API Buffer e **armazená-la no Anthares Secrets / secret store do executor como BUFFER_API_KEY**. Nunca compartilhar a chave por mensagens ou copiá-la para código/GitHub/CI.
3. Ler canais via GraphQL API autenticada para confirmar `name=Universo Anthares`, `service=linkedin` e `externalLink` correspondente à página; injetar seu ID real como `BUFFER_LINKEDIN_CHANNEL_ID`. Nunca adivinhar o ID.
4. Configurar `ANTHARES_SOCIAL_COMMIT=1` **somente** no executor autorizado com fencing e ledger/lease ativos. Não expor a chave no frontend do Buffer/WordPress.
5. Verificar agendamento, publicação efetiva e URL do post público em cada ciclo. Buffer API retorna ID de agendamento, não prova de publicação no LinkedIn.

## Adaptador de publicações
`social_adapters/buffer_linkedin.py` recebe JSON validado em stdin. Sem `ANTHARES_SOCIAL_COMMIT=1`, devolve DRY_RUN e não consulta rede. Requer mídia HTTPS *.mp4 em domínio `anthares.us` e título não vazio; valida intervalo 30–90s quando informado e página do LinkedIn estritamente. O texto da legenda começa pelo título terminado em ` ● Universo Anthares` e contém `www.anthares.us`, preservando hashtags.

Após validar conta/chave/canal, a API Buffer recebe `createPost` com `assets.video.url`, `schedulingType=automatic` e `mode=addToQueue`. Resultado bem-sucedido é `SCHEDULED_IN_BUFFER`, com ID Buffer e `requires_linkedin_readback=true`. Não marcar `confirmed` no Neon neste estágio: aguardar post `sent` + URL do LinkedIn. Falhas de criação são `UNCERTAIN_OR_REJECTED` sem novo envio automático, para não criar duplicações.

## Limites e agenda
LinkedIn: teto artificial de 20/dia revogado. Meta: **todos os curtos também destinados ao Kwai no próprio dia**. Limite real informado pelo Buffer: **50 publicações LinkedIn por 24h**, inclusive com rota alternativa. No plano Buffer Free, máximo de dez posts **na fila por canal de uma vez**; a reposição deve ser feita após vagas liberadas, respeitando horários, API rate limits e políticas contra spam. A conta Buffer Free permite 10 posts pendentes por canal a qualquer instante, não 10 publicações por dia. Preencher slots liberados até o fim da rodada, sem agendar silenciosamente para amanhã.

## Obrigação de conclusão no próprio dia — 2026-10-21

Todos os cortes curtos elegíveis da rodada do Kwai devem ser destinados ao LinkedIn com SLA de publicação efetiva até 23:59:59, no fuso America/Campo_Grande, **no próprio dia da rodada**. A primeira publicação confirmada define o marco inicial para calcular os intervalos dos posts restantes do mesmo dia. Replanejar slots disponíveis durante a rodada.

Buffer é uma das rotas possíveis, não o único publicador. Se sua capacidade de fila impedir o processamento de todos os cortes, encaminhar os excedentes apenas a outra rota oficialmente permitida, autenticada, independente e já comprovada, com ledger compartilhado, deduplicação, fencing e reconciliação. Nunca transferir uma entrega Buffer agendada, iniciada ou incerta para outra rota antes de verificar que não haverá postagem duplicada.

Limites obrigatórios das plataformas continuam válidos entre rotas; outro executor não concede publicações além do que o LinkedIn permite. Se não houver capacidade lícita suficiente, manter o arquivo e abrir incidente QA de prioridade máxima com razão `BLOCKED_SAME_DAY_CAPACITY`, quantidade afetada e data original. O corte NÃO pode ser tratado como publicado, nem rolar silenciosamente para o dia seguinte. O descumprimento configura falha explícita do SLA, mesmo quando a mídia é preservada.

Work, Claude Code, Kilo, OmniRoute, 9Router e Anthares Browser são recursos de operação e automação, não quotas adicionais. A publicação ordinária deve ocorrer em serviços fora do computador do proprietário. O Anthares Remote do PC permanece apenas como diagnóstico/redundância passiva; não publicar por essa máquina.

### Estado de execução

O consumidor LinkedIn GitHub-hosted e o segredo Buffer já estão implementados. A fila Neon e o resultado real precisam confirmar entrega; a existência de um workflow de sucesso ou de um agendamento Buffer não prova vídeo publicado no LinkedIn. Não alegar 100 posts/dia sem evidências de capacidade e publicações efetivas.

## Testes
`python -m unittest discover -s tests -p test_buffer_linkedin.py -v` e `python -m unittest discover -s tests -p test_media_model.py -v`; completamente sintéticos.

## Referências
- https://developers.buffer.com/guides/authentication.html
- https://developers.buffer.com/guides/your-first-post.html
- https://developers.buffer.com/examples/create-video-post.html
- https://support.buffer.com/articles/using-linkedin-with-buffer-K7tRkGD3mH
