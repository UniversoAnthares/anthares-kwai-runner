# CORTES — Pinterest e LinkedIn: habilitação segura

STATUS: SOURCE_READY / LIVE_AUTH_PENDING
DATE: 2026-10-20

## Regra editorial universal
Para títulos futuros em todas as redes: terminar literalmente com ` ● Universo Anthares`. Função idempotente: `anthares_publisher.editorial.branded_title`. Sempre que a plataforma oferecer descrição, hashtags, palavras-chave ou tags, incluir também o texto literal `www.anthares.us`. A URL tem pontos e portanto deve ficar como texto ou link, jamais tentar convertê-la integralmente numa única hashtag. Manter outros termos relevantes.

As adaptações implementadas neste PR abrangem os scripts Python de TikTok (cloud), Instagram, Kwai físico e o adaptador existente Instagram/Threads/X, além dos dois novos publicadores Pinterest/LinkedIn. Publicadores fora desses pontos de integração, especialmente a emissão do WordPress para YouTube/Facebook e rotas adicionais, precisam de validação separada antes de declarar conformidade universal em produção.

## Política de distribuição
- Pinterest: todos os masters curtos elegíveis de cada rodada por conta (limite lógico ausente, `daily_limit=None` no modelo; fila Worker v17: `Number.MAX_SAFE_INTEGER`). Respeitar limites API/conta, 429 e condições anti-spam; bloquear com `BLOCKED_PLATFORM_LIMIT`, preservar item e fazer reconciliação antes de repetir.
- LinkedIn: máximo de 20 cortes curtos confirmados por dia por conta. A fila separa `platform+account_id`, leases e dedupe.
- Duração dos masters curtos: 30–90 segundos, conforme política canônica 2026-10-13. Reutilizar checksum, sem segundo corte por rede.

## Pinterest — pré-requisitos
1. Conta Pinterest com quadro de destino, app autorizado para API v5 e permissões `boards:read`, `boards:write`, `pins:read`, `pins:write`.
2. Injetar `PINTEREST_ACCESS_TOKEN` e `PINTEREST_BOARD_ID` no executor seguro. Disponibilizar `PINTEREST_COVER_IMAGE_URL` https ou `cover_image_url` por job; URL https do MP4 ou `media_path`.
3. O adaptador registra mídia, envia MP4 ao endereço presigned do Pinterest, espera `succeeded`, cria o Pin no quadro e verifica ID remoto independentemente.
4. Não marcar publicada quando faltar board/capa/token, ocorrer 429, ou o upload/POST estiver incerto. Registrar UNCERTAIN e reconciliar. Cada Pin deve incluir título com sufixo, descrição com domínio e link para `https://www.anthares.us`.

## LinkedIn — pré-requisitos
1. App e conta administradora da página ou membro autor. Conceder `w_organization_social` ou `w_member_social` conforme identidade. Releitura independente dos posts pode exigir permissão de leitura adicional aprovada.
2. Injetar `LINKEDIN_ACCESS_TOKEN` e `LINKEDIN_AUTHOR_URN` (`urn:li:person:...` ou `urn:li:organization:...`) no executor autorizado. Versão padrão do cabeçalho `LINKEDIN_API_VERSION=202606`.
3. Adaptador chama `videos?action=initializeUpload`, faz PUT de cada segmento, finaliza usando ETags, aguarda vídeo AVAILABLE, cria post orgânico com título/caption e verifica ID remoto.
4. Respeitar 20 confirmações por dia e bloqueios da API. Não compartilhar token nem assumir perfil/página.

## Operação / gates
Executar `python social_adapters/direct_social.py` com JSON validado em stdin. Sem `ANTHARES_SOCIAL_COMMIT=1`, retorna READY ou AUTH_OR_CONFIG_REQUIRED (sem publicar). A execução real exige consumer autenticado com lease/fence, estado STARTED imediatamente antes do passo irreversível, reconciliação após UNCERTAIN e callback de confirmação central por remote_id. O adaptador isolado *não é* executor da fila e não elimina esses gates.

PR e CI com testes sintéticos são prova somente de implementação. Falta comprovar autorização OAuth de ambas as plataformas, identificação de conta/quadro/página, configuração de secret store e primeira publicação remota com URL/id conferidos.

Documentação das APIs:
- https://developer.pinterest.com/docs/work-with-organic-content-and-users/create-boards-and-pins/
- https://developer.pinterest.com/docs/reference/rate-limits/
- https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api
- https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
