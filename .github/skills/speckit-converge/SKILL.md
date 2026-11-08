---
name: "speckit-converge"
description: "Avalia a base de código atual em relação à especificação, ao plano e às tarefas da funcionalidade e adiciona qualquer trabalho restante não construído como novas tarefas em tasks.md, para que o implement possa concluí-lo."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/converge.md"
---


## Entrada do Usuário

```text
$ARGUMENTS
```

Você **DEVE** considerar a entrada do usuário antes de prosseguir (se não estiver vazia).

## Verificações Pré-Execução

**Verifique a existência de hooks de extensão (antes da convergência)**:

- Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas na chave `hooks.before_converge`
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue normalmente
- Filtre os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar expressões `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir um `condition` não vazio, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hifens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a saída a seguir conforme o seu flag `optional`:
  - **Hook opcional** (`optional: true`):

    ```text
    ## Hooks de Extensão

    **Pré-Hook Opcional**: {extension}
    Comando: `/{command}`
    Descrição: {description}

    Prompt: {prompt}
    Para executar: `/{command}`
    ```

  - **Hook obrigatório** (`optional: false`):

    ```text
    ## Hooks de Extensão

    **Pré-Hook Automático**: {extension}
    Executando: `/{command}`
    EXECUTE_COMMAND: {command}

    Aguarde o resultado do comando do hook antes de prosseguir para o Objetivo.
    ```
    Depois de emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que você executaria o comando por conta própria neste agente/sessão (a invocação pode diferir do id literal `{command}` exibido acima, por exemplo, um agente em modo de skills o executa como `/skill:speckit-...` ou `$speckit-...`). Apenas emitir o bloco não executa o hook.

- Se nenhum hook estiver registrado ou `.specify/extensions.yml` não existir, ignore silenciosamente

## Objetivo

Fechar a lacuna entre o que a especificação, o plano e as tarefas de uma funcionalidade
exigem e o que a base de código implementa atualmente. Leia `spec.md`, `plan.md` e
`tasks.md` como a **única fonte de intenção** (com a constituição como restrições
governantes), avalie o estado atual do código, determine quais requisitos, critérios de
aceitação, decisões do plano e tarefas existentes não foram atendidos, estão incompletos ou
foram satisfeitos apenas parcialmente, e **adicione cada parte do trabalho restante como uma
nova tarefa rastreável** ao final de `tasks.md`, para que o `/speckit-implement` possa
concluí-la. Este comando DEVE ser executado somente depois que o `/speckit-implement` tiver
sido executado sobre o `tasks.md` atual, e depois que o `/speckit-tasks` tiver produzido um
`tasks.md` completo.

Esta **não** é uma ferramenta de diff e **não** rastreia mudanças. Ela avalia o estado atual
do código em relação aos artefatos da funcionalidade — sem git, sem comparação de branches,
sem histórico.

## Restrições de Operação

**SOMENTE ADIÇÃO, NUNCA REESCREVER**: A **única** escrita do comando é adicionar uma nova
seção `## Fase N: Convergência` ao final de `tasks.md`. Ele NÃO DEVE:

- modificar `spec.md` ou `plan.md` de nenhuma forma;
- reescrever, renumerar, reordenar ou excluir qualquer tarefa existente (incluindo tarefas
  de uma fase de Convergência anterior);
- modificar, criar ou excluir qualquer código da aplicação — concluir as tarefas adicionadas
  é trabalho do `/speckit-implement`.

Quando a base de código já satisfizer tudo, o comando DEVE deixar `tasks.md`
**inalterado byte a byte** (sem cabeçalho de Convergência vazio) e relatar um resultado limpo.

**Autoridade da Constituição**: A constituição do projeto (`.specify/memory/constitution.md`)
é **inegociável**. Código que viole um princípio DEVE da constituição é o achado de maior severidade e
produz uma tarefa de remediação correspondente. Se a constituição for um template não
preenchido, ignore as verificações de constituição de forma tranquila, em vez de falhar.

## Etapas de Execução

### 1. Inicializar o Contexto de Convergência

