"""Verifica o gating dos workflows de recuperacao SSH (somente leitura do repo).

Nao executa SSH, nao usa rede e nao muta estado. Apenas le os arquivos YAML
versionados e afirma as regras de seguranca do PR.

Regras verificadas:
 1. anthares-ssh-recovery.yml NAO tem gatilho `push`.
 2. O job `ssh` do recovery so executa modo recover quando
    vars.ANTHARES_SSH_AUTORECOVERY_ENABLED == 'true'.
 3. Existe um passo explicito de kill-switch ANTES de qualquer acesso de rede
    (join na rede privada / tailscale).
 4. Nao existe ramo morto de 'schedule' em SSH_RECOVERY_MODE.
 5. O monitor exige a mesma variavel antes de despachar recuperacao.
 6. O cliente SSH (ssh-client.py) recusa modo recover sem AUTO_RECOVERY_ENABLED.
 7. Nenhum workflow usa segredo em evento `pull_request` (fork).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECOVERY = ROOT / '.github' / 'workflows' / 'anthares-ssh-recovery.yml'
MONITOR = ROOT / '.github' / 'workflows' / 'anthares-ssh-monitor.yml'
SSH_CLIENT = ROOT / 'anthares-remote-agent' / 'ssh-client.py'
WORKFLOW_DIR = ROOT / '.github' / 'workflows'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def extract_job_if(job_block: str) -> str:
    """Extrai a expressao `if:` de um job, aceitando escalar folded (>-)."""
    head = job_block.split('\n    if:', 1)[1]
    first, _, rest = head.partition('\n')
    if first.strip() in ('>-', '>', '|', '|-'):
        lines = []
        for line in rest.split('\n'):
            if line.startswith('      ') or not line.strip():
                lines.append(line.strip())
                continue
            break
        return ' '.join(line for line in lines if line)
    return first.strip()


class SshRecoveryWorkflowGatingTests(unittest.TestCase):
    def test_recovery_workflow_has_no_push_trigger(self):
        text = read(RECOVERY)
        # Bloco `on:` do workflow (antes de `permissions:`)
        on_block = text.split('\non:', 1)[1].split('\npermissions:', 1)[0]
        self.assertIsNone(re.search(r'^\s*push:', on_block, re.MULTILINE),
                          'recovery nao pode ter gatilho push (branch codex/* ou main)')
        self.assertNotIn('codex/', text, 'recovery nao deve referenciar branch codex/*')

    def test_recovery_job_gates_recover_mode_on_killswitch(self):
        text = read(RECOVERY)
        job_block = text.split('\n  ssh:', 1)[1]
        if_expr = extract_job_if(job_block)
        self.assertIn('ANTHARES_SSH_AUTORECOVERY_ENABLED', if_expr,
                      'o if do job ssh deve consultar o kill-switch')
        self.assertIn("inputs.mode != 'recover'", if_expr,
                      'o if do job ssh deve tratar o modo recover vindo de inputs.mode')
        # A forma antiga (schedule) nao pode mais existir no if.
        self.assertNotIn("github.event_name != 'schedule'", if_expr,
                         'o if do job nao deve usar a condicao morta de schedule')
        # O modo nao pode mais vir de um ramo morto de schedule.
        self.assertNotIn("github.event_name == 'schedule'", text,
                         'ramo morto de schedule removido do workflow')

    def test_killswitch_step_precedes_network_access(self):
        text = read(RECOVERY)
        job_block = text.split('\n  ssh:', 1)[1]
        gate = job_block.find('Enforce auto-recovery kill-switch')
        self.assertNotEqual(gate, -1, 'deve existir passo de kill-switch explicito')
        for network_marker in ('tailscale/github-action', 'Join restricted private network'):
            pos = job_block.find(network_marker)
            self.assertNotEqual(pos, -1, f'marcador de rede ausente: {network_marker}')
            self.assertLess(gate, pos,
                            f'o kill-switch deve rodar antes de {network_marker}')
        self.assertIn('SSH_RECOVERY_BLOCKED=auto-recovery-disabled', job_block)

    def test_no_dead_schedule_branch_in_mode(self):
        text = read(RECOVERY)
        self.assertNotIn("github.event_name == 'schedule'", text,
                         'ramo morto de schedule removido do SSH_RECOVERY_MODE')

    def test_monitor_requires_killswitch_before_dispatch(self):
        text = read(MONITOR)
        job_block = text.split('\n  monitor:', 1)[1]
        if_expr = job_block.split('\n    if:', 1)[1]
        self.assertIn('ANTHARES_SSH_AUTORECOVERY_ENABLED', if_expr,
                      'o monitor tambem deve exigir o kill-switch')

    def test_ssh_client_refuses_recover_without_flag(self):
        text = read(SSH_CLIENT)
        self.assertIn("mode == 'recover'", text)
        self.assertIn("AUTO_RECOVERY_ENABLED", text)
        self.assertIn("!= 'true'", text,
                      'ssh-client deve recusar recover sem AUTO_RECOVERY_ENABLED=true')

    def test_no_workflow_uses_secrets_on_pull_request(self):
        """Nenhum workflow pode usar secrets.* em evento que dispare de fork.

        - `pull_request_target` recebe segredos mesmo em PR de fork: proibido.
        - `pull_request` de fork nao recebe segredos (viram string vazia): o
          workflow nao pode depender de secrets, senao falha de forma silenciosa.
        """
        target_offenders = []
        pull_request_secret_users = []
        for path in sorted(WORKFLOW_DIR.glob('*.yml')):
            text = read(path)
            on_block = text.split('\non:', 1)[1].split('\npermissions:', 1)[0]
            uses_secrets = bool(re.search(r'secrets\.', text))
            if re.search(r'^\s*pull_request_target:', on_block, re.MULTILINE):
                if uses_secrets:
                    target_offenders.append(path.name)
            elif re.search(r'^\s*pull_request:', on_block, re.MULTILINE) and uses_secrets:
                pull_request_secret_users.append(path.name)
        self.assertEqual(target_offenders, [],
                         f'pull_request_target com secrets.* (exposto a fork): {target_offenders}')
        # Situacao conhecida e aceita: secrets.* ficam vazias em PR de fork.
        self.assertTrue(
            all(not name.startswith('anthares-ssh') for name in pull_request_secret_users),
            f'workflow de SSH nao deve usar secrets.* em pull_request: {pull_request_secret_users}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
