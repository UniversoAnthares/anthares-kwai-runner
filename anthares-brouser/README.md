# Anthares-browser

Navegador remoto persistente do ecossistema Anthares para autenticação manual, recuperação visual e automação controlada sobre a mesma sessão Chromium.

> O diretório ainda se chama `anthares-brouser/` por compatibilidade histórica. `Anthares-browser` é o nome canônico do produto. A renomeação física deverá ser feita de forma atômica em uma etapa separada.

O Chromium usa `/data/chrome-profile` como `user-data-dir`, portanto cookies, Local Storage, IndexedDB e demais dados do perfil sobrevivem a reinicializações quando `/data` está em volume persistente.

## Portas

- `6080`: interface noVNC para login/recuperação manual.
- `8080`: API de controle protegida por Bearer token.
- `9222`: CDP interno, vinculado exclusivamente a `127.0.0.1`; não deve ser publicado pelo container/plataforma.

## Variáveis obrigatórias

- `VNC_PASSWORD`: senha da sessão visual remota.
- `CONTROL_TOKEN`: token Bearer para a API de controle.

Opcionais:

- `DISPLAY` (default `:99`)
- `CHROME_PROFILE_DIR` (default `/data/chrome-profile`)
- `START_URL` (default `https://www.kwai.com/`)
- `CDP_PORT` (default `9222`, loopback-only)

## Execução

```bash
docker build -t anthares-browser ./anthares-brouser
docker run --rm -p 6080:6080 -p 8080:8080 \
  -e VNC_PASSWORD='...' -e CONTROL_TOKEN='...' \
  -v anthares_browser_data:/data anthares-browser
```

Não publique a porta 9222. A API FastAPI acessa o CDP somente via loopback dentro do mesmo container.

## API

`GET /health` não exige token e informa saúde, existência do perfil, Chromium e disponibilidade do CDP.

Todos os endpoints abaixo exigem `Authorization: Bearer <CONTROL_TOKEN>`:

- `GET /status`: perfil, tamanho, PIDs, CDP e `session_claim`.
- `GET /page`: URL, título e texto visível atual.
- `GET /targets`: alvos Chromium sem expor WebSocket debugger URL.
- `POST /navigate`: navega para URL absoluta `http/https`.
- `POST /click`: clica um seletor CSS.
- `POST /type`: foca um seletor CSS e insere texto pelo CDP.
- `POST /wait`: aguarda um seletor existir/ficar visível.
- `POST /evaluate`: executa JavaScript no alvo atual; é uma operação privilegiada e deve permanecer atrás do `CONTROL_TOKEN`.
- `GET /screenshot`: captura PNG em base64 sem persistir a imagem no volume.

Exemplos:

```bash
curl -H "Authorization: Bearer $CONTROL_TOKEN" http://HOST:8080/page

curl -X POST \
  -H "Authorization: Bearer $CONTROL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.kwai.com/","wait_ms":1500}' \
  http://HOST:8080/navigate
```

## Persistência e autenticação

Persistência de perfil não equivale a autenticação comprovada. O campo `session_claim` permanece `not_verified` até que um adaptador específico valide, na própria interface do serviço, uma condição inequívoca de usuário autenticado depois de reiniciar Chromium/container com o mesmo `/data`.

O fluxo correto é:

1. subir o Anthares-browser com volume persistente;
2. fazer autenticação/recuperação visual por noVNC quando necessário;
3. reiniciar Chromium/container com o mesmo volume;
4. validar a sessão real pelo serviço alvo;
5. somente então permitir que o adaptador de automação reutilize a sessão.

Não execute dois Chromiums simultaneamente contra o mesmo `CHROME_PROFILE_DIR`. A API serializa comandos dentro de uma instância, mas coordenação entre múltiplos containers/processos continua exigindo lease/mutex externo ou perfis isolados.

## Segurança

Não grave `VNC_PASSWORD`, `CONTROL_TOKEN`, cookies, QR, OAuth tokens ou conteúdo de `/data/chrome-profile` no repositório ou em artifacts. O endpoint visual deve ficar atrás de TLS/controle de acesso e ser aberto somente quando necessário. O CDP não é uma API pública: permanece em loopback e a única superfície externa de automação é a API autenticada na porta 8080.

## QA

Os workflows de persistência/runtime validam a infraestrutura Chromium e sobrevivência do perfil. Eles não afirmam autenticação no Kwai. A automação programática acrescentada aqui deve ser validada separadamente por testes de token, bind loopback do CDP, navegação, interação e reinício com o mesmo perfil antes de ser usada para publicação real.
