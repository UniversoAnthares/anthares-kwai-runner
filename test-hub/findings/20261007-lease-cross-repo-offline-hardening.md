# Lease — hardening e documentação offline cross-repo
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-07
RUN: none
JOB: MDE9nE00YIndrW2UFftCo3
COMMIT: pending
SUPERSEDES: none
EXPIRES: 2026-10-07T16:15:00Z

## Objetivo
Aplicar correções locais de baixo risco em documentação, referências de assets, manifesto npm, portabilidade de shell e respostas que vazam detalhes de upstream. O escopo exclui revogação/saneamento de credenciais, reescrita de histórico, mudança de autenticação/quotas, deploy, publicação, dados reais e decisões de branding.

## BASELINE_PROVEN
A auditoria cross-repo de 2026-10-07 confirmou referências de CSS inexistentes e exclusões Jekyll obsoletas no github-slideshow, ausência de `package.json`, README mínimo na wiki e respostas do serviço de transcrição que devolvem stderr/texto upstream ao cliente.

## FAILED_AVOIDED
Não executar `script/stage`, não fazer push/force-push, não escolher conta TikTok, não inventar logos/assets, não revogar cookies, não reescrever histórico Git e não mudar contratos de autenticação ou rate limit sem decisão do consumidor.

## SUCCESS_SIGNAL
Cada correção possui validação local reproduzível; `git diff --check` passa; referências locais corrigidas existem; documentação não contém segredos; testes mockados não exibem detalhes upstream.

## FAILURE_SIGNAL
Qualquer patch depender de serviço externo, credencial, asset oficial ausente, execução de publicação ou alteração destrutiva; nesse caso registrar BLOCKED em finding separado.

## TEST_VALIDITY
Somente verificações offline: sintaxe, testes mockados, inventário Git, JSON/manifestos e busca de referências locais. Ausência de Ruby/Docker/serviços não será tratada como aprovação funcional.
