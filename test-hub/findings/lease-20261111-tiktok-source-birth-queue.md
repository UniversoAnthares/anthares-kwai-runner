# Lease: prioridade da fonte mais recente no TikTok Neon

STATUS: RUNNING
AREA: tiktok-publish
BASELINE_UTC: 2026-11-12T01:20:38.617Z
EXPIRES_UTC: 2026-11-12T01:48:38.617Z
OWNER: sessão ChatGPT corrente com usuário autorizando a conclusão do CORTES.

Objetivo: corrigir somente a seleção de `cortes_tiktok_publications` no serviço oficial `cortestiktok`, preservando as verificações OIDC, lease_generation, proibição de replay, 100/publicações/dia, janela 180–240 s e recuperação de UNCERTAIN. O seletor anterior usa o vídeo enfileirado mais recentemente, o que favorece reposições antigas: fonte A7BsgCe3-oo teve novos registros em 2026-11-11 22:12 UTC; fonte atual cOhqEaY3-08 surgiu em 2026-11-11 20:42 UTC; MIN(created_at) de cada fonte em todas as suas entradas prioriza cOhqEaY3-08. Evidência SQL de leitura retorna a fonte e os cinco primeiros segmentos corretos.

Falhas evitadas: reenvio de posts incertos, mutação manual em Neon's `created_at`, qualquer remoção de dados e testes concorrentes do TikTok. Produtor e publicador ativos continuam sob identidade oficial e sua cadência. Sinal de sucesso: testes unitários passam, deploy Neon torna-se `completed`, próximo job confirmado da fonte cOhqEaY3-08 com vídeo público e ledger confirmado. Sinal de falha: regressão em auth, cap/cadence, divergência de SHA ou erro de deployment; interromper sem alternar fila.

Fechamento: registrar finding append-only com provas exatas de teste, deploy, Neon e publicação. Se outra sessão possuir lease anterior `tiktok-publish`, este lease cede e nenhum deploy será feito.
