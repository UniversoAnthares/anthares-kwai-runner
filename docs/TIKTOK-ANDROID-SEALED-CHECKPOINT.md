# TikTok Android: checkpoint criptografado entre runners na nuvem

## Situação

- AVD Android 35 com KVM já iniciou nos GitHub Actions.
- Restauração de snapshot completo entre runners foi provada no projeto Kwai, mas a sessão autenticada do TikTok ainda precisa de teste próprio.
- A camada de armazenamento cifrado usa `tools/tiktok_avd_sealed_state.py`, com AES-256-GCM em blocos de 1 MiB e verificação de truncamento, adulteração e integridade do último bloco.
- O segredo `ANTHARES_BROWSER_STATE_KEY` já existe nos secrets do projeto; deve permanecer estável em execuções diferentes. Não registrar seu valor.
- O teste isolado `.github/workflows/tiktok-avd-sealed-persistence-smoke.yml` usa apenas um perfil sintético; primeiro job cifra, segundo job restaura e rejeita arquivo alterado. **Esse teste não restaura uma conta Google verdadeira.**
- Hostinger atual não dispõe de `/dev/kvm`; os dois testes do VPS configurado no repositório falharam antes da identificação do host. Logo não há servidor KVM gratuito e permanente comprovado.

## Contrato de captura em um runner Android efetivamente autenticado

1. Crie AVD com nome exato `tiktok-persist` no caminho `$HOME/.android/avd`, imagem Android 35 Google Play x86_64, sem `-wipe-data` nas reinicializações.
2. Certifique-se de que o usuário confirmou o login no Google Play e de que o aplicativo TikTok instalado e autorizado está no estado correto. **Verificar identidade da conta também após a restauração.**
3. Pare qualquer ação de publicação e execute `bash tools/tiktok_avd_checkpoint.sh capture /tmp/tiktok-avd-encrypted-state.bin`. O script salva snapshot `tiktok-ready`, encerra o emulador, espera liberação do dispositivo e cifra a pasta completa do AVD.
4. Armazene **apenas o arquivo cifrado** com Actions artifact ou cache privado, retenção limitada, nunca a pasta Android `avd/` nem seus dados sem cifra. Não publique o arquivo no repositório.
5. Para restaurar, em novo runner com Android SDK e Play Store system image instalados, baixe o artefato cifrado, use o mesmo segredo e execute `bash tools/tiktok_avd_checkpoint.sh restore /tmp/tiktok-avd-encrypted-state.bin`. O processo verifica a autenticação AES-GCM antes de extrair o arquivo, valida `tiktok-ready` e confirma nos logs do emulador que o snapshot foi realmente carregado.
6. Faça verificação independente de conta Google/TikTok e teste somente leitura antes de qualquer LIVE. Uma restauração de arquivo não comprova autenticação.
7. O GitHub Actions continua um ambiente temporário: o backup resiste entre execuções, embora não garanta LIVE 24h nem chave/controle LIVE.

## Restrições

- Não guardar tokens de sessão no GitHub Actions em formato aberto; não publicar screenshot, e-mail, senha nem dados do Android.
- Não reciclar o cache existente do Kwai para este AVD. O identificador `tiktok-persist` é exclusivo do TikTok.
- Não ativar automaticamente transmissão enquanto não existir um controle LIVE válido e confirmação pública independente.
- O uso real de perfis autenticados exige um workflow de captura e restauração integrado ao GUI remoto. Esse acionamento ainda está pendente, pois a sessão Google do Android anterior foi encerrada antes de salvar o AVD.
