# Lease — MEmu4 ghost VM transport repair

STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-15
RUN: none
JOB: Anthares Remote live roundtrip
COMMIT: pending
SUPERSEDES: none
LEASE_OWNER: chatgpt-memu4-ghost-vm-repair-20261015
LEASE_EXPIRES: 2026-10-15T22:49:00-04:00

## Objetivo
Recuperar o transporte ADB do `MEmu_4` sem limpar dados, reinstalar Kwai ou publicar conteúdo, para retomar a prova F17 de sessão autenticada.

## BASELINE_PROVEN
Anthares Remote está conectado via Vercel+Neon e executando comandos reais. `MEmu_4` possui forwarding `127.0.0.1:21543 -> 10.0.2.15:5555`; `adb connect` retorna `offline`.

## FAILED_AVOIDED
Já foram tentados anteriormente `adb start-server`, disconnect/connect, polling e reinício controlado do backend sem recuperar o transporte. Não repetir esses caminhos isoladamente.

Mudança causal desta rodada: evidência nova mostra `MEmuHeadless.exe --comment MEmu_4 --startvm ...` e `MEmu.exe MEmu_4` ainda em execução, mas `MEmuManage list runningvms` está vazio e `showvminfo MEmu_4` informa `VMState="poweroff"`. Isto caracteriza processos fantasma/stale do frontend/headless, não um guest Android realmente executando.

## SUCCESS_SIGNAL
Após remover somente os processos fantasma de `MEmu_4` e iniciar a VM pelo hypervisor, `MEmuManage list runningvms` deve listar `MEmu_4`, `VMState` deve ser `running` e `D:\Program Files\Microvirt\MEmu\adb.exe devices -l` deve mostrar `127.0.0.1:21543 device` (não `offline`).

## FAILURE_SIGNAL
VM continua `poweroff`/ausente de `runningvms`, startvm falha, ou ADB permanece `offline` depois de um boot real confirmado.

## TEST_VALIDITY
Nenhum `pm clear`, factory reset, reinstalação, remoção de userdata, mudança de conta ou publicação é permitida. O teste é inválido se não houver prova independente do estado real da VM antes e depois da correção.
