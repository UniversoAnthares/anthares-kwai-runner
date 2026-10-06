# Firebase Test Lab credential/project discovery
STATUS: PARTIAL
AREA: android
DATE: 2026-10-06
RUN: none
JOB: AI Commander gcloud read-only probe
COMMIT: none
SUPERSEDES: none

## Objetivo
Reduzir o bloqueio externo do ANDROID_SECONDARY sem tocar no lease kwai-login.

## Resultado
A máquina autorizada já possui gcloud autenticado como conta do usuário e 11 projetos GCP visíveis. O projeto universo-anthares já tem testing.googleapis.com habilitado. Portanto o bloqueio anterior "Firebase/GCP credentials unavailable" foi reduzido: há identidade GCP e projeto candidato existentes. Application Default Credentials não estão configuradas, e o CLI firebase não está instalado; nenhum teste foi disparado para evitar habilitar/mutar serviços sem lease próprio.

## Evidência decisiva
gcloud auth list => conta ativa presente; gcloud projects list => universo-anthares ACTIVE; gcloud services list --enabled --project universo-anthares => testing.googleapis.com.

## Consequência
Próximo agente Android-secondary deve adquirir lease android-secondary, usar universo-anthares como primeiro candidato, verificar Test Lab/Firebase registration e executar um smoke virtual mínimo com APK de teste. Evitar criar projeto GCP novo antes de testar o projeto existente. Não tocar em kwai-login enquanto o lease semântico atual estiver ativo.
