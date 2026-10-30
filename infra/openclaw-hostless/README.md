# OpenClaw Gateway — prova isolada Hostless (30/10/2026)

## Escopo
Executar **somente** um Gateway descartável, em nuvem, com os limites máximos publicados para a franquia gratuita Hostless. Este branch não modifica ARA, TikTok, X, Neon, Hostinger nem os publicadores existentes.

**Bloqueios para operação real:**
1. A conta Hostless ainda não foi autenticada nem conectada ao GitHub por este agente.
2. A Hostless Free inclui CPU/RAM para o processo, porém o volume persistente de aplicação fica fora da franquia gratuita. O OpenClaw usa SQLite em disco e exige persistência local. Portanto, esta configuração descartável não deve receber credenciais, dados ou integrações reais.
3. A CPU de 0,5 vCPU está abaixo da recomendação de 1 vCPU; um teste HTTP verde sozinho não atesta capacidade operacional de múltiplos agentes.

## Implantação de verificação (sem cobranças)
- Entre em https://hostless.cloud com GitHub e confirme o plano **Free**, sem informar cartão.
- Crie aplicativo de teste isolado a partir de `UniversoAnthares/anthares-kwai-runner`, branch `aoi/openclaw-hostless-validation-20261030`.
- Hostless file: `hostless.yaml` (na raiz). O manifesto configura Docker na pasta `infra/openclaw-hostless`, uma réplica de 0,5 vCPU e 1024 MB.
- Selecione **No volume**; interrompa caso a interface solicite cartão, pagamento ou recursos além do plano Free.
- Defina em Secrets uma chave `OPENCLAW_GATEWAY_TOKEN` longa, aleatória e **descartável**, exclusiva desta prova. Jamais inclua o valor no GitHub, logs, prompts, comentários ou capturas.
- Após o build, a URL HTTPS deve responder `/healthz`; conferir também a negociação WebSocket `wss://` com token. A efetividade depende dos logs reais, não somente do manifesto.
- Desative o aplicativo de teste após a verificação de recursos. **Antes de conectar OpenClaw Desktop ou qualquer integração**, é indispensável comprovar armazenamento SQLite local durável dentro do orçamento R$0, retenção após reinicialização, isolamento, autenticação e capacidade.

## Integridade e segurança
- O contêiner lê apenas `OPENCLAW_GATEWAY_TOKEN` do ambiente e sai imediatamente se estiver ausente.
- Diretórios internos em `/tmp/anthares-openclaw-home` são **efêmeros**; sessão, SQLite, configuração e workspace podem desaparecer num restart.
- A imagem base é a imagem oficial GHCR, versão fixa `2026.9.36-slim`; sem navegador Chromium nem APIs de postagem.
- Este ensaio **não** conclui a migração, não publica conteúdos e não cria uma segunda autoridade operacional.
- Sem autorização/conta Hostless e sem armazenamento persistente elegível ao plano gratuito, o resultado permanece `BLOCKED_PERSISTENCE_AND_AUTH`.

Fontes: https://docs.hostless.cloud/app/hostlessfile ; https://docs.hostless.cloud/plans/limits ; https://docs.openclaw.ai/install/docker/networking-and-storage
