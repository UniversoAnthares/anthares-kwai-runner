# Arsenal de agentes locais e contingência do Desktop Commander
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Registrar o arsenal adicional disponível para continuar o Anthares quando Work, Kilo ou Remote Desktop Commander atingirem limites.

BASELINE_PROVEN: o hub continua sendo a fonte de verdade; GitHub Actions público é executor remoto comprovado e PC local não pertence à arquitetura de produção.
FAILED_AVOIDED: não tratar indisponibilidade/cota de uma interface de agente como falha da arquitetura Anthares.
SUCCESS_SIGNAL: cada ferramenta instalada responde localmente e os agentes recebem a obrigação de consultar README/AGENTS/findings antes de mutações.
FAILURE_SIGNAL: instalação quebrada, ferramenta sem execução ou dependência paga obrigatória.
TEST_VALIDITY: versão/execução do binário ou extensão deve ser observada; mera presença de arquivos não prova funcionamento.

## Resultado
- Cline VS Code instalado: extensão saoudrizwan.claude-dev v4.1.22.
- OpenCode instalado e executado: v1.18.34.
- Gemini CLI chegou a responder v0.62.0, mas uma reinstalação concorrente deixou o pacote inconsistente; requer reparo antes de ser considerado disponível.
- Aider foi redirecionado para Python 3.11 após incompatibilidade da tentativa em Python 3.13; instalação ainda precisava de verificação final.
- Remote Desktop Commander permanece disponível, porém a cota mensal estava em 96% no momento deste registro.
- GitHub MCP continua sendo via independente para leitura/escrita do hub e repositórios.
- Alternativa pesquisada: AI Commander oferece remote shell/jobs por MCP/REST e plano gratuito para até 10 máquinas; ainda requer instalação/pareamento antes de ser considerado PROVEN.

## Consequência
Próximos agentes devem preferir, nesta ordem operacional conforme disponibilidade: GitHub MCP para operações GitHub; Cline/OpenCode/Aider/Gemini para trabalho local; Remote Desktop Commander enquanto houver cota; AI Commander após instalação e prova real. Nenhuma dessas ferramentas altera a regra arquitetural de produção sem PC. Todo agente deve consultar o hub antes de testes e registrar findings append-only.
