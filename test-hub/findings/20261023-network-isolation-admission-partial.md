# Isolamento do CORTES — controlador de admissão
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-23
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/185
JOB: WinRemote — suite temporária offline e preflight da governança real
COMMIT: 2fec81583c71c059324abc4ff92c6b0631595f85
SUPERSEDES: none

## Objetivo
Estabelecer verificação obrigatória documental e escopo de edição por rede.

## Resultado
Branch independente architecture/network-isolation-guard-20261023, PR draft #185.
Implementados ci/network_scope_guard.py e ci/network_change_admission.py.
Suite offline: 24 testes, 23 PASS, 1 SKIP por restrição de symlink Windows.
Preflight real recusa worktree Git sem documentação; aprova cópias válidas
em docs/anthares, versão 898630c1c5143f34; resultado admission=PASS,
scope=threads, deploy_authorized=false.
Bloqueios testados: arquivos de outra rede, módulos compartilhados, merges,
mudanças revertidas no histórico, documentação alterada e base Git inválida.

## Consequência
STATUS PARTIAL. PR draft ainda não integrada. Não há garantia de isolamento
de OS, secrets, perfis Browser Hub, fila, ledger, execução ou implantação.
O controlador privilegiado de releases e os limites ACL devem ser integrados
antes de entregar acesso de escrita por agente. Nenhum publicador, serviço,
perfil, fila ou autenticação foi alterado neste teste.
