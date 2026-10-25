# REL19 — controlador de revisao de release, contrato offline comprovado
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-25
RUN: none
JOB: REL19-20261025
COMMIT: 760aaebb9ebc545fe925e51ffac26141279fb6e5
SUPERSEDES: test-hub/findings/20261025-rel19-review-gate-running.md
LEASE_AREA: cortes-release-review-readonly
LEASE_OWNER: ChatGPT-REL19
LEASE_STATUS: CLOSED

## Objetivo
Adicionar atestacao de pacote ZIP e recibo independente sem qualquer caminho de deploy, preservando os publicadores e as suites de teste anteriormente restritas.

## Resultado
PR DRAFT https://github.com/UniversoAnthares/anthares-clipper/pull/205, base main db6c12fdaa0af01e3b68b8a527b2e02c12c21837. Adicoes: ci/network_release_controller.py, tests/test_network_release_controller.py e docs/RELEASE_CONTROLLER_REL19.md. Sem alteracoes de CI, filas, segredos, triggers, banco, executores, publicadores ou branch main.

## Evidencia decisiva
Execucao real Windows via Anthares Remote / py -3, sandbox independente com sete arquivos lidos por conector GitHub e gravados sem checkout operacional. Comando python -m unittest discover -s tests -p test_network_release_controller.py -v. Saida: "Ran 8 tests in 0.158s" / "OK" / "REL19_EXIT=0" / "REL19_CLEAN=True". Resultados: 8 PASS; negativas para PIN autorizador, origem fora do controller, pacote sob agente, SHA alterado, campo extra, symlink, falha de verificador e recibo duplicado. Pacote sintetico; independent verifier mocked, nao considera integracao end-to-end. A primeira tentativa via clone teve resultado incerto e deixou diretorio .git incompleto (sem processo de git ativo na reconciliacao); metodo corrigido transferiu os blobs pelo GitHub conector. Primeira captura de unittest foi interrompida pelo tratamento PowerShell de stderr; corrigida a captura usando cmd.exe e log temporario. Nenhuma suite restrita foi reexecutada.

## Consequencia e limites
PROVEN SOMENTE CONTRATO REVIEW-ONLY do novo modulo; entrega implementada em DRAFT sem merge/implantacao. Recibos incluem deploy_authorized=false, promotion_authorized=false e publisher_invoked=false. Continua PENDENTE: ACL/IAM de identidade externa, fonte de PIN assinada e protegida em runtime real, gate obrigatorio de promocao, CI e rollback, duas identidades negativas e reconciliacao de governanca INDICE.md local f6fc9ca59a96e451 versus GitHub main 2e28d54043d6bad1. Nao usar este registro para liberar postagem social, cutover ou rede inteira.
