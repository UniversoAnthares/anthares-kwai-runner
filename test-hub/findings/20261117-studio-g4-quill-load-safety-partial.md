# G4 — proteção de importação Quill isolada e verificada em código

STATUS: PARTIAL
DATE: 2026-11-17
AREA: anthares-studio/g4/quill-load-safety
JOB: studio-g4-quill-load-safety-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/319
COMMIT: 599a72284e61510ec2f7e92e518f490e02a5a541
SUPERSEDES: test-hub/findings/20261117-studio-g4-quill-load-safety-running.md

## Implementação de código (PR draft)
- `setupEditor()`: catch de `editor.setContents()` preserva o Delta e oferece preview somente leitura, com texto escapado.
- `chapterLoadBlockedId`: identifica falha de importação para impedir qualquer `POST /chapters/{id}` posterior pelo `saveChapter()` e impedir `queueSave()`.
- Desabilita título, botão salvar e marcação no erro; status explícito de carregamento inválido.
- Teste de regressão em `test_g6_fixed_navigation.py`.

## QA isolado confirmado
- Checkout efêmero Hostinger da HEAD 599a72284e61510ec2f7e92e518f490e02a5a541.
- Python 3.6.8: `Ran 67 tests ... OK` (67/67 PASS), após ajuste de selector para preservar contrato antigo de ações HTML.
- PHP 8.3: `php -l` quatro módulos 4/4 PASS.
- Manifesto QA: `auditable=665 assigned=665 exactly_once=yes` PASS.
- Orquestrador QA: 11/11 PASS.
- Job remoto 2f683e230bc4c32f1c9d0e1cfe67938b FINAL_EXIT=0.
- JS de 136584 caracteres carregado via SSH em memória: Node v24 `--check` PASS; job 75ddda29c2703ae37bcd0f06adcb3277.
- Teste Node com VM e mocks em primeira tentativa falhou por mapeamento do controle no harness (`Controls enabled`), sem comprovação de falha real da interface. Tentativas subsequentes de reteste encontraram erros internos do conector; classificar essa prova dinâmica como INCONCLUSIVA.

## Estado do deploy
- Plugin legado PHP SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf intocado.
- Produção ainda com JS SHA256 65f51b87ad599258270f4a2264ef998a43866271882751d9d3bab1d69c889a2a; a linha de risco `catch(e){editor.setText('','silent')}` segue no arquivo vivo (verificado 22:46 UTC).
- Deploy/merge NÃO realizados. A PR #316 tem lease G4 de outra frente e requer homologação funcional antes de promoção; riscos de código original protegidos na branch independente.
- Sem mutação produtiva e sem teste REST real de gravação. ACF runtime permanece OFF.
