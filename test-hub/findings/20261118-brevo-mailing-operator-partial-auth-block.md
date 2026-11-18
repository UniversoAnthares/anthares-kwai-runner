# Brevo — operações de mailing instaladas e bloqueio do envio
STATUS: PARTIAL
AREA: email
DATE: 2026-11-18
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44378937748
JOB: 135065548021
COMMIT: 658c1f522a6b441516e772257d16f680f40cec24
SUPERSEDES: 20261118-brevo-hostinger-auth-readonly-proven.md

## Resultado comprovado
- Hostinger: release privada `658c1f522a6b441516e772257d16f680f40cec24`, Git blob da ferramenta `brevo_operations.py` igual a `4f2ca41cc2a223271febbeb6ccf42e84548a1e34`. O retorno remoto teve ruído de fim de linha, seguido de verificação independente do deploy e status.
- API Brevo GET, execução real com chave dedicada do titular: uma lista (id 2), `uniqueSubscribers=1`; `draft_count=0`; controles de envio desligados.
- Reconciliação de supressões: um contato verificado, zero supressões existentes, zero estados desconhecidos. Dados guardados em SQLite privado com registro cumulativo. A API geral omite informação de descadastro em alguns registros, corrigida consultando cada lista individualmente; requisição real deu `missing_list_status=0`.
- Painel administrativo **CLI privado**, autenticado pela conta SSH/Hostinger: `brevo_operations.py` executa `status`, `sync-suppressions`, `campaign-index`, `campaign-report`. Saídas restringidas a metadados e contagens; operação de status real: 1 lista, 1 assinante e 0 rascunhos.
- Testes CI no GitHub: `42/42` contratos Brevo e `9/9` regressões. Testes na Hostinger: `42/42` contratos Brevo. As rotas de leitura são GET; fluxo do mailing em massa bloqueado até aprovação.
- A verificação de envio consulta um ledger local de supressões recentes e falha com status incompleto/antigo, além de exigir aprovação de conteúdo e audiência.

## Bloqueios reais
- A API da chave dedicada aceita GET /account, /contacts, /contacts/lists e /emailCampaigns. GET /webhooks?type=marketing retornou HTTP 403. O próprio Brevo permite configurar permissões restritas por recurso. Sem acesso permitido não há sincronização webhook instalada.
- Foi tentada **uma** criação de rascunho técnico estritamente para ensaio, para remetente `contato@anthares.us` e destinatário de teste autorizado. POST /emailCampaigns respondeu **HTTP 405**. A aplicação marcou `RECONCILE_REQUIRED`, fez consulta somente de leitura e confirmou `draft_count=0`, nenhum rascunho com o identificador técnico e `brevo_id=null`. Não repetiu o POST nem acionou outra rota de envio. Sem rascunho não foi possível chamar /sendTest nem confirmar entrega.
- Atualmente um único contato permanece na lista Brevo; a lista de pastores ainda depende de coleta, qualificação, autorização, remoções e consentimentos; ela não foi importada.
- Não existe painel web de aprovação autenticada, apenas CLI interno; referências manuais arbitrárias de aprovação não constituem autorização verificável para disparar campanha.
- O serviço de cron automático não foi instalado: `crontab` não está disponível no shell da hospedagem; será preciso mecanismo de agendamento hospedado já autorizado e seguro antes de informar monitoramento recorrente.
- Falha de comunicação do Anthares Remote em sondagens posteriores; último resultado útil confirmado é a consulta de status da release acima. Não inferir continuidade após esta evidência.

## Próximo passo
Confirmar na interface Brevo se a chave **Anthares Mailing** tem permissão `Todos` em `Campanha de e-mail` e `contato`, sem conceder permissões desnecessárias de SMS. Se o POST seguir 405 com permissão correta, consultar suporte Brevo e documentação do plano. Não repetir POST sem mudança causal. Para envio real, exigir campanha e destinatários aprovados, teste controlado concluído e integração de eventos/contatos verificada.

## Evidências de segurança
Zero e-mails enviados nesta operação; zero destinatários externos; credencial nunca registrada em Git ou logs; WordPress e WP Mail SMTP preservados; nenhuma alteração de DNS ou contratação.
