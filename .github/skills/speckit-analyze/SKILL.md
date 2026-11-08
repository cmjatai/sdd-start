---
name: "speckit-analyze"
description: "Realiza uma análise não destrutiva de consistência e qualidade entre os artefatos spec.md, plan.md e tasks.md após a geração das tarefas."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/analyze.md"
---


## Entrada do Usuário

```text
$ARGUMENTS
```

Você **DEVE** considerar a entrada do usuário antes de prosseguir (se não estiver vazia).

## Verificações Pré-Execução

**Verifique se há hooks de extensão (antes da análise)**:
- Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas na chave `hooks.before_analyze`
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue normalmente
- Filtre os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar expressões de `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir um `condition` não vazio, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hifens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a seguinte saída conforme o seu campo `optional`:
  - **Hook opcional** (`optional: true`):
    ```
    ## Hooks de Extensão

    **Pré-Hook Opcional**: {extension}
    Comando: `/{command}`
    Descrição: {description}

    Prompt: {prompt}
    Para executar: `/{command}`
    ```
  - **Hook obrigatório** (`optional: false`):
    ```
    ## Hooks de Extensão

    **Pré-Hook Automático**: {extension}
    Executando: `/{command}`
    EXECUTE_COMMAND: {command}

    Aguarde o resultado do comando do hook antes de prosseguir para o Objetivo.
    ```
    Após emitir o bloco acima, você DEVE efetivamente invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que executaria o comando você mesmo neste agente/sessão (a invocação pode diferir do id literal `{command}` exibido acima, por exemplo, um agente em modo de skills o executa como `/skill:speckit-...` ou `$speckit-...`). Emitir apenas o bloco não executa o hook.
- Se nenhum hook estiver registrado ou `.specify/extensions.yml` não existir, ignore silenciosamente

## Objetivo

Identificar inconsistências, duplicações, ambiguidades e itens subespecificados nos três artefatos principais (`spec.md`, `plan.md`, `tasks.md`) antes da implementação. Este comando DEVE ser executado somente depois que `/speckit-tasks` tiver produzido com sucesso um `tasks.md` completo.

## Restrições de Operação

**ESTRITAMENTE SOMENTE LEITURA**: **Não** modifique nenhum arquivo. Produza um relatório de análise estruturado. Ofereça um plano de remediação opcional (o usuário deve aprovar explicitamente antes que quaisquer comandos de edição subsequentes sejam invocados manualmente).

**Autoridade da Constituição**: A constituição do projeto (`.specify/memory/constitution.md`) é **inegociável** dentro do escopo desta análise. Conflitos com a constituição são automaticamente CRÍTICOS e exigem ajuste da especificação, do plano ou das tarefas — não a diluição, reinterpretação ou omissão silenciosa do princípio. Se um princípio em si precisar mudar, isso deve ocorrer em uma atualização da constituição separada e explícita, fora de `/speckit-analyze`.

## Etapas de Execução

### 1. Inicializar o Contexto da Análise

Execute `.specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks` uma vez a partir da raiz do repositório e interprete o JSON para obter FEATURE_DIR e AVAILABLE_DOCS. Derive os caminhos absolutos:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md

Aborte com uma mensagem de erro se algum arquivo obrigatório estiver ausente (instrua o usuário a executar o comando pré-requisito que falta).
Para aspas simples em argumentos como "I'm Groot", use a sintaxe de escape: por exemplo 'I'\''m Groot' (ou aspas duplas, se possível: "I'm Groot").

### 2. Carregar os Artefatos (Divulgação Progressiva)

Carregue apenas o contexto mínimo necessário de cada artefato:

**De spec.md:**

- Visão Geral/Contexto
- Requisitos Funcionais
- Critérios de Sucesso (resultados mensuráveis — por exemplo, desempenho, segurança, disponibilidade, sucesso do usuário, impacto no negócio)
- Histórias de Usuário
- Casos de Borda (se presentes)

**De plan.md:**

- Escolhas de arquitetura/stack
- Referências ao Modelo de Dados
- Fases
- Restrições técnicas

**De tasks.md:**

- IDs das tarefas
- Descrições
- Agrupamento por fase
- Marcadores de paralelismo [P]
- Caminhos de arquivos referenciados

**Da constituição:**

- Carregue `.specify/memory/constitution.md` para validação dos princípios

### 3. Construir Modelos Semânticos

Crie representações internas (não inclua os artefatos brutos na saída):

- **Inventário de requisitos**: Para cada Requisito Funcional (FR-###) e Critério de Sucesso (SC-###), registre uma chave estável. Use o identificador explícito FR-/SC- como chave primária quando presente e, opcionalmente, derive também um slug de frase imperativa para legibilidade (por exemplo, "Usuário pode enviar arquivo" → `usuario-pode-enviar-arquivo`). Inclua apenas itens de Critérios de Sucesso que exijam trabalho construível (por exemplo, infraestrutura de testes de carga, ferramentas de auditoria de segurança) e exclua métricas de resultado pós-lançamento e KPIs de negócio (por exemplo, "Reduzir chamados de suporte em 50%").
- **Inventário de histórias/ações de usuário**: Ações discretas do usuário com critérios de aceitação
- **Mapeamento de cobertura das tarefas**: Mapeie cada tarefa para um ou mais requisitos ou histórias (inferência por palavra-chave / padrões de referência explícita, como IDs ou frases-chave)
- **Conjunto de regras da constituição**: Extraia os nomes dos princípios e as declarações normativas DEVE/DEVERIA

### 4. Passagens de Detecção (Análise Eficiente em Tokens)

Concentre-se em achados de alto sinal. Limite a 50 achados no total; agregue o restante em um resumo de excedentes.

#### A. Detecção de Duplicação

- Identifique requisitos quase duplicados
- Marque a redação de menor qualidade para consolidação

#### B. Detecção de Ambiguidade

- Sinalize adjetivos vagos (rápido, escalável, seguro, intuitivo, robusto) sem critérios mensuráveis
- Sinalize marcadores não resolvidos (TODO, TKTK, ???, `<placeholder>`, etc.)

#### C. Subespecificação

- Requisitos com verbos, mas sem objeto ou resultado mensurável
- Histórias de usuário sem alinhamento com critérios de aceitação
- Tarefas que referenciam arquivos ou componentes não definidos na especificação/plano

#### D. Alinhamento com a Constituição

- Qualquer requisito ou elemento do plano que conflite com um princípio DEVE
- Seções ou portões (gates) de qualidade exigidos pela constituição que estejam ausentes

#### E. Lacunas de Cobertura

- Requisitos sem nenhuma tarefa associada
- Tarefas sem requisito/história mapeado
- Critérios de Sucesso que exigem trabalho construível (desempenho, segurança, disponibilidade) não refletidos nas tarefas

#### F. Inconsistência

- Deriva terminológica (o mesmo conceito nomeado de forma diferente entre arquivos)
- Entidades de dados referenciadas no plano, mas ausentes na especificação (ou vice-versa)
- Contradições na ordenação das tarefas (por exemplo, tarefas de integração antes das tarefas fundacionais de preparação, sem nota de dependência)
- Requisitos conflitantes (por exemplo, um exige Next.js enquanto outro especifica Vue)

### 5. Atribuição de Severidade

Use esta heurística para priorizar os achados:

- **CRÍTICA**: Viola um DEVE da constituição, artefato central da especificação ausente, ou requisito sem cobertura que bloqueia a funcionalidade básica
- **ALTA**: Requisito duplicado ou conflitante, atributo ambíguo de segurança/desempenho, critério de aceitação não testável
- **MÉDIA**: Deriva terminológica, cobertura de tarefas não funcionais ausente, caso de borda subespecificado
- **BAIXA**: Melhorias de estilo/redação, redundância menor que não afeta a ordem de execução

### 6. Produzir um Relatório de Análise Compacto

Produza um relatório em Markdown (sem gravação de arquivos) com a seguinte estrutura:

## Relatório de Análise da Especificação

| ID | Categoria | Severidade | Localização(ões) | Resumo | Recomendação |
|----|-----------|------------|------------------|--------|--------------|
| A1 | Duplicação | ALTA | spec.md:L120-134 | Dois requisitos semelhantes ... | Unificar a redação; manter a versão mais clara |

(Adicione uma linha por achado; gere IDs estáveis prefixados pela inicial da categoria.)

**Tabela de Resumo de Cobertura:**

| Chave do Requisito | Possui Tarefa? | IDs das Tarefas | Observações |
|--------------------|----------------|-----------------|-------------|

**Problemas de Alinhamento com a Constituição:** (se houver)

**Tarefas Não Mapeadas:** (se houver)

**Métricas:**

- Total de Requisitos
- Total de Tarefas
- % de Cobertura (requisitos com >=1 tarefa)
- Quantidade de Ambiguidades
- Quantidade de Duplicações
- Quantidade de Problemas Críticos

### 7. Fornecer os Próximos Passos

Ao final do relatório, produza um bloco conciso de Próximos Passos:

- Se existirem problemas CRÍTICOS: Recomende resolvê-los antes de `/speckit-implement`
- Se houver apenas BAIXA/MÉDIA: O usuário pode prosseguir, mas forneça sugestões de melhoria
- Forneça sugestões explícitas de comandos: por exemplo, "Execute /speckit-specify com refinamento", "Execute /speckit-plan para ajustar a arquitetura", "Edite manualmente o tasks.md para adicionar cobertura para 'performance-metrics'"

### 8. Oferecer Remediação

Pergunte ao usuário: "Gostaria que eu sugerisse edições de remediação concretas para os N principais problemas?" (NÃO as aplique automaticamente.)

### 9. Verificar hooks de extensão

Após o relatório, verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas na chave `hooks.after_analyze`
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue normalmente
- Filtre os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar expressões de `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir um `condition` não vazio, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hifens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a seguinte saída conforme o seu campo `optional`:
  - **Hook opcional** (`optional: true`):
    ```
    ## Hooks de Extensão

    **Hook Opcional**: {extension}
    Comando: `/{command}`
    Descrição: {description}

    Prompt: {prompt}
    Para executar: `/{command}`
    ```
  - **Hook obrigatório** (`optional: false`):
    ```
    ## Hooks de Extensão

    **Hook Automático**: {extension}
    Executando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Após emitir o bloco acima, você DEVE efetivamente invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que executaria o comando você mesmo neste agente/sessão (a invocação pode diferir do id literal `{command}` exibido acima, por exemplo, um agente em modo de skills o executa como `/skill:speckit-...` ou `$speckit-...`). Emitir apenas o bloco não executa o hook.
- Se nenhum hook estiver registrado ou `.specify/extensions.yml` não existir, ignore silenciosamente

## Princípios de Operação

### Eficiência de Contexto

- **Mínimo de tokens de alto sinal**: Concentre-se em achados acionáveis, não em documentação exaustiva
- **Divulgação progressiva**: Carregue os artefatos de forma incremental; não despeje todo o conteúdo na análise
- **Saída eficiente em tokens**: Limite a tabela de achados a 50 linhas; resuma o excedente
- **Resultados determinísticos**: Reexecutar sem alterações deve produzir IDs e contagens consistentes

### Diretrizes de Análise

- **NUNCA modifique arquivos** (esta é uma análise somente leitura)
- **NUNCA invente seções ausentes** (se estiverem ausentes, reporte-as com precisão)
- **Priorize violações da constituição** (elas são sempre CRÍTICAS)
- **Use exemplos em vez de regras exaustivas** (cite instâncias específicas, não padrões genéricos)
- **Reporte zero problemas de forma adequada** (emita um relatório de sucesso com estatísticas de cobertura)

## Contexto

$ARGUMENTS
