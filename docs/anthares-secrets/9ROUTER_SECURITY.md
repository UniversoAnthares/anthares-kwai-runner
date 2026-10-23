# Anthares Secrets / 9Router — integração e segurança

Estado: **proposta implementável documentada**, sem ativação em produção (2026-10-19).

## Decisões preservadas
- **Anthares Secrets:** Bitwarden Secrets Manager remoto como armazenamento central de chaves/tokens e credenciais de serviço.
- **Anthares AI Hub:** autoridade principal de roteamento e escolha de modelos, independentemente da disponibilidade do 9Router.
- **9Router:** roteador secundário, isolado, sem acesso administrativo aos sistemas Anthares, sem credenciais globais, sem privilégios sobre GitHub/GitLab/Cloudflare e sem escrita nos cofres.
- **Gateway Anthares:** responsável por autenticar clientes e fornecer somente a credencial necessária ao destino autorizado, com tempo de vida curto quando o provedor suportar emissão temporária. Para APIs que só disponibilizam chaves estáticas, usar proxy servidor-servidor em vez de entregar a chave ao 9Router.

## Bloqueio de segurança
A instalação 9Router v0.5.104 foi relatada anteriormente com 2 alertas HIGH relacionados à dependência node-forge 1.4.0 após npm audit, sem correção disponível naquela ocasião. Servidor desativado. **Nunca iniciar nem expor 9Router na rede pública até revisão de dependências e testes verificáveis.** Segregar em sandbox sem egress indiscriminado, restringir inbound a gateway autenticado e negar acesso a armazenamento local, variáveis de outros projetos, metadata cloud e rede interna.

## Integração futura
1. Inventariar APIs que AI Hub e 9Router realmente precisam. Segredos separados por provedor, projeto e ambiente.
2. Guardar segredos no projeto AI do Bitwarden, com permissão de leitura para identidade de máquina de AI Hub/gateway; 9Router não receberá BWS_ACCESS_TOKEN.
3. AI Hub requisita inferência ao gateway; gateway resolve chave conforme política e realiza upstream proxy quando a chave é estática. Se suportado pelo provedor, credenciais efêmeras com TTL limitado podem ser usadas.
4. Circuit breaker e failover no AI Hub para provedores já existentes; 9Router é opcional. Nunca iniciar dois roteadores concorrentes com a mesma autoridade/lease.
5. Testes: autorização por segredo, redaction de logs, isolamento de rede, falha do cofre, chave expirada/revogada, resistência a SSRF e endpoint interno, auditoria de dependências e tráfego, ausência de regressão do CORTES.
6. Ativação somente após relatório de evidências de build, deploy e requisições reais. Nenhum teste deve mudar trabalhos de publicação em produção.

## Pré-requisitos
- Organização Anthares Secrets criada no Bitwarden SaaS.
- Contas de máquina/segredos reais cadastrados pelo proprietário sem envio a chat ou commits.
- Serviço remoto autorizado para gateway, IAM e configuração de rede/egress.
- 9Router revisado (patch da dependência quando existir ou mitigação suficientemente demonstrada).
