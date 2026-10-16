# WordPress QA Orchestrator v2 — 2026-10-16

STATUS: PROVEN
OWNER: QA migration/orchestrator agent
SOURCE_REPO: UniversoAnthares/anthares-wordpress
SOURCE_COMMIT: f086664eadec96da9329e0edb8bea5ff29e450a9
VERCEL_DEPLOYMENT: dpl_3qovPwmGYeK1wUgqT57o3SWTs4WP

## Implementado
- Vercel permanece como executor estrutural principal.
- Cinco revisores em rotação: ChatGPT, Gemini, Groq, Cloudflare Workers AI e Mistral.
- Cinco blocos A–E, 12 áreas por bloco; em 5 rodadas cada IA percorre todos os blocos.
- Manifesto v2 atribui cada arquivo auditável exatamente uma vez, sem lacunas nem sobreposição.
- Todos os blocos usam o mesmo `review_budget_chars=36000`; o digest inclui inventário de todos os arquivos do bloco.
- Fila de correção simples: ChatGPT -> Copilot Coding Agent -> GitLab CI.
- Watchdog Copilot do GitHub Actions ficou manual-only; o acionamento preferencial é pela integração GitHub de uma sessão agente, evitando depender do runner hospedado quebrado.
- Retenção: 100 eventos recentes; anomalia só persiste após reincidência, contador máximo 5; 100 anomalias reincidentes; 100 revisões de IA.

## Provas
- Auditoria local de cobertura: 487 arquivos auditáveis, 487 atribuídos, 0 duplicados, 0 ausentes, 0 desconhecidos.
- Simulação Latin-square 5x: cada um dos 5 revisores visita A, B, C, D e E em cinco rodadas.
- Vercel em `f086664`: PHP lint PASS; regressões estruturais PASS; contrato Minha Conta/Gestões PASS; auditoria estática ampla PASS; contrato do orquestrador PASS; deploy público PASS; telemetria comportamental disponível PASS.
- Deployment terminou READY.

## Observações
- GitLab CI continua como último fallback e não deve ser tratado como executor disponível enquanto `ci_quota_exceeded` persistir.
- GitHub hosted Actions não é autoridade desse QA.
- OpenRouter segue como fallback de revisão; AI Hub também tem adaptadores para Hugging Face, NVIDIA e OpenAI-compatible, sujeitos a configuração/cota.
