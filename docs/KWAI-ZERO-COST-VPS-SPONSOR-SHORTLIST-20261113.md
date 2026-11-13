# ARQUIVADO — pesquisa histórica de patrocínios, fora das próximas ações (13/11/2026)

**REVOGADO PARA PLANEJAMENTO:** o titular descartou qualquer proposta que exija aguardar respostas, aprovações, cadastros ou patrocínios. Este arquivo é somente evidência histórica, jamais uma lista de tarefas. Não enviar pedidos a estes provedores. Plano atual: `docs/KWAI-PLANO-SEM-ORACLE-20261113.md` e política obrigatória `ci-hub/executor-routing.json`.

# Kwai ReDroid — candidaturas pesquisadas anteriormente (histórico)

**Objetivo:** duas contas brasileiras `lucasrosalem`/`universoanthares`, servidor independente do PC e Android físico, software oficial Kwai/Kwai Lite, publicação 06h–23h com fila Neon, sem mensalidade nova (R$0), operação contínua. **Status:** candidatos reais de patrocínio encontrados, nenhuma concessão/VM emitida ou autorização de uso recebida. Oracle, CutMotions, Kuaishou Open e Android publicador em GitHub Actions permanecem vetados.

## Candidaturas recomendadas em ordem de adequação

| Prioridade | Provedor e link oficial | Prova encontrada | O que ainda falta confirmar |
|---|---|---|---|
| 1 | VPSDime — https://vpsdime.com/free-vps | Formulário **Communities** de VPS gratuita patrocinada, separado da exigência de repositório Open Source. Empresa com VPS root e linha Linux 2 vCPU, 4 GiB. Contato pré-vendas público: sales@vpsdime.com | Aceitação do Universo Anthares como comunidade e de automação de conteúdo social; concessão permanente de KVM 2 vCPU/4 GiB/**40 GiB** (plano Linux básico de 20 GB totais é inferior à política de 20 GiB livres); binder/binderfs, tráfego, cobrança efetivamente zero e caducidade da oferta. |
| 2 | Enzonic Grants — https://enzonic.com/grants | Public projects e content creators elegíveis para servidor patrocinado em troca de “Powered by Enzonic”. Catálogo VPS **M 2 vCPU/4 GB/60 GB, KVM com root e kernel próprio**: https://enzonic.com/vps. Contato oficial admin@enzonic.com (https://enzonic.com/contact). | A concessão específica abrange VPS KVM M ou superior? A página só promete servidor do tamanho definido por análise, e o plano Free Minecraft hiberna após ~15min. Confirmar exceção de hibernação, proibição de proxy, operação comercial de postagens, duração, moeda R$0; requer aprovação do titular para divulgação. |
| 3 | Rabisu Sponsorship — https://www.rabisu.com/br/sponsorship-program | Patrocínio menciona EXPRESSAMENTE VPS/dedicado gratuitos para criadores e comunidades, avaliação ~5 dias úteis. VPS x4 comercial tem 2vCPU/4GB/40GB, root total: https://www.rabisu.com/br/vps. Contato oficial info@rabisu.com. | Programa prioriza games/tech, portanto aceitar canal literário depende de análise. Confirmar patrocínio contínuo, 40GB disco, binder, termos comerciais, quota, custo R$0. Avaliações públicas heterogêneas/possível verificação KYC: https://www.trustpilot.com/review/rabisu.com. Não enviar login Kwai em fase de candidatura. |
| 4 | Ryvix Partners Brasil — https://www.ryvix.com.br/pt-br/parceiros | Inscrição aberta a criadores YouTube/TikTok e comunidades, benefício de **VPS gratuitas para teste**. Provedor brasileiro com linha VPS de jogos. | “Para testar” é temporário, não afirma concessão permanente. Público preferencial gaming/tech; verificar se patrocina operação literária por prazo indeterminado, root/KVM/binder e R$0 integral. Contato via link oficial do programa. |
| 5 | AlienX Cloud Beta — https://www.alienxservers.co.uk/cloud/ | VM Linux verdadeiramente grátis sem cartão, tier Starter **2 vCPU/4 GB/50 GB root** após convite e análise individual. Páginas `/cloud` e `/terms` descrevem as condições. | **REJECTED_FOR_PRODUCTION**: operador avisa que é homelab doméstico no Reino Unido sem SLA; pode encerrar/delete VMs quando quiser; discos podem ser examinados e não são privados. Adequado só para preflight isolado **sem tokens Kwai**, se aprovação chegar. |
| 6 | PlayHost Referral — https://playhost.lol/referral | Oito convites DISCORD genuínos liberam VPS anunciada 3 cores/8GB RAM/40GB SSD. Entrega root por DM, sem mensalidade anunciada. | Virtualização KVM e binder não comprovados; reputação/continuidade e prazo não comprovados; oito convites legítimos não estão disponíveis na conta verificada. 4 convites dão 4GB/**20GB total**, insuficiente para 20GB LIVRES. **EXPERIMENTAL_ONLY** até prova do operador. |

