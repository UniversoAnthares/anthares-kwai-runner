# Anthares Android Runtime

Camada própria entre Anthares Remote e backends Android. O runtime encapsula detalhes de MEmu/ADB e expõe operações de status, recovery, launch e identidade.

## Estado atual

- Adapter completo inicial: `MEmuAdapter` para `MEmu_4`.
- Transporte ADB encapsulado em `AdbTransport`.
- Estados estruturados incluem `RUNNING_TRANSPORT_OFFLINE`.
- Recovery progressiva: disconnect/connect, restart do daemon ADB e requery.
- Estado/eventos persistidos em `C:\ProgramData\AntharesAndroidRuntime`.
- Watchdog com lease TTL para evitar concorrência destrutiva.
- Testes unitários cobrem parsing ADB, state model e health score.

## CLI

```powershell
py -3 -m anthares_android_runtime.runtime status
py -3 -m anthares_android_runtime.runtime recover
py -3 -m anthares_android_runtime.runtime launch-kwai
py -3 -m anthares_android_runtime.runtime identity
py -3 -m anthares_android_runtime.runtime ui-dump
```

A saída é JSON para consumo pelo Anthares Remote. O Anthares Remote não precisa conhecer path do ADB, serial, porta ou processo do backend.

## Recovery ladder

1. observar transport state;
2. disconnect serial;
3. reconnect serial;
4. restart do daemon ADB;
5. requery;
6. adapter-specific recovery;
7. restart controlado do backend somente após as etapas leves falharem;
8. failover futuro para adapter elegível.

## MEmu_4 — finding operacional 2026-10-15

O runtime reproduziu o estado real `process_running=true`, serial `127.0.0.1:21543` e transport offline/missing. A recovery ADB leve falhou semanticamente. A inspeção do guest mostrou BIOS parando em `Could not read from the boot medium! System halted.`. Também foi encontrado um path inválido no `hyperv.json`: attachment 0 apontava para um `disk1.vmdk` ausente dentro do diretório da VM, enquanto o disco base real existe em `D:\Program Files\Microvirt\MEmu\image\71\MEmu71-2022103100023FFF-disk1.vmdk`. O arquivo foi preservado com backup antes da correção local.

A VM e o disco de dados não devem ser apagados, recriados ou formatados. F17 continua aberta até haver prova de `@lucasrosalem` antes e depois de restart controlado.

## Adapters futuros

A interface atual separa manager, adapter e transporte. AOSP, BlueStacks, Nox e MuMu devem implementar a mesma superfície sem expor ADB ao Anthares Remote.
