# Android em nuvem — qualificação de VPS gratuita de terceiros

Data: 2026-11-13. Escopo: triagem de **Verta Cloud** e **NanoKVM** como possíveis hosts ReDroid, sem dependência de PC ou Android físico. Não altera a fila de publicação, o workflow Oracle, ou autenticações de Kwai.

## Situação pública atual

| Candidato | Informação verificável em 13/11/2026 | Decisão |
|---|---|---|
| Verta Cloud (`vertacloud.biz`) | O catálogo indexado anuncia Ubuntu 22.04.5 LTS, 2 vCPU, 4 GB RAM e 50 GB de disco SAS a custo zero. Tentativas independentes de acesso **ao portal real** (`portal.vertacloud.biz`) falharam: `web` timeout, Browserless `chrome-error://chromewebdata/` e TinyFish `proxy_error`/`timeout` para registro. A página institucional `/about` inclui textos modelo `[YEAR]`, `[LOCATION]`, `[X]+` clientes: procedência e confiabilidade pendentes. | **REJECTED_FOR_AUTHENTICATED_WORKLOAD**, até comprovar entrega/operador/autorização, não armazenar sessão Kwai; nenhum pedido criado. |
| NanoKVM (`nanokvm.net`) | Estoque no formulário consultado ao vivo: Sandefjord, Fremont, Liberty Lake, Eygelshoven **Out of Stock**, Paris **Low Stock**. Contrato da página de pedido oferece 1 vCPU, até 2 GB RAM e até 25 GB de storage. Site institucional afirma até 4 GB, mas no pedido apenas 2 GB selecionáveis. Requer fórum LowEndTalk, LowEndSpirit ou HostedTalk com conta >3 meses, 50 posts e 15 posts recentes. Nenhuma conta elegível comprovada nas fontes conectadas; pesquisa de emails dos fóruns na caixa principal não retornou correspondências, o que por si só **não prova** inexistência de conta. | **REJECTED_FOR_PRODUCTION** no porte anunciado (1 vCPU / 2 GB), elegibilidade e aprovação pendentes; nenhuma solicitação foi enviada. |

Verta e NanoKVM são marcas distintas de **Vertra Cloud** (`vertracloud.app`), **VetraCloud** (`vetracloud.com`) e o projeto de hardware **Sipeed NanoKVM**. Não reutilizar credenciais ou usar páginas de outra marca.

## Pré-teste offline implementado

Arquivo: `tools/redroid_free_vps_preflight.py`. Executar **dentro de uma futura VM Linux contratada de forma autorizada**, antes de instalar Docker, ReDroid ou Kwai:

```bash
python3 tools/redroid_free_vps_preflight.py
```

O programa usa só a biblioteca padrão e realiza leituras locais, sem escrever arquivos, executar `modprobe`, iniciar Docker, mexer no firewall, transmitir endereços IP ou acessar a internet.

Critérios mínimos conservadores para **considerar** um host de produção ReDroid + Kwai + MacroDroid:

- Linux ARM64 ou AMD64 com privilégios root reais; LXC/OpenVZ/Docker/Podman não são qualificados como acesso ao kernel de host.
- Pelo menos 2 vCPUs, 4.096 MiB RAM e 20 GiB **livres** na partição raiz. Valores são uma política operacional de confiabilidade, não requisitos universais do ReDroid.
- `binder_linux` carregado, kernel com módulo/localização identificável ou `binderfs` presente. Se o resultado for `BINDER_PROOF_REQUIRED`, caberá checar suporte de módulos e `modprobe` num host de teste autorizado.
- Resultado `CANDIDATE_FOR_ISOLATED_INSTALL_TEST` **não autoriza transferir credenciais**. Permanecem pendentes validação de custo zero/persistência, Docker privilegiado real, criação de dispositivos binder, Android inicializado e homologação do mecanismo de publicação por lease/fencing Neon.

Saída em JSON: `REJECTED`, `BINDER_PROOF_REQUIRED`, ou `CANDIDATE_FOR_ISOLATED_INSTALL_TEST`; nenhum resultado é interpretado como Kwai publicado.

Testes automatizados: `tests/test_redroid_free_vps_preflight.py`: 7 PASS (ARA `cb6db3b22bbea449df5990f1aa44360b`), incluindo rejeição explícita de NanoKVM com 1 vCPU, 2 GB e 10 GB e de hosts sem root / com LXC.

## Próxima condição operacional

Disponibilizar **uma VM Linux realmente utilizável** com contrato gratuito e persistente, acesso root, isolamento e pelo menos 2 vCPU / 4 GB / 20 GB livres. Só então executar o preflight no host. Se aprovado, instalar ReDroid por digest ARM64 ou AMD64 verificado, ADB apenas `127.0.0.1:5555`, criar armazenamento persistente, homologar com conta de teste e preservar a exclusão mútua do publicador existente. A rota Oracle foi expressamente encerrada pelo titular em 13/11/2026, PR #2575: é proibido voltar a consultar ou provisionar a Oracle sem nova ordem. Ver `docs/KWAI-PLANO-SEM-ORACLE-20261113.md`.

