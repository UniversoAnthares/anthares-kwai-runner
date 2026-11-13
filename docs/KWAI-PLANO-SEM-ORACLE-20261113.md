# Kwai: plano operacional sem Oracle, sem Android físico e sem PC
Decisão do titular: 2026-11-13. Custo recorrente autorizado: R$ 0. Duas contas Kwai brasileiras.

## Decisão irrevogável nesta fase
- PARAR consultas de capacidade, provisão, cron e alertas Oracle; dois workflows OCI transformados em ações manuais inertes pelo PR #2575, e alerta ChatGPT Oracle desativado. Não reativar Oracle sem novo pedido explícito.
- Preservar o publicador Android físico até confirmação operacional completa do sucessor. Não duplicar tarefas Neon nem reeditar tarefas STARTED/UNCERTAIN sem reconciliação.
- Exigir autonomia: nenhum computador pessoal ou Android físico executando publicações após o corte. Nenhum novo custo mensal, cadastro pago, cartão, compra ou teste que exponha credenciais em provedor não comprovado.

## Prioridade 1: publicação por plataforma oficial sem Android
O próprio endpoint antigo de publicação do Kwai (`https://cp.kwai.com/`) informa a descontinuação e aponta para CutMotions (`https://www.cutmotions.com/`). Isso **é uma pista de serviço oficialmente recomendado**, não é prova de que o CutMotions suporta cada conta brasileira, que o upload/agendamento é gratuito/sem limites, ou que permite automação externa.

Gate 1 (prova de produto): no CutMotions aberto pelo redirecionamento oficial, verificar (a) autenticação individual nas contas `lucasrosalem` e `universoanthares`; (b) upload de MP4 para cada perfil brasileiro; (c) agendamento futuro de uma publicação com fuso local; (d) confirmação de gratuidade compatível com o volume e de operação totalmente hospedada; (e) método autorizado de automação (API oficial, integração, ou recurso de agendamento nativo). Se houver pagamento obrigatório, funcionalidade ausente, vínculo incompatível ou permissão insuficiente, encerrar essa rota SEM enviar senhas, cookies ou vídeos de produção. Nunca presumir API.
Gate 2 (prova controlada): usando um corte autorizado e duas contas em momentos distintos, primeiro fazer um teste de agendamento/rascunho sem envio; somente com fluxo comprovado, testar uma publicação real autorizada por conta e verificar no próprio perfil público o ID externo, horário e conteúdo.
Gate 3 (integração): adaptar controlador cloud existente + fila Neon para agendar no serviço oficialmente suportado, respeitando lease_generation, target_key, expected_account, nenhuma duplicação e distribuição após primeiro post até 23h no fuso America/Campo_Grande. Publicações com resultado incerto -> reconciliação sem reenvio. Tokens restritos e criptografados, sem persistência no PC.
Gate 4 (corte): operar por um ciclo completo de publicações com contas corretas e provas externas, com PC e Android físico efetivamente fora do circuito. Só então remover os devices locais do roteamento.

## Prioridade 2: parceiro autorizado / API com escopo real
Se CutMotions não fornecer o fluxo, procurar acesso **documentado e autorizado** de publicação para as contas Kwai internacionais. A plataforma chinesa Kuaishou (`open.kuaishou.com`) tem API de publicação com `user_video_publish`, mas é **outro ecossistema de autenticação**; antes de escrever qualquer cliente, comprovar formalmente que escopo/app_id/OAuth autorizam estes usuários no Kwai Brasil. Teste de upload sem postagem antes do primeiro commit. Sem confirmação do serviço, esta rota permanece BLOCKED.

## Critério de viabilidade econômica — sem promessas
Servidores gratuitos de 1 GB (ex.: Google e2-micro) não suportam a configuração ReDroid 4 GB validada pelo projeto. A oferta Northflank Sandbox até US$ 20/mês em recursos é inferior ao preço listado de 2 vCPU/4 GB (~US$ 48/mês); além disso é necessário confirmar isolamento/kernels, permissões Android e contrato de produção. Não afirmar VPS gratuita viável apenas por mostrar página de plano.
Cloud phones freemium com minutos gratuitos não equivalem a telefone gratuito 24/7. Não iniciar compras, testes pagos ou provisionamento de hosts duvidosos.

## Próxima ação
Acessar `https://cp.kwai.com/` e seguir apenas o redirecionamento oficial para CutMotions; usuário faz autenticação no site, sem transmitir senha no chat. Com sessão autenticada, verificar compatibilidade de duas contas, publicação/agendamento e limites de custo, para decidir o Gate 1. Se os recursos não forem oferecidos, reportar bloqueio factual e avançar apenas para parceiro/API autorizada, sem voltar à Oracle por iniciativa do agente.

## Estado verificável em 13/11/2026
- Oracle: cron e API desativados em dois workflows + alerta ChatGPT pausado.
- CutMotions: oficialmente recomendado pelo site anterior do Kwai; página autenticada bloqueia inspeção pública; acesso do usuário e permissão de agendamento de Kwai Brasil **não comprovados**.
- Kwai: Android físico é o publicador atual; Neon e roteador cloud preparados para futura promoção, sem operação cloud comprovada.
- Objetivo final: duas contas, até 23h, custo R$0, publicação independente do PC e celular, com prova real.
