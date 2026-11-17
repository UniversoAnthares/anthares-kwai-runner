# Studio G5 — auditoria dos grupos ACF e do mapa de campos

STATUS: PROVEN
AREA: anthares-studio/g5/acf-schema-readonly
DATE: 2026-11-17
JOB: studio-g5-acf-schema-audit-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/317
COMMIT: 81484ac4e0a284f8a3d45afca19abca595251b70
SUPERSEDES: none

## Auditoria
Foram lidos, do GitHub, os 12 grupos JSON do Studio e o manifesto de migração ACF, na branch feat/studio-g5-private-cpt-admin-20261117. Todas as verificações seguintes PASS:
- 12 grupos válidos e OFF (active=false, show_in_rest=0).
- 40 campos, com 40 chaves field_anst* distintas e 40 nomes studio_* distintos.
- 52 entradas no mapa e 40 campos declarados no manifesto.
- 24 mapeamentos de projeto, 6 de nota, 11 de capítulo e 9 de cartão; duas entradas adicionais de user/options completam 52.
- Toda entrada aponta para field key e field name existentes e concordantes.
- Todos os post_object apontam exclusivamente para anst_projeto e usam retorno id.
- Zero problemas encontrados nesta auditoria de schema estático.

## Limites
O resultado cobre somente a estrutura e os vínculos formais do ACF. Ativação do ACF permanece OFF; migração de dados, roundtrip no WordPress real e exibição das telas administrativas dependem dos gates G4/G5. Sem writes produtivos.
