# AGENTE 05 — Autenticação e recuperação de sessões no SpawnDroid
Data: 2026-11-14
Estado: GATE DE SEGURANÇA EM BRANCH, HOMOLOGAÇÃO DE AUTENTICAÇÃO REAL PENDENTE
Escopo: Kwai @universoanthares / com.kwai.video; Kwai Lite @lucasrosalem / kwai.lite.video.

## Evidências verificadas
1. SpawnDroid declara que o contêiner Android, os dados dos aplicativos e a identidade do dispositivo são descartados ao fechar cada sessão. A documentação não oferece API de snapshot/restauração oficial entre runners. A capacidade Appium noReset não constitui estado persistente entre runners. Fontes: https://spawndroid.io/security/ ; https://docs.spawndroid.io/docs/concepts/ ; https://docs.spawndroid.io/docs/guides/appium-capabilities-android/ .
2. O SpawnDroid oferece APIs oficiais para listar/consultar/encerrar sessões e para UiAutomator2 (WebDriver). Essas APIs autorizam operação do runner, não login nas contas Kwai: https://docs.spawndroid.io/docs/api/ .
3. O Kwai documenta login por telefone e código de verificação, canais de terceiros quando vinculados e proteção de login para novos dispositivos. OTP/MFA/CAPTCHA devem permanecer sob controle do titular: https://www.kwai.com/pt-BR/support/account/como-recuperar-conta ; https://www.kwai.com/pt-BR/safety/controls .
4. O cofre existente de Cloudflare KV + GitHub OIDC armazena bytes cifrados de sessão de uma implementação anterior. Test Hub 20261010-2028 comprovou persistência de canário entre runs, enquanto 20261010-2029 registrou ausência de autenticação Kwai válida no cofre. A prova 20261016-f17 vale para reinício do MEmu4, não para SpawnDroid descartável.
5. Documentação de limites do Hobby diverge (visões de 200 e 500 device-minutes). O site atual https://spawndroid.io/pricing/ afirma 200 minutos, 1 runner e sessão de 15 minutos. O saldo efetivo da organização só pode ser confirmado na conta; nenhum consumo foi autorizado por esta etapa.
6. Governança de 13/11 fixa custo incremental R$0 e cloud_cutover.enabled=false. Preservar publicador físico e MEmu até aceite independente. Não reativar Oracle, CutMotions ou rota Kuaishou para contas brasileiras.

## Comparação de estratégias
| Prioridade | Estratégia | Segurança/compatibilidade | Custo | Confiabilidade nesta implantação |
|---|---|---|---|---|
| 1 | Persistência/snapshot oficial SpawnDroid | Não documentado/disponibilizado publicamente; contêiner destruído | Sem nova despesa comprovada | INELEGÍVEL até contrato oficial |
| 2 | Renovação por OAuth/refresh autorizado do próprio Kwai | Nenhum endpoint de refresh/publish para estas contas brasileiras foi homologado | Desconhecido | INELEGÍVEL até autorização explícita do serviço |
| 3 | Novo login pelo fluxo nativo, acionado via Appium | Permitido somente se o serviço aceitar automação e todos os fatores forem atendidos legitimamente; identidade deve ser revalidada | Minutos Hobby | EM ESPERA de Agentes 03/04 |
| 4 | Recuperação assistida pelo titular | Segura, observa MFA/OTP/CAPTCHA e confirmações de dispositivo | Minutos Hobby dentro da quota | FAIL-CLOSED IMPLEMENTADO no contrato |
| 5 | Executor Android remoto com armazenamento persistente | Exige host e login previamente homologados, reboot e isolamento reais | R$0 obrigatório | PENDENTE de infraestrutura elegível |

## Módulo implementado
Arquivo: tools/kwai_spawndroid_auth_recovery.py.

A função decide(...) recebe exclusivamente metadados e prova de interface produzida pelo controlador confiável na sessão Appium ativa. Não acessa secrets, Cloudflare KV, cookies, Android /data, OTP ou APIs não autorizadas. Não escreve arquivos de estado, não chama SpawnDroid e não publica.

