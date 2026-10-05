# Profile/login matrix completed: harness and resource gate
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37378176856
JOB: matrix of 10
COMMIT: b71089fb032edbed2287558cb40a22a7458b24a0
SUPERSEDES: test-hub/findings/20261005-2150-profile-login-probes-running.md

## Objetivo
Comparar dez rotas após o onboarding adaptive para chegar a Profile/login.

## Resultado
A matriz terminou com conclusão global failure por uma falha de infraestrutura em me-coordinate: SDK/emulator archive inválido e conexão ADB recusada. Os demais jobs executaram. Nenhuma rota comprovou login. profile-text e back-then-profile chegaram à navegação principal, mas a UI exibiu "Can't connect to server" e "Resource downloading ...". profile-coordinate, inspect-profile, profile-twice, discover e login-deeplink permaneceram no onboarding. profile-deeplink e inbox terminaram com "Pixel Launcher isn't responding".

## Evidência decisiva
profile-text: KWAI_LAUNCHED; PROFILE_UI contém "can’t connect to server" e "resource downloading".
back-then-profile: mesmo gate.
me-coordinate: "Error on ZipFile unknown archive", depois TCP 5554 Connection refused; isto é falha do mecanismo de teste, não da hipótese.

## Consequência
Não repetir a matriz inteira. Preservar adaptive como travessia comprovada. O próximo teste deve isolar rede/backend/download de recursos em um único Android, com checkpoints HTTP/DNS e progresso da UI, antes de retestar Profile. Não marcar me-coordinate como estratégia FAILED.
