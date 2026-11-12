# SEC-01 — Bitwarden: contas, escopos e tokens verificados na sessão dedicada — 2026-10-26

STATUS: PARTIAL (inventário e matriz de acesso CONFIRMADOS; proteção e persistência do perfil ainda sem aceite).

## Fontes e governança

- GitHub private UniversoAnthares/anthares-governance main: REGRAS-OBRIGATORIAS.md, INDICE.md, PROMPT-MESTRE.md, AGENTS.md, manifest.json consultados; manifesto remoto versão 2e28d54043d6bad1; local Windows versão f6fc9ca59a96e451 diverge. Não sobrescrever automaticamente. Preflight local em WinRemote: SEC01-AUTH-VERIFY-20261026-R2 com exit0. ARA conectado.
- Sessão autenticada pelo titular no Chrome exclusivo com user-data-dir `D:\AntharsWork\browser-profiles\AntharesBitwardenAdmin`, Chrome PID 29224 Windows Session 1, UIAutomation com acessibilidade e `InvokePattern` na janela exata 26738726; CDP não exposto (port=0). Nenhum valor de segredo aberto, copiado ou exportado.
- Organização: Anthares Secrets; plano Bitwarden Secrets Manager Free e Password Manager gratuito previamente verificados no painel de assinatura. Inventário: 3 projetos, 3 contas de máquina, 8 segredos.

## Matriz de autorização administrativa (comprovada via GUI real)

| Conta de máquina | Projetos atribuídos (contagem) | Projeto | Direito efetivo mostrado | Tokens cadastrados |
|---|---:|---|---|---:|
| anthares-ai | 1 | Anthares AI | Pode ler e gravar | 1 |
| anthares-automation | 1 | Anthares Automation | Pode ler e gravar | 3 |
| anthares-core | 1 | Anthares Core | Pode ler | 1 |

- Guia Pessoas verificada: cada conta vinculada à identidade administrativa `Universo Anthares` com permissão `Pode ler e gravar` sobre a conta de máquina. Isto **não** aumenta os direitos do token na coluna Projetos.
- Guia Tokens de acesso, somente metadados:
  - anthares-ai: `anthares-omniroute-local` — Active, nunca expira.
  - anthares-automation: `anthares-automation` — Active, nunca expira; `github-anthares-automation` — Active, nunca expira; `CORTES-provisionamento-temporario-20261021` — Expiring soon, vence 2026-10-28 07:15:22 exibido pela interface.
  - anthares-core: `CORTES-executor-readonly-definitivo-20261021` — Active, nunca expira.
- NÃO foram revelados valores de tokens, tokens novos não foram criados e nenhuma permissão foi alterada. O prazo do token temporário exige verificar consumidores antes de renovação/revogação.
- **Correlação do GitHub, escopo da conta:** o workflow da PR draft #1399 usou exclusivamente `secrets.BWS_ACCESS_TOKEN`, autenticou no Bitwarden e leu metadata do segredo `THREADS_ACCESS_TOKEN` cujo projeto `Anthares Automation` foi conferido. Run 40235027169, job 121294643997, logs: `SEC01_AUTH=PASS`, `SEC01_THREADS_SECRET_METADATA=PASS`, `SEC01_THREADS_PROJECT_NAME=Anthares_Automation_VERIFIED`. Considerando as 3 contas do inventário atual e suas atribuições únicas, a conta de máquina autorizada para esse segredo é `anthares-automation`, forte evidência operacional da conta emissora de `BWS_ACCESS_TOKEN`. A correspondência exata entre `BWS_ACCESS_TOKEN` e o **rótulo** `github-anthares-automation` (vs. `anthares-automation`) NÃO é verificável sem acesso a metadados criptográficos ou identificadores do token; não presumir.
- Observação do event log da conta `anthares-automation`: a página de eventos de 2026-09-26 a 2026-10-26 retornou `Não há eventos para listar`; a ausência no painel não invalida teste SDK. Não alegar auditoria de eventos concluída.

## Segurança do perfil: operação parcial e bloqueios

- Chrome exclusivo foi fechado **graciosamente** via CloseMainWindow em PID 29224, `GRACEFUL_CLOSE=PASS`, e 0 processos desse perfil após fechar, para manutenção de ACL.
- Tentativa de ajustar ACLs de arquivo pelo WinRemote (identidade Windows Lucas) retornou mensagens **Acesso negado** em diretório e arquivos; os logs mostraram `PASS` indevido em stdout por problema de interpretação do processo e NÃO são comprovação. Leitura posterior da raiz via ARA (somente leitura) constatou `AreAccessRulesProtected=False` e regras herdadas amplas, portanto **endurecimento NÃO executado**. Não contornar o bloqueio de ACL alterando segurança por uma identidade mais privilegiada.
- Backup do ACL gerado em `D:\AntharsWork\browser-profiles\AntharesBitwardenAdmin-acl-prehardening-20261026.txt`. Backup anterior 20261025 permanece. Não foram alterados os outros perfis.
- A tentativa subsequente de reabrir a janela exclusiva via WinRemote foi **bloqueada por controles de segurança da ferramenta**; não reenviar a mesma operação via outro agente/instrumento para contornar. Consequentemente **reabertura e preservação do login após reinício não foram comprovadas**, e é necessária retomada somente por um caminho expressamente autorizado.
- O Chrome pessoal não foi encerrado ou alterado.

## Aceite e riscos residuais

1. **Inventário/quotas/projetos/contas/atribuições: PROVEN** via GUI e workflow de leitura; plano Free usa 3/3 projetos e 3/3 contas, 8 segredos.
2. **Identidade de conta para token GitHub: forte evidência por escopo exclusivo** (`anthares-automation`), mas token-label exato UNVERIFIED.
3. **Perfil administrativo dedicado: PARTIAL/AUTH_REOPEN_NOT_VERIFIED**, ACLs herdadas e manutenção bloqueada; não alegar isolamento forte ou login persistente.
4. **Operação humana realmente necessária**: reabertura autorizada do perfil pela própria estação se a janela precisar permanecer acessível; nenhuma senha/token deve ser enviada ao chat.
5. **SEC-01 no agregado: PARTIAL**, porque a robustez de identidade e segurança do perfil ainda não está comprovada. Não confundir conclusão da auditoria read-only com implantação de política de proteção do navegador.

Nenhum custo, compra, permissão, assinatura, segredo, deploy, fila ou publicação alterados.
