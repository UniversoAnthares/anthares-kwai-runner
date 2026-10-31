# Lease — correção de apresentação da configuração de contos beta
STATUS: RUNNING
AREA: wordpress-beta-config-ui
DATE: 2026-10-31
RUN: none
JOB: chatgpt-20261031-beta-config-ui
COMMIT: 1c250c17706d0861472c84aa69df583d4b7b71ea
SUPERSEDES: none

## Escopo e prazo
Owner: ChatGPT GPT-6. Arquivo exclusivo: `anthares-pix-sales/includes/65-leitura-beta.php` no repo `UniversoAnthares/anthares-wordpress`. Modificação exclusivamente de layout HTML/CSS da página `/leitura-beta/?configurar=contos` (rótulo do checkbox, título e metadados, campos e botão). Expira 30 minutos após esta entrada.
BASELINE_PROVEN: formulário existente tem checkbox `ativo` com texto “Exibir no perfil” e `anth-beta-home__conto-cabecalho` sem estilização escopada; regra global `.anth-beta-page label { display:grid }` desconfigura checkbox e posicionamento. Screenshot real do usuário confirma sobreposição e checkbox sem legenda próxima.
SUCCESS_SIGNAL: checkbox identificável como ativação de oferta, status/dados separados do título, campos e botão organizados, responsividade; PHP lint/QA, render HTML WordPress, sem gravar ofertas nem alterar Runas. Implantação somente após GitHub e conferência da Hostinger.
FAILURE_SIGNAL: mudança em processadores financeiros, divergência live/blob, regressão no carregamento PHP, falha QA ou alterações concorrentes.
FAILED_AVOIDED: não mexer nos dados existentes nem no fluxo de reserva/transferência; QA na Hostinger externa sem criar arquivos no PC.
