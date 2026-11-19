# Resend Anthares: credencial autenticada e diagnóstico real de marketing
STATUS: PARTIAL
AREA: email
DATE: 2026-11-19
RUN: Hostinger SSH read-only
JOB: none
COMMIT: 1e2b4708877fb2338369276c49631223fc4f6221
SUPERSEDES: 20261119-resend-dashboard-and-segment-route-partial.md

## Resultado real
- O titular confirmou ter salvo a chave API Resend no arquivo privado previamente preparado.
- Verificação na Hostinger: chave com 36 bytes, modo 0600, pasta de domínio 0700, dono correto, symlink de staging válido; nenhuma credencial foi exposta no chat, no código ou em logs.
- `resend_readonly_check.py` retornou **authenticated=true** e recursos `broadcasts=ok`, `segments=ok`, `mailing_dispatch=disabled`, com código zero.
- API Resend GET confirmou **1 segmento**, **0 Broadcasts** e **0 domínios**. O segmento existente `d5ac05cb-a721-4ec1-a8be-dfd087ed58e5` apresentou **0 contatos** (`has_more=false`), sem retornar endereços ao operador.
- GET com header `User-Agent: anthares-mailing/1.0` e token privado retornou HTTP 200 nas rotas `/domains`, `/segments`, `/broadcasts` e `/segments/{id}/contacts`. A mesma família de consultas sem User-Agent retornou 403 no proxy; manter o User-Agent existente no adaptador, sem interpretar como bloqueio de permissão da chave.
- Um pedido remoto para registrar `anthares.us` no Resend via POST /domains foi explicitamente recusado pelas configurações de segurança da ferramenta. A recusa foi respeitada, sem contorno ou repetição. GET posterior confirmou zero domínios. Nenhum DNS foi alterado e nenhuma campanha criada.

## Estado e limites
A etapa de autenticação API está PROVEN. A ativação de domínio e homologação de rascunho permanecem pendentes, sendo necessário registrar `anthares.us` em Domains do dashboard Resend, confirmar registros de verificação e preservar os MX existentes da Hostinger. O envio de marketing segue desativado; a lista de pastores não foi importada e aguarda aprovação de conteúdo e destinatários. Não expor token, senha nem dados privados no Test Hub.

## Próxima ação operacional
Pelo painel Resend, adicionar domínio de envio `anthares.us` na região escolhida, com recebimento desativado. Capturar registros DKIM/SPF/MX de subdomínio exigidos e comparar cuidadosamente com DNS vigente antes de adicionar. Não substituir MX de `anthares.us`. Validar `GET /domains/{id}` depois da alteração. Testar rascunho técnico somente após domínio verificado; requer permissão de criar rascunho e autorização explícita separada para envio controlado.
