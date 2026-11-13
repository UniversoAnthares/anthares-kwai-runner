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

**Estado atualizado em 13/11/2026:** o código atualizado das duas rotas foi implantado na função Neon `cortesqueue`, branch `br-crimson-unit-b89nau08`, deployment de produção **#74 (completed/active)**. O deployment **#8** da branch QA `br-silent-mud-b8fzvqta` também foi concluído e respondeu `ok=true`, `database_ok=true`. A identidade `kwai-persistent-cloud` continua bloqueada por flag/token desativados; nenhum token remoto foi criado, nenhum ReDroid ou postagem de teste foi ativado. Próximas pendências: obter executor real gratuito autorizado, autenticar duas contas, provas independentes e cutover explícito. A implantação do código NÃO equivale à ativação do publicador.

## Atualização operacional — 13/11/2026 após reconciliação

- As três publicações anteriormente em `uncertain`, `started` e `cancelled` foram comprovadas por seis quadros SIFT cada, reconciliadas como `confirmed` no Neon e reconhecidas como `completed` pelo WordPress; resta **0** tarefa `started` ou `uncertain` nas duas contas. Provas: [run #43516677494](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43516677494) e `test-hub/findings/20261113-kwai-three-posts-confirmed-oneoff-revoked-neon76.md`.
- A autorização temporária do workflow OIDC foi revogada no PR #2590 e implantada em Neon `cortesqueue` **produção #76 (completed/active)** e **QA #10 (completed/active)**. Identidade cloud ReDroid permanece desativada até servidor real e provas específicas.
- A função de produção está localizada no projeto Neon `anthares-ara-ha` `purple-flower-35918989`, branch `br-crimson-unit-b89nau08`. O antigo diagnóstico de falta de acesso está obsoleto.
- **RLS continua pendente:** `cortes_publications` tem `relrowsecurity=false`, `pg_policies=[]`; a função utiliza `DATABASE_URL` com papel administrativo e o health declara `UNPROVEN_SQL_ROLE_AND_RLS_SCOPE`. A migração de função/credenciais/políticas exige segregação em QA antes de qualquer implantação de política SQL de produção.
- Custo incremental R$0; Oracle, CutMotions, fornecedores pagos e novos pedidos dependentes de aprovação continuam descartados. Os publicadores atuais permanecem em operação, `cloud_cutover.enabled=false`.

## Pacote de implantação auditável

O workflow `.github/workflows/kwai-neon-persistent-cloud-bundle.yml` compila `kwai-neon-function-bundle.zip` contendo `index.mjs`, `kwai-pacing-policy.mjs` e `kwai-persistent-cloud-identity.mjs` no mesmo diretório. Os imports relativos são preservados, com SHA-256 do arquivo e testes Node. O ZIP é artefato de GitHub Actions por sete dias. Essa etapa é somente build: não usa chave de produção, não modifica a Function e não autoriza dispositivo.

**Acesso corrigido e comprovado em 13/11/2026:** `cortesqueue` está no projeto Neon `anthares-ara-ha` (`purple-flower-35918989`), branch main `br-crimson-unit-b89nau08`, endpoint `br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech`. `list_functions` revelou versão de produção 73; `deploy_function` aplicou o pacote de fonte da `main` (três módulos) mantendo as variáveis de ambiente existentes, resultando em deployment **74 completed/active**; GET `?action=health` retornou `ok=true`, `database_ok=true`. Consulta SQL read-only antes/depois confirmou totais idênticos para ambos os perfis: principal 606 confirmados, 16 queued, 2 uncertain, 14 failed e 2 cancelled; secundária 47 confirmados, 52 queued, 1 started, 1 failed e 5 cancelled. Ambiente atual continua reportando `network_isolation=false`, `rls_attested=false`; essas propriedades permanecem pendentes de comprovação e devem impedir qualquer afirmação de RLS validado. Nenhuma publicação, lease ou alteração em registros da fila foi realizada por este deploy.
