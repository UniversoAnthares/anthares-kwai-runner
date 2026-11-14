# AGENTE 05 — recuperação segura de autenticações Kwai no SpawnDroid
Data: 2026-11-14
STATUS: SOURCE_STAGED / OFFLINE_PROVEN / ANDROID_REAL_UNVERIFIED
Proprietário: Agente 05, artefatos novos exclusivamente.
Custo real de sessões neste trabalho: 0 minutos; sem upload, login ou publicação.

## Fontes oficiais consultadas
- SpawnDroid Core concepts: https://docs.spawndroid.io/docs/concepts/
- SpawnDroid CI/Appium stable hub: https://docs.spawndroid.io/docs/ci-tests/
- SpawnDroid API: https://docs.spawndroid.io/docs/api/
- SpawnDroid Hobby e retenção: https://docs.spawndroid.io/docs/plans/
- Kwai BR: https://www.kwai.com/pt-BR/support/account/como-recuperar-conta

O SpawnDroid declara que cada runner é um contêiner isolado e destruído
quando a sessão termina. A API pública documenta persistência de artefatos
e históricos de testes, mas nenhuma API de snapshot de /data/data, restauração
de app data ou clonagem de estado autenticado entre runners. A persistência
de login após destruir o runner é INCOMPATÍVEL com o contrato documentado
até prova adicional formal do fornecedor.

Hobby: 200 device-minutes/mês por pessoa, 1 dispositivo concorrente,
até 15 min por sessão, reaper após 3 min sem atividade; ao esgotar retorna
HTTP 402; corrida por slot retorna 429; APK expira após 7 dias.

API oficiais do provedor:
- Stable WebDriver Hub: POST/DELETE /wd/hub/session, Appium 3 UiAutomator2;
- GET /api/v1/sessions/:id para verificar estado, DELETE para teardown;
- POST /api/v1/sessions com Idempotency-Key no modo API versionada;
- GET /api/apps, GET /api/sessions para cadastro e auditoria de execução.

O Kwai BR documenta login por telefone com código, e caminhos de
autenticação de terceiro condicionados ao vínculo da conta. Um OTP,
CAPTCHA, MFA, aprovação de dispositivo ou recusa de segurança requer
intervenção legítima do titular. Não há autorização aqui para automatizar
desafios ou transportar credenciais do Android físico para o cloud.
A API OAuth de open.kuaishou.com tem escopos de publicação documentados
para o serviço Kuaishou; falta prova de elegibilidade/autorização dessas
duas contas Kwai brasileiras. Não usar como rota de produção.

## Estratégias, em ordem
1. Persistência oficialmente suportada pelo SpawnDroid: não documentada.
2. Renovação automatizada oficial: ainda não comprovada nas duas contas BR.
3. Login UI oficial em sessão nova: suportado condicionalmente, após
   autorização específica, identidade verificada e sem desafios humanos.
4. Login assistido: estado NEEDS_HUMAN, sem envio.
5. Android cloud realmente persistente: alternativa arquitetural,
   pendente de host gratuito, aprovação e duas provas reais.

## Contrato implementado
- tools/kwai_spawndroid_session_recovery.py
- tests/test_kwai_spawndroid_session_recovery.py
- .github/workflows/kwai-spawndroid-session-recovery.yml

O coordenador recebe o identificador real do WebDriver em memória; grava
somente fingerprint SHA-256 em DurableStore externo. Usa CallbackCASStore
para integrar ao read/CAS da autoridade já existente (Neon/controle),
sem criar novas credenciais. InMemoryStore é proibido em production=True.
As contas usam chaves de CAS distintas.

Integração exigida no publicador que possuir o lock:
  1. Antes de provisionar: preflight(account, queue_clean, quota_available).
  2. O Agente 02 inicia a sessão do Appium e valida package/teardown;
     o Agente 03/04 injeta probes e login UI oficial por conta.
  3. verify_new_session(account, package, session_id, ...). Só READY após
     perfil autenticado correto e recurso de upload disponível.
  4. Imediatamente antes de enviar cada mídia:
     assert_publishable(account, session_id, queue_clean).
  5. Se o comando de publicação iniciou e o efeito é duvidoso:
     mark_uncertain(...), reconciliar pela fila canônica/recibo público.
  6. Em finally, finalizar Android por API oficial e CONFIRMAR estado terminal;
     somente então confirm_teardown(provider_terminal=True).
  7. Qualquer challenge, mismatch, expiração ou falha de quota bloqueia;
     nunca disparar uma segunda sessão após teardown sem prova.

Não confiar em retorno READY offline como login real; o adapter identity_probe
precisa obter usuário e indicador de login na UI oficial, com readback novo.
Não salvar XML bruto, telas de login ou dados de autenticação em logs.
Não transferir tokens/browser cookies entre Kwai e Kwai Lite.

## Estados e comportamento
READY: sessão, pacote, conta, validade e uploader verificadas; somente esta
sessão poderá publicar após conferência do ledger.
NEEDS_HUMAN: interromper e solicitar interação do titular no fluxo oficial.
AUTH_DENIED/AUTH_REVOKED/AUTH_EXPIRED: bloquear; respeitar motivo e política.
NEEDS_HUMAN, AUTH_DENIED, AUTH_REVOKED, AUTH_EXPIRED e IDENTITY_MISMATCH
continuam bloqueados mesmo após teardown confirmado; desbloqueio exige
procedimento explícito na autoridade canônica e nova verificação oficial.
IDENTITY_MISMATCH: bloquear para evitar publicação em conta trocada.
UPLOAD_UNAVAILABLE: autenticação pode existir, publicação segue suspensa.
QUOTA_BLOCKED: cancelar tentativa própria, confirmar término; não fazer retry
em quota compartilhada, sem reserva independente apta.
PROVIDER_UNAVAILABLE: não criar novas sessões até saúde confirmada.
TEARDOWN_UNVERIFIED: reconciliar o dispositivo anterior antes de outro boot.
RECONCILE_REQUIRED: impedir segundo envio até ledger/efeito externo reconciliado.
SESSION_REUSED, SESSION_UNVERIFIED, EVIDENCE_EXPIRED, CAS_CONFLICT: bloquear.

## Homologação
CI offline: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43596415580
26 testes aprovados (prova do contrato, não do Android real).

Aceite real ainda exige, SEPARADAMENTE, para cada conta:
- APK de procedência assinada cadastrado, saldo gratuito confirmado,
  ausência de agente concorrente e autorização explícita dos Agentes 02–04;
- sessão A com identidade autenticada, capacidade de upload verificada,
  teardown e GET terminal no provedor;
- sessão B nova com reautenticação pelo fluxo oficial ou persistência
  oficialmente atestada; identidade readback, capacidade de upload;
- fechamento seguro da sessão B sem divulgação de segredo;
- reconciliação e prova independente antes de qualquer publicação de teste.

O cutover para cloud permanece DESABILITADO; não modificar
KWAI_PERSISTENT_CLOUD_PUBLISH_ENABLED, cloud_cutover.enabled ou as filas.
