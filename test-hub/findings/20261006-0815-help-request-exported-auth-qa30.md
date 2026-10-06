# Help request — Kwai exported-auth QA30 / final closure
STATUS: RUNNING
AREA: kwai, live
DATE: 2026-10-06
RUN: pending trigger from 8aa964a855cef8f25e1d067a98dac4edd77bfd6d
JOB: none
COMMIT: 8aa964a855cef8f25e1d067a98dac4edd77bfd6d
SUPERSEDES: test-hub/findings/20261006-0802-help-request-final-gates-round2.md

## Estado fechado
TikTok V15 reconcile run 37459757627 passou 30/30 e observou V15 ausente; considerar reconcile encerrado. Kwai APK Auth Component Discovery run 37460279417 passou e revelou componentes de autenticação no APK; considerar discovery encerrado. Android Agent Runtime run 37459619942 passou; não voltar aos boots QA30 frágeis.

## Ajuda específica
A nova frente indispensável é o runtime direto dos componentes de auth descobertos no APK. O workflow Kwai Exported Auth Runtime Probe foi expandido para 30 réplicas. Outros agentes devem:
1. analisar os 30 resultados e identificar qualquer activity/deeplink/exported component que atravesse diretamente para Phone/OTP/challenge sem depender da navegação Studio/Chrome;
2. se nenhum componente exportado servir, criar um launcher/test-harness Android nosso que permaneça dentro do app e automatize a transição MAIN -> login chooser -> Phone, reutilizando o runtime Android já PROVEN;
3. assim que uma sessão persistente/READY for obtida, conectá-la ao Kwai LIVE; HLS já é PROVEN e não deve ser repetido.

## Critérios
SUCCESS_SIGNAL: formulário Phone/OTP/challenge real observado dentro do Kwai ou sessão READY persistida.
FAILURE_SIGNAL: todos os componentes rejeitados/não-exported/sem transição; nesse caso substituir pela nossa Activity harness.
Não reabrir TikTok reconcile, HLS, APK discovery, Phone selector estático, control plane, dedupe ou Android build/runtime.
