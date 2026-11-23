# Studio Mercado Pago, item 16 — PR #419, entrega de código e bloqueio da operação financeira

Data: 2026-11-23 (America/Campo_Grande). Owner: GPT6 / item16. Lease: test-hub/findings/lease-studio-mp-payout-20261123.md.
WordPress repo: UniversoAnthares/anthares-wordpress; PR #419 merged, main SHA 4ec1643f5ffecbe945649fe4e65e63cd11ecd36c.
PR #418 (retention 0%-100%) entrou concorrencialmente; branch MP incorporou main e reconciliou os dois manifestos QA sem descartar registros.

## Funções adicionadas
- BRL do autor via checkout WooCommerce Mercado Pago já instalado, após sugestão aceita; servidor confere a compra em /v1/payments/:id por token de checkout da conta e valor/moeda/status exatos, além dos estados do Woo.
- Registro opt-in Pix do participante, criptografado AES-256-GCM, nunca exposto ao autor.
- Payouts Pix de saída a partir da conta institucional, assinatura Ed25519, X-Idempotency-Key estável, lock, registro permanente de início antes de chamar o provedor para evitar repetição em caso de resposta incerta.
- Acesso restrito manage_options, nonce e confirmação no painel Ferramentas > Repasses Studio Mercado Pago. Webhook somente sinaliza conciliação; verificação oficial GET. paid_brl somente após success/accredited.
- Configuração falha fechada por ANST_MP_BRL_ENABLED, token Payouts, token Payments/Checkout e arquivo privado PEM. Sem tokens produtivos nem remunerações reais neste job.

## Deploy e QA
- Produção WordPress em anthares.us/studio (legado /estudio preservado), DEPLOY_PR419_OK. Backup privado /home/u566597497/domains/anthares.us/studio-private-backups/20261123-studio-mercadopago-pr419.
- Hashes de arquivos de produção conferidos contra blobs GitHub: anst-estudio bootstrap 43303a06d8994adf05044ccce6290fef11a62a7a; G7 beta PHP c0d4937bc10bd4db14a9ebf446bcc92028a55ab7; adapter MP 107e1a211da13469593b30d4c31c2e6ace909b14; beta author JS 33f688874eb012444992a3ffbd559595bd833df3. Public CDN JS matches. /studio e /estudio HTTP 200. Legacy PHP hash intact e4a9812ac21b5c977b93e53fe65131b43e23ba85.
- WordPress real post-deploy: QA MP BRL 20 PASS (ROLLBACK); mocked HTTP Payouts 6 PASS, no real HTTP; QA Runa wallet 9 PASS (ROLLBACK); mentor 9 PASS (ROLLBACK); continuous retention 26 PASS (ROLLBACK). Total 70 passing checks.
- Python contracts Mercado Pago 6 PASS, continuous retention 3 PASS; manifest preflight 775/775 exact assigned once; PHP 8.3 lint valid.

## Estado/pendências
- Código e UI de cobrança/repasses instalados, execução financeira deliberadamente DESABILITADA até app Payouts autorizado e credenciais operacionais aprovadas. Não afirmar pagamentos reais, transferência real, nem homologação de rede Mercado Pago.
- O titular escolheu Mercado Pago. Exige criar/autorizar app Payouts institucional, cadastrar par público Ed25519, guardar privado fora do webroot, token Payouts, token Payments verificador da mesma conta, ativação e QA de ponta a ponta em ambiente permitido; revisar taxas, encargos, estornos e custódia antes de pagar colaboradores.
- Item 9 foi identificado como funcionalidade já coberta genericamente pelo item 8: eventos pessoais de estrutura, herança da etapa do capítulo, distinção de ordem narrativa e cronológica. Remover item 9 como pendência independente; QA visual permanece item 23.
- Arquivo local PENDÊNCIAS URGENTES.md atualizado para 18 itens, numeração original preservada.
