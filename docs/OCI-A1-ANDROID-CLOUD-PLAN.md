# Item 8 — Android físico sem dependência permanente do PC e standby Oracle A1

**Escopo:** código criado em 12/11/2026 e incorporado à `main` por PR #2487; reparos subsequentes nos PRs #2489 e #2490. A configuração de autenticação e a implantação do Android exigem provas independentes. Governança: `D:\AntharsWork\governance\REGRAS-OBRIGATORIAS.md`; `ci-hub/executor-routing.json` é a autoridade dos publicadores.

## 1. Oracle A1 — workflow hospedado

- Workflow: `.github/workflows/oci-a1-android-cloud-watch.yml`.
- Cliente: `tools/oci_a1_capacity_watch.py`.
- Periodicidade proposta: `17 */4 * * *` UTC (seis consultas por dia), runner GitHub hospedado, sem tarefa permanente no computador.
- Região aprovada: `sa-saopaulo-1`; previsão de VM `VM.Standard.A1.Flex`, 1 OCPU, 6 GiB de RAM, boot de 50 GiB, Ubuntu 24.04 aarch64 e sem alteração da fila Kwai. O IP público efêmero é permitido somente se a sub-rede pública já existente mantiver firewall estrito SSH TCP/22 de um único CIDR IPv4 /32 e Internet Gateway funcional; caso contrário exige rede privada com NAT.
- O relatório `create_compute_capacity_report` consulta a configuração antes do lançamento. `OUT_OF_HOST_CAPACITY` encerra a execução sem criar VM.
- Se a capacidade aparecer, há **duas proteções de habilitação independentes**: `OCI_A1_AUTO_PROVISION=1` e `OCI_A1_LAUNCH_GUARD=ALWAYS_FREE_SINGLE_A1`. Ausência de qualquer uma impede o lançamento.
- Inventaria instâncias A1 e armazenamento boot/block de todos os compartimentos acessíveis; com inventário inconclusivo, aborta.
- Zero ações de publicação, zero novos recursos pagos e sem exponenciar consumo. SSH público, quando necessário para inicialização, somente de um IP /32 autorizado com chave SSH; ADB/Android permanecem fechados ao tráfego da internet.
- Quando houver VM, **o ReDroid, MacroDroid e Kwai ainda exigirão instalação, compatibilidade binder/binderfs e testes operacionais**; provisionar Linux não equivale a concluir o item 8.

### Variáveis e segredo (configuração ainda pendente)

O trabalho foi integrado via pull requests conforme a proteção da `main`. Para habilitar a execução hospedada:

**Repository Actions Secret**: `OCI_A1_WATCH_AUTH_JSON` com JSON válido contendo `user`, `tenancy`, `fingerprint`, `private_key` (PEM com quebras de linha codificadas dentro do JSON), `region` (sempre `sa-saopaulo-1`), `subnet_id` da rede Android existente e `ssh_public_key`. O segredo deve ser preenchido diretamente no GitHub com conta autorizada, por canal seguro: **nunca publicar no PR, arquivos versionados, chat, logs ou issues**. Recomenda-se identidade OCI com permissões mínimas para Compute, identidade, rede e volume no compartimento necessário e chave restrita; preferir GitHub OIDC/Oracle workload identity federation quando o tenant estiver configurado para ela.

**Repository Actions Variables**:
- `OCI_A1_WATCH_ENABLED=1`: inicia a verificação a cada quatro horas.
- `OCI_A1_AUTO_PROVISION=1`: permite a tentativa quando houver disponibilidade real.
- `OCI_A1_LAUNCH_GUARD=ALWAYS_FREE_SINGLE_A1`: autorização independente para apenas 1 A1 gratuita.

A ativação do monitor e do provisionamento deve passar por controle de cota gratuita GitHub Actions e revisão da política de recursos em sua conta OCI. Sem secret/vars, o workflow permanece seguro e inativo. As permissões da GitHub App conectada não incluem editar secrets/variables de Actions; por isso a configuração está pendente de administração do repositório. Nenhuma chave privada foi copiada.

**Alternativa sem chave OCI:** A Oracle lançou troca JWT→RPST em agosto/2026, compatível com GitHub OIDC. Requer configurar no IAM Identity Domain aplicativo, confiança de identidade e políticas restritas antes de mudar o modo de autenticação. Fonte: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/token_exchange_grant_type_workload_id-federation.htm .