## Evidências públicas

- Verta plano: https://portal.vertacloud.biz/index.php?rp=/store/free-vps
- Verta sobre: https://www.vertacloud.biz/about
- NanoKVM requisitos: https://nanokvm.net/
- NanoKVM formulário e estoque: https://nanokvm.net/index.php?p=deploy
- NanoKVM limitações: https://nanokvm.net/index.php?p=about
- ReDroid oficial — kernel binder/portas ADB e suporte AMD64/ARM64: https://github.com/remote-android/redroid-doc

**NENHUMA VM PROVISIONADA NESTA ETAPA; nenhuma credencial Kwai, compra, gasto, migração ou postagem.**

## Bootstrap portável pronto para VPS AMD64 e ARM64 (13/11/2026)

Após superar o pré-teste de root, CPU, RAM, armazenamento, kernel e legitimidade do provedor, o operador poderá aplicar `infra/oci-android/redroid-firstboot.cloud-config.yml` em VM Ubuntu compatível. A escolha da imagem passou a ser automática, conforme a arquitetura física, com digests SHA-256 aprovados pela API oficial Docker Hub para ARM64 e AMD64. O `binder_linux` é configurado para voltar após reboot e o script pode recuperar um container existente que esteja parado; ADB continua limitado ao localhost.

Esta portabilidade foi homologada em testes isolados: **22 Python PASS, Bash -n PASS e seleção exata de digest/plataforma para aarch64, arm64, x86_64, amd64**. Não comprova compatibilidade do kernel da futura VPS, Docker privilegiado efetivo, funcionamento dos APKs Kwai/MacroDroid ou autenticação. Nenhum servidor terceirizado foi contratado, nenhuma credencial ou sessão foi transferida, e nenhum publicador foi alterado.

## Rechecagem de 13 de novembro de 2026 — critérios e próximos passos

**VPSFree.io:** a página inicial descreve planos e seletor de memória de 2–6 GB, mas o catálogo `/plans` de 13/11 mostra como gratuito apenas o plano de 192 MB RAM e 3 GB de disco por 10 dias renováveis. Os planos imediatamente seguintes são pagos. Resultado: **CATÁLOGO GRATUITO REPROVADO** pelo requisito de memória e espaço, até o provedor apresentar pedido real de VPS gratuita de pelo menos 4 GB e 20 GB livres. Fontes: https://vpsfree.io/ e https://vpsfree.io/plans.

**Verta Cloud:** o catálogo ainda anuncia Linux 2 vCPU / 4 GB / 50 GB gratuitamente. Uma nova tentativa automatizada de acesso ao portal não retornou conteúdo (timeout). A página `/about` continua contendo marcadores `[YEAR]`, `[LOCATION]` e `[X]`. Resultado: **OFERTA ANUNCIADA, SEM ENTREGA OU CONFIABILIDADE COMPROVADA**; não transmitir credenciais pessoais nem Kwai ao provedor. Fontes: https://portal.vertacloud.biz/index.php?rp=/store/free-vps e https://www.vertacloud.biz/about.

**NanoKVM:** o formulário público lista opções de 1 núcleo e até 2048 MB RAM; requer elegibilidade em comunidade. Resultado: **ABAIXO DOS MÍNIMOS PARA PRODUÇÃO**, independentemente de locais que anunciem baixo estoque. Fontes: https://nanokvm.net/index.php e https://nanokvm.net/index.php?p=deploy.

**Nevatal Cloud (alternativa nova):** anuncia cloud Android/Waydroid sem cobrança, mas o serviço em https://cloud.nevatal.id/ retorna erro Cloudflare **530 / 1033** (túnel sem origem) nas consultas reais; sem painel de provisionamento utilizável. Resultado: **SERVIÇO INACESSÍVEL E OPERADOR NÃO HOMOLOGADO**. A descrição comercial, por si só, não comprova VM.

O script `tools/redroid_free_vps_catalog_watch.py` e o workflow `redroid-free-vps-catalog-watch.yml` reconsultam diariamente as páginas públicas, com relatórios e testes sem credenciais. **Uma alteração no catálogo nunca habilita o Android remoto nem altera o publicador.** Com uma VPS real entregue, executar o preflight local, validar Docker privilegiado + binder, confirmar custo e persistência antes de autenticar as contas.

**Estado atualizado em 13/11/2026:** nenhum pedido externo, cadastro, patrocínio ou contratação deve ser solicitado. O titular exige custo incremental R$0 e nenhum tempo aguardando aprovações. Investigações só podem continuar com infraestrutura já conectada e imediatamente acessível. Uma VPS não entregue mantém a migração BLOQUEADA_POR_RECURSO_REAL. Nenhum dos quatro fornecedores acima entregou uma máquina comprovada nesta investigação. Não contratar ofertas com cobrança, anunciar sucesso com base em páginas de marketing ou transferir senha/cookies do Kwai para sites ainda sem legitimidade comprovada.
