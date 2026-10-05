# ANTHARES TEST HUB

> FONTE DE VERDADE OPERACIONAL COMPARTILHADA
>
> Antes de criar, repetir ou corrigir qualquer teste deste projeto, leia este arquivo.
> Depois de obter evidência nova, atualize este hub no mesmo trabalho.
> Nunca repita uma rota marcada como DESCARTADA sem evidência nova que invalide a decisão.

## Regras de classificação

- **PASS REAL**: o comportamento final foi comprovado no serviço/plataforma real.
- **PASS TÉCNICO**: somente o componente indicado foi comprovado; não implica aceitação final.
- **FAIL CONHECIDO**: falha reproduzida e causa identificada.
- **DESCARTADO**: rota que não deve ser tentada novamente.
- **PENDENTE**: ainda precisa de prova real.
- Workflow verde, preflight, compilação, instalação ou launch NÃO equivalem a publicação/login/LIVE real.

## Estado atual — Kwai Android remoto

| Componente | Estado | Evidência / conclusão |
|---|---|---|
| GitHub-hosted Android remoto | PASS TÉCNICO | API 35 inicia com KVM |
| Native bridge ARM64 | PASS TÉCNICO | x86_64 + arm64-v8a; libndk_translation.so |
| Kwai Package Vault | PASS TÉCNICO | checksum e pacote validados |
| Split selection | PASS TÉCNICO | base única + arm64 + density; instalação comprovada |
| Instalação Kwai | PASS TÉCNICO | com.kwai.video instalado |
| Launch Kwai | PASS TÉCNICO | KWAI_LAUNCHED e PID comprovados |
| Permission dialog Android | PASS TÉCNICO | bloqueio identificado e handler implementado |
| Onboarding 1/11 | PASS TÉCNICO / handler implementado | resource-ids tiny_discovery_like_button/dislike_button |
| UI selector map | PASS TÉCNICO | checks estáticos passam |
| Autologin Kwai | PENDENTE | ainda não existe prova de login real concluído |
| Auth probe | PENDENTE | só vale após autologin real |
| Publicação de corte Kwai | PENDENTE | exige post real confirmado |
| LIVE Kwai 6h | PENDENTE | exige sessão real de 6h confirmada |

## Bateria observável

Run 37377426655:
- 01 BOOT — PASS TÉCNICO
- 02 INSTALLER — PASS TÉCNICO
- 03 PERMISSIONS — PASS TÉCNICO
- 04 ONBOARDING — PASS TÉCNICO
- 05 UI MAP — PASS TÉCNICO
- 06 AUTOLOGIN E2E — NÃO É PROVA REAL: job era apenas gate informativo
- 07 AUTH PROBE — NÃO É PROVA REAL: job era apenas gate informativo

## Falhas já explicadas — não diagnosticar novamente como causa nova

- Run 37370378251: AUTOLOGIN_FAILED_RC=3. Android/vault/install/launch passaram. O autologin não encontrou campo de login.
- Run 37370733856: RC=3 novamente. Evidência posterior mostrou diálogo Android de permissão bloqueando navegação.
- Run 37371976406: RC=3 após permissão. Evidência mostrou onboarding Kwai 1/11 com controles icon-only.
- Runs experimentais posteriores com exit 127 após KWAI_LAUNCHED: falha de comando/estrutura do diagnóstico; NÃO prova falha do Android ou do Kwai.
- Erro antigo /usr/bin/sh: set: Illegal option -o pipefail: causado por dash dentro do emulator runner; corrigido usando Bash/atomic wrapper.
- FAIL_INSTALL_MULTIPLE antigo: primeiro por split ABI estrangeiro; depois por duas bases com basis.apk. Ambos corrigidos.

## Decisões consolidadas

- Arquitetura final: 100% remota/cloud; PC desligado.
- R$0; nada que exija cartão/billing.
- GitHub Actions público é executor Android descartável escolhido para cortes.
- Cloudflare anthares-control é plano de controle central.
- TikTok: cortes apenas. TikTok LIVE fora do escopo.
- Kwai: cortes + LIVE de 6h.
- LIVE de 12h foi descartada permanentemente.
- Não usar PC, MEmu, ADB local, PowerShell local, Kilo/Work local como executor.
- Não usar Oracle/Ampere.
- Não usar Google Cloud se exigir billing/cartão.
- Não usar Kuaishou Open Platform para Kwai brasileiro/internacional.
- Não usar CutMotions, cp.kwai.com antigo ou Kwai Studio para posts comuns.
- Não voltar à aquisição Play Store/Aurora/goopdl como rota principal do APK.
- Não usar APK não confiável.
- Não usar túnel/VNC público como controle operacional.
- Não publicar screenshots/XML de conta autenticada em artefatos públicos.
- Nunca expor KWAI_LOGIN, KWAI_PASSWORD, tokens, cookies ou sessões no hub.

## Critério para fechar itens

1. Login: sessão autenticada comprovada por estado real do aplicativo.
2. Corte Kwai: post novo confirmado na conta correta + estado central concluído.
3. Corte TikTok: post novo confirmado em @universo.anthares + estado central concluído.
4. LIVE Kwai: transmissão real de 6h comprovada.
5. Idempotência: retry não pode gerar duplicata; estado uncertain bloqueia repost cego.

## Protocolo obrigatório para chats/agentes

1. Ler este arquivo antes de propor uma nova tentativa.
2. Procurar a causa/rota em **Falhas já explicadas** e **Decisões consolidadas**.
3. Não repetir mecanismo descartado.
4. Isolar a camada ainda não comprovada.
5. Preferir testes paralelos de componentes independentes; nunca multiplicar logins/publicações concorrentes.
6. Registrar run ID, componente, resultado, causa e correção quando houver evidência nova.
7. Atualizar o estado PENDENTE/PASS somente conforme o critério de aceitação real.
8. Se um resultado contradizer o hub, preservar os dois registros e marcar a contradição até haver nova prova.
