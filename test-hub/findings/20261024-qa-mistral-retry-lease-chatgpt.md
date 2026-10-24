# Lease de correção exclusiva — QA das cinco IAs
Owner: chatgpt
Job: wp-qa-five-reviewers-20261024
Escopo: UniversoAnthares/anthares-wordpress/anthares-pix-sales/includes/94-qa-ai-rotation.php e teste de contrato relacionado, sem CORTES.
Início UTC: 2026-10-24T14:57:05.045Z
Expiração UTC: 2026-10-24T15:27:05.045Z
Baseline: WordPress main 01c73c716b5034fbe52754cc6bb8c029060851b1, file SHA conferido antes da PR.
Evidência: WP round 41501 completed=4/5; Mistral HTTP429 bloqueado até 1792882757; OpenRouter HTTP200 fim incompleto; NVIDIA HTTP200 JSON inválido; HuggingFace 402.
Plano: retry único de fallback na segunda oportunidade, com JSON estrito e saída suficiente; preservar independência de backends, orçamento gratuito, cron 12h, locks e limite de tentativas. Validar teste de contrato e PHP lint antes do merge; só assinalar sucesso se a resposta real retornar 5/5 provedores independentes. Não alterar dados ou filas dos outros sistemas.
