# 2026-10-07 — localização real do anthares-control

- STATUS: PROVEN
- AREA: architecture/cloudflare-control
- REPOSITORY: UniversoAnthares/anthares-clipper
- DATE: 2026-10-07
- RUN: manual repository audit
- COMMIT: 39f7c889f9a569d7ebd1b2c8c635965fa118548f

## Finding

O código-fonte do Worker Cloudflare `anthares-control` está no repositório GitHub `UniversoAnthares/anthares-clipper`, em `cloudflare-worker/`. O Worker é denominado `anthares-control` em `cloudflare-worker/wrangler.toml`.

A implementação atual contém o Worker de controle, Durable Object `AntharesQueue`, persistência `ANTHARES_STATE`, autenticação GitHub OIDC, heartbeat, leasing/reconciliação de jobs, seleção de executores e endpoints de diagnóstico/saúde.

## Evidence

- Commit `709fc13d3630bb4b63f40f7188d345c0c8d4d3d6`: criação inicial do Worker `anthares-control`.
- Commit `5eca885070d8bac9216808c311ef72c2eb61b3c0`: binding KV `ANTHARES_STATE`.
- Commit `289f98f18f141938b6d68ef2f3301f610b23764e`: leasing distribuído e reconciliação.
- Commit `087ce35a52a6774f37acc323f0e04f5f085a6ab9`: máquina de estados de jobs.
- Arquivo atual: `cloudflare-worker/src/index.js`.

## Correction

A conclusão anterior de que o código-fonte não estava em nenhum repositório GitHub conectado estava incorreta. O código está no `anthares-clipper`; o problema real é que ele não é um repositório separado e o estado de espelhamento GitLab dos repositórios ainda não está configurado.

## Next action

Manter `anthares-control` em `anthares-clipper/cloudflare-worker/` como fonte versionada enquanto a sincronização GitHub↔GitLab é concluída. Não criar um segundo control plane.
