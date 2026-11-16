# Item 2 — Auditoria read-only da instalação e bloqueios do Anthares Studio
STATUS: RUNNING
AREA: anthares-studio-item2-live-version-and-writegate
DATE: 2026-11-16
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: audit-studio-item2-20261116
BASELINE_PROVEN: item 1 implantado em run 43968541815; PHP clone sha256 042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7; CSS principal 6fc81afb986db6c427da558fd6ed13218575ea90446cbabd0400a9f8e827de97; escuro 2917c1acbfa82098989915b7f1725b729d6345fe920a71398b19f4757563435b; original PHP 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.
FAILED_AVOIDED: acesso do serviço SYSTEM à chave pessoal foi rejeitado, não repetir; reaproveitar ponte SSH protegida de CI de execução anterior e hostkey pinada.
SUCCESS_SIGNAL: plugin correto ativo, versão identificada, hashes confirmados e mapeados a PRs, página privada, escrita e limpeza desativadas, GET permitido para usuário autorizado e POST bloqueado em função permission_cb sem salvar, original intacto.
FAILURE_SIGNAL: hash inesperado, plugin inativo, opção de escrita ativada, prova de permissão divergente, página pública, falha SSH/CLI.
TEST_VALIDITY: acesso SSH read-only com WordPress CLI. Nenhum endpoint de escrita, nenhum wp option update, nenhuma edição do site; testar permission_callback apenas em memória PHP.
BLOCK: não reimplantar CSS, não mudar o plugin original, não criar dados, não ativar gravação, não mesclar PRs.
