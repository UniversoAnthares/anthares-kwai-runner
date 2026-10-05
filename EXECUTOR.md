# Anthares Android Executor Contract

The executor is a disposable Android VM created only when a job exists.

Lifecycle:
1. controller requests a job;
2. GitHub provisions a standard public Ubuntu runner;
3. workflow boots the Android emulator with KVM acceleration;
4. validated Kwai vault is downloaded and checksum-verified;
5. job automation runs;
6. result/evidence is returned;
7. VM is destroyed.

Operational invariants:
- no PC dependency;
- no persistent runner host;
- no credentials in repository files;
- no private repository dependency;
- one active Kwai Android job at a time;
- retries must be idempotent;
- visual tunnel is diagnostic only;
- standard GitHub-hosted runners only; never larger runners.

The public repository is infrastructure only. Private publishing policy and controller state remain outside it.
