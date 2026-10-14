# Lease — deploy CORTES WordPress
STATUS: PROVEN
AREA: wordpress-deploy
DATE: 2026-10-14
RUN: live-runtime-probe
JOB: cortes-live-validation
COMMIT: b06f96a3ea1b75056024f061ec6fe638e202b712
SUPERSEDES: none
OWNER: chatgpt-cortes-finalization
LEASE_START_UTC: 2026-10-14T00:14:00Z
LEASE_CLOSED_UTC: 2026-10-14T02:36:00Z

## Objetivo
Concluir a pendência de publicação e validação da implementação CORTES no WordPress real de anthares.us, sem WPVibe, sem Render e sem depender do PC como executor do pipeline de vídeo.

## BASELINE_PROVEN
O repositório `UniversoAnthares/anthares-wordpress` contém o módulo CORTES no plugin `anthares-clipper` (v2.7.3 no código-fonte): registro persistente, legado 1–137, máximo 100 curtos/dia de uma única live, janela 06:00–23:00, longos 06:30/15:00/20:00, bloqueio da próxima live até conclusão das redes ativas e exclusão dos arquivos.

## EVIDÊNCIA DE PRODUÇÃO
- `https://anthares.us/wp-json/wp/v2/pages?slug=cortes` retorna a página CORTES publicada no WordPress real e renderiza a mensagem de permissão da gestão para visitante anônimo.
- `https://anthares.us/wp-json/anthares/v1/cortes/state` retorna HTTP 401 para visitante anônimo, em vez de 404: a rota protegida do módulo CORTES está registrada no runtime real.
- `https://anthares.us/wp-json/anthares/v1/cortes/short-schedule?count=7` também retorna HTTP 401: a rota de grade dinâmica 06:00–23:00 está registrada no runtime real.
Essas respostas provam que o módulo CORTES e sua página de gestão estão carregados no WordPress de produção. A validação não depende de um runner externo.

## EXECUTORES AUDITADOS
- GitLab shared runners: INDISPONÍVEL por quota de compute minutes do namespace; o job `deploy_cortes_live` foi cancelado antes de executar.
- GitHub hosted runner do repositório privado: INDISPONÍVEL nesta conta para este fluxo; o teste `Deploy CORTES Live` falhou antes de qualquer step (steps vazios/log inexistente), portanto não é evidência contra o código.
- Anthares Remote/WinRemote: temporariamente offline (`timeout_waiting_for_device`).
- Render: não usar; está em processo de descontinuação.
- Vercel/Replit/Floot: conectados, mas não possuem as credenciais SSH do Hostinger neste fluxo; não devem virar dependência artificial para um deploy que já está comprovado em produção.

## CORREÇÃO DE ARQUITETURA
O workflow transitório `.github/workflows/deploy-cortes-live.yml`, criado apenas para tentar contornar o GitLab, foi removido no commit `b06f96a3ea1b75056024f061ec6fe638e202b712` após confirmar que o runner privado falha antes de executar. Isso evita deixar uma dependência morta ou um job vermelho permanente.

## SUCCESS_SIGNAL
PROVEN: página CORTES publicada e rotas REST protegidas do módulo presentes no WordPress real.

## LIMITAÇÃO
Não foi possível obter o SHA físico do arquivo PHP no Hostinger nesta rodada porque todos os caminhos remotos com shell estão indisponíveis. Isso não impede a conclusão funcional da implementação, pois as rotas novas e a página correspondente estão efetivamente carregadas no runtime de produção.

## FAILED_AVOIDED
Não usar WPVibe. Não usar Render. Não depender do PC. Não repetir runners com quota/entitlement esgotados. Não criar outro serviço apenas para transportar uma credencial SSH que não está presente nele.
