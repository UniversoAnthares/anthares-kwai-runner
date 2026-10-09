# Kwai: Chrome remoto interativo e privado (sem Android)

STATUS: PREPARED / NOT YET AUTHENTICATED
LAST VERIFIED: 2026-10-09

## Iniciar (apenas duas ações)

1. Abra **[Criar Codespace remoto](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=1406232047)**. Confirme **Create codespace** com a configuração do repositório. O GitHub executa a instalação na nuvem; seu computador é somente o visualizador.
2. Quando o Codespace terminar de preparar, abra **PORTS**. Na porta **6080**, confirme **Visibility: Private** e clique no link para abrir o **Chrome remoto** (noVNC). Entre na sua conta do Kwai no navegador exibido. Para verificar a identidade, abra a porta **8765** (também **Private**) e clique **Verificar identidade da conta**.

Não copie códigos, senhas, cookies ou tokens para o chat, Issues, Actions, commits ou artefatos. Não torne as portas públicas. Os links individuais das portas só existem depois que o Codespace for criado.

## Arquitetura

- O GitHub Codespaces executa Debian/Chromium, Xvfb, Openbox, x11vnc e noVNC **inteiramente na nuvem**.
- A porta 6080 é o desktop HTML5; a 8765 é o inspetor de identidade. Ambas usam encaminhamento **privado autenticado pelo GitHub**; a configuração padrão do Codespaces é Private. A porta VNC 5900 e o endpoint CDP 9222 ficam em loopback dentro do Codespace e **não são encaminhados**.
- O perfil do navegador fica em `$HOME/.kwai-remote-private/chrome-profile`, fora do repositório. Ele contém dados sensíveis após o login e **não é exportado automaticamente**.
- O inspetor abre uma aba de perfil dentro do mesmo Chrome, observa indicadores de propriedade e menu da conta e retorna **apenas booleanos**. Ausência do botão de login não é suficiente para identidade comprovada. Sem indicadores completos, o resultado é `identity_verified=false`.
- O inspetor não coleta senhas, cookies, tokens ou o conteúdo integral da página; não grava sessões nem as envia para Actions.
- O Codespace pode ter cota gratuita em contas pessoais, mas a disponibilidade e os limites devem ser conferidos na própria conta. Não habilite cobrança para este teste.

## Encerramento seguro

No terminal **do Codespace**, executar `bash .devcontainer/kwai-clear-session.sh` para encerrar o navegador e apagar o perfil local. Não executar no computador pessoal. Para reabrir, `bash .devcontainer/kwai-start.sh`.

## Limites e próximos critérios de aceite

Os testes do workflow `Kwai Codespaces Browser Security QA` verificam sintaxe, configuração privada, falha fechada e a interface local. Eles **não provam** que um Codespace foi criado, que a conta Kwai foi autenticada, nem que a identidade foi verificada.

Para concluir a autenticação, é preciso observar `identity_verified=true` com evidência do controle de edição do perfil **e** da identidade no menu da conta. A verificação de servidor independente e a transferência criptografada para runners GitHub Actions são trabalhos posteriores; o inspetor mantém `persistence_permitted=false` mesmo após prova visual.

O Chrome browser-only de Actions #37936848163, o teste sintético entre runners #37935784822 e o QA de cache #37936417696 permanecem preservados. Não usar Android virtual, API Kuaishou, túnel público nem PC como executor.
