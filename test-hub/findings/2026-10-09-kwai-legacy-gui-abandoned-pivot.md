# Kwai: abandonar GUI efêmera e estabelecer aceite por publicação
STATUS: ABANDONED
AREA: kwai
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38015538907
JOB: none
COMMIT: none
SUPERSEDES: none

## Decisão autorizada
O usuário aprovou encerrar as tentativas repetitivas de login via noVNC, HTTP Basic Auth e Cloudflare Quick Tunnel. O acesso da conta Kwai correta é lucasrosalem.

## Evidência
A interface Android inicia, mas a autenticação humana no navegador não foi comprovada. Testes de boot, HTTP 200, WebSocket 101 e sucesso de CI não provam login ou publicação. O publicador falhou no run 38015622201.

## Próximo caminho
Não repetir o workflow legado automaticamente. Preservar código e evidências. Priorizar executor remoto com estado autenticado persistente e armazenamento privado criptografado, sem PC local, custo ou cartão; só declarar PROVEN após publicação real verificada na conta lucasrosalem, com ledger de deduplicação. Verificar capacidade e limites reais do provedor antes de prometer persistência 24/7 gratuita.

## Coordenação
Não sobrescrever fluxos de outros agentes nem interferir no workflow de 40 probes em andamento. O workflow legado ainda pode existir; este finding não o desativa tecnicamente.
