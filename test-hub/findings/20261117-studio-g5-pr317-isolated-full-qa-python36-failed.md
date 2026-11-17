# Studio PR317 — QA integral Hostinger: incompatibilidade Python 3.6

STATUS: FAILED
DATE: 2026-11-17
AREA: anthares-studio/g5/qa-isolated-pr317
JOB: studio-pr317-hostinger-full-qa-20261117
COMMIT: ef6db8c94395bbbc448925fc66887c04f9f59060
SUPERSEDES: test-hub/findings/20261117-studio-g5-pr317-isolated-full-qa-running.md
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/317

## Teste válido e causa
- Clone privado e efêmero de HEAD exata na Hostinger: PASS.
- Python 3.6.8; 58 testes encontrados, 57 PASS e 1 ERROR. A única falha foi test_cpt_registry_real_php_stub (test_acf_contract.TestAcfContract): TypeError na invocação subprocess.run(text=True,capture_output=True), parâmetros disponíveis somente em Python >=3.7. A função PHP do plugin não chegou a ser executada nesta rodada.
- PHP 8.3 lint dos quatro arquivos: 4/4 PASS.
- qa/manifest-coverage-preflight.py --check: PASS auditable=665 assigned=665 exactly_once=yes.
- php83 qa/anthares-orchestrator-qa.php: todos os 11 itens PASS.
- Diretório temporário de clone removido e ausência verificada; nenhum arquivo da produção modificado.

## Correção causal planejada
Substituir apenas subprocess.run(text=True,capture_output=True) por subprocess.run(universal_newlines=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE), suportado no Python 3.6. Executar de novo em clone novo e registrar evidencia. Não alterar WordPress, dados, opções ou plugin original.

## Limites
Este FAILED é do harness de QA Python, sem evidência de falha do Studio no WordPress. Nenhum teste de escrita real ou acesso ao navegador autenticado foi tentado.
