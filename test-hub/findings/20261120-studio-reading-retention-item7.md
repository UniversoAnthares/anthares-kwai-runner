# Anthares Studio — Item 7: Progresso e retenção de leitura

Data: 2026-11-20/21. Resultado: **implementado em produção, QA de integração aprovado**.

Fonte funcional: `PENDÊNCIAS URGENTES.md`, item 7; `site-anthares.docx`, passagem “cada vez que um usuário começa uma leitura...”.

## Entregas
- O avanço é proporcional à posição visível no corpo do texto, com indicação percentual e marcos 10/25/50/75/90/100.
- O leitor autenticado autoriza expressamente o registro; a interface usa nonce REST, sem enviar identificador de sessão ao servidor.
- Um registro por leitor/edição é identificado por HMAC do ID interno do usuário, sem disponibilizar o ID ao autor.
- A API de status recupera o progresso em sessões posteriores; a API de exclusão remove o registro do próprio leitor.
- O autor recebe somente dados agregados, após o mínimo de dez leitores distintos, com contagens e taxas por marco. Métricas permanecem indisponíveis abaixo do limiar.
- O registro mantém limite de duração mínima de 10 segundos, prevenção de avanços retroativos e bloqueio concorrente.
- Edições públicas seguem as regras de publicação existentes; a versão `/estudio/` permanece intacta.

## Evidências
- Implementação: [PR #393](https://github.com/UniversoAnthares/anthares-wordpress/pull/393), merge `4ff1ec3664ed9cd9be1388b13eff6206fb7333bf`.
- Produção Hostinger: `class-anst-g7-retention.php` SHA `2e7d7ca141e222007003d71afaad00a0acfdc39c`, `class-anst-g7-publishing.php` SHA `00e7946a33eedaad3b320114bf867584f73b1074`, `studio-g7-public-reader.js` SHA `00403dc81b680c5b8122a64ebbd7b0b9cec12b15`.
- PHP 8.3 lint em ambos os arquivos: PASS; `node --check` do JS: PASS.
- Teste WordPress transacional: **9/9 PASS** (identificadores distintos, autenticação, nonce, ausência de registro sem consentimento, recuperação, exclusão, bloqueio anônimo). `ROLLBACK` executado.
- `/studio/` e `/estudio/` HTTP 200; registros de leitura no banco: 0 após testes.
- Backup privado dos três arquivos originais fora de `public_html`, pasta `studio-private-backups/20261120-item7`.

## Limite de evidência
A verificação confirmou código ativo, sintaxe, segurança de identificação e operações de persistência/exclusão em transação. A exibição visual em navegador com dez leitores reais, além da distribuição dos dados no relatório de autor, ainda depende de tráfego real ou de um teste controlado de dez contas. A retenção real somente será exibida após dez participantes distintos consentirem.
