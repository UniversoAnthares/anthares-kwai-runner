# Anthares Studio G7 — leitura beta privada e exercícios de quatro campos
STATUS: PARTIAL
AREA: anthares-studio/G7/private-invitations
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g7-beta-invites-20261118
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/335
COMMIT: 6f7a33795e77eb2776ed2c95a12cfeb608a77778
SUPERSEDES: test-hub/findings/20261118-studio-g7-domain-lease.md

## Resultado implantado
- Leitor beta autenticado por convite restrito a uma conta WordPress, capítulo e data de expiração.
- Aceitação expressa, revogação, cópia textual privada e estável do capítulo, marcação de parágrafo, respostas de leitura.
- Autor pode registrar retorno em pendência G7 vinculada ao capítulo, com idempotência.
- Área Revisão contém formulário de convite com prévia e confirmação, lista de convites, links e retorno.
- Exercicio Fórmula 1: quatro campos editáveis; conteúdo didático específico permanece sem definição pela fonte.
- Code Hostinger: duas classes/scripts beta + inclusões mínimas e CSS; preservadas diferenças locais do plugin ativo. Nenhum backup criado.

## Evidências
- REST GET convites projeto 21453: dono HTTP 200 e lista zero; outra conta HTTP 404; visitante HTTP 401; convite inexistente HTTP 404.
- Chrome autenticado: área Revisão renderizou 1 capítulo, consentimento, prazo e formulário após carregamento.
- QA manifest: 681/681 arquivos auditáveis exactly_once. PHP lint núcleo/beta: PASS.
- Segurança: nenhum convite real enviado, nenhuma conta externa convidada e nenhum capítulo privado publicado durante a homologação.

## Aberto
- Teste ponta a ponta com duas contas autorizadas: convite, aceitação, leitura, feedback, revogação e reabertura.
- Publicação com direitos Hotmart/compra direta, integração com homes, leitores públicos e retenção por capítulo.
- Requisitos G7 restantes dependentes de conteúdos didáticos e de integrações comerciais do projeto.

## Consequência
Preservar o fluxo beta e seus bloqueios de autoria; considerar G7 parcialmente implantado até homologação real do leitor e conclusão do restante da matriz.
LEASE: concluído, sem janelas próprias mantidas.
