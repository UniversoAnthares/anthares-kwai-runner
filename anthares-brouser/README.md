# Anthares-browser

Navegador remoto persistente do ecossistema Anthares para autenticação manual, recuperação visual e automação controlada sobre a mesma sessão Chromium.

> O diretório ainda se chama `anthares-brouser/` por compatibilidade histórica. `Anthares-browser` é o nome canônico do produto. A renomeação física deverá ser feita de forma atômica em uma etapa separada.

O Chromium usa `/data/chrome-profile` como `user-data-dir`, portanto cookies, Local Storage, IndexedDB e demais dados do perfil sobrevivem a reinicializações quando `/data` está em volume persistente.

## Regra obrigatória: sessão isolada e invisível

Toda automação Anthares-browser DEVE criar ou reutilizar exclusivamente seu próprio ambiente remoto isolado (container + Xvfb + Chromium + perfil dedicado). Nunca conectar-se a uma janela, aba, perfil, sessão CDP ou navegador já aberto pelo usuário. Nunca controlar o desktop hospedeiro, mover o mouse real, enviar teclas globais, roubar foco, exibir janelas locais ou interromper atividades correntes do computador.

- A execução normal é invisível no computador do usuário; noVNC é somente uma visualização remota opcional e explicitamente aberta para login/recuperação.
- Toda interação deve ocorrer dentro do Chromium isolado via CDP interno. Não usar automação de mouse/teclado do sistema operacional hospedeiro.
- Um perfil Chromium pertence a uma única instância por vez; sessões paralelas precisam de perfis/volumes separados e isolamento de concorrência.
- É proibido anexar o CDP a um navegador externo ou usar o perfil padrão do Chrome/Edge do usuário.
- Se o ambiente isolado não estiver disponível, a operação deve falhar de forma segura; não fazer fallback para o navegador/desktop do usuário.
- Testes de aceitação devem confirmar: nenhum processo/janela criado no desktop do usuário, nenhum foco roubado, nenhum evento de mouse/teclado enviado ao hospedeiro e nenhum perfil pessoal acessado.

## Portas

- `8080`: única porta da API e do gateway noVNC autenticado; expor apenas por HTTPS.
- `5900`: VNC interno, vinculado a `127.0.0.1`; não publicar.
- `6080`: websockify/noVNC interno, vinculado a `127.0.0.1`; não publicar.
- `9222`: CDP interno, vinculado a `127.0.0.1`; não publicar.

## Variáveis obrigatórias

- `VNC_PASSWORD`: senha da sessão visual remota.
- `CONTROL_TOKEN`: token Bearer para a API de controle e acesso visual; usar valor aleatório com pelo menos 24 caracteres.

Opcionais:

- `DISPLAY` (default `:99`)
- `CHROME_PROFILE_DIR` (default `/data/chrome-profile`)
- `START_URL` (default `https://www.kwai.com/`)
- `CDP_PORT` (default `9222`, loopback-only)

## Execução

```bash
docker build -t anthares-browser ./anthares-brouser
docker run --rm -p 127.0.0.1:8080:8080 \
  -e VNC_PASSWORD='...' -e CONTROL_TOKEN='TOKEN_ALEATORIO_COM_PELO_MENOS_24_CARACTERES' \
  -v anthares_browser_data:/data anthares-browser
```

Não publique as portas 5900, 6080 ou 9222. O exemplo publica a API somente no loopback do host; um proxy HTTPS autenticado deve expor a porta 8080 remotamente. A API acessa CDP/VNC/websockify apenas pelo loopback do container.

Para acesso visual, abra `https://DOMINIO_DO_SERVICO/novnc/login` e informe o `CONTROL_TOKEN` no formulário HTTPS. A sessão é temporária (10 minutos), em cookie HttpOnly/Secure/SameSite; o WebSocket `/novnc/websockify` só aceita a mesma origem e uma sessão válida. O endpoint `POST /novnc/session` também emite sessão mediante Bearer token. `POST /novnc/logout` (com Bearer) revoga a sessão. **Não coloque o token em URL, logs ou repositórios.**

## API

`GET /health` não exige token e informa apenas liveness. `GET /ready` valida perfil, Chromium e CDP; pode retornar HTTP 503.

Todos os endpoints abaixo exigem `Authorization: Bearer <CONTROL_TOKEN>`:

- `GET /status`: perfil, tamanho, PIDs, CDP e `session_claim`.
- `GET /page`: URL, título e texto visível atual.
- `GET /session/evidence`: evidência conservadora de login Kwai; retorna `unauthenticated` apenas quando encontra solicitação explícita de login, ou `unknown`. Nunca retorna `authenticated` sem prova.
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
