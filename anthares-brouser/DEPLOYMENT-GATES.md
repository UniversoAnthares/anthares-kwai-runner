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
