# Anthares Studio — textos corrigidos e JS ativo sincronizado
STATUS: PARTIAL
AREA: studio/interface-and-code-parity
DATE: 2026-11-19
RUN: Anthares Remote 8e9fcc57154af67a1a1bb75db8a9cb5e, c674c2fbe00da4e5ebe45819c0188197
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/341
COMMIT: f59c2aa36dd57f8989d3a5a2ab32c12760d253ff
SUPERSEDES: 20261119-studio-analytics-trash-reconciled-qa97.md

## Alteração
- Corrigidos 24 rótulos, mensagens e textos corrompidos em planejamento, versões, fichas e manuscrito.
- Ícone decorativo de arraste de capítulo alterado de '?' para '⋮⋮'; comando Escrever utiliza uma seta legível e separadores informativos.
- Correções anteriores preservadas: sete áreas fixas, criação serializada e análises mensuráveis permanentes com/sem ACF.
- GitHub JS e Hostinger JS agora coincidem byte a byte no arquivo assets/estudio.js; SHA256 8f70c516e6b0352cc8e19652514249073feb94c911ac701f3b9a524d4f31a1c9.

## QA
- Branch: 98/98 testes automatizados PASS, compilação Bun PASS, manifesto de QA 705/705 exactly once PASS.
- Instalação Hostinger: 37/37 testes Python PASS; backend PHP Studio SHA256 7de81057cbd9f637395d0e5c2390925ceac208a466292708381d5f65c28a2e3e.
- Plugin legado /estudio/ SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf permanece intacto.
- Backup privado do JS anterior studio-ptbr-prev-20261119T163236Z.js, chmod 0600.

## Limite
- Equivalência de CSS continua sujeita a diferenças somente de linhas em branco; comentários PHP também diferem.
- PRs da cadeia continuam em rascunho, sem merge no main. Homologação manual com usuários foi adiada pelo titular até concluir o produto; outras 188 verificações ainda precisam de cobertura individual.
- Esta evidência registra as provas automatizadas e o deploy de código; a interface autenticada ainda requer aceite final.