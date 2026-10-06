# Social destinations — official API feasibility inventory
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: inventory-social-secret-names
COMMIT: none
SUPERSEDES: none

## Objetivo
Determinar caminhos oficiais atuais para Instagram, Threads e X e inventariar autenticação já disponível sem expor secrets.

## Resultado
Instagram: API oficial Meta suporta publicação para contas profissionais; Instagram Login usa instagram_business_basic + instagram_business_content_publish e mídia pública por URL. Threads: API oficial usa OAuth 2.0, threads_basic + threads_content_publish, container /me/threads e publish /me/threads_publish. X: POST /2/tweets exige tweet.write/users.read/tweet.read; em 2026 o modelo oficial é pay-per-use, com Post Create cobrado por request, portanto não satisfaz requisito de API oficial gratuita.

Inventário local/GitHub: secrets presentes apenas para KWAI_LOGIN/KWAI_PASSWORD e TIKTOK_LOGIN/TIKTOK_PASSWORD; nenhum KWAI_SECONDARY_*, Meta/Instagram/Threads ou X encontrado. Nenhuma integração Meta/X prévia foi encontrada no anthares-wordpress.

## Evidência decisiva
Documentação atual da Meta/Postman oficial e X docs consultadas em 2026-10-06. GitHub secret-name inventory executado sem ler valores.

## Consequência
Instagram/Threads: próximo gate é criar/usar app Meta e OAuth da conta correta; depois canário único via API oficial. X: avaliar custo oficial versus automação web sustentável antes de publicar. Kwai secundário: exige credenciais/sessão próprias; primary não pode ser fallback.
