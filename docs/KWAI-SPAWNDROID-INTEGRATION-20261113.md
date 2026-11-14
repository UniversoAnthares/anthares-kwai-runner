# Kwai — integração experimental SpawnDroid Hobby (2026-11-13)

## Escopo autorizado
- Testar um Android remoto ARM64, sem usar o computador pessoal como executor.
- Custo adicional permitido: R$ 0. Sem plano pago, cartão, upgrade ou excedente.
- Contas finais: `@lucasrosalem` (Kwai Lite) e `@universoanthares` (Kwai).
- Este teste limita-se ao pacote Kwai `com.kwai.video` já reconhecido no repositório; o pacote exato do Kwai Lite deverá ser verificado separadamente.
- O código **não publica**, **não autentica contas**, **não altera o Neon** e **não muda a seleção atual de executores**.

## Diagnóstico de arquitetura
A tenancy Oracle `lucasyahn` / `sa-saopaulo-1` teve tentativas A1 e E2 Always Free que retornaram `OUT_OF_HOST_CAPACITY`; não há VM efetivamente criada. A Hostinger corrente é conta SSH compartilhada, sem `root`, Docker, binder e KVM. Cloudflare e Neon podem coordenar tarefas, mas não emprestam dispositivos Binder à Hostinger.

SpawnDroid oferece um Android em contêiner ARM64 com API/CI, porém **descarta os dados do aplicativo ao término da sessão**. Hobby: 200 minutos/mês por pessoa, uma sessão simultânea, 15 minutos por sessão, encerramento ocioso em 3 minutos, sem excedente pago, artefatos expiram em sete dias. Isso impede tratar o serviço como substituto produtivo permanente de duas contas sem primeiro demonstrar autenticação em cada sessão e capacidade de publicação dentro da franquia.

Fontes de referência:
- https://docs.spawndroid.io/docs/api/
- https://docs.spawndroid.io/docs/plans/
- https://spawndroid.io/security/
- https://docs.oracle.com/pt-br/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## Integração adicionada
- `tools/kwai_spawndroid_probe.py`: consulta `GET /api/apps` e `GET /api/device-profiles`; só inicia Android com duas autorizações explícitas, APK já registrado e pacote exato `com.kwai.video`. A sessão de teste tem no máximo 180 segundos e é encerrada via `DELETE /api/v1/sessions/:id` no `finally`.
- `tests/test_kwai_spawndroid_probe.py`: simula API, quota esgotada, recusa de APK incorreto, chave ausente, limites e encerramento.
- `.github/workflows/kwai-spawndroid-preflight.yml`: valida contratos em PR/push e faz consulta de conta **somente mediante disparo manual**; canário requer autorização manual, artefato conhecido e confirmação do plano Hobby.
- Segredos, URL de WebDriver e cookies nunca devem ser registrados no log nem incorporados ao Git.

## Gatilhos futuros, sem usuário repetir configurações já existentes
1. Criar espaço Hobby em https://app.spawndroid.io/ com conta própria e confirmar plano `Hobby`.
2. Em `API & CI/CD → API keys`, criar chave com escopo `read` para inspeção; `upload` para o canário, caso a plataforma exija iniciar a sessão.
3. Gravar a chave como GitHub Actions Secret `SPAWNDROID_API_KEY` — nunca exibi-la no chat.
4. Verificar a procedência/assinatura do APK oficial do Kwai, carregá-lo no workspace e registrar o slug `app.slug`.
5. Rodar manualmente o workflow em `status`. O modo `canary` exige variável `SPAWNDROID_HOBBY_FREE_CONFIRMED=1`, slug registrado e autorização explícita.
6. Antes de qualquer publicação real: avaliar login da conta correta, persistência externa autorizada, carregamento do MP4, retorno público, custo e controle de duplicações.

## Critérios de interrupção
- HTTP 402 da API: quota do Hobby esgotada. Suspender.
- HTTP 429: único dispositivo ocupado. Suspender.
- Falha de encerramento: bloquear nova sessão e reconciliar manualmente na interface do provedor.
- Falta de APK autenticado ou dados descartados após sessão: reprovar o uso produtivo. Preservar o executor local até existir substituto homologado.
- Sem prova pública de publicação nas duas contas: `cloud_cutover.enabled` permanece `false`.

## Alternativas em espera
- Firebase Test Lab (cotação e execução transitória).
- Northflank + Android (restrições de kernel/memória).
- Ramus/Appetize (limites de tempo).
- APIs Kwai, apenas se houver compatibilidade demonstrada com contas brasileiras.
- Oracle mantém monitoramento/provisionamento desativados por decisão do proprietário; nenhuma nova tentativa automática.
