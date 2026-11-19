# Anthares Studio — cópia privada de histórico por capítulo
STATUS: PARTIAL
AREA: studio/revision-backup
DATE: 2026-11-19
RUN: Anthares Remote 3787d8ac3d3e3bb9a939536a1a05d967, 314f33da3e2d50eb4ead7bee8a890950, e447707b35e574eaf601b75abfe68f24, dab2be11150ab210cce51564b7523436
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/342
COMMIT: e83586c7d1887c9b307a7810881e0e61a396ccc4
SUPERSEDES: none

## Implementação
- Comando Exportar histórico JSON na área Revisão, capítulo selecionado.
- API privada GET chapters/{id}/versions e consultas individuais das versões. Dados: projeto, capítulo atual (Delta) e até doze versões preservadas, com datas e títulos.
- API aplica checagens de usuário e projeto. O cliente aborta caso uma versão seja inválida ou indisponível; zero escritas em banco no fluxo de exportação.
- O arquivo exportado não possui importador automático. Restauração dentro do Studio já existe; aceitação do pacote externo permanece pendente.

## Evidência
- Hostinger JavaScript vivo SHA256 7c43587126d6bb90b5b60859e50806b5fa08ddea0a515344e1440848c6209360; código da branch correspondente byte a byte.
- Backup privado Hostinger studio-history-prev-20261119T163945Z.js (modo 0600).
- Branch 99 testes PASS; inclui execução Bun VM para sucesso, histórico vazio e falha de consulta sem download parcial.
- Bun build PASS, inventário QA exactly once 705/705 PASS. Plugin instalado: 37 testes PASS.
- Plugin legado /estudio/ SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf preservado.

## Limitações
- Aceite autenticado em navegador real, importação da cópia externa, restauração end-to-end e backup integral de todo o projeto ainda não homologados.
- Branch depende de #341 e PRs ancestrais em rascunho; reconciliar antes de merge/deploy integral.