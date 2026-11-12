# Anthares Secrets — estados reais

2026-10-19

| Escopo | Estado | Evidência/próximo requisito |
|---|---|---|
| Nome e contrato técnico | PREPARADO | Anthares Secrets, Bitwarden SaaS como armazenamento |
| GitHub | INVENTARIADO | 13 repositórios UniversoAnthares listados; nenhuma credencial lida |
| GitLab | PARCIALMENTE INVENTARIADO | Projetos localizados; integrações não alteradas |
| Bitwarden organização/cofre | NÃO CONFIGURADO | Criar organização e 3 projetos |
| Contas de máquina | NÃO CONFIGURADO | Criar identidades e permissões por grupo |
| Variáveis bootstrap GitHub/GitLab | NÃO CONFIGURURADO | Gravar BWS_ACCESS_TOKEN em cada secret store necessário |
| Consumidores de segredos | NÃO MIGRADOS | Testar em branch/ambiente isolado |
| WordPress/Cloudflare/Remote/Browser/AAR/CORTES/AI | NÃO MIGRADOS | Mapear consumidores e verificar acesso real |
| Teste ponta a ponta | PENDENTE | Recuperação remota + consumo + rotação + indisponibilidade |
| Segurança | PENDENTE | Revisar escopos, logs, branches protegidas e direitos |

Nunca declarar a integração concluída sem prova de recuperação real de um segredo por cada consumidor. Nenhum workflow de produção deve depender de exemplos com IDs fictícios.
