# ARA sem dependência de Render — estado e implantação

## Confirmado em produção (13/10/2026)
- Controle ativo: `https://anthares-ara-backup.anthares1.workers.dev`.
- Agente Windows canônico `DESKTOP-FTDK0HP` na sessão SYSTEM (sessão 0).
- Comando real `echo CLOUDFLARE-ARA-OK` concluído no controle Cloudflare.
- Supervisor escolhe Render principal, canary Render ou Cloudflare, com `force-tertiary.flag` ativo.

## Dependências restantes
1. O gateway MCP que recebe requisições do ChatGPT ainda é hospedado no Render. O controle Cloudflare não é um servidor MCP público nem substitui sozinho a integração OAuth do ChatGPT.
2. O controle Cloudflare busca as chaves públicas dos MCPs em endpoints Render. Uma alteração do código em `cloudflare-ara-backup/src/index.js` aceita agora a variável `ARA_TRUSTED_MCP_PUBLIC_KEYS_JSON` (JSON array de chaves públicas Ed25519 PEM SPKI) como fontes locais prioritárias. **O commit não equivale a deploy**. É necessário configurar a variável no Cloudflare e implantar o Worker.
3. O controlador `anthares-control` e o espelhamento GitLab/Codeberg do Anthares-Reserva são fluxos diferentes do gateway MCP.

## Requisitos para fechar a independência
- Configurar no Worker Cloudflare `ARA_TRUSTED_MCP_PUBLIC_KEYS_JSON` com as chaves públicas válidas e persistentes dos dois serviços MCP. Não armazenar chaves privadas no Git, nos logs ou em documentos.
- Implantar `cloudflare-ara-backup` com Wrangler e verificar `/healthz`, `/v1/mcp/capabilities` assinado e execução real. Uma implantação sem a variável mantém a dependência Render anterior.
- Construir um gateway MCP Streamable HTTP em Cloudflare Workers com autenticação OAuth compatível com o ChatGPT, registro de ferramentas e assinatura Ed25519 de controle. Publicar em URL independente do Render.
- Configurar o conector Anthares Remote no ChatGPT para a URL Cloudflare. Não desligar o gateway Render antes de autenticação, listagem de ferramentas e execução real pelo novo conector.
- Garantir que as chaves públicas do gateway Cloudflare sejam fixadas no controle Cloudflare e verificar rotação sem interrupção.
- Testar falha dos serviços Render com o controle e o gateway Cloudflare ativos, sem interromper o dispositivo nem abrir janelas na área de trabalho.

## Restrições
- Custo R$ 0; sem cartão, cobrança ou plano pago.
- Não usar o PC como runner de CI, publicação ou fallback de serviços.
- Não assumir que endpoints HTTP públicos autenticados por Bearer bastam para o fluxo OAuth de um conector ChatGPT.
- Não declarar independência completa antes do teste ponta a ponta com Render indisponível.
