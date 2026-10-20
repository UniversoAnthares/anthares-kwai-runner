# Anthares AI Hub — protocolo de colaboração ChatGPT, Claude e Work

## Estado

**PROVEN EM PRODUÇÃO:** ChatGPT abriu a issue #230, o gateway GitHub Actions validou o proprietário e acionou o Claude Code remoto, que produziu o artefato esperado. **WORK EM SESSÃO PRÓPRIA: NÃO TESTADO** (precisa iniciar Work com o conector GitHub habilitado). O Claude Free → Anthares MCP → Claude Code GitHub Actions → resultado está comprovado pela execução 39352658418 e aceite do usuário. ChatGPT/Work já podem criar e ler GitHub Issues pelo conector GitHub, quando conectados e autorizados. Work não pode ser acionado diretamente por um workflow GitHub sem recurso Work oficialmente disponível: o usuário inicia uma tarefa em Work para trabalhar sobre a fila.

Fila: https://github.com/UniversoAnthares/anthares-kwai-runner/issues
Solicitação guarda-chuva: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/222
Aceite real: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/230
Execução Claude Code aprovada: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39356635285
Executor atual: `.github/workflows/anthares-free-claude.yml`
Gateway implantado: `.github/workflows/anthares-collab-plan.yml`

## Chamadas e papéis

| Origem | Entrada | Atuação | Saída |
|---|---|---|---|
| ChatGPT | Plugin GitHub: criar issue | Planejar e auditar resultado; acompanhar Actions e PR | Comentário no issue, evidência no Test Hub |
| Claude Free | Conector Anthares: `run_claude_code`, `get_claude_code_status`, `get_claude_code_result` | Executa Claude Code remoto; revisa o retorno na sessão | Artefato do run; PR draft para edições |
| Work | Modo Work + conector GitHub autorizado, issue de colaboração | Pesquisa, consolida revisão, testa e propõe mudanças como PR | Comentários/PR/documentos no GitHub |
| Claude Code | GitHub Actions efêmero + 9Router/Gemini gratuito | Plano ou, fora deste gateway, edição limitada de um arquivo | Artefato com validade de dois dias |

NÃO inventar APIs de Work/Claude.ai. Nenhum executor tem permissão de mesclar mudanças sem revisão humana.

## Como submeter pelo ChatGPT ou Work

Crie uma issue com título começando EXATAMENTE por:

`[ANTHARES-COLLAB-PLAN] ` seguido de um resumo.

O corpo **inteiro** deve ser este JSON, substituindo a tarefa e a origem:

```json
{"schema":"anthares.collab.plan.v1","origin":"work","task":"Prepare um plano seguro para validar testes JavaScript, sem editar arquivos."}
```

Origem permitida: `chatgpt`, `work`, `claude`. O gateway somente processa issues criadas pelo proprietário do repositório de ID fixo `81930373`, cuja ação do evento também seja desse proprietário. Work e ChatGPT devem usar a identidade GitHub já autorizada. Para cada issue válida:

1. Verifica o JSON, rejeita modo edit, campos inesperados, caracteres de controle e padrões óbvios de segredo; título explícito; tarefa máx. 1600 caracteres; ignora issues comuns.
2. Deriva UUID determinístico do ID imutável da issue; procura marca de *claim* em comentários.
3. Registra o *claim* antes de qualquer dispatch. **Se houver incerteza ou queda posterior, não despacha novamente** até revisão da evidência. Reexecução do mesmo evento não duplica chamadas.
4. Chama `anthares-free-claude.yml` com `mode=plan`, `request_id` e task validados. Publica `DISPATCH_ACCEPTED` e, quando possível, `COMPLETED` ou `AWAITING_RESULT` com URL de execução.
5. O artefato completo fica no GitHub Actions; não o cola nos comentários públicos. Não executa comandos arbitrários nem altera `main`.

Execuções que excedam a janela do gateway permanecem `AWAITING_RESULT` sem perda do `request_id`. O responsável pela tarefa pode consultar o run pelo GitHub e o Claude Free usa `get_claude_code_result(request_id)`.

## Para revisar no Work

Iniciar **ChatGPT Work** e conectar a mesma conta GitHub autorizada (se o recurso estiver disponível no plano/configuração). Pedir para:

> Abra as issues do repositório UniversoAnthares/anthares-kwai-runner com prefixo [ANTHARES-COLLAB-PLAN]; acompanhe as tarefas sem segredos; consulte os artefatos e PRs; valide testes, aponte problemas nos comentários e faça PRs separados a partir de branches próprias, sem mesclar a main. Respeite AGENTS.md e Test Hub.

Work não recebe *push* automático desta implementação. Seu trabalho começa quando o usuário inicia ou agenda explicitamente uma atividade Work, conforme os recursos disponíveis no produto. O teste específico é pedir ao Work para abrir a issue #230, ler o run 39356635285 e registrar uma revisão via comentário ou PR. Criar uma issue nova com a origem literal `work` só comprova a participação real se a emissão foi feita por uma sessão Work, não por ChatGPT em nome dele.

## Para revisar no Claude

Conector Anthares existente: `run_claude_code`, `get_claude_code_status`, `get_claude_code_result`, `github_get_file`.
O complemento implantado é `collab_get_task(repo,issue_number)` e `collab_list_tasks(repo)`, ambos em `github.read`, sem escrita. Se o catálogo do Claude ainda mostrar apenas as ferramentas antigas, atualize a conexão Anthares no Claude para recarregar o catálogo. Depois teste `collab_get_task` para a issue #230 e consulte o resultado remoto usando `get_claude_code_result` com o request_id mostrado na issue. Não chamar `run_claude_code` novamente para o mesmo `request_id`.

## Segurança e execução

- O repositório é público. **Nunca inserir credenciais, conteúdo confidencial, sessões, dados de clientes nem prompts privados em issues, comentários ou workflows.**
- A chamada automática limita-se a planejamento; edição remota exige outra autorização pelo caminho já existente e abre somente PR draft.
- Não usar máquina Windows como executor. Cloudflare autentica o Claude Free; GitHub Actions executa temporariamente sem VPS ou cobrança adicional garantida (sujeito a cotas/políticas dos fornecedores).
- Mantenha `proteger-main` no GitHub. Se a regra de bloqueio impedir merge de um PR revisado, peça correção administrativa da regra com manutenção das restrições de revisão, nunca faça push forçado.
- Aceite de ChatGPT em produção obtido na issue #230: claim, dispatch único, run 39356635285 completed/success, artefato contendo `ANTHARES_COLLAB_CHATGPT_WORK_OK`, comentário final COMPLETED. Aceite de Work continua dependendo de operação iniciada dentro do Work.
- Antes de qualquer edição: seguir `AGENTS.md`, Test Hub, lease, HEAD e SHA, verificação peer GitLab, testes e revisão.