### Homologação e proteção de rede (13/11/2026)

- PR [#2489](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2489), merge `b059d30ffea0070b7675049dcd6d73432765d00e`: corrige `oci.exceptions.InvalidConfig` do SDK 2.187.1 quando usado com o signer existente em memória. Teste real em modo somente leitura: `ANTHARES_A1_CAPACITY=OUT_OF_HOST_CAPACITY` e `REAL_WATCH_READ_ONLY_RESULT 0`. Nenhuma VM lançada.
- PR [#2490](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2490), merge `33603a0512d4622cfc19b0f5f738860821781e31`: bloqueia tentativa de VM sem IP público em sub-rede pública/sem NAT. O relatório de capacidade continua executável independentemente da rede da VM.
- **Teste em OCI real:** a sub-rede atual `anthares-android-subnet` permite IP público, possui apenas rota padrão para Internet Gateway e **não possui NAT Gateway**. O watcher solicita `assign_public_ip=False`. O guard `private_network_egress_ready` devolveu `False`; portanto, se houver capacidade e o modo de provisionamento estiver armado, o código emitirá `ANTHARES_A1_STATE=PRIVATE_NAT_EGRESS_UNAVAILABLE`, preservando a quota.
- A configuração final recomendada é outra sub-rede **privada**, com rota padrão para NAT Gateway ativo da mesma VCN e acesso administrativo protegido por Bastion. O custo e a cota de qualquer novo recurso precisam de verificação antes da criação: a presente implementação **não cria NAT, subnet, IP público ou Bastion automaticamente**.
- Oito testes unitários aprovaram sintaxe/configuração, paginação, rejeição de região, configuração SDK com signer, e validação da rede privada/NAT. Ainda é necessária execução real do workflow GitHub com identidade OCI configurada (Actions Secret/Variables ou federação JWT→RPST com trust IAM e política revisados).
- **Android local:** MacroDroidService em foreground, serviço de acessibilidade habilitado e app whitelist `deviceidle` confirmados; o aparelho alcançou o endpoint Neon por HTTPS (HEAD retornou 404, método sem autenticação). Isso demonstra prontidão do runtime e conectividade, **sem comprovar macro principal ativa, token, leasing ou publicação**. Não executar ações de postagem ou mudar a prioridade Android físico > MEmu até homologação independente.


### Terceira revisão: rede pública restrita já existente (13/11/2026)

O PR #2490 permanece como proteção histórica de rede privada sem NAT. Foi encontrada uma alternativa **sem criar NAT Gateway, nova sub-rede ou rota**: o recurso já existente `anthares-android-subnet` está na VCN `10.92.0.0/16`, com rota IPv4 padrão para Internet Gateway e lista de segurança `anthares-android-ssh-locked`:

- Uma única regra de ingresso: TCP/22 de um CIDR IPv4 `/32` autorizado; nenhum acesso a ADB, ReDroid, MacroDroid, interface Android, portas HTTP ou outras portas.
- Saída IPv4 permitida para baixar dependências; a Oracle informa que endereços IPv4 públicos efêmeros são gratuitos. Fonte: https://blogs.oracle.com/developers/setting-up-a-virtual-cloud-network-vcn-in-oracle-cloud-infrastructure .
- O novo guard `safe_instance_network_mode` rejeita public subnet com entrada SSH aberta, regras adicionais, porta diferente de 22, rotas de Internet Gateway indisponíveis ou com associações ambíguas. Com esses requisitos verificados, permite `assign_public_ip=True` e `nsg_ids=[]`. Também conserva o modo NAT privado se uma sub-rede desse tipo for provisionada futuramente com autorização.
- Consulta real no OCI retornou **`REAL_SAFE_NETWORK_MODE LOCKED_PUBLIC`**, sem criar VM, gateway ou alterá-los. **12 testes unitários passaram**, sem falhas: validação do modo público restrito, negação de `0.0.0.0/0`, ingresso extra e porta ADB.
- A escolha reduz dependências para a futura VM; ainda são necessários capacidade A1 na região, autenticação Actions e bootstrap Linux/Android em uma instância realmente provisionada.
- A regra SSH com /32 precisa ser reconfirmada no instante da alocação automática. O monitor realiza essa conferência antes de qualquer tentativa de lançar a VM. Se a origem administrativa autorizada mudar, deverá ser reconciliada pelo titular, sem abertura indiscriminada do firewall.


### Bootstrap automático do Android na primeira inicialização (13/11/2026)

- O watcher anexa ao campo OCI `user_data` (Base64) o contrato `infra/oci-android/redroid-firstboot.cloud-config.yml`. Apenas metadados públicos de inicialização são transmitidos; **nenhum token Kwai, MacroDroid, OAuth ou chave OCI**.
- No Ubuntu 24.04 ARM64 da futura VM A1, o cloud-init instala Docker, tenta carregar `binder_linux` e valida a existência de `/dev/binder`, `/dev/hwbinder` e `/dev/vndbinder`. Se o kernel da imagem Oracle não fornecer esses dispositivos, interrompe explicitamente a instalação sem promover a VM a reserva Android.
- Após os requisitos do kernel, baixa a imagem oficial ARM64 `redroid/redroid:12.0.0_64only-240527`, cria um único container `anthares-redroid` com persistência em `/var/lib/anthares-redroid/android-data` e `--restart unless-stopped`.
- **Segurança de ADB:** encaminha a porta apenas para `127.0.0.1:5555`, mantendo-a inacessível pela internet mesmo com IP público efêmero. A security list já permite somente SSH TCP/22 de IPv4 /32. Acesso administrativo futuro deve usar túnel SSH restrito.
- O script é idempotente: se o container já existe, encerra sem recriá-lo. Uma falha de kernel, Docker ou container deixa prova local em `/var/log/anthares-redroid-firstboot.log`, sem alterar o publicador atual.
- **Validação concluída:** sintaxe YAML com PyYAML `PASS`; codificação Base64 do `user_data` `PASS`; Bash `-n` `PASS`; **15 testes do monitor `PASS`**, incluindo recusa de bootstrap com ADB público ou cabeçalho ausente.
- **Ainda pendente:** A1 com capacidade real disponível, segredo/variáveis do GitHub Actions configurados, primeira execução cloud hospedada, confirmação de `cloud-init` no Linux, instalação/autenticação de MacroDroid e Kwai na VM, e prova de failover e publicação com leases Neon. Nenhuma VM foi provisionada nesta etapa.

Fontes: [reDroid arm64 e imagens](https://hub.docker.com/r/redroid/redroid), [documentação de instalação](https://github.com/remote-android/redroid-doc/blob/master/deploy/ubuntu.md), [binder kernel modules](https://github.com/remote-android/redroid-modules).


### Proteção adicional contra lançamentos duplicados (13/11/2026)

- O cliente `tools/oci_a1_capacity_watch.py` agora envia `opc_retry_token` em `ComputeClient.launch_instance`: UUIDv5 estável derivado de região, tenancy, subnet e definição da única máquina A1 permitida (shape, CPU, RAM e boot). Nenhum segredo integra esse identificador.
- A Oracle documenta que o token associa tentativas idênticas por até **24 horas**, evitando criar duas instâncias se houver perda de resposta HTTP e uma chamada for repetida. A lógica existente ainda inventaria instâncias A1 de todos os compartimentos acessíveis, verifica o teto de volumes, limita concorrência do GitHub Actions, exige os dois guards de ativação e utiliza `NoneRetryStrategy` (uma chamada por execução).
- A proteção do token não resolve estados de execução ambíguos após 24 horas; antes de nova tentativa, exigir inventário OCI íntegro e reconciliação quando houver qualquer indício de lançamento anterior. O monitor somente pode marcar `INSTANCE_CREATED` quando a API retornar a instância; estados incertos permanecem pendentes.
- Testes regressivos: verificam determinismo, escopo diferente para outra tenancy/subnet e passagem literal do token ao método `launch_instance`. **17 testes Python aprovados, zero erros e falhas**, execução de QA autorizada `dc827af30b7b88d54ad60d6903aa621d`. Não houve criação de VM, publicação Kwai ou ativação de GitHub Actions nessa auditoria.
- Referência oficial: https://docs.oracle.com/en-us/iaas/tools/python/latest/api/core/client/oci.core.ComputeClient.html#oci.core.ComputeClient.launch_instance .

## 2. MacroDroid Android físico — consultas independentes

- A API Neon existente já reconhece `kwai-mobile-primary` via credencial própria do aparelho `M2004J19C`; o contrato `kwai-physical-stats` é de leitura. O controle da fila, pacing até 23h, geração de leases, dedupe e estados `STARTED/UNCERTAIN` permanecem em Neon.
- Macro independente foi **gerada e validada** pelo serviço MacroDroid 6.0+ para consultar o status HTTPS diretamente do celular a cada 180 segundos, somente entre 06h e 23h. Nome: `Anthares Kwai — Neon status (somente leitura)`.
- Link de importação até 20/11/2026 UTC: https://macrodroidlink.com/m/YhAvtvS2oufP .
- Essa macro vem **desabilitada e com variável global vazia `kwai_neon_device_token`**. A credencial deve ser configurada localmente pelo titular, sem reproduzi-la no chat ou na exportação compartilhada; só então ativar. Nenhum token foi exportado nem revogado.
- A macro consulta `POST ?action=kwai-physical-stats` e registra o HTTP no MacroDroid. **Não adquire lease, não abre Kwai nem publica vídeo.** É somente um primeiro componente de observabilidade no aparelho, e exige importação e verificação de autenticação pelo dispositivo.

### Etapa de conclusão operacional, ainda pendente

A autonomia integral do Android físico exige que o aparelho consuma a fila central **com o mesmo lease/cerca geracional**, respeite a janela 06h–23h e o ritmo proporcional até 23h, valide a conta, possua um processo de publicação MacroDroid real, envie prova de publicação, atualize o Neon com confirmação e preserve estados incertos para reconciliação. O contrato `tools/kwai_physical_queue_daemon.py` funciona atualmente em Windows com ADB, portanto deve ser portado ao próprio Android ou substituído por macro validada. Evitar duas rotas ativas simultaneamente e não tocar nos executores físicos que já funcionam.

## 3. Critérios para marcar item 8 🟢

1. Monitor GitHub realmente agendado e autenticado, com ao menos uma execução comprovada sem uso do PC.
2. Instância A1 gratuita provisionada quando houver capacidade; Linux, Docker, binderfs e ReDroid verificados, sem porta ADB pública e SSH acessível apenas de um /32 autorizado, conforme validação real do firewall.
3. Kwai e MacroDroid instalados e autenticados na VM com prova real de sessão e persistência.
4. Fencing e confirmações de publicação comprovados de ponta a ponta; Android físico preservado como principal, VM em standby, MEmu local somente reserva legada até a transição controlada.
5. Nenhuma cobrança, nenhuma duplicata, nenhuma violação do pacing 6h–23h.

**Estado atual:** fluxo do GitHub preparado em branch; macro de status validada para importação; execução hospedada, autenticação secreta e ReDroid ainda pendentes. Item 8 segue 🔴 até homologação operacional.

### Imagem ReDroid ARM64 imutável — 13/11/2026

O Docker Hub confirmou que a tag original `redroid/redroid:12.0.0_64only-240527` foi publicada em 28/05/2024 e oferece uma imagem `linux/arm64` com digest `sha256:3c7f9450188226bf8042c0159b9b38abe2106f1ceb0dfa45fae1cbc6409cd9bb`. A primeira inicialização passa a baixar `redroid/redroid@sha256:3c7f9450188226bf8042c0159b9b38abe2106f1ceb0dfa45fae1cbc6409cd9bb`; a função `redroid_cloud_init_data` rejeita bootstraps sem esse identificador aprovado.

O endpoint público `https://hub.docker.com/v2/repositories/redroid/redroid/tags/12.0.0_64only-240527` foi consultado em 13/11/2026 e devolveu as arquiteturas ARM64 e AMD64 com digests diferentes; somente o ARM64 foi aceito. Foi testado o conteúdo real do arquivo cloud-init: **18 testes Python, 0 falhas/0 erros**, `CLOUD_CONFIG_PARSED=True`, `ARM64_DIGEST_PINNED=True`, `DIGEST_FORMAT=True` (ARA `b4ea4a5d3a76a2c45e7fbe5b101cee5d`) e `REPRODUCIBLE_REDR0ID_BASH_SYNTAX=PASS` (ARA `84d0fffb4c81338daafb78acdc6454ba`). Nenhuma VM foi criada; a execução do bootstrap em host permanece sem prova. Fonte oficial: https://hub.docker.com/r/redroid/redroid/tags .

### Bootstrap portável ARM64/AMD64 e recuperação após reinicialização — 13/11/2026

O cloud-init `infra/oci-android/redroid-firstboot.cloud-config.yml`, originalmente preparado somente para A1 ARM64, foi ampliado para Linux ARM64 (`aarch64`/`arm64`) e AMD64 (`x86_64`/`amd64`). Ambos usam a mesma tag oficial ReDroid Android 12, fixada nos **manifestos específicos** obtidos da API pública Docker Hub em 13/11/2026:

- ARM64: `redroid/redroid@sha256:3c7f9450188226bf8042c0159b9b38abe2106f1ceb0dfa45fae1cbc6409cd9bb`.
- AMD64: `redroid/redroid@sha256:e6f799d56b9a9a2bbc6224b5b7a6dc744c9b4d878ac856f27f0c4ec793ef55d3`.

O script escolhe a plataforma de acordo com `uname -m`, recusa arquiteturas desconhecidas, mantém ADB apenas em `127.0.0.1:5555`, instala configuração de `binder_linux` em `/etc/modules-load.d/anthares-redroid.conf` e opções em `/etc/modprobe.d/anthares-redroid.conf` para reinicializações. Um container existente que esteja parado é iniciado e novamente verificado, sem repetir `docker pull`. O monitor OCI exige os dois digests e os marcadores de segurança/recuperação no bootstrap.

Verificação: **22 testes Python, 0 falhas, 0 erros**; YAML válido, Bash `-n` aprovado, quatro variações de arquitetura executadas em Bash isolado; arquivos de módulos e ordem de recuperação validados (ARA `4a169c3298434a71b3f1457fb432a38f`). Testes são sintáticos e de contrato: a VM ainda não foi obtida, portanto Docker, binderfs e ReDroid permanecem sem teste real, assim como login Kwai e failover Neon. O monitor GitHub Actions permanece desarmado até autenticação autorizada.

### Preflight real de sub-rede e acesso SSH para futura criação A1 — 13/11/2026

Após o primeiro monitor GitHub Actions [#43458571942](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43458571942) ter sido autenticado e concluir com `OUT_OF_HOST_CAPACITY`, detectou-se uma pendência: o segredo `OCI_A1_WATCH_AUTH_JSON` fornecido pelo proprietário inclui somente `user`, `tenancy`, `fingerprint`, `private_key` e `region`. A rotina de provisionamento anterior exigia adicionalmente `subnet_id` e `ssh_public_key` no mesmo segredo; seria bloqueada mesmo quando houvesse capacidade.

O código foi ajustado para descobrir **exatamente uma** sub-rede já existente chamada `anthares-android-subnet`, no compartimento raiz `sa-saopaulo-1`, com CIDR `10.92.1.0/24` e estado `AVAILABLE`. O acesso SSH é configurado com a **chave pública ed25519 já existente**, aprovada e versionada em `infra/oci-android/approved-admin-ssh.pub` no repositório privado. A impressão digital SHA-256 é verificada antes de usar a chave; **nenhuma chave privada SSH** foi copiada, versionada ou impressa. Se o JSON opcionalmente trouxer outros `subnet_id` ou `ssh_public_key`, uma divergência causa falha fechada. `safe_instance_network_mode` continua exigindo Internet Gateway válido e firewall com **apenas SSH TCP/22 vindo de /32**, sem ADB público.

O **preflight é executado mesmo enquanto a Oracle apresenta falta de capacidade**. Cada job reporta `ANTHARES_A1_NETWORK_MODE` e `ANTHARES_A1_PROVISION_PREFLIGHT=READY_SSH_SUBNET_NETWORK` após conferir a sub-rede, chave e firewall. A situação de Compute continua `OUT_OF_HOST_CAPACITY`, sem tentativa de criar VM nesta fase: o GitHub Actions mantém `OCI_A1_AUTO_PROVISION='0'` e `OCI_A1_LAUNCH_GUARD='DISABLED_FOR_MONITORING'`.

**Evidências:** 27 testes Python concluídos em dois grupos, **21 PASS + 6 PASS**, zero falhas/erros (ARA `2c384269b48ffd1cd5629bf727e4d273` e `00825a70361e6c891912be6cb8ef8bc9`); o primeiro grupo também validou o SHA-256 da chave pública real do repositório. Uma chamada **autenticada e somente leitura** à API OCI validou os mesmos recursos reais, retornando `OCI_REAL_PREFLIGHT READY`, sub-rede aprovada e modo `LOCKED_PUBLIC` (ARA `12e577bd5ffc01ee4900c20481ecb3bd`). A verificação hospedada com a credencial exclusiva GitHub Actions será realizada pelo workflow em `main`.

A confirmação de preflight **não certifica que a VM possa ser criada**: ainda requer `AVAILABLE` no relatório de capacidade, inventário de todos os compartimentos, limite de volumes Always Free, uma imagem Ubuntu ARM64 compatível, controle de idempotência e habilitação específica de criação. O status do Android/Kwai permanece pendente.

### Autoprovisionamento limitado a uma única A1 Always Free — 13/11/2026

Após o proprietário aprovar o avanço do monitor autenticado, a execução agendada `.github/workflows/oci-a1-android-cloud-watch.yml` foi habilitada para **criar uma VM somente quando o relatório OCI voltar a `AVAILABLE`**, com `OCI_A1_AUTO_PROVISION=1` e `OCI_A1_LAUNCH_GUARD=ALWAYS_FREE_SINGLE_A1`. As condições fixadas no código exigem `sa-saopaulo-1`, único AD, **`VM.Standard.A1.Flex` com 1 OCPU e 6 GiB RAM**, boot volume **50 GiB**, imagem oficial `Canonical-Ubuntu-24.04-aarch64`, sub-rede Android auditada, chave pública SSH pinada, ingress único SSH TCP/22 de um IPv4 /32, e ADB apenas em `127.0.0.1:5555`. A chave privada SSH permanece no ambiente administrativo do proprietário e fora do repositório.

O inventário antes de qualquer `ComputeClient.launch_instance` percorre compartimentos acessíveis e rejeita A1 existente ou volume total que exceda **200 GiB**. `occupied_block_volume_gib` agora rejeita explicitamente volumes ativos com tamanho ausente ou inválido; a versão anterior contabilizava tamanho desconhecido como zero, risco de extrapolação de cota. O `opc_retry_token` UUIDv5 estável permanece para impedir duplicações em retentativas dentro da janela de 24h da OCI. O workflow mantém concorrência exclusiva e `permissions: contents: read`.

**Verificações reais previamente concluídas, ainda no modo somente leitura:** A1 e E2 Micro `OUT_OF_HOST_CAPACITY`; zero instâncias A1, **zero GiB de volumes alocados**, 50 GiB cabem na cota Always Free; **três imagens Ubuntu 24.04 ARM64 elegíveis** disponíveis; sub-rede, firewall e chave aprovados; a origem atual de administração SSH corresponde à única origem /32 permitida, conforme teste sem expor IP no resultado (ARA `b3ac80d20f372ea252c35f2f3bdc25e6`). A Oracle documenta 1.500 horas OCPU / 9.000 GB-hora mensais gratuitos para o Ampere A1 na região home, equivalentes a 2 OCPUs/12 GiB numa tenancy Always Free, com 200 GiB de block volumes. Fonte: https://docs.oracle.com/pt-br/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm .

**Testes antes de liberar:** 27 testes prévios PASS e **mais quatro cenários** (contabilização estrita de volumes; lançamento único simulado autorizado; bloqueio por cota; bloqueio por guard desativado), executados com API mockada, sem criação real. O provisionamento real só ocorrerá num próximo job que observe `AVAILABLE`. Mesmo que OCI aceite a VM e execute o cloud-init, **a instalação/auth do Kwai e do MacroDroid, o controle remoto do ReDroid e a homologação de publicação com leases Neon continuam fases separadas**. O recurso será criado como Android de contingência não publicador.

Caso seja necessário interromper futuras tentativas, reverta `OCI_A1_AUTO_PROVISION` para `0` no workflow e mantenha `OCI_A1_LAUNCH_GUARD` diferente de `ALWAYS_FREE_SINGLE_A1`. A desativação de novos lançamentos não destrói recursos existentes: eventual VM criada precisa ser inspecionada e gerenciada separadamente.

### Observação automática após futura criação da VM A1 — 13/11/2026

O mesmo monitor passa a fazer inventário **somente leitura** das instâncias A1 dos compartimentos acessíveis em cada consulta, inclusive durante `OUT_OF_HOST_CAPACITY`. O campo `ANTHARES_A1_TARGET_INSTANCE` indica `NONE`, o estado da instância aprovada (`PROVISIONING`, `RUNNING`, `STOPPED` etc.) ou `AMBIGUOUS_OR_OTHER_A1`, sem divulgar IP, credenciais ou OCID no log. Uma instância é considerada alvo somente quando única e compatível com nome, shape e etiquetas de governança. Essa observação serve para reconhecer a máquina depois de criada, mesmo quando a capacidade da região voltar a se esgotar; não promove o Linux a publicador Kwai. Continuam pendentes a homologação real do binder, Docker, ReDroid, MacroDroid, autenticação Kwai e publicação em fila Neon.

### Homologação automatizada de inicialização Android — 13/11/2026

Após a criação futura da A1, o cloud-init instala `adb` dos repositórios Ubuntu 24.04 ARM64 junto com Docker, conserva o contêiner ReDroid com `--restart unless-stopped` e executa `/usr/local/sbin/anthares-redroid-readiness-check`. Esse script confirma que o contêiner está rodando, que a porta 5555 está **exclusivamente** em `127.0.0.1`, conecta o ADB local e verifica `sys.boot_completed=1` em prazo limitado. Somente a confirmação efetiva grava `ANDROID_BOOT_READY_ADB_LOCAL` em `/var/lib/anthares-redroid/readiness-state`; falhas deixam `NOT_READY` e log/exit code. Um serviço e timer systemd conferem novamente a cada 15 minutos após a conclusão anterior, inclusive após reinicialização, sem acessar a internet pela porta ADB e sem publicar vídeos. A suíte CI confere YAML, Bash e a presença das proteções.

**Limite explícito:** esses testes verificam o contrato do cloud-init em CI, ainda sem um host A1 disponível. Na VM real, é necessário confirmar `readiness-state`, os logs locais, `docker inspect`, versão do Android, ADB local, compatibilidade dos aplicativos, login Kwai/MacroDroid e integração Neon com fencing. `ANDROID_BOOT_READY_ADB_LOCAL` significa somente Android inicializado. A fila de Kwai e o Android físico permanecem intactos até a prova de publicação do novo executor.

## Melhoria de tentativa Always Free — preferência por 6 GiB, alternativa 4 GiB (13/11/2026)

A consulta de capacidade autenticada em 13/11/2026 às 18:52 UTC confirmou a mesma indisponibilidade de uma A1 com 1 OCPU / 6 GiB. A forma aprovada para aumentar as oportunidades de alocação é consultar uma alternativa de **1 OCPU / 4 GiB**, preservando os mesmos 50 GiB de boot, a única VM, a região São Paulo, a chave SSH aprovada, a rede restringida e o Docker/ADB local-only.

No monitor `tools/oci_a1_capacity_watch.py`: primeiro consulta exatamente 1 OCPU/6 GiB. **Somente quando o resultado dessa configuração for `OUT_OF_HOST_CAPACITY`**, consulta 1 OCPU/4 GiB. Qualquer resultado `LIMIT_EXCEEDED`, erro de política ou estado inesperado interrompe a tentativa; somente `AVAILABLE` permite prosseguir. O inventário completo da tenancy continua obrigatório, e um único disco de 50 GiB continua sujeito ao limite total de 200 GiB. O token OCI de idempotência agora inclui a memória efetivamente solicitada para que chamadas de 4 GiB e 6 GiB jamais compartilhem indevidamente um token. Os logs exibem `ANTHARES_A1_CAPACITY_6GB`, `ANTHARES_A1_CAPACITY_4GB`, `ANTHARES_A1_CAPACITY` e, quando houver disponibilidade, `ANTHARES_A1_SELECTED_MEMORY_GB`.

O contrato de Android exige comprovação efetiva do ReDroid. A criação de uma VM com 4 GiB, mesmo que bem-sucedida, não comprova inicialização do Android nem publicação pelo Kwai. O valor 4 GiB cumpre o requisito mínimo de RAM adotado na triagem dos provedores gratuitos. Não provisionar instâncias pagas, múltiplas instâncias ou RAM inferior a 4 GiB.
