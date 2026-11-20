# Anthares Studio — item 1 instalado e verificado na Hostinger
Data: 2026-11-20, execução 15:45–15:47 UTC. Estado: DEPLOYED_VERIFIED.

## Requisito concluído
- Referência: `ANTHARES_STUDIO_PENDENCIAS_ATIVAS_RENUMERADAS_2026-11-20.md`, item 1, briefing `site-anthares.docx`.
- Marcadores por parágrafo, painel lateral responsivo, respostas encadeadas, moderação de comentários pendentes e aprovados, notificações e vínculo a versão imutável.
- Código incorporado ao GitHub em `UniversoAnthares/anthares-wordpress#385`, merge `34f73c11b0cddf45fb8428bc078b1b60332e4279`.
- Testes prévios no PR: 130/130 Python; 22 verificações REST com três contas existentes e transação revertida; teste sintético do navegador 390, 768, 1440px.
  
## Implantação efetiva
- Conexão: ARA Cloudflare autenticado, túnel SSH configurado para Hostinger. Sem novas credenciais.
- ZIP fonte: `/home/u566597497/domains/anthares.us/public_html/wp-content/uploads/anthares-studio-item1-comentarios-20261120.zip`, SHA-256 `7796efad7e9e3590bb2c2d977de1bc3b6bdc548ebb401e5fbe1ae476adc20fbc`.
- Instalados no `wp-content/plugins/anthares-studio/`:
  - `assets/studio-g7-comments.js` SHA-256 `17cd7a9b7edb5f1af006010d469fd9224307b83ae0ca68217a1468ef345af4dc`.
  - `assets/studio-g6-navigation.css` SHA-256 `7c12296834cd8fc7de374dc8bd8e354099cac8c334017e5d3f63266efa676035`.
  - `includes/domain/class-anst-g7-comments.php` SHA-256 `f9eccef7b819a263b8ecbbc7da7e426db2e26f7a39cfb112c9ef0cff0357338b`.
- Backup anterior, privado, para eventual restauração: `/home/u566597497/.anthares-studio-private-backups/item1-comments-before-20261120.99pVhX`.
- O primeiro comando foi interrompido ANTES de tocar os arquivos por problema de process substitution `/dev/fd/62`, corrigido no mesmo caminho de execução. A segunda tentativa terminou `INSTALLATION=SUCCESS`, três hashes iguais ao ZIP.
- PHP lint do arquivo instalado: PASS; `python3 -m unittest discover -s tests -q` no plugin de produção: **51/51 PASS**.
- JavaScript e CSS servidos em `https://anthares.us/wp-content/plugins/anthares-studio/assets/` confirmados com hash idêntico ao arquivo local (consulta HTTP com parâmetro de cache).
- `https://anthares.us/studio/` HTTP 200; `https://anthares.us/estudio/` HTTP 200; plugin ativo. **22 projetos originais** da conta de homologação preservados.
- Foram preservados dados existentes e a versão legada, sem alteração de post/comment real ou cadastros.

## Evidência e limitações
- Item 1 concluído como **implementado, implantado e validado tecnicamente**.
- A publicação pública e testes visuais com uma edição realmente publicada continuam sujeitos a conteúdo e direitos autorizados (outros itens, sobretudo 17 e 21); o teste de interface foi sintético, e o teste REST transacional abrangeu respostas e moderação entre usuários reais preexistentes.
- Não presumir que os itens 2–22 foram concluídos. A atualização não altera o escopo comercial excluído anteriormente.
