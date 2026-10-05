# Declared Kwai login activities are mostly non-exported
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388030409
JOB: 112026171392
COMMIT: d9a144b23fbca831e4b382aa710549b68d9af77a
SUPERSEDES: none

## Objetivo
Auditar a consequência do finding PROVEN de Manifest antes de interpretar o direct-activity probe atualmente em execução.

## Resultado
O Manifest prova que as Activities existem, mas também mostra que SplashLoginActivity, PhoneAccountActivityV2, EmailLoginActivity e LoginActivity têm android:exported=false. CommonLoginActivity não apresenta exported no bloco observado e não há intent-filter associado no trecho. Em contraste, KwaiAuthActivity e LivePartnerAuthActivity têm android:exported=true e intent-filter VIEW/BROWSABLE.

## Evidência decisiva
Run 37388030409/job 112026171392: SplashLoginActivity exported=0x0; PhoneAccountActivityV2 exported=0x0; EmailLoginActivity exported=0x0; LoginActivity exported=0x0; KwaiAuthActivity exported=0xffffffff; LivePartnerAuthActivity exported=0xffffffff.

## Consequência
O run 37388231997 não pode transformar Permission Denial ao iniciar as quatro Activities internas em evidência de que a UI/login não existe. Isso provaria somente que shell externo não pode iniciar componente não-exportado. Interpretar separadamente start permission, foreground component e UI. Se o objetivo é entrar nas Activities internas, o próximo caminho causal deve ser navegação interna/deeplink/exported gateway/Accessibility, não repetição de am start externo.