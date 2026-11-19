# Anthares Studio — código principal reconciliado com Hostinger
STATUS: PROVEN
AREA: studio/source-release
DATE: 2026-11-19
RUN: ARA jobs e2767bd79067669de4b228eeb0f4d19d, d2762c80021b2b051dd936b5a09ec8ef, ca7b17c5e501d7602b1457471e1a76b5, a234770056a0e44032ad65c40e7469d5, aee7e01c2f8d9e532444b06fab7e7984, 143817a33b5d63e8e26f3b82ce2e1206
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/344
COMMIT: 4f7a01c9a80ab8cde980f1b08f8d30c87003f5e8
SUPERSEDES: none

## Escopo e integridade
- PR #344 MERGED em main por squash de uma branch originada diretamente do main 552f45374c1590096999c9e9b5e17aa097ce050f.
- 85 arquivos alterados, todos dentro do plugin anthares-studio, dois manifestos QA e cinco workflows relacionados. Alteração independente de anthares-fields foi excluída; produção ainda contém os tipos existentes nessa extensão.
- Comparação SHA256 dos 59 arquivos executáveis .php/.js/.css/.json entre o main pós-merge e /wp-content/plugins/anthares-studio/ real: 59/59 idênticos, sem exceções.
- Plugin legado /estudio/ SHA256 PHP 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf, intacto.
- A tentativa de alinhar quebras de linha no CSS da Hostinger foi revertida quando falhou um teste do plugin instalado; os quatro arquivos de produção foram conferidos nos hashes anteriores, e o código GitHub foi reconciliado com a versão viva.

## Provas de QA
- Branch clean e main pós-merge: 99/99 testes Python/Bun PASS (teste de import/export, privacidade estática e contratos); Bun build PASS; PHP 8.3 lint PASS; orquestrador PHP PASS; manifest-coverage-preflight 705/705 exactly-once PASS.
- Testes na instalação Hostinger: 37/37 PASS; wrapper temporário não criou dados de usuário nem alterou o legacy.
- Confirmação de segurança de workflows da alteração: todos os 85 caminhos são ignorados pelos três workflows `runs-on: self-hosted Windows` e pelo deploy seletivo Vercel para evento `push/main`. GitHub Actions listou zero runs atrelados ao merge no momento da inspeção.
- Aviso menor em `git diff --cached --check` antes do merge: 3 linhas com espaço final/blank EOF já presentes nos arquivos da Hostinger. Preservadas para respeitar o hash e contratos de teste publicados. Sem impacto sintático.

## Limites
- Este resultado fecha o item 19 (sincronização e consolidação executável Hostinger/main) do backlog de 20 itens.
- A homologação com duas contas reais, gate ACF, auditoria E2E das 188 funções e restauração integral permanecem tarefas próprias. Não extrapolar provas estáticas para cobertura de E2E.
- Branch do Test Hub rastreia esta execução e seu lease deve ser encerrado no mesmo PR.