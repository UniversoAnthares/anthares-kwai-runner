# Lease temporário — correção QA05
owner: chatgpt
job: forgejo-qa-20261024-0924
início_utc: 2026-10-24T13:30:56Z
expira_utc: 2026-10-24T14:00:56Z
baseline_wordpress: c128bda182f18114f5620e130dd59c98b39a8002
arquivos: qa/anthares-qa-sections.json; anthares-pix-sales/qa-sections.json
escopo: registrar qa/qa05-retention-wp-sqlite-contract.php exatamente uma vez no bloco D, preservando mudanças simultâneas.
prova_inicial: preflight --check = FAIL missing=[qa/qa05-retention-wp-sqlite-contract.php]
aceite: preflight --check = PASS; manifestos idênticos; verificação Forgejo para SHA merge.
segurança: nenhum arquivo CORTES, credencial, publicador ou produção alterado.
