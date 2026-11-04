# CORTES — comprovação de 68 mídias externas e recuperação exata do ledger, sem publicação
STATUS: PARTIAL
AREA: architecture
DATE: 2026-11-04
RUN: none
JOB: read-only Neon SELECT + four ARA one-shot HTTP HEAD audits + read-only SHA-256 comparison
COMMIT: 55807ac002d7cd2ce8e5be6017df7f3d6271db00
SUPERSEDES: none
OBSERVED_UTC: 2026-11-04T02:36:04.923Z
GOVERNANCE_MANIFEST: 223433740e807a90
OWNER: Reestruturação e Otimização / CORTES

## Escopo e invariantes
Comprovar disponibilidade real das 68 mídias WordPress vinculadas a publicações Kwai UNCERTAIN, recuperar integridade do ledger remoto e verificar capacidade remota do executor sem publicar, alterar fila, modificar tokens, reativar PC como runner ou gerar despesa. A prova de existência no WordPress é diferente da prova da publicação no Kwai.

## PROVEN — 68 objetos externos legíveis
- O Neon de CORTES informou exatamente 68 linhas uncertain da conta kwai:lucasrosalem, com 68 URLs HTTPS distintas sob o host oficial anthares.us e o diretório de clipes. Todos pertencem ao executor nominal physical_android.
- Conferi os 68 URLs, um HEAD por URL, em quatro grupos de 17, sem baixar mídia, sem gravar arquivos e sem reenviar publicações.
- Resultado: 68/68 HEAD HTTP 200, Content-Type video/mp4, Content-Length maior que 10.000 bytes; nenhum erro ou 404. O tamanho combinado informado pelo servidor é 384.492.972 bytes. Fontes distribuídas em 51, 16 e 1 segmentos.
- Três inspeções iniciais adicionais (uma por fonte) também obtiveram HTTP 200 / video/mp4.
- Evidência ARA read-only: jobs 826edff5f530e64dcd55f4ee9518e61a, 919d5a9b285e9b606ed6cb7ffaae1c35, 606db14af90a6e6f0ecc32dca61fc3bb, 31409c603196c905ef1533ed57527c8c; sem segredos ou URLs privados registrados.
- Conclusão limitada: disponibilidade HTTP e tamanho dos 68 arquivos. HEAD não valida o conteúdo binário completo nem publicação no Kwai. O campo media_hash_kind do ledger é dispatch_identity, não um hash independente dos bytes MP4.

## PROVEN — recuperação do checkpoint de segmentos
- O Neon contém snapshots do ledger revisões 14688 e 15399; ambos com tamanho declarado igual aos bytes armazenados e SHA-256 calculado no banco igual ao digest de controle.
- Snapshot mais recente: revisão 15399, data de captura 2026-10-31T04:42:38.710Z, 2.932.006 bytes, JSON válido versão 1, com cinco fontes.
- Auditoria com Get-FileHash SHA256 da cópia histórica de revisão 15399 no PC retornou MESMO SHA-256 e MESMO TAMANHO da cópia no Neon. A cópia remota pode ser recuperada integralmente sem depender do PC como depósito canônico. Nenhum dado local foi apagado nem executado.
- Esta é prova de integridade do objeto de checkpoint. A restauração em um executor de produção com permissões, writer único e fencing permanece UNVERIFIED.

## RECONCILE_REQUIRED — publicação Kwai
- O Neon permanece com 456 registros confirmed e 68 uncertain para kwai:lucasrosalem. Os 68 carecem de remote_id e confirmation_evidence. Nenhum foi reenfileirado, atualizado, confirmado ou marcado failed.
- A busca pública não retornou recibos inequívocos para essas 68 mídias. GET público ao perfil Kwai via acesso administrativo leu HTTP 405; outros navegadores consultados não tinham quota gratuita (Browserless Free: 0 de 1000 unidades restantes; TinyFish: saldo não positivo e sem recarga). Nenhum pagamento, bypass ou perfil do usuário foi utilizado.
- É obrigatório verificar cada publicação pelo ID/URL oficial e conta exata, compatível com o validador do repositório, antes de transição de estado. Ausência de resposta na busca pública não demonstra ausência do vídeo na rede.

## PARTIAL — migração dos dois produtores de mídia
- O código do refill Ubuntu foi implantado no Clipper no commit 55807ac002d7cd2ce8e5be6017df7f3d6271db00; a variável de ativação continua ausente, e não houve publicação.
- Os workflows cortes-daily.yml e cortes-short-resume.yml ainda exigem Windows self-hosted e caminhos locais para gerador, estado e mídia; os dois cron automáticos do Clipper foram previamente removidos.
- Hostinger acessível por SSH fornece Python 3.11, porém a consulta read-only não encontrou ffmpeg nem ffprobe no PATH. Quota GitHub Actions não pôde ser comprovada pelo endpoint de cobrança autorizado.
- A tarefa local F1 de replicação de masters permanece agendada a cada 30 minutos; sua última execução observada em 2026-11-04T02:29Z produziu idle_no_eligible_media e verified_masters=0. A tarefa diária adicional permanece habilitada; nenhuma foi desligada porque falta verificar equivalência/continuidade de backup.
- Google Drive externo disponibiliza amostras de mídia, canários e backups de configurações; a cobertura de todos os masters/checkpoints para daily/resume continua UNVERIFIED.

## Bloqueios de aceite
1. Kwai: observar remotamente os 68 recibos no perfil correto com autorização/quota gratuita válida; classificar cada registro somente após prova direta. Manter a fila em hold até então.
2. CORTES: demonstrar uma restauração funcional do ledger Neon no executor remoto, mídia de origem completa, manifestos/hashes, backup e capacidade de processamento sem PC e sem exceder a quota contratada.
3. Validar identidade do escritor único, locks/fencing, recuperação de UNCERTAIN e recibo remoto em publicação real autorizada; proibir postagem para testar.
4. Provar RPO/RTO e continuidade independente para daily/resume; planejar suspensão das duas tarefas locais após migração e prova dos backups.
5. A PR pública draft #2057 contém contrato Cloudflare/Neon revisado, sem implantação. A Vercel principal retornou HTTP 402 no teste anterior e não deve receber nova tentativa ou compra sem revisão autorizada.

## Classificação final
PROVEN somente a disponibilidade HTTP dos 68 MP4 e a igualdade exata do checkpoint Neon de revisão 15399. UNVERIFIED execução de produção totalmente remota e posts Kwai. RECONCILE_REQUIRED os 68 registros. PARTIAL o programa de migração. Nenhuma despesa, vídeo, fila ou serviço de produção foi alterado nesta auditoria.
