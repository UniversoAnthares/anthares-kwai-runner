# Coordenação — restabelecer ACF OFF no piloto privado /studio
STATUS: RUNNING
AREA: wordpress/studio/g5-live-safety
DATE: 2026-11-17
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-acf-live-runtime-remediation-20261117
SCOPE: exclusivamente opção WordPress `anst_acf_runtime_enabled` da instalação Hostinger, de 1 para 0, após preflight e verificação de conflito.
EVIDENCE: `anst_writes_enabled=0`, `anst_acf_runtime_enabled=1`, função `anst_acf_runtime_enabled()` respondeu ACF_ON em WP-CLI PHP8.3. Plugin novo em página 21383 private; plugin antigo hash SHA-256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.
RATIONALE: G4 não homologado e PRs G5/G6/G7 em draft, logo ativação ACF em produção conflita com autorização dupla contratada. O clone preserva metadados originais para leitura com ACF OFF.
PRECONDITIONS: verificar ausência de mutação concorrente, obter estado original e backup reversível de valor da opção, verificar `anst_writes_enabled=0`.
ALLOW: alterar apenas `anst_acf_runtime_enabled` para 0 e verificar resultado; restauração condicionada a nova aprovação G4/G5, sem automatismo.
BLOCK: nenhuma mudança em /estudio, arquivos PHP, ACF Local JSON, CPTs, dados dos autores, páginas, publicação ou `anst_writes_enabled`.
ROLLBACK: `wp option update anst_acf_runtime_enabled 1` somente se a reversão for autorizada após análise; valor anterior registrado 1.
