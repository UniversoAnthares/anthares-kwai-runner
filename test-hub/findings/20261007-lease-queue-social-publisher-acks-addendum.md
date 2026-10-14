# Addendum do lease — ACK HTTP de `started`/`result`
STATUS: RUNNING
AREA: architecture
LEASE_AREA: queue
LEASE_OWNER: Manus task fC58le6HtsUjTsBorwFbaA
LEASE_EXPIRES: 2026-10-07T17:10:00Z
DATE: 2026-10-07
RUN: none
JOB: fC58le6HtsUjTsBorwFbaA
COMMIT: anthares-wordpress `a26053a0303b41114ad0b10d4e6ea493970b70f5`
SUPERSEDES: none

## Baseline comprovado

No cutoff `a26053a`, `ATD_DB::mark_started` retorna `false` quando `$wpdb->update(...) === false`, mas `ATD_API::publisher_started` verifica somente `is_wp_error($ok)` e, no caso `false`, responde `{ok:true}`. Isso pode fazer o worker avançar para o POST público apesar de a marcação de início não ter sido persistida. `publisher_result` também deve preservar o ACK estrito de sucesso.

## Extensão de escopo

Dentro do mesmo lease `queue`, incluir em `anthares-wordpress` uma correção fail-closed dos handlers `publisher_started` e `publisher_result`: só responder `{ok:true}` quando o método de banco retorna `true`; qualquer retorno falso deve ser HTTP não-2xx/erro WP. A extensão não muda automações ativas e não autoriza deploy.

## SUCCESS_SIGNAL

Teste local comprova que os handlers não convertem retorno `false` em ACK positivo; validações estáticas/unitárias e `php -l` (se PHP CLI estiver disponível) passam. Sem WordPress real, banco ou rede.

## FAILURE_SIGNAL / TEST_VALIDITY

Se a rota puder responder `ok:true` com persistência falsa, a correção falhou. Teste sem PHP CLI não prova sintaxe PHP e deve ser reportado como limitação, não como sucesso de sintaxe.
