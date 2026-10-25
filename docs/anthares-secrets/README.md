# Anthares Secrets — contrato de integração remota

**Estado:** bootstrap preparado; conexão ao cofre Bitwarden ainda depende de organização, contas de máquina e tokens reais. Nenhum valor secreto deve ser commitado.

## Objetivo
Bitwarden Secrets Manager (nuvem gerenciada) como fonte central de credenciais de serviço para GitHub, GitLab, WordPress, Cloudflare, Anthares Remote/Browser/Android Runtime, CORTES e Anthares AI Hub. O gerenciamento não depende de computador pessoal; os executores Android existentes continuam onde operam hoje.

## Limites da edição Free (validar no painel antes de ativar)
3 projetos, 3 contas de máquina, 2 usuários, segredos ilimitados. Logs de auditoria do Bitwarden indisponíveis no Free.

## Projetos e identidades
- CORE: WordPress, pagamentos, bancos e hospedagem.
- AUTOMATION: CORTES, GitHub/GitLab, Remote, Browser, Android Runtime, relay e sincronização.
- AI: Anthares AI Hub e provedores.

Uma conta de máquina por projeto, com acesso mínimo. Cada serviço recebe IDs de segredos específicos e nunca obtém todos os segredos de uma vez. Guardar tokens bootstrap **somente** nos secret stores criptografados do próprio provedor (GitHub Actions secrets, GitLab masked/protected variables ou secret store nativo do runtime). O token bootstrap é a exceção explícita ao princípio da fonte central.

## Contrato para todos os consumidores
1. Autenticar usando `BWS_ACCESS_TOKEN` lido da variável secreta do provedor, jamais de código, artefato ou log.
2. Consultar o segredo pelo **ID** Bitwarden, mapeado por aplicação; limitar permissões por conta de máquina.
3. Injetar em memória/ambiente do processo específico; nunca imprimir nem persistir credenciais em CI artifacts, traces ou relatórios.
4. Validar sucesso real da operação com resposta da API de destino (sem registrar dados sensíveis).
5. Política fail-closed para credenciais indisponíveis; nunca executar publicação repetida ou fallback concorrente em caso de incerteza.
6. Migrar consumidor por consumidor, preservando credenciais antigas até teste de ponta a ponta e plano de reversão.
7. Segredos para serviços em execução contínua: resolver no início e renovar antes de expirar. Os sistemas que precisam operar em falha do Bitwarden exigem contingência independente com escopo e prazo limitados.
8. Nunca mudar autoridade SYSTEM/ARA/AAR, reiniciar PC, forçar sessões ou executar publicação para testar a integração.

## GitHub Actions
Adicionar secret criptografado `BWS_ACCESS_TOKEN` ao repositório/ambiente conforme o projeto. Recuperar segredos específicos com `bitwarden/sm-action@v3`. Exemplo **ilustrativo**, com ID fictício que deve ser substituído antes de executar:

```yaml
- name: Read specific Anthares Secret
  uses: bitwarden/sm-action@v3
  with:
    access_token: ${{ secrets.BWS_ACCESS_TOKEN }}
    secrets: |
      00000000-0000-0000-0000-000000000000 > ANTHARES_SAMPLE_SECRET
```

Aplicar apenas nos workflows que precisarem de cada segredo. Fixar action ao commit SHA revisado antes do uso em produção.

## GitLab CI/CD
Criar variável `BWS_ACCESS_TOKEN` do tipo masked, hidden quando disponível e protected somente em branches protegidas. Instalar `bws` versão fixada de release oficial, com verificação de hash e acesso à rede Bitwarden. Exemplo de comando após instalação:

```sh
bws secret get "$ANTHARES_SECRET_ID" | jq -er '.value' >/dev/null
```

Essa linha demonstra verificação de acesso **sem imprimir o valor**. Em integração real, passar o segredo diretamente ao processo consumidor evitando saída para logs. Nunca habilitar shell tracing (`set -x`).

## Inventário inicial confirmado em 2026-10-19
GitHub UniversoAnthares: github-slideshow, wiki, anthares-transcricao, home, anthares-clipper, anthares-telegram-relay, anthares-wordpress, anthares-kwai-runner, anthares-kwai-session-vault, anthares-browser-state, anthares-ara-queue, anthares-memu4-remote-lab, anthares-memu4-remote-probe.
GitLab localizado: anthares-wordpress, anthares-clipper, anthares-telegram-relay, anthares-transcricao, anthares-kwai-runner (mais de um namespace).
Inventário de **segredos e consumidores** permanece pendente; lista de repositórios não comprova dependências efetivas.

## Pré-requisitos bloqueantes
- Organização Bitwarden Secrets Manager criada, plano verificado e conta de máquina autorizada.
- IDs reais de segredos e bootstrap tokens armazenados apenas nos secret stores protegidos.
- Inventário de consumidores/variáveis por serviço; testes em ambiente isolado de não produção.
- Aprovação da revisão de segurança e implantação por etapas.

Fontes: https://bitwarden.com/help/secrets-manager-plans/ ; https://bitwarden.com/help/github-actions-integration/ ; https://bitwarden.com/help/gitlab-integration/ ; https://github.com/bitwarden/sm-action
