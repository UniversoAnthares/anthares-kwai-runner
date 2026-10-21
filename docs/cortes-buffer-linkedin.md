# CORTES → Buffer → LinkedIn (20 cortes/dia)

STATUS: SOURCE_READY / BUFFER_CHANNEL_AND_API_KEY_PENDING
DATE: 2026-10-20

## Objetivo
Publicar cortes curtos na página corporativa do LinkedIn **Universo Anthares** via integração autorizada do Buffer, sem aguardar a aprovação da Community Management API do app próprio. A permissão para a página é obtida pelo OAuth do próprio Buffer, não por login automatizado do LinkedIn. Destino corporativo existente: https://www.linkedin.com/company/145345334/ .

## Pré-requisitos externos
1. Acessar https://publish.buffer.com/settings/channels na sessão do proprietário e conectar **LinkedIn Page Universo Anthares** (não o perfil pessoal). Fazer a autorização OAuth no LinkedIn pelo perfil Super Admin da página. Antes desta implementação, o Buffer possuía **0/3 canais conectados**.
2. Acessar https://publish.buffer.com/settings/api , criar chave da API Buffer e **armazená-la no Anthares Secrets / secret store do executor como BUFFER_API_KEY**. Nunca compartilhar a chave por mensagens ou copiá-la para código/GitHub/CI.
3. Ler canais via GraphQL API autenticada para confirmar `name=Universo Anthares`, `service=linkedin` e `externalLink` correspondente à página; injetar seu ID real como `BUFFER_LINKEDIN_CHANNEL_ID`. Nunca adivinhar o ID.
4. Configurar `ANTHARES_SOCIAL_COMMIT=1` **somente** no executor autorizado com fencing e ledger/lease ativos. Não expor a chave no frontend do Buffer/WordPress.
5. Verificar agendamento, publicação efetiva e URL do post público em cada ciclo. Buffer API retorna ID de agendamento, não prova de publicação no LinkedIn.

## Adaptador de publicações
`social_adapters/buffer_linkedin.py` recebe JSON validado em stdin. Sem `ANTHARES_SOCIAL_COMMIT=1`, devolve DRY_RUN e não consulta rede. Requer mídia HTTPS *.mp4 em domínio `anthares.us` e título não vazio; valida intervalo 30–90s quando informado e página do LinkedIn estritamente. O texto da legenda começa pelo título terminado em ` ● Universo Anthares` e contém `www.anthares.us`, preservando hashtags.

Após validar conta/chave/canal, a API Buffer recebe `createPost` com `assets.video.url`, `schedulingType=automatic` e `mode=addToQueue`. Resultado bem-sucedido é `SCHEDULED_IN_BUFFER`, com ID Buffer e `requires_linkedin_readback=true`. Não marcar `confirmed` no Neon neste estágio: aguardar post `sent` + URL do LinkedIn. Falhas de criação são `UNCERTAIN_OR_REJECTED` sem novo envio automático, para não criar duplicações.

## Limites e agenda
LinkedIn: teto de 20 por dia/conta da política CORTES, já aplicado no backend da fila Neon. No plano Buffer Free, máximo de dez posts **na fila por canal de uma vez**; a reposição deve ser feita após vagas liberadas, respeitando horários, API rate limits e políticas contra spam. Não agendar 20 publicações simultaneamente.

## Integração operacional pendente
O adapter é uma peça isolada em repositório. **Não há consumidor automático Buffer/Neon habilitado nem secret armazenado confirmado.** É necessário conectar o producer, o consumidor, a reconciliação e o cron ao pipeline real com fencing. O projeto continua aceitando publicação oficial direta futuramente, sem trocar a identidade do destino.

## Testes
`python -m unittest discover -s tests -p test_buffer_linkedin.py -v` e `python -m unittest discover -s tests -p test_media_model.py -v`; completamente sintéticos.

## Referências
- https://developers.buffer.com/guides/authentication.html
- https://developers.buffer.com/guides/your-first-post.html
- https://developers.buffer.com/examples/create-video-post.html
- https://support.buffer.com/articles/using-linkedin-with-buffer-K7tRkGD3mH
