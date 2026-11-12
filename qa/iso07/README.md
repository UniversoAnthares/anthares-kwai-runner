# CORTES-ISO-07 — verificação de admissão (QA, leitura)

Escopo fixo: TikTok `lucasrosalem4`. Este pacote funciona separado dos publicadores: nunca acessa credenciais, banco, navegador ou API social, e jamais inicia publicações. Inspeciona contratos de dois workflows e metadados fornecidos por leitura autorizada.

Uso em checkout atualizado da **branch de QA**:

```bash
python3 -m unittest qa.iso07.test_preflight -v
python3 -m qa.iso07.preflight --cloud .github/workflows/cortes-tiktok-lucasrosalem4-cloud-publisher.yml --fallback .github/workflows/cortes-tiktok-lucasrosalem4-windows-fallback.yml
```

Resultado `BLOCKED` enumera todos os impedimentos; `REVIEW_REQUIRED` significa apenas que os dados declarados passaram nas verificações sintáticas. O campo `authorized_to_publish` permanece **false**. Evidência real precisa vir diretamente de GitHub/Neon/TikTok, com duas identidades operacionais de privilégio mínimo, negativas recíprocas, media/conta identificadas, writer único, rollback e recibo público conferido. Só o fluxo de aprovação e publicação já homologado pode executar um canário.

Fotografia Neon (leitura real em 25/10/2026): tabelas `cortes_publications` e `cortes_tiktok_lucasrosalem4_publications` com RLS=false, FORCE=false e policies=0; role de consulta `neondb_owner` com BYPASSRLS. Essa fotografia é contexto, não seed aplicada em produção.

Toda implementação de IAM/provisionamento deve obedecer à revisão autorizada da PR #1332. Impedimentos anteriores de aprovação/provisão e de alteração de roles permanecem; não repetir a ação recusada por outro canal. Código QA desta branch não é alteração de produção nem aceite do item 13.
