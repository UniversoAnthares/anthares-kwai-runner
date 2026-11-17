# Studio PR317: reteste integral após correção Python 3.6

STATUS: RUNNING
DATE: 2026-11-17
AREA: anthares-studio/g5/qa-isolated-pr317
JOB: studio-pr317-hostinger-python36-retest-20261117
OWNER: ChatGPT / OBSERVATORIO IPB
SOURCE: UniversoAnthares/anthares-wordpress PR #317 HEAD 4d2b12a2d8a81a57b3448a952f464985f8204c11
SUPERSEDES: test-hub/findings/20261117-studio-g5-pr317-isolated-full-qa-python36-failed.md
BASELINE_PROVEN: 57/58 unittest passaram na execução anterior; único erro era subprocess.run(text=True,capture_output=True) incompatível com Python 3.6.
FAILED_AVOIDED: substituição causal por universal_newlines=True,stdout=PIPE,stderr=PIPE; novo checkout temporário de origem GitHub, sem tocar na instalação ativa.
SUCCESS_SIGNAL: 58/58 PASS, PHP8.3 lint quatro módulos, preflight manifesto 665/665, orquestrador 11/11.
FAILURE_SIGNAL: qualquer falha explicitamente registrada com traceback, sem deploy.
TEST_VALIDITY: teste de código isolado e contratos; gravação real WordPress e screenshots ainda não cobertos.
ROLLBACK: remoção obrigatória em trap do clone temporário em Hostinger.
