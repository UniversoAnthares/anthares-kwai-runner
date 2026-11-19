# Mailing pastoral Mente Cristã — implantação limitada e auditada (19/11/2026)

**Estado real:** cadastro privado importado, consulta de supressões ativa manualmente, rotina diária de respostas agendada. **Envio comercial desativado.**

## Fonte e destinação
- Origem: planilha Observatório IPB, aba `Cadastro pastoral consolidado`, 5.501 linhas de pastores.
- Importação para SQLite **privado da Hostinger**: 4.993 endereços únicos válidos; 508 entradas sem e-mail. A lista **não foi importada ao Resend**.
- Diretório de código no servidor: `/home/u566597497/.anthares-pastoral-mailing/current`.
- Base protegida: `/home/u566597497/.anthares-pastoral-mailing/state/pastors.sqlite3`, fora de `public_html`.
- Consentimentos: **0 comprovados**, por isso o grupo selecionável para disparo permanece vazio.
- Senhas e API keys permanecem fora de GitHub. Nenhum destinatário privado foi copiado ao repositório.
- Mensagem original de 14/10/2021, assunto `Contato`: texto integral e inventário de cinco anexos guardados privadamente no servidor em `state/original_2021_mail.json` (0600), após validação JSON. Os cinco PDFs foram recuperados do Gmail do titular, porém seus **bytes ainda precisam ser transferidos ao armazenamento privado da Hostinger** antes da preparação final.
- Anexos originais: `Catálogo-Mente-Cristã.pdf`, `Nova Vida.pdf`, `A Fé que Confessamos.pdf`, `Prontos Para Servir.pdf`, `Grandes Temas do NT.pdf`.

## Controles técnicos entregues
- `pastor_mailing_queue.py`: extração de primeiro nome, IDs e estado de contato, bloqueio de endereço sem opt-in verificado, SQLite idempotente e supressão de hard bounce/reclamação/descadastro, teto local **100/dia e 3.000/ciclo** mais disponibilidade reportada pela API, e **nenhum mecanismo de POST de envio**.
- `pastor_mail_import_b64.py`: importação privada em blocos validados, sem endereços em logs.
- `resend_suppression_sync.py`: GET paginado de `/suppressions` do Resend, reconciliando exclusivamente entradas correspondentes ao banco local, sem operações de envio ou exclusão. Verificado real: HTTP 200, 0 suppressions iniciais.
- `pastor_mail_inbox_cli.py`: lista e marca de forma idempotente UIDs de mensagens da Hostinger; os UIDs devem ser marcados somente após a confirmação de entrega do relatório.
- 11 testes offline de cadastro/consentimento/cotas e 4 de supressões aprovados na Hostinger.
- Integrador Resend já autenticado e domínio verificado. A API gratuita informa 100 e-mails/dia e 3.000/ciclo para rota `/emails`.

## Relatório RESPOSTAS
Foi criada a automação ChatGPT `6afeddea55ac8191bc524cdb7b20e5de` (título `RESPOSTAS pastores`), com RRULE diária em `America/Campo_Grande`, primeira ocorrência agendada para 19/11/2026 às 08:00 locais, em horário flexível. A tarefa:
1. Lê a caixa Hostinger `contato@anthares.us` e consulta UIDs ainda não processados.
2. Reconciliará supressões do Resend via GET real na Hostinger.
3. Enviará pelo conector Hostinger Mail um resumo diário ao Gmail do titular com assunto exato `RESPOSTAS`, mesmo quando não houver novidades.
4. Após sucesso confirmado, marcará UIDs revisados. Falhas 5xx comprovadas e descadastros são bloqueados na fila privada; rejeições transitórias permanecem em acompanhamento.
**A criação da automação comprova agendamento, mas a primeira execução e entrega ainda requerem observação de resultado.**

## Critérios para habilitar disparo
Resend AUP exige opt-in explícito e proíbe cold outreach ou lista de contatos extraída de diretório público: https://resend.com/legal/acceptable-use. A intenção anterior de enviar automaticamente a todos os 4.993 contatos violaria essas regras, portanto não foi ativada.

Pré-requisitos: comprovação individual de permissão; conteúdo comercial de 2021 conferido para atualidade; cinco PDFs originais disponíveis em storage privado; link de descadastro funcional com List-Unsubscribe; endereço comercial válido no rodapé; aprovação de público e conteúdo; executor e idempotência de POST /emails com teste de caixa controlada; histórico de bounces/queixas. O consumo de envios deve respeitar a quota diária **e** mensal, além de impedir reenvios incertos.

## Resultado
- Cadastro: 4.993 registros privados, 0 elegíveis.
- Resend: autenticado/verificado; 0 campanhas enviadas; envios comerciais **OFF**.
- Relatório RESPOSTAS: agendado e dependente de verificação da primeira execução.
- Supressões: mecanismo testado, 0 ocorrências no provedor no momento da verificação.
