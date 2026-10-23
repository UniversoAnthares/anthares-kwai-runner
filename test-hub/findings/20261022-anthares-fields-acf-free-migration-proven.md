# Anthares Campos: ACF PRO 5.10.2 substituído em produção
STATUS: PROVEN
AREA: wordpress-security
DATE: 2026-10-22
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/70
COMMIT: GitHub main 5730f33797a34d8b93d87cc95041519429b56779; GitLab main ba389c41cea9dce6b79e556118ff878cefeed4e1
SUPERSEDES: test-hub/findings/lease-wordpress-acf-selfhosted-20261022-gpt6.md

## Escopo e baseline
- Hostinger registrava ACF PRO 5.10.2 ativo junto com ACF gratuito 6.8.10.
- 12 grupos, 33 campos, 31 nomes, tipos apenas post_object/range/text/textarea/true_false. Nenhum repeater/flexible/gallery/options_page em uso.
- WP CLI shadow boot sem ACF PRO mostrou 12 grupos e 33 campos, get_field() presente.
- Plugin original Anthares Campos 1.0.0 em anthares-fields/anthares-fields.php, depende do ACF gratuito e não copia código PRO; fornece endpoint REST health restrito e valida versão/tipos/inventário.
- PHP 8.4.27 lint e cinco testes offline PASS.
- PR #70 merged no GitHub e reconciliação no GitLab; plugin na Hostinger tem git blob c36b3eb5dbf4677b4f37e052c704dca4cdceed67 e PHP host lint PASS.

## Evidências definitivas
- Cópia privada compactada do ACF PRO preservada fora de public_html.
- wp plugin activate anthares-fields e wp plugin deactivate advanced-custom-fields-pro executados.
- ACF health: PASS; engine 6.8.10; ACF PRO ativo: NÃO; grupos 12; campos 33; tipos incompatíveis 0.
- HTTP GET 200 para homepage, CORTES, desafios, minha-conta e enviar-capitulo; REST health sem autorização 401.
- Tentativa de excluir os arquivos físicos do ACF PRO bloqueada por ferramenta ANTES da execução; o diretório antigo permanece no servidor, embora o plugin esteja INATIVO. Não declarar desinstalado.

## Limites
- Não foi clonada a API completa do ACF PRO. Migração abrange todos os tipos e campos realmente usados no site na data; campos premium futuros não estão implementados.
- Não foi realizado teste manual autenticado de cada formulário de edição. Risco mitigado por inspeção de todos os tipos e grupos e confirmação das rotas públicas.
- PHP Hostinger 8.3.35 segue sem atualização.
- Aulas 04,05,06 estudadas com legendas automáticas completas, sem implantação de novas proteções dessas aulas.

## Consequência
Sem necessidade de pagar nova licença ACF PRO para os 33 campos em uso. Manter ACF Free + Anthares Campos ativos; não reativar o PRO antigo sem revisar segurança. Lease fechado.
