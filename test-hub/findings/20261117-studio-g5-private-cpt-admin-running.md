# Studio G5 — CPTs privados administráveis com capacidade administrativa

STATUS: RUNNING
AREA: anthares-studio/g5/private-cpt-admin
DATE: 2026-11-17
JOB: studio-g5-private-cpt-admin-20261117
OWNER: ChatGPT / OBSERVATORIO IPB
SOURCE: UniversoAnthares/anthares-wordpress PR #316, HEAD 1dfdf570f63eea91f7a30bb481880af8aeff8cec
PEER: GitLab feat/studio-g5-private-cpt-admin-20261117 = 404 (sem branch correspondente).
BASELINE_PROVEN: G0-G3 copiados; G1 backup+restore isolado; /studio plugin 0.7.8 ativo, ACF=OFF, 71/71 registros; plugin legado SHA-256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.
FAILED_AVOIDED: nenhum teste de escrita em produção ou automação de navegador após bloqueios anteriores.
SCOPE: branch exclusiva derivada de HEAD fix/studio-g4-admin-write-guard-20261117; arquivos anthares-studio/anthares-estudio.php e anthares-studio/tests/test_acf_contract.py apenas. Corrigir exclusivamente show_ui e capacidades administrativas dos CPTs anst_*, mantendo public=false, publicly_queryable=false, show_in_rest=false e nenhuma alteração no legado.
SUCCESS_SIGNAL: lint PHP e testes de contrato; verificação CPT em WordPress isolado; zero exposição pública.
FAILURE_SIGNAL: qualquer acesso não-admin aos CPTs privados, falha de lint, conflitos com branch G4.
TEST_VALIDITY: somente alterações de código em branch de rascunho. Produção, flags, dados e página /studio inalterados.
COORDINATION: PR #316 continua RUNNING para G4 e PR #315 para ACF; não fazer merge nem deploy deste patch até homologação G4 e reconciliação de ambos.
ROLLBACK: descartar branch/PR desta correção, sem rollback produtivo.
