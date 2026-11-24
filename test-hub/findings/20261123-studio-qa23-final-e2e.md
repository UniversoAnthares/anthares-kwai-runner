# Test Hub — Homologação operacional QA23 final (2026-11-23)
STATUS: PROVEN
AREA: studio
DATE: 2026-11-23
OWNER: ChatGPT / QA_STUDIO_23_E2E_20261123
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/426
JOB: WordPress PHP 8.3 CLI + Playwright Chromium + axe-core 4.10.3, executados em 23/11/2026 America/Campo_Grande
COMMIT: e5def88beaa69118d0f4ba1961c705c66ab49fe4
SUPERSEDES: test-hub/findings/20261123-studio-qa23-results.md ; test-hub/findings/20261123-studio-qa23-e2e-lease.md

## Objetivo
Concluir o teste operacional do Anthares Studio, conforme item 23 de PENDÊNCIAS URGENTES.md, preservando as contas existentes e a versão /estudio.

## Resultado comprovado
- Perfis autenticados sintéticos em navegador real: dono, comprador com direito ativo, comprador expirado, leitor sem direito e membro Anthares. Respostas REST 200/403 conforme direitos; visitante com endpoints privados 401. Sem efetuar compra externa.
- Proteção entre contas: leitura indevida e escrita indevida rejeitadas; dois editores simultâneos com hash antigo recebem HTTP 409 sem perder texto; Delta inválido HTTP 400; interrupção de rede e retorno com dados preservados.
- Volume: 260 cartões e 65 capítulos sintéticos. Originalmente 250 de 260 cartões visíveis; PR #423 corrigiu consulta e removeu limite artificial de duplicação. Após implantação: 260/260 cartões e 65/65 capítulos; 35/35 verificações Playwright, desktop1365px e mobile390px/320px, 0 transbordamento e 0 JS page errors.
- Acessibilidade: auditoria axe-core 4.10.3 (WCAG 2.0/2.1 A/AA) em Visão geral, Planejamento, Manuscrito, Análises. PR #424 corrigiu 19 falhas de contraste no tema escuro; reexecução na produção 16/16 PASS, 0 violações detectadas. PR #425 corrigiu contraste no tema claro; reexecução na produção 17/17 PASS, 0 violações detectadas. Chromium Accessibility Tree e navegação por teclado verificados.
- WordPress WP-CLI: 281 asserções aprovadas em dez suítes com ROLLBACK=EXECUTED: gerador16, retenção26, marcadores83, aparições28, biblioteca30, mentoria9, beta11, comentários35, seguir34, Runas9.
- Contratos Python: 270 casos, 257 PASS, 13 SKIP, 0 FAIL. Inventário de QA: 775/775 arquivos atribuídos exatamente uma vez.
- Invariantes de limpeza de produção: cinco contas QA temporárias excluídas e IDs removidos da allowlist; número de usuários voltou a 69, número de registros anst_% voltou a 82, arquivos de manifestos QA eliminados de /tmp. /estudio intacto.
- Amostra de tempo de resposta de bootstrap de projeto sintético 260 cartões/65 capítulos: 2539, 1830, 1400, 1376 e 1408 ms; mediana aproximadamente 1,41 s; maior amostra 2,54 s.
- Entregas PR WordPress #423, #424, #425 implantadas na Hostinger, cada arquivo com SHA-256 verificado e backup fora de public_html. Registro final PR #426 incorporado à main; matriz 188 corrigida para os requisitos 046, 186, 164, 178, 111.

## Ressalvas e escopo de aceite
Status PROVEN aplica-se somente aos cenários automáticos, transacionais, visuais e de acessibilidade digital de navegador descritos neste registro. Pagamentos reais WooCommerce/Hotmart/Mercado Pago não foram realizados: são responsabilidade do item urgente 16. Testes manuais com NVDA/VoiceOver e dispositivos móveis físicos não foram realizados: axe registrou 1–2 critérios como incomplete por tela. A dimensão de teste de volume 260 cartões e 65 capítulos não representa SLA global. O PR #420 (capítulos/lembretes) permanecia fora da baseline instalada; exige QA após deploy.

## Evidências e consequência
Relatório técnico em https://github.com/UniversoAnthares/anthares-wordpress/blob/main/docs/anthares-studio/06-QUALIDADE-SEGURANCA-E-TESTES.md. Matriz https://github.com/UniversoAnthares/anthares-wordpress/blob/main/docs/anthares-studio/09-MATRIZ-188-REQUISITOS.csv.
Aprovar o item 23 quanto ao conjunto operacional homologado nesta versão; manter ressalvas de serviços externos/hardware e novas versões em seus respectivos gates. Não reproduzir falhas corrigidas sem verificar a versão instalada e os SHA de referência.
