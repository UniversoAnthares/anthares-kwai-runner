# Brevo — autenticação real de leitura no executor Hostinger
STATUS: PROVEN
AREA: email
DATE: 2026-11-18
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44373686748
JOB: 135047002439
COMMIT: fc562b6360da45c060b27c1a06bd4ec1ef42ace2
SUPERSEDES: 20261118-brevo-hostinger-private-staging-partial.md

## Objetivo
Homologar o uso da chave dedicada `Anthares Mailing` salva pelo titular no arquivo privado do executor Hostinger, comprovando somente a autenticação e consultas GET na API Brevo.

## Resultado
- **PROVEN (API real)**: execução no Hostinger da ferramenta `brevo_readonly_check.py` com saída sanitizada: `{"authenticated":true,"read_endpoints":{"account":"ok","campaigns":"ok","lists":"ok"},"sending":"disabled"}`. Código de saída SSH 0.
- **PROVEN (segurança do segredo)**: arquivo controlado pelo titular, modo 0600, pasta 0700, fora de `public_html`; chave ausente de GitHub, logs e resposta. Nenhum token exibido pelo teste. Link do estado privado validado.
- **PROVEN (deploy de staging)**: release imutável no Hostinger apontando para commit `fc562b6360da45c060b27c1a06bd4ec1ef42ace2`, SHA blob `brevo_readonly_check.py` = `d89d2564f21258eca8b9d23e5ed63e72525becf0`. Após retorno parcialmente ruidoso do shell, checagem independente verificou o link e a integridade, sem repetir a implantação.
- **PROVEN (testes offline)**: CI `29/29` testes Brevo e `9/9` regressões do sistema anterior. Hostinger executou `29/29` testes Brevo usando transporte fictício.
- Todas as variáveis de escrita de listas, campanhas, rascunhos e envios estavam desabilitadas durante a verificação. As três chamadas de verificação foram GET, sem importação, alteração de lista, envio de teste ou e-mail massivo.

## Limites
A autenticação de leitura em Brevo está operacional. O serviço ainda não tem interface de aprovação autenticada, reconciliação automática de descadastros e bounces, integração de lista consentida, scheduler nem envio real homologado. O código permanece na PR draft #2656; staging privado foi instalado separadamente. O conteúdo editorial antigo foi rejeitado e não será usado; os dois aceites (campanha e público destinatário) permanecem obrigatórios.
