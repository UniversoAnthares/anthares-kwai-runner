# Lease: item 5 — descoberta pública de obras

STATUS: CLOSED_DEPLOYED_VERIFIED
OWNER: ChatGPT
DATA: 2026-11-20
ORIGEM: `site-anthares.docx`, parágrafos 3–8: cadastro com título, descrição, etiquetas, gênero; tags agrupam gêneros e assuntos para pesquisa.
ESCOPO: `anthares-wordpress/anthares-studio`; nova descoberta em `/studio/?descobrir_obras=1`, busca pública por palavra, gênero, assunto e etiqueta; campos explícitos do autor no formulário de publicação; paginação, sanitização e retorno só de projetos efetivamente públicos.
EXCLUSÕES: segmentação demográfica e direcionamento de anúncios do briefing (itens D descartados pelo titular); publicação comercial nova; pagamento; conteúdo privado; tema ativo `anthares-customify/author.php` com drift identificado.
GATES: conferência atual dos arquivos e hashes, testes com dados sintéticos transacionais reversíveis, segurança de acesso anônimo e de publicações retiradas, layout responsivo e PHP/JS lint, backup privado antes de implantação, comparação dos arquivos públicos e relatório final.

CLOSED_UTC: 2026-11-20T23:10:00Z
RESULT: WordPress PR #391 merged, six plugin files installed on Hostinger with private backup, all 6 hashes match main. 191 Python PASS, 37 transactional WP REST PASS/ROLLBACK, 729 QA manifest PASS, 51 production plugin tests PASS. Anonymous public HTML/REST HTTP200, three viewport QA 390/768/1440 no overflow, 22 originals preserved. Current eligible public G7 works count zero; fixtures verified discovery and filters. Full report: test-hub/findings/20261120-studio-item5-public-discovery-deployed.md
