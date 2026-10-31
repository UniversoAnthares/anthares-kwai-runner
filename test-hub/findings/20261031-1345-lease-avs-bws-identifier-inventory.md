# AVS — lease para inventário de identificadores no Anthares Secrets
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-31
RUN: pending
JOB: pending
COMMIT: 7a44b8c64f83fd4498d81c18d3d773424a844467
SUPERSEDES: none

OWNER: ChatGPT AVS item 4
SCOPE: Somente branch feat/avs-bws-identifier-inventory-20261031, workflow anthares-secrets-inventory.yml, consulta BWS somente-leitura.
EXPIRES_UTC: 2026-10-31T14:14:00Z

## BASELINE_PROVEN
Run 40154415901 em 2026-10-25 concluiu o workflow de inventário BWS na conta de máquina Anthares Automation, SDK oficial pinado no sm-action v2. GitHub tem BWS_ACCESS_TOKEN existente; não coletar valores. Repositório peer GitLab possui mesmo blob d0442e538154109f81f412da07fb6dee2636fb6a para o workflow. Branch de teste deriva do main HEAD 7a44b8c64f83fd4498d81c18d3d773424a844467.

## FAILED_AVOIDED
Finding 20261020-cortes-bws-oauth-inventory-partial.md: SDK instalado isoladamente 1.0.0 falhou na autenticação; reutilizar exatamente o workflow pinado que passou, alterando somente a impressão de status de nomes. Não transferir nem divulgar valores, não abrir credenciais em navegador e não modificar produção/main. A recusa de segurança à transferência por ferramenta remota é vinculante e não será contornada.

## SUCCESS_SIGNAL
Execução manual de workflow em branch isolada termina com BWS_INVENTORY_METADATA_AUDITED=PASS e imprime exclusivamente BWS_AVS_BLOB_READ_TOKEN_PRESENT, BWS_AVS_BLOB_HOMOLOGATION_TOKEN_PRESENT e BWS_AVS_SECRET_PROJECT_MATCH (YES/NO/AMBIGUOUS), sem valores nem UUIDs de segredos.

## FAILURE_SIGNAL
Workflow falha antes do inventário ou nenhum acesso à listagem de metadata BWS; classificar escopo da conta de máquina como desconhecido e preservar segredos existentes.

## TEST_VALIDITY
Run deve usar branch isolada com mesmo código SDK pinado, BWS_ACCESS_TOKEN autorizado e saída positiva de login/listagem. O resultado de nomes ausentes vale somente para os itens VISÍVEIS à conta de máquina; não prova inexistência global no Bitwarden. Uma conclusão verde sem as linhas decisivas é PARTIAL.
