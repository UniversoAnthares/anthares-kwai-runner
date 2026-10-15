# CORTES daily cycle policy + remote partial extraction
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-15
RUNS: 38760605877, 38760914190
COMMITS: anthares-clipper 79b9e8e3b542d395557cbf4cc484deb8d988d89d, cdcb52d2c8f609aef696606b19d8f8d47d9e9bb3, 6c8d55790c909858096d1d1f1240058117b9dd84, bb63746cbcef012abf39afe210084e30812289a7; anthares-kwai-runner e362bfeefe347ea169fc8ce7e1a4471eabb7503a, 39ed6a47f692d3349af32e9e25240647349aa876, 40a96f710f7ccd76f19b55f2110e44d55f9eb9e3
SUPERSEDES: test-hub/findings/20261015-1119-lease-cortes-content-cycle-partial-remote.md

## Implementado
- `cortes_cycle_policy.py` fixa uma única fonte por dia e impede avanço até todos os masters dessa fonte estarem finalizados.
- Fallback: lives em ordem → vídeos comuns estritamente >15 min, nunca Shorts e nunca YouTube → retorno às lives.
- O limiar `mais de 5` foi codificado como >=6 novas lives em relação ao snapshot feito quando a lista de lives se esgota; com 5 ou menos, reinicia da primeira live do canal.
- Retenção: master só fica `delete_ready` após confirmação de todos os destinos plataforma/conta e uma verificação final separada.
- Longos fora do YouTube: masters finais 5–14 min, microcortes obrigatórios; com >3 candidatos válidos, exatamente 4 são mantidos, IA/ranking privilegia escrita/técnica/teoria literária, último slot às 22:00, excedentes descartados.
- `AGENTS.md` torna esses invariantes obrigatórios para producers/schedulers/dispatchers/cleanup e futuros workers CORTES.

## Validação da política
Foi criado teste unitário específico, mas a execução GitHub Actions do repositório privado `anthares-clipper` não recebeu runner (`runner_id=0`, steps vazios). Portanto o CI desta rodada ficou BLOCKED/INVALID por cota/recurso do provider e não conta como aprovação nem reprovação do código.

## Teste real métodos 1 + 2
Foi criado smoke público que solicita somente um intervalo limitado do YouTube (`--download-sections`) e processa o trecho em runner remoto, removendo um intervalo interno de 3 s para comprovar o segundo estágio de edição. Não existe caminho de download integral nesse smoke e não existe publicação social.

Run 38760605877: runner público alocado; instalação de mídia passou; extração limitada falhou antes de produzir MP4.
Run 38760914190: runner público alocado; FFmpeg + yt-dlp + provider de PO-token instalaram com sucesso; extração limitada voltou a falhar. Nenhum artifact ficou registrado para o run, logo não existe MP4 que possa ser declarado como corte comprovado.

Classificação: TEST INVALID/INCONCLUSIVE para o mecanismo 1+2 neste provider. O runner remoto está funcional, mas o acesso ao fluxo de mídia do YouTube não foi comprovado. Não promover esse caminho a PROVEN sem MP4 + manifest verificáveis.

## Não feito por decisão explícita
O método 3 (download integral temporário remoto → cortar → confirmar persistência dos masters → apagar original) permanece PENDING_NEXT_ROUND e não deve ser antecipado nesta rodada.

## Integração ainda não comprovada
A política está codificada e marcada como contrato obrigatório, porém o adapter legado WordPress/CORTES que hoje fornece o `blocker` ainda não foi localizado/provado nesta rodada para executar o fallback operacional para vídeos comuns. O worker longo CORTES correspondente também não foi identificado no repositório `anthares-clipper`. Não declarar migração runtime completa até esses dois pontos serem conectados e testados.

## Segurança/regressão
Nenhum publicador Kwai foi alterado. Nenhum job social foi enfileirado por este teste. Roteamento físico Android primário / MEmu_4 fallback permanece intacto.
