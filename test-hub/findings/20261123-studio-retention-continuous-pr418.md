# Anthares Studio: retenção contínua, estados declarados — PR #418

Data: 2026-11-23, America/Campo_Grande. Repositório: UniversoAnthares/anthares-wordpress. PR #418 squash em `main`: `d69d7a98646deb19d0a1d123f0a40cfd58246e38`.

## Requisitos implementados

- Registro opt-in de posição observada por edição publicada, de 0 a 100 em passos inteiros de 1%.
- Manutenção do maior percentual observado e do percentual atual da visita; restauração por usuário/versão, com HMAC restrito ao servidor.
- Ações explícitas de leitura: iniciar, interromper, retomar e confirmar conclusão após alcançar 100%. Escrolar até 100% não declara conclusão.
- Registros antigos com stage start/10/25/50/75/90/100 continuam aceitos; registros sem declaração de estado permanecem em andamento.
- Relatório privado do autor com 101 pontos de curva, seletor de 1%, tabela acessível e quatro categorias agregadas: em andamento, interrompida expressamente, concluída expressamente e sem atividade há >7 dias. Inatividade não é denominada abandono.
- Mesma proteção de privacidade: contagens só após 10 leitores distintos consentidos, uma identidade HMAC por edição, rota privada, exclusão definitiva do dado do próprio leitor, recalculando limiar após exclusão.
- Versão anterior `/estudio/` preservada.

## QA e deploy

- WordPress real pós-deploy: `qa_g7_retention_continuous_transaction.php` 26/26 PASS, `qa_g7_retention_transaction.php` 9/9 PASS, ambos `ROLLBACK=EXECUTED`.
- Python: `test_retention_continuous_contract.py` 3/3, `test_retention_reports_contract.py` 3/3.
- 770/770 arquivos atribuídos exatamente uma vez no QA manifest.
- PHP 8.3 lint para retenção e publicação: PASS. V8 parse dos três scripts JS: PASS.
- Pré-deploy CAS por hash Git para seis arquivos, validação da origem em GitHub main e staging, backup privado e rollback automático em falha.
- Implantação: `DEPLOY_PR418_OK`; backup em `/home/u566597497/domains/anthares.us/studio-private-backups/20261123-retention-continuous-pr418`.
- Conferência CDN HTTPS com cachebuster: `studio-g7-public-reader.js` `129787476e20b083be582f3bd90900a8b8bffaa3`, `studio-g7-retention-reports.js` `aaf04d2763dfdcb93e8ede0b201dcaaf8e1e1229`, `studio-g7-publishing.js` `1bc8db91fa53749ad5f527226bfed2722e37bcfa`, `estudio.css` `ba766ddc53883869839507cc1f7d96368c333ed0`.
- `/studio/` HTTP 200 e `/estudio/` HTTP 200. Hash do PHP legado `e4a9812ac21b5c977b93e53fe65131b43e23ba85` preservado.
- Rotas públicas não autenticadas `/g7/retention/status` e `/g7/retention/summary` retornam HTTP 401.

## QA pendente

- Homologação visual autenticada com leitores e autores reais, consentimento, pausa, retomada, conclusão e exclusão em celulares/navegadores diferentes.
- Auditoria de acessibilidade de controles SVG e comportamento do gráfico com pelo menos 10 leitores consentidos reais.
- Método de observação usa posição visível de rolagem proporcional à altura do texto; seu número é uma estimativa de avanço por posição visual e não prova leitura atenta.

Documentos atualizados para substituição pelo titular, preservando nomes dos arquivos fornecidos: `PENDÊNCIAS URGENTES (1).md` e `PENDÊNCIAS.md`.
