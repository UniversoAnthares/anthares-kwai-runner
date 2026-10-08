# Dual-provider execution architecture

GitHub e GitLab são providers pares. Nenhum é autoridade permanente.

## Invariants

1. O plano de controle é externo aos dois providers.
2. Uma operação possui no máximo um lease de execução ativo.
3. A seleção normal usa apenas providers READY e alterna entre os pares.
4. BLOCKED_QUOTA, DOWN, AUTH_REQUIRED, UNKNOWN e BUSY não podem ser selecionados.
5. Failover só ocorre depois que o provider atual deixa de estar READY.
6. O provider de destino precisa estar READY.
7. O provider de destino precisa corresponder ao checkpoint de conteúdo verificado do lease.
8. O mesmo commit é prova suficiente de equivalência. Commits diferentes também podem ser equivalentes quando ambos expõem o mesmo `content_id` verificado (por exemplo, o Git tree SHA).
9. Divergência de conteúdo bloqueia o failover.
10. Cada failover incrementa lease_generation.
11. Renovação/heartbeat prolonga o mesmo lease; não cria um segundo executor.
12. O GitHub pode voltar a ser escolhido depois que sua saúde retornar a READY.
13. O GitLab pode voltar a ser escolhido pelo mesmo mecanismo. Não existe preferência estrutural.
14. Dentro do provider que detém o lease, qualquer mudança de HEAD após a aquisição invalida o lease, mesmo que a nova árvore tenha conteúdo equivalente. Isso detecta escrita concorrente.

## Fluxo

operation
  |
  v
anthares-control
  |
  +--> health snapshots: github / gitlab
  |
  +--> acquire lease + checkpoint(head, content_id)
  |
  +--> choose READY peer
  |
  +--> execute
  |
  +--> heartbeat / renew
  |
  +--> complete
  |
  +--> se provider cair:
          verificar checkpoint de conteúdo
          verificar outro provider
          exigir mesmo commit OU content_id equivalente
          transferir lease
          incrementar generation
          continuar

## Contrato do snapshot

```json
{
  "provider": "github",
  "repository": "UniversoAnthares/anthares-kwai-runner",
  "ref": "main",
  "head": "commit-sha",
  "content_id": "git-tree-sha",
  "status": "READY"
}
```

`content_id` é opcional por compatibilidade, mas passa a ser obrigatório para permitir failover entre históricos independentes com commits diferentes. Sem `content_id`, commits diferentes continuam sendo tratados como divergência.

Estados aceitos:
- READY
- BLOCKED_QUOTA
- DOWN
- AUTH_REQUIRED
- UNKNOWN
- BUSY

## Contrato do lease

O estado persistente do lease deve conter:
- operation_id
- owner
- provider
- lease_generation
- repository
- ref
- checkpoint_commit
- checkpoint_content_id
- expires_at

O anthares-control continua sendo o local de persistência, fencing e heartbeat. O módulo `tools/provider_router.py` contém a política determinística; ele não armazena secrets e não grava diretamente em GitHub/GitLab.

## Failover

Exemplo permitido com o mesmo commit:

checkpoint_commit = ABC
checkpoint_content_id = TREE1

GitHub:
  status = BLOCKED_QUOTA
  head   = ABC
  content_id = TREE1

GitLab:
  status = READY
  head   = ABC
  content_id = TREE1

=> failover permitido

Exemplo permitido com históricos diferentes, mas conteúdo igual:

checkpoint_commit = GH123
checkpoint_content_id = TREE1

GitHub:
  status = BLOCKED_QUOTA
  head   = GH123
  content_id = TREE1

GitLab:
  status = READY
  head   = GL987
  content_id = TREE1

=> failover permitido
=> provider = gitlab
=> lease_generation incrementa

Exemplo bloqueado:

checkpoint_commit = GH123
checkpoint_content_id = TREE1

GitHub:
  status = BLOCKED_QUOTA
  head   = GH123
  content_id = TREE1

GitLab:
  status = READY
  head   = GL987
  content_id = TREE2

=> CHECKPOINT_DIVERGED
=> não executar
=> reconciliar antes

## Read-before-write e reconciliação

Antes de qualquer mutação, o agente deve ler o arquivo atual, registrar HEAD/blob SHA, conferir o provider par, adquirir lease e usar escrita condicional. Se o HEAD mudar antes da gravação, deve abortar, reler e recalcular o patch. Force push, reset de branch compartilhada e mirroring cego são proibidos.

Quando históricos divergirem, mas as árvores forem byte-equivalentes, pode-se preservar ambos os históricos com um merge normal de dois pais. Quando o conteúdo divergir, cada arquivo divergente deve ser reconciliado explicitamente e validado antes de qualquer convergência.

## Testes

`tools/test_provider_router.py` cobre:
- alternância entre peers;
- bloqueio de segundo escritor;
- failover somente após indisponibilidade;
- rejeição de checkpoint divergente;
- failover entre commits diferentes com `content_id` equivalente;
- rejeição de `content_id` diferente;
- fencing do lease quando o HEAD do provider ativo muda;
- ausência de provider disponível;
- recuperação após expiração do lease.

## Integração com o control plane

A implementação de persistência/deploy do Worker Cloudflare deve adaptar o contrato acima às operações já existentes de lease/heartbeat/fencing do anthares-control. Não deve ser criado um segundo controller.
