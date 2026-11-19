# Resend: painel autenticado e contrato de segmento corrigido
STATUS: PARTIAL
AREA: email
DATE: 2026-11-19
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44449356310
JOB: 135309209344
COMMIT: 1e2b4708877fb2338369276c49631223fc4f6221
SUPERSEDES: 20261118-resend-broadcasts-staging-partial.md

## Objetivo
Reconciliar o cadastro visual confirmado do Resend com o staging de integração privado no Hostinger e alinhar a rota de destinatários ao contrato oficial.

## Baseline e evidências
- Screenshot do titular em sessão autenticada de `resend.com/emails`, com abas `Broadcasts`, `Domains`, `API keys` e indicador de zero emails enviados. O conector Browser leu a mesma aba e confirmou sua navegação e login de sessão. Nenhuma conta ou e-mail de autenticação foi inferido a partir do nome do workspace.
- A rota antiga `GET /contacts?segment_id=UUID` divergia da documentação. Corrigida para `GET /segments/{id}/contacts?limit=100`, com testes de paginação e supressões ajustados.
- API oficial: https://resend.com/docs/api-reference/segments/list-segment-contacts
- CI: run 44449356310, 18 testes Resend e 9 testes regressivos aprovados. Nenhum teste de API real com credencial foi possível.
- Hostinger: link da release atual lido como `releases/1e2b4708877fb2338369276c49631223fc4f6221`; hash blob de `resend_marketing.py` confirmado `efa0a772299514a9d208df24a28afb192d5fa60f`.
- O resultado de uma chamada de implantação via Anthares Remote foi incerto (erro 500), mas uma leitura posterior independente confirmou o link e hash corretos, sem repetição.
- Chave API em `domains/anthares.us/anthares-resend-mailer/resend-api-key.txt`: tamanho zero; permissões privadas 0600 já comprovadas em execução anterior. Nenhuma importação nem envio.

## Limites e consequência
O painel está autenticado no Chrome do titular. O servidor Hostinger ainda precisa de uma chave API Resend criada e armazenada fora do GitHub e do chat. Acesso de leitura da aba do Chrome não transmite credenciais nem autoriza copiar cookies. Não reexecutar tentativa de cadastro. Aguardar chave e confirmar domínio remetente antes de qualquer POST de rascunho. Broadcasts para pastores continuam desativados.
