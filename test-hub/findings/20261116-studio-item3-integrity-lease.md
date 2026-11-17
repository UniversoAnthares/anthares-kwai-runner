# Lease — Item 3: auditoria exaustiva dos 71 pares Estúdio antigo/novo
STATUS: RUNNING
AREA: studio-g3-71-records-readonly-integrity
DATE: 2026-11-16
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g3-item3-integrity-20261116
BASELINE_PROVEN: WordPress 7.1.4, plugin anthares-studio 0.7.8-staging, /studio private ID 21383, anst_writes_enabled=0 e anst_trash_cleanup_enabled=0 (item 2: run 43978826585). Hash do plugin novo 042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7; CSS 6fc81afb986db6c427da558fd6ed13218575ea90446cbabd0400a9f8e827de97 e dark 2917c1acbfa82098989915b7f1725b729d6345fe920a71398b19f4757563435b; original 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.
FAILED_AVOIDED: sem execução de migrador --apply ou SQL write; sem interferência em gravações; usar ponte SSH protegida via CI já validada, sem chave pessoal Windows SYSTEM.
SUCCESS_SIGNAL: comparação 71/71 de posts e 40/31 por status; mapeamento 1:1 com checksums de origem, zero duplicações, 100% metadados e referências remapeadas, 7/7 Delta brutos/JSON iguais, donos e datas coerentes, zero órfãos, preferências de mural coerentes, fingerprint origem estável, nenhuma escrita no legado/destino.
FAILURE_SIGNAL: divergência de valores/hash/Delta/owner/status, órfãos, referência interprojetos, contagem distinta, flags ativas ou rede indisponível. Falhas devem ser registradas com contagens/códigos, jamais com conteúdo privado.
TEST_VALIDITY: consulta SQL apenas SELECT no WordPress real via PHP CLI 8.3. Ler origem/destino, sem alterar opções, links, posts, usuários, arquivo, cache, WP-CLI migration ou CDN.
SCOPE: test-hub finding e script de auditoria unicamente em branch isolada; nenhum arquivo de WordPress alterado.
ROLLBACK: não aplicável à auditoria read-only; nenhum dado deve ser criado.
SUPERSEDES: test-hub/findings/20261116-studio-g3-integrity-rest-readonly-verified.md (nova leitura de integridade, sem substituir histórico).
