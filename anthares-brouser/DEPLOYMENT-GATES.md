# Anthares-browser — critérios de conclusão e implantação dupla

Status: PENDENTE DE VALIDAÇÃO OPERACIONAL. Este documento não comprova que a conta Kwai esteja autenticada.

## Regra de isolamento (obrigatória)
Executar Chromium somente em container remoto com Xvfb próprio, DISPLAY próprio e CHROME_PROFILE_DIR dedicado. Nunca anexar a sessões Chrome/Edge existentes, nunca usar mouse/teclado/foco do host e nunca fazer fallback para desktop local. Acesso noVNC somente quando o proprietário abrir voluntariamente a interface remota. Cada instância concorrente deve usar volume e perfil distintos; bloquear compartilhamento simultâneo do perfil.

## Portões de aceitação
- [ ] QA de container: build, boot, health, CDP somente loopback, autenticação da API, teste de navegação e captura.
- [ ] QA de isolamento: nenhum acesso a abas/perfis existentes, nenhum evento de mouse/teclado/foco no computador do usuário.
- [ ] Ambiente remoto gratuito, sem cartão ou billing, com armazenamento persistente real e acesso protegido ao noVNC.
- [ ] Autenticação manual Kwai @lucasrosalem pelo proprietário (somente quando interface segura estiver pronta).
- [ ] Reinicialização total da instância e comprovação de sessão autenticada sem nova intervenção.
- [ ] Upload de vídeo de teste, deduplicação por trecho, confirmação inequívoca de publicação no perfil e registro de evidências sem dados sensíveis.
- [ ] Tratamento de falhas, lease por sessão, limites, recuperação e verificação de ausência de vazamento de credenciais.
- [ ] Implantação A: avaliar Render apenas se plano gratuito e persistência efetiva forem comprovados.
- [ ] Implantação B: infraestrutura Anthares própria, paralela e independente do Render; projeto ainda em desenvolvimento. Deve executar o mesmo container, oferecer HTTPS, armazenamento persistente, supervisão/restart, autenticação, observabilidade e recuperação. **Não considerar a redundância concluída até executar e provar o fluxo de reinício e login nos dois ambientes.**

## Limites conhecidos
GitHub Actions fornece testes efêmeros e não substitui um serviço persistente. Volume Docker declarado no Dockerfile não garante persistência em hospedagem que descarte o filesystem. Não abrir a porta CDP 9222 publicamente. Não publicar noVNC 6080 sem autenticação e TLS. Não alegar login ou publicação a partir de HTTP 200, cookies ou inicialização do Chromium.

## Intervenção exclusiva do usuário
Apenas quando existir URL HTTPS privada da instância persistente com noVNC protegido: abrir a interface, autenticar Kwai pelo método exigido (QR/OTP/confirmação no celular) e avisar que concluiu. Nunca enviar senhas ou códigos no chat.


## Administração remota — atualização 2026-10-12
- Anthares-remote é o único plano de administração remota adotado. Não utilizar MeshCentral, Remote Desktop Commander ou AI Commander.
- Serviços Render verificados: anthares-remote-control, anthares-remote-mcp e anthares-remote-mcp-v2; deploys recentes em estado `live`. Isso **não** prova capacidade de executar Chromium persistente nem constitui autorização para expor o noVNC.
- Integração do navegador com Anthares-remote deve preservar `CONTROL_TOKEN`, acesso noVNC somente por túnel/proxy HTTPS autenticado, perfis isolados e registro de evidência sem segredos.
- Serviço de QA `anthares-browser-qa-render` criado no Render (plano free). Deploy confirmado `live`, `/ready` retornou Chromium/CDP operacionais, `/novnc/login` respondeu e `/novnc/vnc.html` negou acesso anônimo com HTTP 401. **Não utilizar para login real enquanto não houver persistência comprovada**.
- GitLab CI: 20 verificações paralelas e teste funcional da API concluídos com sucesso na execução 2940648485. Não confundir testes de contrato com login ou publicação real.

## Evidência operacional mais recente
- URL de QA: https://anthares-browser-qa-render.onrender.com/novnc/login
- A implementação de gateway noVNC está presente no repositório, com testes próprios. Verificações externas comprovaram formulário e negação de conteúdo sem sessão, mas **não** comprovaram handshake WebSocket autenticado de ponta a ponta.
- O campo `durable_volume_verified` permanece `false`; a sessão Kwai não deve ser estabelecida neste ambiente efêmero.
- Há deploys concorrentes de outros agentes: consultar o commit implantado antes de atribuir qualquer resultado à versão mais recente do código.

## Plano de recuperação do perfil — decisão técnica pendente
- Render free não fornece volume persistente ao serviço de QA. Não confundir `VOLUME ["/data"]` do Dockerfile com armazenamento durável gerenciado.
- Não usar banco de dados compartilhado de Anthares-remote como armazenamento de cookies/sessões. Banco gratuito com expiração informada também não atende persistência de longo prazo.
- Solução candidata: arquivo de perfil Chromium criptografado com chave exclusiva e versionamento em repositório **privado** ou armazenamento remoto gratuito. Exige implementar restauração antes do Chromium, backup consistente após parada do Chromium, verificação de integridade, recuperação e rotação de chaves. Nunca enviar cookies em claro a GitHub público ou logs.
- Critério de aceite: perfil sintético sobrevive a reinicialização e substituição da instância; restauração verificável por hash, sem expor credenciais. Só então habilitar login Kwai manual.
