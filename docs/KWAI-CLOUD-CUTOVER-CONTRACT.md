# Kwai — transição definitiva do Android físico para Android em nuvem
Data: 2026-11-13. Autoridade de roteamento: `ci-hub/executor-routing.json`.

## Objetivo e estado atual

Executar a publicação de CORTES nas duas contas Kwai de forma persistente, independente do Android físico e do computador, com custo incremental R$ 0 e integridade da fila Neon. O mecanismo de publicação deve continuar usando o app oficial Kwai/Kwai Lite, com identidade de conta comprovada e horários de 06h até 23h (fuso da operação). A aplicação web do Kwai e a emulação GitHub Actions **não são publicadores homologados**.

Estado: Oracle OCI A1 no monitor automático, mas a capacidade consultada apresentou `OUT_OF_HOST_CAPACITY` e `TARGET_INSTANCE=NONE` no run #43472721346. ReDroid tem cloud-init/checagem ADB preparados; Android remoto com Kwai autenticado permanece pendente. Enquanto isso, o Android físico publica em produção. Nenhuma alteração deste contrato equivale à existência de uma VM nem a uma publicação.

## Contrato de migração protegida

`cloud_android_verified` aparece em primeiro no array de prioridades do manifest, porém o guard `android_execution.cloud_cutover.enabled=false` bloqueia sua seleção por padrão. O seletor ignora declarações `ready=true` enviadas por um runtime sem o guard de repositório. O Android físico e o MEmu4 mantêm suas posições durante a preparação.

Para autorizar uma futura mudança explícita no repositório de `cloud_cutover.enabled` para `true`, obter evidência independente e atual para TODOS estes itens:

1. `android_ready`: host Linux real, persistentemente acessível, Android/ReDroid/ADB locais funcionais.
2. `official_apps_authenticated`: Kwai e Kwai Lite instalados, login e identidade positiva das contas `lucasrosalem` e `universoanthares`.
3. `sessions_survive_reboot`: app, login, armazenamento e serviço Android funcionam após reinicialização do host, sem PC.
4. `independent_public_readback`: publicação efetiva de um vídeo autorizado em cada conta, comprovada por leitura independente das páginas públicas com links e IDs externos, após a integração segura com fila.
5. `neon_fencing_verified`: `lease_generation`, identidade de tarefa e idempotência registrados e respeitados; jobs `STARTED/UNCERTAIN` são reconciliados antes de qualquer tentativa.
6. `schedule_06_to_23_verified`: alocação diária proporcional à quantidade de cortes restantes, até as 23h, conforme regra de produção.
7. `host_independent_of_pc`: execução efetivamente remota; o PC e Android físico desligados não impedem o serviço.
8. `cost_zero_confirmed`: plano e recursos autorizados sem cartão adicional, cobrança ou Pay As You Go.

O estado remoto fornecido ao seletor deve declarar `online`, `healthy`, `ready`, `authenticated` estritamente verdadeiros, `verified_accounts` contendo exatamente ambas as contas e `proofs` com todos os oito itens verdadeiros. Também exige `observed_at_epoch` como timestamp Unix numérico recente (idade de 0 a 120 segundos), evitando promoção com status cacheado ou de execução anterior. Esse estado não substitui a validação humana/técnica necessária para alterar o guard versionado.

Depois do corte autorizado, `disable_local_executors=true` proíbe fallback silencioso para o Android físico ou MEmu4: se o Android remoto cair, o seletor informa `NONE` e a fila deve permanecer íntegra até haver capacidade remota. Não repetir tarefa com publicação iniciada.

## Pendências concretas de execução

- Conseguir host Android remoto gratuito e persistente, com kernel binder e acesso suficiente para o ReDroid; Oracle A1 continua em tentativa automática, terceiros ainda sem prova.
- Instalar, autenticar e preservar Kwai/Kwai Lite, MacroDroid ou Anthares Android Agent; comprovar a execução do fluxo real de upload em ambas as contas.
- Ligar o novo executor ao controlador e à fila Neon, verificar fencing, intervalos e comprovação externa de publicação.
- Verificar autonomia de rede e reboot, aprovar as oito evidências e só então promover `cloud_cutover.enabled` no repositório e descontinuar os dispositivos físicos.
- Avaliar os demais processos CORTES, lives e controle para dependências restantes do PC, de modo independente do corte Kwai.

A aprovação dos testes unitários de roteamento confirma exclusivamente que o código respeita esse bloqueio. Nenhum teste simulado de Android ou vídeo autoriza o corte.
