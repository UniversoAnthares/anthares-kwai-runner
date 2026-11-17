# Studio G4 — risco de perda de texto na falha de importação Quill

STATUS: PARTIAL
DATE: 2026-11-17
AREA: anthares-studio/g4/editor-load-data-safety
JOB: studio-g4-editor-error-static-review-20261117
COMMIT: cc9f0d07cb7e4d2338d4da9b640c901b88ffe74c
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/316
SUPERSEDES: none

## Código efetivamente observado
Em `anthares-studio/assets/estudio.js`, `setupEditor()` chama `editor.setContents(c.delta,'silent')` e, sob exceção, executa `editor.setText('','silent')` sem notificação. A função ainda informa `aest-save-status='Salvo'`. `editorDelta()` retorna a cópia do editor e `saveChapter()` envia essa cópia ao REST quando há edição posterior.

## Risco
Se o Delta existente produzir exceção na importação Quill, a interface mostrará o documento vazio sem aviso. Uma edição subsequente poderá salvar essa versão em lugar do Delta original. O cenário é plausível pela sequência explícita de código e precisa de teste com exceção simulada; sem evidência de perda real ocorrida.

## Próxima ação sob lease de G4
A frente proprietária G4 deve impedir a edição/gravação após falha de setContents, preservar o objeto c.delta intocado e exibir erro de recuperação. Regressão obrigatória: setContents lança; nenhum POST ocorre; status Salvo não aparece; restauração só sob controle explícito.
O comentário foi adicionado à PR #316. Esta revisão não alterou código, banco, opções, editor nem plugin original.
