# CORTES — worker Neon restrito e recuperação de armazenamento do runner
STATUS: PARTIAL
AREA: architecture / quota-failover / media
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40507427035
JOB: 122201417144
COMMIT: 0594f6aa122ef6708e1347744f0af499890f0aa4
SUPERSEDES: none

## Mudança realmente integrada
- Clipper PR #216: entrada `secure_drain_once` no main; autenticação PostgreSQL independente e privilégio mínimo obrigatórios antes de retirar qualquer entrega da outbox. Não ativado automaticamente em processos produtivos por falta de credencial viável.
- Neon `cortes_quota_worker_login`: sem superusuário, sem membership administrativo, sem senha habilitada após a rejeição de propagação segura de segredo à Vercel; proibido iniciar consumer com owner/admin.
- Clipper PR #215 permanece integrado: política de seleção de scratch alternativo, mas o caminho configurado em F: ainda não se mostrou gravável no dispositivo.
- No Windows ARA, F: reportava 43,5 GiB livres mas `New-Item` falhou com `System.IO.IOException` (dispositivo inexistente). `Update-HostStorageCache` foi executado, sem recuperar diretório verificável. Não foi efetuado remount, formatação, deleção ou alteração de partições.
- D: inicialmente 6,4 GiB livres; depois passou a 11,1 GiB. A alteração de espaço ocorreu enquanto outras execuções estavam ativas; não atribuir a causa a esta intervenção. Arquivos Photoshop Temp foram preservados; tentativa de compressão de um arquivo resultou em 0 arquivos compactados.
- Run CORTES diario #40507427035 em curso; origem selecionada, render long iniciado. Não disparar concorrente enquanto ativo.

## Bloqueios que permanecem
1. Implementar/implantar consumer externo com autenticação realmente restrita; segredo entre Neon e Vercel foi bloqueado pelas configurações de segurança, manter senha desativada até provisionamento autorizado.
2. Homologar estado de F: com controlador de volume que confirme escrita real; números de espaço livre sem criação de diretório não autorizam uso.
3. Confirmar conclusão do render longo atual e seu ledger antes de qualquer reprocessamento de fonte.
4. Limite do plano Neon impede novo snapshot independente; preservar backup existente. Falta terceiro destino comprovado para masters.

## Critérios
Nenhum master pessoal, perfil, publicação ou arquivo de usuário foi excluído. Nenhum job produtivo foi cancelado. Evidência em logs nativos e PRs acima.
