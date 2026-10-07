# Dual-provider execution architecture

GitHub e GitLab são providers pares. Nenhum é autoridade permanente.

## Invariants

1. O plano de controle é externo aos dois providers.
2. Uma operação possui no máximo um lease de execução ativo.
3. A seleção normal usa apenas providers READY e alterna entre os pares.
4. BLOCKED_QUOTA, DOWN, AUTH_REQUIRED, UNKNOWN e BUSY não podem ser selecionados.
5. Failover só ocorre depois que o provider atual deixa de estar READY.
6. O provider de destino precisa estar READY.
7. O HEAD do destino precisa coincidir com o checkpoint confirmado do lease.
8. Divergência bloqueia o failover.
9. Cada failover incrementa lease_generation.
10. Renovação/heartbeat prolonga o mesmo lease; não cria um segundo executor.
11. O GitHub pode voltar a ser escolhido depois que sua saúde retornar a READY.
12. O GitLab pode voltar a ser escolhido pelo mesmo mecanismo. Não existe preferência estrutural.

## Fluxo

operation
  |
  v
anthares-control
  |
  +--> health snapshots: github / gitlab
  |
  +--> acquire lease
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
          verificar checkpoint
          verificar outro provider
          exigir HEAD idêntico
          transferir lease
          incrementar generation
          continuar

## Contrato do snapshot

{
  "provider": "github",
  "repository": "UniversoAnthares/anthares-kwai-runner",
  "ref": "main",
  "head": "abc123",
  "status": "READY"
}

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
- expires_at

O anthares-control continua sendo o local de persistência, fencing e heartbeat. O módulo tools/provider_router.py contém a política determinística; ele não armazena secrets e não grava diretamente em GitHub/GitLab.

## Failover

Exemplo permitido:

checkpoint = ABC

GitHub:
  status = BLOCKED_QUOTA
  head   = ABC

GitLab:
  status = READY
  head   = ABC

=> failover permitido
=> provider = gitlab
=> lease_generation = 2

Exemplo bloqueado:

checkpoint = ABC

GitHub:
  status = BLOCKED_QUOTA
  head   = ABC

GitLab:
  status = READY
  head   = XYZ

=> CHECKPOINT_DIVERGED
=> não executar
=> reconciliar antes

## Testes

tools/test_provider_router.py cobre:
- alternância entre peers;
- bloqueio de segundo escritor;
- failover somente após indisponibilidade;
- rejeição de checkpoint divergente;
- ausência de provider disponível;
- recuperação após expiração do lease.

## Integração com o control plane

A implementação de persistência/deploy do Worker Cloudflare deve adaptar o contrato acima às operações já existentes de lease/heartbeat/fencing do anthares-control. Não deve ser criado um segundo controller.
