# Ponte Neon para Android persistente em nuvem — preparado, desativado
Data: 13/11/2026. Fluxo de produção existente preservado.

## Problema corrigido no código
O serviço Neon autorizava o publicador primário do GitHub por token OIDC transitório e o dispositivo físico/Redmi por identidades próprias. A conta secundária tinha permissão somente para Android físico e Redmi. Uma VM ReDroid permanente não poderia receber leases nem confirmar um vídeo em nenhuma das duas contas usando esses caminhos corretamente.

## Solução incorporada ao repositório
- `infra/neon-cortes-queue/kwai-persistent-cloud-identity.mjs` cria o papel `kwai-persistent-cloud` para as duas contas; restrito a lease, renew, start, confirm e fail. Nenhum acesso a enqueue, funções de administrador, recuperação especial ou outras redes.
- A nova autenticação exige `KWAI_PERSISTENT_CLOUD_PUBLISH_ENABLED=1` e `KWAI_PERSISTENT_CLOUD_TOKEN_SHA256` com o digest SHA-256 de um token aleatório de 32 bytes (43 caracteres base64url). **Ambas as variáveis permanecem ausentes/desativadas na produção até a homologação.** O token íntegro reside somente no host autorizado em `KWAI_PERSISTENT_CLOUD_TOKEN`, nunca no repositório nem em logs.
- As duas rotas da função Neon reconhecem o mesmo papel. Cada job permanece amarrado a `target_key`, `expected_account`, `lease_owner` e `lease_generation`, mais o cronograma proporcional do próprio banco.
- Ao habilitar a produção na função Neon, novas operações `kwai-lease` ou `kwai-start` do Android físico/Redmi retornam `KWAI_LOCAL_CUTOVER_ACTIVE` em ambas as contas. Renovações, confirmações e falhas de tarefas já iniciadas continuam disponíveis para a reconciliação e conclusão segura.
- `tools/kwai_persistent_cloud_queue.py`: cliente independente de GitHub OIDC com `--account lucasrosalem|universoanthares`; usa `kwai-lease|kwai-renew|kwai-start|kwai-confirm|kwai-fail`, rejeita troca de conta, exige geração de lease, não repete HTTP em caso de resposta ambígua, e grava recibo em arquivo exclusivo de permissão 0600.
- A confirmação continua exigindo prova independente com `CORTES_KWAI_INDEPENDENT_ATTESTATION_KEY` já prevista no serviço Neon. Essa chave deve permanecer fora do Android executor; o verificador de perfil público constitui uma identidade separada.

## Ativação posterior e ordem obrigatória
1. Obter VM com custo zero comprovado, isolamento e kernel compatível; instalar ReDroid/ADB local, Kwai e Kwai Lite. Comprovar login em ambas as contas, reboot e publicações independentes controladas.
2. Gerar no **servidor autorizado** 32 bytes aleatórios; manter o token só lá e configurar apenas seu SHA-256 no ambiente secreto da Neon Function, `KWAI_PERSISTENT_CLOUD_TOKEN_SHA256`. Nunca reutilizar token ou chave do Redmi 9/PC.
3. Comprovar o contrato Neon em um ambiente isolado/sem tarefas publicáveis, especialmente lease/fence e confirmação do mesmo conteúdo. Reconciliar todos os jobs started/uncertain anteriores.
4. Aprovar formalmente e alterar `cloud_cutover.enabled` na autoridade versionada, integrando o supervisor remoto à fila e registrando um heartbeat efetivo a cada 120 segundos; somente depois ativar `KWAI_PERSISTENT_CLOUD_PUBLISH_ENABLED=1` na função Neon e desabilitar o fluxo físico.
5. Validar duas publicações reais com link público e relatório da fila. Testar Android físico e PC desligados, ausência de repetição, recuperação do ReDroid e limites de 06h–23h.

**Estado:** autenticação e cliente preparados e testáveis offline, nenhum token remoto criado ou usado, nenhum host ReDroid em operação, função Neon em produção ainda não recebeu essa atualização comprovada. Não declarar item 4 operacional antes de implantação real do código, habilitação controlada e teste com o host.
