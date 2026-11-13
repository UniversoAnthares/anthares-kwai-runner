# Item 8 — Android físico sem dependência permanente do PC e standby Oracle A1

**Escopo:** código criado em 12/11/2026 e mantido em branch isolada até PR aprovado e integração. A configuração de autenticação e a implantação do Android exigem provas independentes. Governança: `D:\AntharsWork\governance\REGRAS-OBRIGATORIAS.md`; `ci-hub/executor-routing.json` é a autoridade dos publicadores.

## 1. Oracle A1 — workflow hospedado

- Workflow: `.github/workflows/oci-a1-android-cloud-watch.yml`.
- Cliente: `tools/oci_a1_capacity_watch.py`.
- Periodicidade proposta: `17 */4 * * *` UTC (seis consultas por dia), runner GitHub hospedado, sem tarefa permanente no computador.
- Região aprovada: `sa-saopaulo-1`; previsão de VM `VM.Standard.A1.Flex`, 1 OCPU, 6 GiB de RAM, boot de 50 GiB, Ubuntu 24.04 aarch64, sem IP público e sem alteração da fila Kwai.
- O relatório `create_compute_capacity_report` consulta a configuração antes do lançamento. `OUT_OF_HOST_CAPACITY` encerra a execução sem criar VM.
- Se a capacidade aparecer, há **duas proteções de habilitação independentes**: `OCI_A1_AUTO_PROVISION=1` e `OCI_A1_LAUNCH_GUARD=ALWAYS_FREE_SINGLE_A1`. Ausência de qualquer uma impede o lançamento.
- Inventaria instâncias A1 e armazenamento boot/block de todos os compartimentos acessíveis; com inventário inconclusivo, aborta.
- Zero ações de publicação, zero novos recursos pagos, sem SSH público e sem exponenciar consumo.
- Quando houver VM, **o ReDroid, MacroDroid e Kwai ainda exigirão instalação, compatibilidade binder/binderfs e testes operacionais**; provisionar Linux não equivale a concluir o item 8.

### Variáveis e segredo (configuração ainda pendente)

O trabalho foi registrado em branch/PR por política de proteção da `main`. Para habilitar de forma operacional, após o merge:

**Repository Actions Secret**: `OCI_A1_WATCH_AUTH_JSON` com JSON válido contendo `user`, `tenancy`, `fingerprint`, `private_key` (PEM com quebras de linha codificadas dentro do JSON), `region` (sempre `sa-saopaulo-1`), `subnet_id` da rede Android existente e `ssh_public_key`. O segredo deve ser preenchido diretamente no GitHub com conta autorizada, por canal seguro: **nunca publicar no PR, arquivos versionados, chat, logs ou issues**. Recomenda-se identidade OCI com permissões mínimas para Compute, identidade, rede e volume no compartimento necessário e chave restrita; preferir GitHub OIDC/Oracle workload identity federation quando o tenant estiver configurado para ela.

**Repository Actions Variables**:
- `OCI_A1_WATCH_ENABLED=1`: inicia a verificação a cada quatro horas.
- `OCI_A1_AUTO_PROVISION=1`: permite a tentativa quando houver disponibilidade real.
- `OCI_A1_LAUNCH_GUARD=ALWAYS_FREE_SINGLE_A1`: autorização independente para apenas 1 A1 gratuita.

A ativação do monitor e do provisionamento deve passar por controle de cota gratuita GitHub Actions e revisão da política de recursos em sua conta OCI. Sem secret/vars, o workflow permanece seguro e inativo. As permissões da GitHub App conectada não incluem editar secrets/variables de Actions; por isso a configuração está pendente de administração do repositório. Nenhuma chave privada foi copiada.

**Alternativa sem chave OCI:** A Oracle lançou troca JWT→RPST em agosto/2026, compatível com GitHub OIDC. Requer configurar no IAM Identity Domain aplicativo, confiança de identidade e políticas restritas antes de mudar o modo de autenticação. Fonte: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/token_exchange_grant_type_workload_id-federation.htm .

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
2. Instância A1 gratuita provisionada quando houver capacidade; Linux, Docker, binderfs e ReDroid verificados, sem IP/ADB público.
3. Kwai e MacroDroid instalados e autenticados na VM com prova real de sessão e persistência.
4. Fencing e confirmações de publicação comprovados de ponta a ponta; Android físico preservado como principal, VM em standby, MEmu local somente reserva legada até a transição controlada.
5. Nenhuma cobrança, nenhuma duplicata, nenhuma violação do pacing 6h–23h.

**Estado atual:** fluxo do GitHub preparado em branch; macro de status validada para importação; execução hospedada, autenticação secreta e ReDroid ainda pendentes. Item 8 segue 🔴 até homologação operacional.
