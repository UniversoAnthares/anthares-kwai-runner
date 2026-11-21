# Anthares Studio — Item 13: gerador estruturado de histórias

**Data:** 20/11/2026 (America/Campo_Grande)  
**Resultado:** IMPLEMENTADO NO GITHUB E NA HOSTINGER; QA transacional real aprovado.

## Contrato aplicado

Fontes: `PENDÊNCIAS URGENTES.md` item 13, `site-anthares.docx` ("uma aba: gerador de histórias"), Plano Mestre B09 e contrato de navegação fixa v2. O gerador fica dentro do **Banco de ideias**, preservando os cinco destinos globais.

A política original de "uma geração por semana e cobrança para repetir" permanece suspensa conforme a decisão documentada no Plano Mestre B09. O servidor tem uma guarda opcional, desativada por padrão, exigindo aprovação explícita em `anst_g7_generator_weekly_approved`; nenhuma cobrança ou integração de pagamento foi iniciada.

## Funcionalidade

- Duas estruturas iniciais e até oito estruturas personalizáveis; nome e texto com campos de substituição.
- Sete listas privadas por usuário: gênero, protagonista, objetivo, obstáculo, cenário, reviravolta e restrição; de 2 a 40 itens por lista.
- Sorteio com `random_int` realizado no servidor. O retorno preserva valores, posições sorteadas, modelo utilizado, revisão de configuração e texto final.
- Propostas guardadas explicitamente com ações de salvar e recuperar o resultado exato. Cada proposta salva usa a entidade `anst_nota` do próprio autor, tipo `idea`, e pode ser vinculada a um `anst_projeto` próprio por meio da ferramenta existente.
- Identificador do sorteio único e reenvio idempotente; bloqueio para outras contas, validação de propriedade, mutex de usuário e controle de revisão concorrente. Proposta temporária expira após 2 horas; nota salva permanece.
- Metadados do gerador escritos por `update_post_meta` nativo para respeitar o modo ACF estrito instalado em produção.

## Códigos e implantação

- PR integrada: https://github.com/UniversoAnthares/anthares-wordpress/pull/394
- Merge: `4407f0f7f575d1867525e4d6101b865b6061bd7b`
- `anthares-studio/anthares-estudio.php`: `7c649628b0484c09b82968cab3690804b0d3f7e8`
- `anthares-studio/assets/estudio.js`: `0ae731e507d52d7a4a112d0d5d2015703d9d277c`
- `anthares-studio/includes/domain/class-anst-g7-generator.php`: `9c37bc6b35d154684fac5fcb804687fa93287558`
- `anthares-studio/assets/studio-g7-generator.js`: `03da1d8cff14d1e886689500657b416634b7831b`
- `anthares-studio/assets/studio-g7-generator.css`: `a836e6e4c35afb15012d233f7060ee0df3cc8228`
- Backups originais de `anthares-estudio.php` e `estudio.js` na pasta privada `studio-private-backups/20261120-item13` fora de `public_html`.
- Código inicial instalado somente após conferência da fonte anterior, PHP 8.3 lint e teste do hash completo.

## Testes

- **16/16 PASS**, WordPress real: configuração padrão, validação inválida, rejeição de placeholder desconhecido, edição de listas persistida, rejeição de revisão antiga, sorteio, reprodução da combinação, anotação gerada, metadados, repetição idempotente, isolamento entre contas, bloqueio de uso do rascunho de outro usuário, projeto nativo e vínculo da anotação.
- Cada execução usou transação InnoDB com `ROLLBACK=EXECUTED`; conferência posterior encontrou zero registros com o título temporário de QA.
- PHP 8.3 lint: PASS em módulo e plugin principal. JavaScript: `node --check` PASS; CSS e JS HTTP 200.
- Cobertura QA: 735 arquivos auditáveis, manifestos idênticos e ausência de arquivos faltantes/duplicados na árvore da branch.
- `https://anthares.us/studio/` HTTP 200; `https://anthares.us/estudio/` HTTP 200. Plugin Anthares Studio ativo.

## Limitações documentadas

A execução em navegador de uma conta de cliente com acesso ao Studio ainda não foi homologada visualmente neste turno. As operações de geração, persistência e permissão foram comprovadas na instalação WordPress real; os controles de interface passaram por verificação de sintaxe e arquivos acessíveis. A regra de cobrança depende de autorização comercial específica e foi deliberadamente mantida inativa.

**Classificação de implementação:** concluído em produção; teste visual de ponta a ponta recomendado como parte do item 21.
