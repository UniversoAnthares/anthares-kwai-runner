# Lease temporário — workflow de preflight QA antes do merge
owner: chatgpt
job: forgejo-qa-20261024-0924
início_utc: 2026-10-24T13:40:28Z
expira_utc: 2026-10-24T14:10:28Z
baseline: UniversoAnthares/anthares-wordpress@2988a491238a23677f7d0964d9eda25b2580d041
files: .github/workflows/qa-manifest-premerge.yml; qa/anthares-qa-sections.json; anthares-pix-sales/qa-sections.json
scope: validar exactly_once em cada PR; somente preflight leve, sem QA completo, credenciais, publicação ou execução na produção.
critérios: código do workflow aprovado em PR, 594/594 arquivo atribuídos, testes práticos, preservar alterações dos outros agentes.
