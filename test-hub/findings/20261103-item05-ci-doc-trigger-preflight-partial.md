# Item 05: gatilhos documentais WordPress — patch isolado, QA preflight bloqueado
STATUS: PARTIAL
AREA: wordpress-ci-triggers
DATE: 2026-11-03T15:41:10.220Z
BASELINE: GitHub WordPress main 75cbfd5d758e3c5cfe9fa903edf963e83695c68d; GitLab peer divergente, preservado.
CHANGE: branch optimization/item05-documentation-trigger-filters-20261103; commit 73febe52496efbbb7e83f2c0d6ac4bf5b10ab99b.
SCOPE: três workflows WordPress; apenas quatro linhas de paths-ignore por arquivo para test-hub/**, docs/**, **/*.md. Preserva PHP/JS/CSS/YAML, workflows, dispatch, cron existente, jobs e writers.
STATIC_PROOF: comparação GitHub: três arquivos, cada um +4/-0; readback de blobs 6b0f6b92a0c7d80098d3db9c5da85ac1d2dedd2c, 5da824f19e8a85a1f5d57740d70bd415adf6f5c0 e 1dd45aecf6057b545b4c2049b36a803ccb6d14a2. Cenários: somente documentos SKIP; PHP ou alteração de workflow RUN; disparo manual e cron intactos.
PREFLIGHT_BLOCKER: validação equivalente da árvore GitHub completa (828 nós, 737 blobs) e dos dois manifestos idênticos encontrou 605 arquivos auditáveis, 601 atribuídos, quatro faltantes do anthares-home: assets/css/dashboard/ler-e-participar-pagina.css; assets/css/dashboard/recem-grid.css; includes/anthares-ler-participar-pagina.php; includes/class-anthares-home-recem-grid.php. Os arquivos anthares-home existentes distribuem-se entre blocos A-E, portanto não inferir dono nem editar manifestos de outros agentes.
CONSEQUENCE: PR/merge produtivo WordPress não iniciado; o commit permanece somente em branch isolada. Ausência de validação de evento documental real; item 05 permanece STAGED/PARTIAL. Reexecutar preflight quando owner do anthares-home atualizar manifestos, depois abrir PR e validar. Não rodar runner PC, não usar quota nova para teste.
LEASE_END: closed without production effects; original lease 20261103-lease-ci-documental-item05.md superseded for activity status.
SUPERSEDES: test-hub/findings/20261103-lease-ci-documental-item05.md
