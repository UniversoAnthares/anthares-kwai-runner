# Forgejo principal — CI/CD isolado de contratos, com homologação pendente
STATUS: RUNNING
AREA: architecture/forgejo-main-ci-cd
DATE: 2026-10-28
RUN: none — Actions do repositório principal ainda desabilitadas
JOB: none
COMMIT: 6599ba3b0e9cc8ddf06b4a8811b28f7f6f811ed3
SUPERSEDES: none

## BASELINE_PROVEN
A verificação viva de 28/10/2026 confirmou: o repositório Forgejo público
`anthares-admin/anthares-kwai-runner` (repo_id=1) está sincronizado com GitHub,
mas `has_actions=false` e não possui `repo_unit` tipo 10 nem execuções próprias
em `action_run`. O runner `anthares-ci-hostinger-v2` (ID 5) está funcional,
porém limitado ao repositório privado `anthares-ci-sandbox` (repo_id=20).
Os 27 workflows migrados de Codeberg usam labels legadas, diversos schedules e
push triggers. Sua ativação indiscriminada não é um teste válido de CI/CD.

## FAILED_AVOIDED
Não reutilizar credenciais nem runners de publicação; não promover runner de
escopo específico para organização; não habilitar todos os workflows legados
por inferência; não repetir pelo mesmo ou outro canal consulta autenticada
bloqueada pelas configurações de segurança. Não gerar publicações.

## SUCCESS_SIGNAL
Após habilitação administrativa autorizada e quarentena dos workflows legados,
um runner Hostinger `anthares-ci-main-host`, com escopo restrito ao repo_id=1
e somente ferramentas de CI, executa `anthares-main-ci-cd.yml` na branch main:
CI comprova sha do checkout, passa verificações locais e testes unitários
offline, e CD instala/valida comprovante imutável de implantação restrito
ao diretório privado `~/.anthares-forgejo/ci-main-cd`.
O resultado é evidenciado por run/job ID, SHA, logs e recibo privado.

## FAILURE_SIGNAL
Actions ainda desabilitadas; runner não atribuído; workflow bloqueado ou sem
testes aprovados; recibo ausente; SHA divergente; label de outro serviço;
qualquer operação de publicação inesperada; fila de workflows legados ativa.

## TEST_VALIDITY
Workflow somente `workflow_dispatch`, permissão `contents: read`, sem tokens
de publicação, sem deploy de aplicações, sem alterar primários ou filas.
A instalação do comprovante privado só ocorre depois do sucesso de CI.
A criação deste finding e do workflow NÃO prova execução e não permite
classificar o item como concluído antes do teste real de CI e CD.

## Próximo passo
O proprietário/admin deve autorizar a habilitação Actions no repo principal
e vincular runner dedicado de escopo repo, preservando o runner de sandbox;
os workflows legados precisam ficar inertes antes do primeiro evento.
Nenhuma ativação foi executada por esta mudança.
