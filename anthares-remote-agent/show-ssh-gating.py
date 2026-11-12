"""Mostra o estado efetivo do gating dos workflows SSH (somente leitura).

Nao usa rede, nao muta nada. Imprime o que o GitHub ActionsAvaliaria a partir
dos arquivos versionados, paraconferencear com o relatorio.
"""
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECOVERY = ROOT / '.github' / 'workflows' / 'anthares-ssh-recovery.yml'
MONITOR = ROOT / '.github' / 'workflows' / 'anthares-ssh-monitor.yml'


def load(path):
    # 'on' vira True no YAML 1.1; normaliza.
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if True in data:
        data['on'] = data.pop(True)
    return data


def main():
    rec = load(RECOVERY)
    mon = load(MONITOR)

    print('=== anthares-ssh-recovery.yml ===')
    print('gatilhos:', sorted(rec['on'].keys()))
    print('modo padrao do dispatch:', rec['on']['workflow_dispatch']['inputs']['mode']['default'])
    ssh = rec['jobs']['ssh']
    print('environment do job ssh:', ssh.get('environment'))
    print('if do job ssh:', ' '.join(ssh['if'].split()))
    print('needs:', ssh.get('needs'))
    steps = [s.get('name', s.get('uses', '?')) for s in ssh['steps']]
    print('ordem dos passos do job ssh:')
    for i, name in enumerate(steps, 1):
        print(f'  {i}. {name}')

    print()
    print('=== anthares-ssh-monitor.yml ===')
    print('gatilhos:', sorted(mon['on'].keys()))
    print('if do job monitor:', ' '.join(mon['jobs']['monitor']['if'].split()))

    print()
    print('=== avaliacao do kill-switch (variavel ANTHARES_SSH_AUTORECOVERY_ENABLED) ===')
    for enabled in ('true', 'false'):
        for mode in ('probe', 'recover'):
            job_runs = (mode != 'recover') or (enabled == 'true')
            step_ok = not (mode == 'recover' and enabled != 'true')
            print(f'  var={enabled:<5} mode={mode:<7} job executa={job_runs!s:<5} passo de bloqueio passa={step_ok}')


if __name__ == '__main__':
    main()
