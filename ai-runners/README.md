# AI runners

Executores locais de desenvolvimento para serviços web de IA usando perfis Chrome dedicados e isolados.

## Claude

`claude_hidden_runner.py` é o caminho PROVEN.

- Perfil dedicado: `C:\Users\Lucas\AntharesWork\claude-hidden-desktop-profile`
- Chrome headful em desktop virtual Win32 oculto
- Controle via CDP/Playwright
- Não reutiliza, lê nem copia cookies do Chrome normal
- Fecha a árvore do Chrome isolado ao terminar
- Saída JSON estruturada
- `--prompt`, `--prompt-file`, `--expect`, `--self-test`

Exemplo:

```powershell
py -3.13 claude_hidden_runner.py --prompt "Responda em uma frase: o que é uma metáfora?"
```

Self-test:

```powershell
py -3.13 claude_hidden_runner.py --self-test
```

O self-test executa três tarefas independentes e exige sucesso em todas.

## Regra de segurança

Não apontar estes runners para o perfil Chrome normal do usuário. Cada provedor deve usar perfil dedicado. Se uma sessão expirar, o bootstrap de autenticação deve usar o fluxo oficial do provedor; não copiar cookies/sessões do navegador normal.
