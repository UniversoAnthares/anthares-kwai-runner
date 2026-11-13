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
