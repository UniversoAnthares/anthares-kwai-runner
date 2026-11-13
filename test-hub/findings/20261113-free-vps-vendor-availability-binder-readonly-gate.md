# Item 8 — outras VPS grátis: Verta / NanoKVM verificação e preflight
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: none (sem host gratuito provisionado)
JOB: ARA cb6db3b22bbea449df5990f1aa44360b
COMMIT: branch feat/redroid-free-vps-preflight-20261113
SUPERSEDES: test-hub/findings/20261113-oci-redroid-arm64-immutable-manifest-proven.md

## BASELINE_PROVEN
O runner de Oracle A1 e cloud-init ARM64 estão versionados. A tenancy OCI ainda não tinha capacidade gratuita; o usuário exige execução 100% na nuvem sem PC, Redmi, MEmu e sem custo mensal.

## OBSERVATION
Verta Cloud anuncia Linux VPS Free com 2 vCPU, 4GB RAM, 50GB HDD. Tentativas de verificação do portal real falharam em três motores (web timeout, Browserless navigation error, TinyFish proxy_error/timeout). Seu /about contém campos de template não preenchidos: [YEAR], [LOCATION], [X]+. Portanto reputação, estoque, identidade, kernel e entrega sem comprovação.
NanoKVM formulário live: Paris Low Stock; Sandefjord/Fremont/Liberty Lake/Eygelshoven Out of Stock; tier selecionável máx. 1core/2GB/25GB (homepage menciona até 4GB com upgrades não garantidos). Aplicação requer conta comunitária com >3 meses, 50 posts, 15 recentes. No navegador já aberto não constava login ligado ao projeto e na caixa Gmail principal consulta de correspondências de fóruns retornou zero; isso não equivale a provar ausência de elegibilidade.

## CHANGE
Novo `tools/redroid_free_vps_preflight.py`, somente leitura, com porta de avaliação conservadora para VPS futura: Linux AMD64/ARM64, 2vCPU, 4GiB, 20GiB livres, root, virtualização que permita controle do kernel, e binder possível; distingue `REJECTED`, `BINDER_PROOF_REQUIRED` e `CANDIDATE_FOR_ISOLATED_INSTALL_TEST`. Nunca publica, conecta ou altera recursos. Documentação `docs/REDROID-FREE-VPS-QUALIFICATION.md` cobre resultados, critérios e fontes.

## SUCCESS_SIGNAL
7 testes PASS, 0 falhas/erros, ARA `cb6db3b22bbea449df5990f1aa44360b`; garantias de rejeição de VPS NanoKVM pequena, Linux sem root, LXC mesmo com root, ausência de binder não confirmada, e resultado de candidato que sempre conserva `mandatory_unverified`.

## FAILURE_SIGNAL
Nenhum host Verta ou NanoKVM entregue; portanto não existe prova de modprobe binder, Docker privilegiado, armazenamento persistente, boot real ReDroid ou login/ação Kwai em cloud. Não houve provisionamento, custo, postagem, interrupção de publicadores ou transferência de credenciais.

## NEXT
Retomar somente com VM gratuita realmente acessível e requisitos aprovados; coletar saída local do preflight e validar binder/Docker em teste isolado antes de instalar Android e autenticar serviços. Não fazer compromissos de compra, cadastro fictício nem transferir autenticações para VPS de procedência incerta.
