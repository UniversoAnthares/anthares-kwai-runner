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

Disponibilizar **uma VM Linux realmente utilizável** com contrato gratuito e persistente, acesso root, isolamento e pelo menos 2 vCPU / 4 GB / 20 GB livres. Só então executar o preflight no host. Se aprovado, instalar ReDroid por digest ARM64 ou AMD64 verificado, ADB apenas `127.0.0.1:5555`, criar armazenamento persistente, homologar com conta de teste e preservar a exclusão mútua do publicador existente. A opção Oracle A1 permanece preparada e pode voltar a ser considerada quando houver capacidade gratuita.

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
