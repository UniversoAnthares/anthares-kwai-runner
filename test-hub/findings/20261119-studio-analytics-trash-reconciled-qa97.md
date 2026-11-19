# Anthares Studio — métricas medidas, controles da lixeira e regressões
STATUS: PARTIAL
AREA: studio/g6/analytics-retention
DATE: 2026-11-19
RUN: Anthares Remote jobs d1547eff4228b8a5a7ec1e133f1c9b53, 467d53d1ce0c2c52bed9da7d0e916d9b, 124d0c913365c8e6dd10f66791f2d3dc
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/341
COMMIT: 912c2bda014ea73d7499dd29465adea862dbdab9
SUPERSEDES: none

## Implementado em produção
- Painel de extensão por capítulo, quantidade de palavras, comparação em gráfico e distribuição entre os três atos. Usa capítulos já salvos, mantém estado vazio verdadeiro e tabelas textuais.
- Curvas de tensão/conflito/fortuna seguem gate ACF desativado até homologação real; nenhuma nota de leitor estimada.
- Instalação JS SHA256 aa97ea41e361a5767f630c72d4588f8c7f94a3f510a1f12fe9c249aa437bd78e e CSS SHA256 02849e99578679cfd7857778e724235757f1517939b5452041593ffc3d4d8139.
- Backups privados na Hostinger: studio-analytics-20261119T155048Z.js e studio-analytics-20261119T155048Z.css. Arquivo do plugin original /estudio/ mantido com SHA PHP 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.

## Reconciliação de código
- Lixeira da Hostinger já apresentava a mensagem condicionada à limpeza automática e retornava project=0 para projetos na lixeira.
- PR #341 adiciona ao GitHub a mesma flag trashCleanupEnabled, a mensagem condicional, a indicação condicional de expiração e a referência de projeto correta, evitando regressões na promoção.
- Arquivos de CSS e algumas linhas de JS mantêm diferenças cosméticas entre GitHub e Hostinger; merge/deploy exige reconciliar todas as diferenças efetivas e preservar as branches base #337, #338 e #340.

## Verificações
- Suíte da branch #341: 97 testes PASS, incluindo VM JavaScript para as duas opções do gate da lixeira e métricas com dados simulados.
- Bun build PASS; lint PHP 8.3 PASS; QA 705/705 auditable exactly once PASS.
- Testes da instalação Hostinger: 37 PASS.
- End-to-end de contas reais/ACF e auditoria total das 188 funcionalidades permanecem pendentes, por decisão de homologar o produto após o desenvolvimento.

## Próximo agente
- Confirmar integridade runtime antes de editar PHP/JS/CSS, sempre com SHA-CAS, backup e lock. Preservar dados existentes.
- Executar as funcionalidades pendentes individualmente; manter o registro do código aprovado em PR draft até reconciliação do deploy.