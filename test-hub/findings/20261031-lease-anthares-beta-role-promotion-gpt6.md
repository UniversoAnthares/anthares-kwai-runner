# Lease — promoção controlada do acesso beta para papel anthares
STATUS: RUNNING
AREA: wordpress-home-beta-role
DATE: 2026-10-31
RUN: none
JOB: chatgpt-20261031-beta-role-promotion
COMMIT: 87961892894ccaa85aeda5e80d5a27a49061da7b
SUPERSEDES: test-hub/findings/20261031-wordpress-beta-role-code-partial-gpt6.md

## Titularidade, expiração e baseline
Owner: ChatGPT/GPT-6; área exclusiva `anthares-pix-sales/includes/65-leitura-beta.php`; expira 30 minutos após este registro. Arquivo live SHA-256 `932f1aae8cf9e4a45dd74fd71d0f65986e0f3497972c37a65639ad246d7c25ac` igual ao GitHub main. Peer GitLab main idêntico ao GitHub main para esse arquivo. Branch fixa `fix/anthares-beta-offer-role-access-20261031`.

## Testes externos comprovados
BASELINE_PROVEN: Hostinger SSH executou PHP 8.3 lint sem erros, `qa/manifest-coverage-preflight.py --check` PASS, auditable=599 assigned=599 exactly_once=yes, e `qa/anthares-orchestrator-qa.php` 11 PASS + contrato íntegro. Clone temporário removido por trap; nenhum armazenamento no PC.
FAILED_AVOIDED: evitar GitHub Actions PR em runner Windows `anthares-wp-qa` e evitar pagamentos; QA equivalente executada na Hostinger. Recusa de segurança não será contornada.
SUCCESS_SIGNAL: PR de código aceita, merge autorizado, produção atualizada com validação de checksum e php -l, API da função libera papel `anthares` e conserva validações existentes.
FAILURE_SIGNAL: conflito de SHA, divergência de live/Git, falha de QA/WordPress, checks obrigatórios não aprovados ou deploy não verificável.
TEST_VALIDITY: HEAD e file-SHA de GitHub revalidados, versão em produção lida por SHA-256, nenhuma transação financeira/teste com ofertas reais.
Sem alteração dos demais papéis, saldo, pagamentos ou serviços compartilhados; não reexecutar uma publicação incerta.
