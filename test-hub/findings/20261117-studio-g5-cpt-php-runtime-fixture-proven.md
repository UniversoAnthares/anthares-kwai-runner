# G5 CPTs — fixture PHP isolada concluída

STATUS: PROVEN
AREA: anthares-studio/g5/private-cpt-admin-qa
DATE: 2026-11-17
JOB: studio-g5-cpt-php-runtime-fixture-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/317
COMMIT: 81484ac4e0a284f8a3d45afca19abca595251b70
SUPERSEDES: test-hub/findings/20261117-studio-g5-cpt-php-runtime-fixture-running.md

## Resultado
- Teste dinâmico permanente em anthares-studio/tests/test_acf_contract.py.
- A implementação pega o bloco anst_register_types() do PHP do plugin, cria um stub de register_post_type() e usa PHP CLI como subprocesso isolado, sem WordPress, arquivos de teste persistentes nem banco.
- Verifica quatro post types exatos, oito características de privacidade/admin por tipo e onze capacidades primitivas por tipo (76 verificações).
- Execução equivalente em executor isolado ChatGPT, usando o bloco efetivo de registro replicado da branch #317: test_cpt_registry_real_php_stub ... ok; Ran 1 test; OK. PHP lint do bloco: PASS.
- A suíte completa da HEAD da PR #317 permanece por executar em checkout isolado. WordPress real com papéis admin e não admin permanece pendente.

## Limites e ação segura
- Apenas o contrato de registro PHP simulado está PROVEN; homologação de permissões WordPress real continua PARTIAL, sem alteração da produção.
- PR #317 DRAFT, dependente G4/PR #316 e demais gates de teste; não fazer merge/deploy até validar.
