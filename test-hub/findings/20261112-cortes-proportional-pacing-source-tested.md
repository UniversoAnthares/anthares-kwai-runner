# CORTES — scheduling proportional por conta até 23:00 (contrato validado)
STATUS: PARTIAL
AREA: social-publishing / social-deadline-pacing
DATE: 2026-11-12
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43228846472
JOB: 131218830797
COMMIT: bb7556d64a9308ad043511b793d1fbdb59dd4489
SUPERSEDES: 20261112-cortes-proportional-pacing-running.md
BASELINE_PROVEN: Para Instagram, Kwai, TikTok, Pinterest, LinkedIn e outros destinos, primeiros comprovantes, cotas e contas permanecem separados no ledger. TikTok/Kwai tinham intervalos fixos, removidos do código no mesmo PR.
FAILED_AVOIDED: Sem posts de teste reais, sem mutação de Neon de produção, sem acesso a arquivos do PC e sem reenvios UNCERTAIN.
SUCCESS_SIGNAL: 12/12 testes Python; py_compile de três consumidores; node --check de infra/neon-cortes-queue/index.mjs; CORTES_PROPORTIONAL_PACING_SOURCE_CONTRACT=PASS.
TEST_VALIDITY: QA de fonte; não representa implantação da função Neon de produção nem ativação das cópias dos consumidores remotos.
## Consequência
A regra de execução é por plataforma + conta, fuso America/Campo_Grande, até 23:00 do mesmo dia e com recomputação após confirmação. A primeira publicação real é a âncora. Cron serve apenas para acordar o publicador. O backend recusa lease antes do instante calculado; os publicadores possuem segunda checagem antes de envio. Qualquer excesso de cota permanece registrado em vez de receber sucesso falso.
## Pendência de implantação
Promover a nova função Neon após revisão de release e comprovar qual projeto controla o endpoint br-crimson-unit-b89nau08-cortesqueue; o conector Neon da sessão só lista projetos próprios distintos. Verificar executores efetivos das demais redes e validação end-to-end sem gerar publicação fictícia.
