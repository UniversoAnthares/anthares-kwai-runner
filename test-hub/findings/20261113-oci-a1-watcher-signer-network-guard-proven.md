# OCI A1 capacity watcher: signer repair and fail-closed network checks
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: none (local transient read-only test)
JOB: ARA b7d95cf00ff8c471ea94963434699b2e; ARA c6d27c95aae45e5b9afc22f95057d1e8
COMMIT: PR #2489 b059d30ffea0070b7675049dcd6d73432765d00e; PR #2490 33603a0512d4622cfc19b0f5f738860821781e31
SUPERSEDES: test-hub/findings/20261112-oci-a1-hosted-capacity-watch-staged.md

## Objetivo
Verificar a execução real do monitor criado na fase anterior e proteger o provisionamento futuro da VM contra configurações OCI que a deixariam sem saída HTTPS.

## BASELINE_PROVEN
Monitor inicial no main (PR #2487); relatório real A1 1 OCPU/6GB `OUT_OF_HOST_CAPACITY`; Android físico e MEmu intocados. Falta GitHub Actions Secret/Vars.

## FAILED_AVOIDED
Execução real inicial revelou `oci.exceptions.InvalidConfig` por ausência de campos de configuração exigidos pelo SDK mesmo com signer; PR #2489 corrigiu com metadata de configuração sem transferir chave privada. Nova auditoria verificou subnet Android pública com rota padrão para internetgateway, **zero NAT Gateway** e watcher `assign_public_ip=False`. PR #2490 adicionou guard para não alocar Linux sem acesso externo.

## SUCCESS_SIGNAL
- Teste contra conta OCI real, sem habilitar provisioning: `ANTHARES_A1_CAPACITY=OUT_OF_HOST_CAPACITY`, retorno 0, nenhuma VM.
- Teste OCI real do guard com sub-rede `anthares-android-subnet`: `REAL_OCI_ANDROID_NETWORK_GUARD False`; evita alocação em rede inadequada.
- 8 testes de regressão, 0 falhas, 0 erros, job ARA `a8d25d95b83c3311f3aab6c314693d2c`.
- No Android físico, serviço MacroDroid foreground, acessibilidade habilitada, whitelist de energia e alarme periódico confirmados; consulta HEAD HTTPS sem token alcançou Neon e recebeu HTTP 404, comprovando conectividade e não autenticidade.

## FAILURE_SIGNAL
Sem segredo de Actions ou identidade WIF OCI, o monitor no GitHub permanece inativo. Sem rede privada com NAT ativo, o modo de provisionamento recusará criar VM. Sem host A1 `AVAILABLE`, relatório permanece `OUT_OF_HOST_CAPACITY`. Nenhum desses estados justifica contratar plano, ativar publicador em duplicidade, ou remover reconciliação.

## TEST_VALIDITY
Testes Python e API real foram realizados por execução transitória autorizada, em modo leitura, usando chaves locais apenas no processo em memória; nenhum segredo foi exportado ao GitHub. O runner hospedado **não executou** um check autenticado, e o MacroDroid principal **não foi comprovado** via lease/ack Neon independente do PC.

## Consequência
Manter item 8 aberto, habilitar autenticação GH Actions por administração legítima, preparar rede privada NAT somente após avaliação de cobrança e controle da cota, e comprovar macro de publicação independente com fencing. Preservar a ordem canônica Android físico principal/MEmu reserva. Critério de conclusão exige ReDroid e Kwai/MacroDroid funcionando de fato na VM e failover sem duplicações.
