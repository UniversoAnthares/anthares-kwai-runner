# Queue lease closure — multichannel destinations
STATUS: PROVEN
AREA: queue
DATE: 2026-10-06
RUN: none
JOB: verify-atd-destination-column
COMMIT: 9c9f8b12302e58082e5614f3966d8f325080db26
SUPERSEDES: test-hub/findings/20261006-0844-lease-queue-multichannel-destinations.md

## Resultado
Lease encerrado. Modelo platform+account_id/destination_key implantado e validado em produção; fencing/started/evidence adicionados ao delivery WordPress.

## Consequência
Mutações futuras de queue devem partir deste baseline e preservar compatibilidade com control plane v16.
