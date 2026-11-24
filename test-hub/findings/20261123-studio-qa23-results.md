# Test Hub — QA23 e matriz 188, execução 23/11/2026
STATUS: PARTIAL
AREA: studio
DATE: 2026-11-23
OWNER: ChatGPT / QA_STUDIO_23_24_20261123
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/421 ; https://github.com/UniversoAnthares/anthares-wordpress/pull/422
JOB: WordPress production CLI with PHP 8.3 (no external job id)
COMMIT: 5ff987ba849f576cbc898b1bce8e6bb52737ff0e
SUPERSEDES: test-hub/findings/20261123-studio-qa23-lease.md

## Objetivo
Executar QA operacional por perfis e validar os 188 registros de rastreabilidade no novo Studio.

## Baseline
WordPress 7.1.5, PHP 8.3.37, site anthares.us, Studio em produção correspondente ao commit 4ec1643f5ffecbe945649fe4e65e63cd11ecd36c quando testado. 68/68 arquivos PHP, JS e CSS com SHA-256 idêntico a GitHub main naquela versão. A versão original /estudio e seus dados foram preservados.

## Evidências realizadas
- PHP 8.3 lint 34/34 PASS; Node check 22/22 JS PASS.
- QA manifest 775/775 arquivos classificados exatamente uma vez.
- 268 contratos Python: 255 PASS, 13 SKIP, 0 FAIL após alinhar as expectativas textuais antigas com a versão corrente; detalhes na PR #421.
- GET do WordPress REST: 120 rotas Studio registradas; visitante recebe 401 nas áreas privadas, descoberta 200.
- Seis papéis existentes testados sem mutação de usuário: 6/6 autorização coerente; dono de projeto acessa, outra conta bloqueada.
- Gerador: anthares-studio/tests/qa_g7_generator_transaction.php => TOTAL_PASS=16 / ROLLBACK=EXECUTED.
- Retenção: anthares-studio/tests/qa_g7_retention_continuous_transaction.php => TOTAL_PASS=26 / ROLLBACK=EXECUTED.
- Marcadores: anthares-studio/tests/qa_manuscript_markers_transaction.php => TOTAL_PASS=83 / ROLLBACK=EXECUTED.
- Aparições: anthares-studio/tests/qa_character_appearances_transaction.php => TOTAL_PASS=28 / ROLLBACK=EXECUTED.
- Biblioteca: anthares-studio/tests/qa_g7_library_transaction.php => TOTAL_PASS=30 / ROLLBACK=EXECUTED.
- Total transacional: 183 PASS em cinco execuções com rollback confirmado e código de saída zero.
- Verificação de leitura reaplicada após execução: permissões e segregação PASS; contagem de posts do Studio 82 antes / 82 depois.
- Matriz CSV 09-MATRIZ-188-REQUISITOS.csv: 188/188 com estado, fonte candidata, teste, evidência, dependência, data e responsável institucional; 55 específicos, 108 parciais, 25 sem implementação específica comprovada. Merge PR #421; evidências transacionais vinculadas a 21 IDs pela PR #422.

## Limites do resultado
O item 24 foi atualizado e incorporado ao main. O item 23 está PARTIAL: não foram realizados browser E2E em sessão autenticada com leitor/autor/mentor real, comprador ativo e expirado, concorrência efetiva, carga extensa, mobile, leitores de tela e restauração isolada. A execução de testes transacionais reais com rollback NÃO autoriza registrar esses cenários como PROVEN. Bun indisponível causou 13 SKIPs.

## Segurança
Somente fixture sintética em transação InnoDB, todos os testes com ROLLBACK=EXECUTED; dados existentes preservados. Não foram executadas operações de postagem pública, comunicação externa, pagamentos ou alteração de permissões de usuários. Nenhum dado sensível, ID ou texto pessoal registrado neste finding.

## Consequência
Encerrar esta lease RUNNING com resultado PARTIAL; as lacunas do QA23 dependem de novas evidências específicas de UX/comércio/performance. Consultar a matriz e o relatório detalhado em docs/anthares-studio/06-QUALIDADE-SEGURANCA-E-TESTES.md antes de repetir testes.
