# Lovecraft — tradução parcial volta a ser elegível (fonte preparada)
STATUS: PARTIAL
AREA: wordpress/lovecraft-publication-recovery
DATE_UTC: 2026-11-12
OWNER: chatgpt-gpt6-lovecraft-partial-20261112
LEASE: CLOSED
SUPERSEDES: test-hub/findings/lease-20261112-lovecraft-partial-translations-gpt6.md
SOURCE_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/268
SOURCE_BRANCH: fix/lovecraft-retry-partial-translation-and-accurate-warning-20261112
SOURCE_HEAD: ea08510419cf5b538cdba20f49f4886b36918bae

## Origem
Capturas do painel autenticado (11/12 Nov 2026): 460 obras, 108 marcadas traduzidas, 338 publicadas, 6 pendentes sem fonte, 2 erros. A ação publicar devolveu quarentena sem lista de IDs. O código atual de anthares_lc_publicar_proxima ignora obra com aviso de tradução parcial, porém retorna mensagem de quarentena mesmo com zero obras em quarentena. A função de tradução procurava somente status pendente/texto_obtido, de modo que obras com status traduzido e aviso de blocos em idioma original não tinham reentrada automática. A captura, isoladamente, não comprova quantas das 108 são parciais versus cooldown; os avisos persistidos exigem leitura autenticada para quantificar.

## Fonte alterada, sem deploy
- anthares-lovecraft-corrigido/includes/18-executar-traducao.php: elegibilidade de traduções parciais explicitamente marcadas, via worker existente, limitando a UM novo agendamento de reparo/hora e preservando os estados editoriais; retomada de bloco já possui backoff para rate limits.
- anthares-lovecraft-corrigido/includes/19-publicar-post.php: diagnóstico distingue obra com blocos originais da obra em quarentena; bloqueio editorial intacto.
- tests/lovecraft-recovery-contract.php: modo partial com verificação de zero publicação, mensagem verdadeira, worker de reparo e ausência de duplo agendamento no intervalo.
- GitLab peer na ref main foi consultado; includes/19 possui blob divergente entre peer e GitHub canônico. Nenhuma tentativa de mirroring ou sobrescrita no peer.

## Validações e limites
Branch GitHub criada a partir do HEAD 8d854424a659ac4de1de89de0deadcdc052aa27a. PR draft #268 aberta, mergeable na última consulta, sem checks CI associados ao HEAD. PHP lint e execução do teste offline pendentes; no Windows php não está instalado em PATH e a execução de código Hostinger fora do hPanel já havia sido negada. Nenhum servidor, cron, mídia, post ou conta modificado. Sem custo adicional.

## Conclusão restrita
Correção SOURCE_STAGED; PRODUCTION_UNVERIFIED. Verificar PHP syntax, qa/manifest-coverage-preflight.py --check, contrato parcial e revisão de concorrência antes de merge e deploy. Só declarar item 3 concluído com recibo de obra publicada conforme regra editorial e nova rodada automática com contadores atualizados.
