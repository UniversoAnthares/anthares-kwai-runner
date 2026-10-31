# Liberação da oferta de contos beta ao papel anthares — código isolado
STATUS: PARTIAL
AREA: wordpress-home-beta-role
DATE: 2026-10-31
RUN: none
JOB: chatgpt-20261031-anthares-beta-role
COMMIT: 87961892894ccaa85aeda5e80d5a27a49061da7b
SUPERSEDES: test-hub/findings/20261031-lease-anthares-beta-role-default-gpt6.md

## Resultado
- Lease original encerrado; somente `anthares-pix-sales/includes/65-leitura-beta.php` foi modificado em `fix/anthares-beta-offer-role-access-20261031`.
- A checagem central `anthares_beta_host_pode_disponibilizar_contos` permite o papel exato `anthares`, mantendo o gate Etapa 3 para demais usuários.
- O salvamento de contos em modo beta aceita o papel `anthares`, conservando posse do conto e validação de nonce.
- Diff confirmado: 1 arquivo, 8 adições e 2 deleções; GitHub/GitLab main equivalentes antes da alteração.
- Teste unitário isolado do trecho via PHP 8.4: sintaxe válida e 3 cenários de autorização aprovados.
- Nenhuma transação de Runas, oferta pública ou escrita no WordPress de produção realizada.

## Limite
- Branch isolada, sem PR/merge/deploy: o workflow obrigatório de PR usa runner `self-hosted, Windows, anthares-wp-qa`, potencialmente o computador do titular; a regra atual impede novos trabalhos/artefatos no PC.
- Workflow hospedado da própria repo tem histórico explícito de bloqueio por billing/quota. Não adquirir recursos pagos.
- PHP lint integral e manifest coverage preflight ainda não foram executados; não declarar homologado em produção.

## Condição de retomada
- Validar manifest coverage e PHP lint integral em executor externo gratuito autorizado; criar PR, revisar, reconciliar branch HEAD, promover pela via canônica e verificar versão executada na Hostinger/WordPress.
- PRESERVAR a branch de código acima sem sobrescrever por outra sessão.
