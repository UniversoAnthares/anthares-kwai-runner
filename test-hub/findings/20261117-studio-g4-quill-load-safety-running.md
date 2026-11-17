# G4 — isolar proteção de importação Quill que falha

STATUS: RUNNING
AREA: anthares-studio/g4/quill-load-safety
DATE: 2026-11-17
OWNER: ChatGPT / OBSERVATORIO IPB
JOB: studio-g4-quill-load-safety-20261117
SOURCE: UniversoAnthares/anthares-wordpress PR #316 HEAD cc9f0d07cb7e4d2338d4da9b640c901b88ffe74c
PEER: GitLab branch fix/studio-g4-quill-load-safety-20261117 404; sem espelho.
BASELINE_PROVEN: G4 isolated PR #316 code suite 66/66 PASS, PHP lint 4/4 PASS, manifest 665/665 PASS; código observado: setupEditor() catch setContents exception chama setText vazio e mostra status Salvo, caminho posterior pode fazer POST por saveChapter().
FAILED_AVOIDED: nenhum teste de escrita REST em produção, nenhuma mudança em branch G4 com lease de outro agente, nenhuma tentativa de acesso a aba autenticada previamente negado.
SCOPE: branch independente da PR #316, alterar apenas assets/estudio.js e tests/test_g6_fixed_navigation.py; impedir salvar conteúdo vazio após falha de importação Quill, preservar Delta do objeto, mostrar aviso, modo somente-leitura e bloquear ações.
SUCCESS_SIGNAL: teste regressivo de código passa e guarda explícita no saveChapter antes de api(); JS syntax Node PASS, unittest suite isolada PASS, PHP/manifest QA PASS.
FAILURE_SIGNAL: teste falha, atualização sem guard, criação de arquivos novos ou mudança em /estudio.
TEST_VALIDITY: contrato de código/mocks isolados, não valida editor real autenticado. Sem merge/deploy até gates G4/QA.
ROLLBACK: descartar branch/PR; nenhuma mutação produtiva.
