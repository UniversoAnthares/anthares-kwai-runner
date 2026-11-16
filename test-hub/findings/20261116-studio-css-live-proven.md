# Anthares Studio — Item 1: correção CSS instalada e verificada
STATUS: PROVEN
AREA: anthares-studio-layout-css-only
DATE: 2026-11-16
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43968541815
JOB: 133654267702
COMMIT: 49712f348bf192584137b78e3195a56b3b5aba15
SUPERSEDES: test-hub/findings/20261116-studio-css-live-lease.md

## Objetivo
Corrigir layout exclusivo /studio, preservando /estudio e as rotinas de leitura/gravação.

## Resultado
- SSH Hostinger protegido previamente existente (variáveis GitLab/CI, nenhuma credencial exposta); job GitHub Actions SUCCESS.
- PHP body_class do novo plugin atribui anst-studio-page somente à rota /studio. PHP 8.3 lint PASS.
- CSS principal: 509 page-id-19344 -> anst-studio-page, 6 article#post-19344 substituídos por article. Modo escuro: 216 substituições da classe de página.
- Inspeção HTTP externa de ambos os CSS depois do deploy: old_page=0, old_post=0, new_scope=509 (principal) e 216 (escuro), CSS principal oculta #sidebar-primary e #page-titlebar no escopo novo.
- Plugin original PHP hash antes/depois inalterado, dados WordPress não modificados.
- Gate anst_writes_enabled=0 preservado (código), sem habilitação de escrita.
- Backup reversível com hashes em armazenamento privado Hostinger: studio-css-rollback-20261116T221710Z.
- SHA256 da versão live após o deploy:
  - estudio.css: 6fc81afb986db6c427da558fd6ed13218575ea90446cbabd0400a9f8e827de97
  - estudio-dark.css: 2917c1acbfa82098989915b7f1725b729d6345fe920a71398b19f4757563435b
  - anthares-estudio.php (clone): 042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7

## Evidência decisiva
STUDIO_CSS_DEPLOY_PROVEN=1
STUDIO_CSS_MAIN_OLD=0 DARK_OLD=0 NEW_SCOPE=PASS
LEGACY_PHP_UNCHANGED=1
BACKUP_PRIVATE_PROVEN=1
WRITE_GATE_PRESERVED=1
STUDIO_CSS_CI_SUCCESS=1
HTTP_MAIN_NEW_SCOPE=509 HTTP_DARK_NEW_SCOPE=216 HTTP_OLD=0

## Limites e próximos gates
- Cópia privada /studio: prova CSS em HTTP e código PHP, sem screenshot autenticada atualizada de desktop/mobile. A matriz G4 exige comparações visuais adicionais e permanece pendente.
- PR #313 contém a implementação versionada dos seletores, mas sua base GitHub difere do PHP G4 live. Reconciliar/rebase antes de merge para preservar o filtro de restauração já implantado.
- Workflow desta branch é operação única; não mesclar workflow operacional temporário no main.
- Manter /estudio intacto, anst_writes_enabled OFF, cache-busting via filemtime padrão.
