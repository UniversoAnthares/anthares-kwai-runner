# Studio G4 — lease para correção de autorização do piloto e fallback Quill

STATUS: RUNNING
DATE: 2026-11-17
AREA: anthares-studio/code-only/pilot-access-quill-fallback
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-pilot-fallback-safety-20261117
RUN: branch fix/studio-pilot-fallback-safety-20261117 (a criar)
BASELINE_PROVEN: anthares-wordpress PR #320 head ea8205a9e7ef715cb158b22ea4b9aa55ed682f0b; QA isolado 69/69 testes Python, 4/4 PHP lint; ACF OFF; legado intocado. Test Hub: 20261117-studio-g4-g5-quill-integration-qa-proven.md.
FAILED_AVOIDED: nenhum uso de aba autenticada ou REST mutável em produção, anteriormente barrados por controles de segurança. Nenhum teste por desvio de canal. Sem edição na PR #316, #319 ou #320.
SCOPE: branch independente GitHub, alterações somente em anthares-studio/anthares-estudio.php, anthares-studio/assets/estudio.js e testes existentes. Corrigir o bloqueio de contas piloto elegíveis por allowlist explícita e perda de Delta formatado se Quill indisponível. Nenhum deploy.
SUCCESS_SIGNAL: regressões sem privilégios administrativos globais, proteção de Delta formatado/embeds em falha de Quill, Python QA, lint PHP/JS e manifesto completos em checkout efêmero.
FAILURE_SIGNAL: permissão ampla, POST acidental de Delta formatado, falha de testes ou mudança do legado.
TEST_VALIDITY: testes estáticos/isolados apenas; não autorizam declarar CRUD autenticado ou UI de produção homologados.
LEASE: código isolado, duração máxima de 30 minutos a partir deste registro; nenhuma alteração em produção e nenhum trabalho sobre branch de outro agente.