Execute `.specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks` uma vez a partir da raiz do repositório e interprete o JSON para obter FEATURE_DIR e AVAILABLE_DOCS. Derive os caminhos absolutos:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md
- CONSTITUTION = `.specify/memory/constitution.md` (se existir)
Se `spec.md`, `plan.md` ou `tasks.md` estiver ausente, PARE com uma mensagem clara e acionável que nomeie o comando pré-requisito a executar (`/speckit-specify` para uma especificação ausente, `/speckit-plan` para um plano ausente, `/speckit-tasks` para tarefas ausentes). Não produza saída parcial.
Para aspas simples em argumentos como "I'm Groot", use a sintaxe de escape: por exemplo, 'I'\''m Groot' (ou aspas duplas, se possível: "I'm Groot").

### 2. Carregar os Artefatos (Divulgação Progressiva)

Carregue apenas o contexto mínimo necessário de cada artefato:

**De spec.md:**

- Requisitos Funcionais (FR-###)
- Critérios de Sucesso (SC-###) — inclua somente itens que exijam trabalho construível;
  exclua métricas de resultado pós-lançamento e KPIs de negócio
- Histórias de Usuário e seus Cenários de Aceitação
- Casos de Borda (se presentes)

**De plan.md:**

- Escolhas de arquitetura/stack e decisões técnicas
- Referências ao Modelo de Dados
- Fases e pontos de contato nomeados (arquivos/componentes que o plano diz que serão criados ou editados)
- Restrições técnicas

**De tasks.md:**

- IDs das tarefas (para calcular o próximo ID e o próximo número de fase)
- Descrições, agrupamento por fase e caminhos de arquivos referenciados

**Da constituição (se não for um template não preenchido):**

- Nomes dos princípios e declarações normativas DEVE/DEVERIA

### 3. Construir o Inventário de Intenção

Crie um modelo interno (não reproduza os artefatos brutos):

- **Inventário de requisitos**: uma chave estável por FR-### / SC-### / cenário de aceitação
  de história de usuário (por exemplo, `US1/AC2`), além das decisões do plano e dos princípios
  da constituição que impõem obrigações construíveis.
- **Mapa de escopo de código**: a partir dos caminhos de arquivos citados em `plan.md` e
  `tasks.md`, mais uma busca por palavras-chave dos conceitos que cada requisito descreve,
  derive o conjunto de arquivos-fonte e componentes no escopo da avaliação. Limite a avaliação
  a eles — **não** infira escopo além do que os artefatos definem.

### 4. Avaliar a Base de Código e Classificar os Achados

Inclua toda tarefa existente no inventário de intenção, independentemente do estado da caixa
de seleção ou da fase de Convergência: alegações de conclusão não são evidência. Verifique o
comportamento atual em relação à especificação, ao plano, às tarefas e à constituição; para
cadeias de tarefas corretivas, avalie o comportamento resultante, não detalhes de
implementação substituídos. Verifique tanto as obrigações não atendidas quanto a
implementação que contradiz, excede ou foge da intenção declarada.

Para cada item do inventário de intenção, inspecione o código atual no escopo e produza um
`Finding` (achado) somente onde houver uma lacuna. Classifique cada achado por **tipo de lacuna**:

- **`missing`**: o trabalho necessário está totalmente ausente do código.
- **`partial`**: o trabalho existe, mas ainda não satisfaz plenamente o requisito /
  critério de aceitação / decisão do plano.
- **`contradicts`**: o código faz algo que conflita com a intenção declarada ou com um
  princípio DEVE da constituição.
- **`unrequested`**: o código contém trabalho não previsto pela especificação, pelo plano ou
  pelas tarefas (exibido para conhecimento — o converge **não** exclui código, apenas
  adiciona uma tarefa para revisar/justificar ou remover).

Cada `Finding` registra: um id estável, o `source-ref` ao qual se rastreia, o `gap-type`, uma
severidade e uma descrição curta legível por humanos com a evidência (o arquivo/área observado).

**Casos de borda:**

- **Pouco ou nenhum código ainda**: trate todo o escopo especificado como trabalho restante
  `missing`, em vez de falhar.
- **Nada resta**: produza zero achados e siga o ramo de convergência concluída na Etapa 7.

### 5. Atribuir a Severidade

- **CRITICAL**: viola um princípio DEVE da constituição, ou é uma lacuna `missing`/`contradicts`
  que bloqueia a funcionalidade básica de uma história de usuário P1.
- **HIGH**: uma lacuna `missing` ou `partial` em um requisito funcional central ou critério
  de aceitação.
- **MEDIUM**: uma lacuna `partial` em um requisito secundário, ou uma adição `unrequested`
  com justificativa pouco clara.
- **LOW**: lacunas parciais menores, acabamento ou adições `unrequested` de baixo risco.

### 6. Apresentar o Resumo de Achados na Sessão

Antes de adicionar qualquer coisa, produza um resumo compacto classificado por severidade
(sem escritas em arquivos ainda):

## Achados da Convergência

| ID | Tipo de Lacuna | Severidade | Origem | Evidência | Trabalho Restante |
|----|----------------|------------|--------|-----------|-------------------|
| F1 | missing        | HIGH       | FR-008 | Exemplo: nenhuma proteção de somente-adição detectada em path/to/module.py ao gravar tasks.md | Adicionar imposição de somente-adição |

**Métricas de resumo:**

- Requisitos / critérios de aceitação verificados
- Decisões do plano verificadas
- Princípios da constituição verificados (ou "ignorado — template")
- Achados por tipo de lacuna (missing / partial / contradicts / unrequested)
- Achados por severidade

### 7. Adicionar Tarefas de Convergência (ou relatar convergência concluída)

**Se houver um ou mais achados acionáveis** (resultado `tasks_appended`):

Adicione ao **final** de `tasks.md`, conforme o contrato de adição:

1. Examine todos os IDs de tarefas existentes; seja `M` o máximo. Determine o próximo número
   de fase `N` (maior fase existente + 1).
2. Escreva um único novo cabeçalho de seção `## Fase N: Convergência`.
3. Emita um item de checklist por achado acionável, ordenados com CRITICAL/HIGH primeiro,
   atribuindo IDs com zeros à esquerda `T{M+1:03d}, T{M+2:03d}, …`:

   ```markdown
   - [ ] T042 <imperative description> per <source-ref> (<gap-type>)
   ```

   `<source-ref>` rastreia a tarefa até sua origem: por exemplo, `FR-003`, `SC-002`,
   `US1/AC2`, `plan: storage decision`, `Constitution II`.

   `<gap-type>` é um entre `missing`, `partial`, `contradicts`, `unrequested`.

   Tarefas de violação da constituição DEVEM ser emitidas primeiro e descritas como
   `CRITICAL`.
4. Nunca reutilize ou renumere IDs existentes. Se já existir uma fase de Convergência
   anterior, adicione uma nova, numerada separadamente, abaixo dela — não toque na antiga.

**Se não houver achados acionáveis** (resultado `converged`):

- **Não** modifique `tasks.md` de forma alguma — sem cabeçalho de fase vazio.
- Relate: **"✅ Convergência concluída — a implementação satisfaz a especificação, o plano e as tarefas."**
- Inclua as contagens de resumo do que foi verificado.

### 8. Fornecer Próximas Ações (Transferência)

- Em `tasks_appended`: informe quantas tarefas foram adicionadas e sob qual fase, e recomende
  executar o `/speckit-implement` para concluí-las; observe que uma nova execução do converge
  encontrará menos itens restantes ou nenhum.
- Em `converged`: recomende prosseguir para a revisão / abertura de um PR. Nenhuma outra
  passagem do implement é necessária para o escopo especificado desta funcionalidade.

### 9. Verificar hooks de extensão

Depois de produzir o resultado, verifique se `.specify/extensions.yml` existe na raiz do projeto.

- Se existir, leia-o e procure entradas na chave `hooks.after_converge`
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue normalmente
- Filtre os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar expressões `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir um `condition` não vazio, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Relate o resultado da convergência (`converged` ou `tasks_appended`) na sessão antes de listar
  quaisquer hooks, para que os usuários possam decidir se executam comandos opcionais de acompanhamento.
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hifens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a saída a seguir conforme o seu flag `optional`:
  - **Hook opcional** (`optional: true`):

    ```text
    ## Hooks de Extensão

    **Hook Opcional**: {extension}
    Comando: `/{command}`
    Descrição: {description}

    Prompt: {prompt}
    Para executar: `/{command}`
    ```

  - **Hook obrigatório** (`optional: false`):

    ```text
    ## Hooks de Extensão

    **Hook Automático**: {extension}
    Executando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Depois de emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que você executaria o comando por conta própria neste agente/sessão (a invocação pode diferir do id literal `{command}` exibido acima, por exemplo, um agente em modo de skills o executa como `/skill:speckit-...` ou `$speckit-...`). Apenas emitir o bloco não executa o hook.

- Se nenhum hook estiver registrado ou `.specify/extensions.yml` não existir, ignore silenciosamente
