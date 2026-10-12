# Anthares-brouser

Navegador remoto persistente para autenticação manual e reutilização controlada de sessão do ecossistema Anthares.

Objetivo imediato: substituir o navegador remoto de terceiros por um container próprio com Chromium, Xvfb, x11vnc e noVNC. O Chromium usa `/data/chrome-profile` como `user-data-dir`, portanto cookies, localStorage, IndexedDB e demais dados do perfil sobrevivem a reinicializações quando `/data` está em volume persistente.

## Portas

- `6080`: interface noVNC para login manual.
- `8080`: API de saúde/status.

## Variáveis obrigatórias

- `VNC_PASSWORD`: senha da sessão visual remota.
- `CONTROL_TOKEN`: token Bearer para a API de controle.

## Execução

```bash
docker build -t anthares-brouser ./anthares-brouser
docker run --rm -p 6080:6080 -p 8080:8080 \
  -e VNC_PASSWORD='...' -e CONTROL_TOKEN='...' \
  -v anthares_brouser_data:/data anthares-brouser
```

Abra `http://HOST:6080/vnc.html`, conecte usando `VNC_PASSWORD` e faça o login manual no Kwai. Não grave credenciais no repositório. A sessão fica no volume persistente, não no Git.

## Segurança

O projeto não envia cookies ou credenciais para logs. Não publique `/data/chrome-profile` nem snapshots de sessão. Em produção, o endpoint visual deve ficar atrás do TLS da plataforma e ser aberto apenas durante autenticação manual.

## QA

O workflow `Anthares-brouser - 40 Persistence QA` testa, em 40 jobs paralelos, se um perfil real do Chromium mantém estado após encerramento e relançamento do navegador. Esses testes validam a camada de persistência; não afirmam autenticação no Kwai.
