# Anthares Control Plane

Serviço próprio e independente do Render para fila, leases, heartbeat, deduplicação e failover dos executores Anthares.

## Objetivo

Manter um segundo plano de controle capaz de assumir a distribuição de tarefas quando o provedor principal falhar. O serviço usa SQLite/WAL local por instância e um protocolo de idempotência + fencing para impedir conclusão por leases antigos.

## Segurança

Defina `ANTHARES_CONTROL_TOKEN` em todos os provedores e clientes. Endpoints mutáveis e administrativos recusam operação quando o token não está configurado.

## Variáveis

- `ANTHARES_CONTROL_TOKEN`: segredo Bearer obrigatório.
- `ANTHARES_DB_PATH`: caminho do SQLite. Padrão `/tmp/anthares-control-plane.db`.
- `ANTHARES_PROVIDER`: nome do provedor, por exemplo `render-primary`, `anthares-backup`.
- `ANTHARES_INSTANCE_ID`: identificador da instância.
- `ANTHARES_ROLE`: `active`, `standby` ou `draining`.
- `ANTHARES_LEASE_TTL`: TTL padrão do lease em segundos.
- `ANTHARES_EXECUTOR_TTL`: janela de saúde dos executores.

## Endpoints

- `GET /health`
- `POST /v1/jobs`
- `GET /v1/jobs/{id}`
- `POST /v1/jobs/next`
- `POST /v1/jobs/{id}/heartbeat`
- `POST /v1/jobs/{id}/complete`
- `POST /v1/jobs/{id}/fail`
- `POST /v1/executors/heartbeat`
- `GET /v1/executors`
- `GET /v1/stats`
- `POST /v1/admin/role`

## Regras de consistência

1. Toda tarefa recebe `idempotency_key` estável.
2. Publicações devem usar `dedupe_key` derivada do conteúdo/conta/plataforma, por exemplo `kwai:<account>:<sha256-video>:<timecode>`.
3. O mesmo `idempotency_key` com payload diferente retorna HTTP 409.
4. Um lease é válido somente com `executor_id + lease_token + lease_generation` correspondentes e dentro do TTL.
5. Cada novo claim incrementa `lease_generation`; executores antigos perdem autoridade imediatamente após expiração/reclaim.
6. `complete` e `fail` aplicam fencing, impedindo um executor atrasado de alterar o estado.
7. O cliente de failover permanece fixado no provedor secundário depois da troca. O retorno ao primário é explícito.
8. O provedor secundário deve iniciar em `standby`; promoção ocorre somente quando o primário foi declarado indisponível pelo mecanismo de failover.
9. Todos os executores devem usar o cliente/roteador do control plane. Acesso direto simultâneo a dois provedores ativos é proibido porque cria risco de split-brain com bancos independentes.

## Execução local

```bash
cd anthares-control-plane
export ANTHARES_CONTROL_TOKEN='troque-isto'
export ANTHARES_PROVIDER='anthares-local'
export ANTHARES_ROLE='active'
pip install -r requirements.txt
python app.py
```

## Docker

Na raiz do repositório:

```bash
docker build -f anthares-control-plane/Dockerfile -t anthares-control-plane .
docker run --rm -p 8080:8080 \
  -e ANTHARES_CONTROL_TOKEN='troque-isto' \
  -e ANTHARES_PROVIDER='anthares-backup' \
  -e ANTHARES_ROLE='standby' \
  -v anthares-control-data:/data \
  -e ANTHARES_DB_PATH=/data/control.db \
  anthares-control-plane
```

## Testes

```bash
pytest -q anthares-control-plane/tests
```

## Modelo de implantação

- Primário: serviço atual, papel `active`.
- Secundário: Anthares Control Plane em provedor independente, papel `standby`.
- Enqueue: espelhado para os dois provedores com a mesma `idempotency_key` e `dedupe_key`.
- Claim: somente o provedor `active` entrega tarefas.
- Falha do primário: promover o secundário; clientes ficam aderentes ao secundário.
- Recuperação do primário: manter primário em `standby`, reconciliar jobs concluídos, depois executar failback explícito.

Esse desenho mantém a operação fora do Render quando necessário e evita failback automático durante recuperação parcial.