## Serviços descartados pelo critério objetivo
- **ZenDevz:** exige contribuição com hardware próprio no pool, falha independência PC.
- **FOSSVPS, Simafri:** uso não comercial e/ou licença de código aberto obrigatória.
- **FreeVPS.org, NanoKVM, FreeMach:** exigem 3 meses de participação em fórum e oferecem 1–2GB RAM; FreeMach está sem estoque.
- **VPSFree.io:** plano efetivamente gratuito de 192MB/3GB, apesar de anúncio maior.
- **Verta Cloud:** cadastro inacessível, detalhes societários de exemplo; risco injustificável para credenciais.
- **Cloudflare Containers:** Workers Paid (custo).
- **SpawnDroid, Multilogin Free, cloud phones gratuitos:** minutos/session limitados e hibernação.
- **HidenCloud Partnerships:** gratuidade é só de game/app servers; VPS KVM começa em €13/mês no programa de parceiros: https://www.hidencloud.com/partners.
- **switched.cloud:** contêiner grátis não tem kernel Binder; VM exige Plus/créditos, e Runtime zera e apaga dados após três dias sem renovação: https://switched.cloud/.
- **AlienX Cloud:** apenas testes sem credenciais, por condições de interrupção e inspeção acima.

## Especificação EXATA para perguntas ao patrocinador (não autorizar/aceitar uma oferta diferente)
- Cessão de VPS **KVM, Ubuntu 24.04, root SSH, Docker `--privileged`, módulos `binder_linux` ou `binderfs`**, com pelo menos 2 vCPU, 4096 MiB RAM, 40 GiB disco total para assegurar >=20GiB livres.
- Serviço persiste ligado 24/7, sem renovação manual diária, minutos, idle shutdown, exigência de executar software em PC ou celular próprio; contrato válido por prazo indeterminado ou renovação automática sem cobrança.
- Tráfego de upload de conteúdo autorizado das **duas contas do titular** no Kwai brasileiro; certificar autorização de uso de terceiro e eventual comercialidade/monetização do canal; ausência de proxy proibido.
- **R$ 0 definitivo para a alocação**, sem cartão, depósito, cartão para garantia ou cobrança automática. Se publicidade/crédito é contrapartida, obter consentimento do titular ANTES de modificar site/canal.
- Autenticação Kwai **somente após** VPS entregue, preflight de root/binder e segurança aprovados; credenciais nunca em formulário patrocinador. Fotos/arquivos sensíveis proibidos em homelab com inspeção de discos.
- Confirmar uso do ADB apenas local, rede segura de saída, disco persistente, reboot, URL do provedor e documentação. Integração Neon será feita após custódia da VPS homologada.

## Ações seguintes, sem inventar aprovação
1. Solicitar **informações de elegibilidade e oferta** aos programas de VPSDime, Enzonic Grants, Rabisu e Ryvix, usando somente canais oficiais. Requer autorização do titular para enviar dados identificáveis, concordar com publicidade e criar cadastros. O pedido deve declarar explicitamente que a VM executará Android/ReDroid e fará uploads de vídeos autorizados de contas próprias, inclusive quando o canal estiver monetizado.
2. **Somente proposta escrita** de uma VPS com as especificações e custo zero autoriza aceitação/ativação. Nunca iniciar serviço pago ou usar meios de faturamento. Resultado esperado: 1 VPS SSH criada com contrato.
3. Executar `tools/redroid_free_vps_preflight.py` no servidor aprovado, seguindo `docs/KWAI-CLOUD-CUTOVER-CONTRACT.md` (8 provas obrigatórias), manter o produtor físico ativo até migração confirmada e rota cloud estritamente isolada.

## Prova das consultas (fontes oficiais inspecionadas)
- https://vpsdime.com/free-vps, https://vpsdime.com/contact-us, https://vpsdime.com/knowledgebase/presales/pre-sales-faq
- https://enzonic.com/grants, https://enzonic.com/vps, https://enzonic.com/contact, https://enzonic.com/legal/tos
- https://www.rabisu.com/br/sponsorship-program, https://www.rabisu.com/br/vps, https://www.rabisu.com/pt/contact
- https://www.ryvix.com.br/pt-br/parceiros
- https://www.alienxservers.co.uk/cloud/, https://www.alienxservers.co.uk/terms
- https://playhost.lol/referral, https://playhost.lol/how-it-works
