# Kwai APK — comprovação independente de assinatura v2 na Hostinger
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: validação server-side em Hostinger, separado dos agentes 01-07
COMMIT: 21db6c02b16915c78bbea74420c95b148e5b675d
SUPERSEDES: none
OWNER: ChatGPT item1, branch feature/spawndroid-kwai-apk-verified-upload-20261114
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## BASELINE_PROVEN
- O repositório contém 44 testes offline de guard de APK/splits, PR #2616 draft. 
- SSH Hostinger autenticado com alias autorizado 'anthares-hostinger'.
- Hostinger /home/u566597497/.anthares-spawndroid-apks/com.kwai.video contém 25 APKs, total 202108730 bytes, 25/25 SHA256 iguais aos manifestos locais.
- URL HTTPS HMAC GET comprovou 200, 12754 bytes, SHA256 idêntico para o componente dfm_ug.
- Teste real histórico com demo SpawnDroid no PC criou sess_4139ebebc97647c894, reportou HTTP 500 no execute installMultipleApks e terminou com terminated_confirmed=true, published=false. Não repetir sem correção causal.
- Verificação APK original integral com 'apksigner' no runner cloud ainda não comprovada.

## FAILED_AVOIDED
Não baixar APKs novamente no PC; não recombinar nem reassinar; não copiar HMAC secret para repositório; não repetir instalação que terminou HTTP500; não iniciar sessão Android nova; não usar quota paga.

## SUCCESS_SIGNAL
Código específico que verifica a cadeia de assinatura v2 do APK (certificado do publicador, assinatura criptográfica signedData e content digest sobre 3 seções protegidas), testado com APKs verdadeiros já armazenados na Hostinger, sem instalar Android. Resultado por arquivo com hash e cert oficial, sem segredos no log.

## FAILURE_SIGNAL
Qualquer APK não contém bloco v2, assinatura inválida, SHA divergente, consumo excessivo de CPU, ambiente sem dependência criptográfica; parar e registrar limitação.

## TEST_VALIDITY
Auditoria independente criptográfica deve ser comparada com apksigner de Google posteriormente. Mesmo com assinatura v2 correta, ainda falta aceitar o comando installMultipleApks no SpawnDroid e efetivamente lançar o Kwai. Sem ativar cloud_cutover.

## LEASE
Arquivos novos 'tools/kwai_apksig_v2_audit.py', 'tests/test_kwai_apksig_v2_audit.py', finding novo e no máximo extensão no workflow já propriedade da branch PR #2616; peer GitLab main verificado sem arquivos homônimos.