Entrada:
- account deve ser universoanthares ou lucasrosalem; package deve corresponder ao aplicativo designado;
- session_id do runner real em estado ready;
- ledger_state é um resultado normalizado do Neon canônico: idle/settled somente após constatação real de ausência de publicação pendente; demais estados implicam RECONCILE_REQUIRED;
- observation.source = appium_live, observation.session_id igual ao runner atual, foreground_package correto, profile_handle exato, owner_edit_control verdadeiro, publisher_entry_visible verdadeiro, observed_at_epoch inteiro recente (até 120 segundos);
- failure contém apenas código sanitizado, se houver. Nunca enviar valores de segredo, XML completo nem screenshots à ferramenta.

Resultado:
- AUTHENTICATED_CURRENT_SESSION autoriza somente prosseguir para o controle existente de lease e CAS. publication_authorized e cloud_cutover_authorized permanecem sempre false.
- AUTH_REQUIRED, REAUTH_REQUIRED ou HUMAN_REQUIRED exigem fluxo oficial de login ou confirmação legítima. O controlador mantém a tarefa na fila até receber nova prova.
- SECURITY_BLOCKED para 403; RUNNER_SLOT_BUSY para concorrência 429; QUOTA_CANCEL_REQUIRED para 402, exigindo cancelamento e comprovação terminal do job pelo adaptador real; SESSION_UNCERTAIN para timeout, impedindo nova sessão até leitura de Runs.
- RECONCILE_REQUIRED para publicação iniciada/incerta, inclusive entre sessões e contas; não lançar reenvio sem prova externa e autorização CAS.
- Prova velha de um runner anterior sempre é rejeitada. Mesmo que a conta tenha sido autenticada anteriormente, cada novo contêiner requer observação nova e exata.

Os metadados de sessão e validade pertencem à infraestrutura existente de controle/Neon, com scope por conta e sessão e retenção da fila canônica. Este módulo não cria um cofre e não emite credenciais. O consumidor deve registrar: account, package, session_id, observed_at_epoch, validade de 120 segundos, status, motivo, geração de lease, idempotência e referência de evidência, sem dados privados. O programa não substitui a assinatura das evidências pelo controlador que as obtém.

## Integração e concorrência
Agentes 03 e 04 continuam donos dos logins e das primeiras publicações. Ao homologarem o WebDriver de cada aplicativo, devem produzir observação sem dados privados e chamar decide(...) antes de qualquer reserva/publicação. Um retorno positivo só habilita a entrada na lógica já existente de Neon: verificação do job, lease_generation, CAS, horário e mídia. Publicação/ACK devem permanecer exclusivamente nos executores canônicos. O contrato Agent 05 não altera tools/kwai_spawndroid_stable_hub.py, os workflows dos Agentes 01–04, a fila de produção, o cofre antigo nem os dispositivos existentes.

## Homologação
A CI dedicada executa testes OFFLINE para as duas identidades, duas sessões sucessivas por conta, prova cruzada, expiração, logout/revogação, fatores humanos, falhas 401/402/403/429/5xx, indisponibilidade e jobs incertos. A aprovação de CI comprova política de bloqueio, não recuperação real do login.

Aceite REAL exige:
1. SpawnDroid Hobby com saldo e quota verificados, app oficial instalado e execução reservada no Test Hub.
2. Agente 03 prova login real em @universoanthares no primeiro runner e encerramento terminal; Agente 04 faz o mesmo em @lucasrosalem com Kwai Lite.
3. Novo runner limpo para cada conta, autenticação renovada exclusivamente por mecanismo oficial ou intervenção autorizada, seguido de readback Appium do perfil exato e da entrada de publicação.
4. Registro do mecanismo e custo, da identidade e da prova de duas sessões distintas. Falha de autenticação por controle do serviço implica HUMAN_REQUIRED/SECURITY_BLOCKED e bloqueio seguro; não declarar recuperação automática.
5. Nenhum vídeo real sem aprovação do canônico controle editorial e de publicação. Não executar novos canários enquanto os Agentes 01–04 e o Test Hub não liberarem sessões.

Resultado arquitetural presente: sessão descartável não permite prometer login persistente; bloqueio por conta, sessão e reconciliação encontra-se implementado em branch de integração, dependente de adoção pelo controlador e de prova operacional.
