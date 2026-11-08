---
name: "speckit-tasks"
description: "Gera um tasks.md acionável e ordenado por dependências para a funcionalidade, com base nos artefatos de design disponíveis."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/tasks.md"
---


## Entrada do Usuário

```text
$ARGUMENTS
```

Você **DEVE** considerar a entrada do usuário antes de prosseguir (se não estiver vazia).

## Verificações Pré-Execução

**Verifique a existência de hooks de extensão (antes da geração de tarefas)**:
- Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas na chave `hooks.before_tasks`
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue normalmente
- Filtre os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar expressões `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir um `condition` não vazio, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hifens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a saída a seguir conforme o seu flag `optional`:
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

    Aguarde o resultado do comando do hook antes de prosseguir para o Roteiro.
    ```
    Depois de emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que você executaria o comando por conta própria neste agente/sessão (a invocação pode diferir do id literal `{command}` exibido acima, por exemplo, um agente em modo de skills o executa como `/skill:speckit-...` ou `$speckit-...`). Apenas emitir o bloco não executa o hook.
- Se nenhum hook estiver registrado ou `.specify/extensions.yml` não existir, ignore silenciosamente

## Roteiro

1. **Preparação**: Execute `.specify/scripts/bash/setup-tasks.sh --json` a partir da raiz do repositório e interprete FEATURE_DIR, TASKS_TEMPLATE_CONTENT, TASKS_TEMPLATE e a lista AVAILABLE_DOCS. `FEATURE_DIR` e `TASKS_TEMPLATE` devem ser caminhos absolutos quando fornecidos. `AVAILABLE_DOCS` é uma lista de nomes/caminhos relativos de documentos disponíveis em `FEATURE_DIR` (por exemplo, `research.md` ou `contracts/`). Para aspas simples em argumentos como "I'm Groot", use a sintaxe de escape: por exemplo, 'I'\''m Groot' (ou aspas duplas, se possível: "I'm Groot").

2. **Carregar os documentos de design**: Leia de FEATURE_DIR:
   - **Obrigatórios**: plan.md (stack tecnológica, bibliotecas, estrutura), spec.md (histórias de usuário com prioridades)
   - **Opcionais**: data-model.md (entidades), contracts/ (contratos de interface), research.md (decisões), quickstart.md (cenários de teste)
   - **SE EXISTIR**: Carregue `.specify/memory/constitution.md` para os princípios do projeto e restrições de governança
   - Observação: Nem todos os projetos têm todos os documentos. Gere as tarefas com base no que estiver disponível.

3. **Executar o fluxo de geração de tarefas**:
   - Carregue plan.md e extraia a stack tecnológica, as bibliotecas e a estrutura do projeto
   - Carregue spec.md e extraia as histórias de usuário com suas prioridades (P1, P2, P3 etc.)
   - Se data-model.md existir: extraia as entidades e mapeie-as para as histórias de usuário
   - Se contracts/ existir: mapeie os contratos de interface para as histórias de usuário
   - Se research.md existir: extraia as decisões para as tarefas de preparação
   - Gere as tarefas organizadas por história de usuário (veja as Regras de Geração de Tarefas abaixo)
   - Gere o grafo de dependências mostrando a ordem de conclusão das histórias de usuário
   - Crie exemplos de execução paralela por história de usuário
   - Valide a completude das tarefas (cada história de usuário tem todas as tarefas necessárias e é testável de forma independente)

4. **Gerar tasks.md**: Use TASKS_TEMPLATE_CONTENT (da saída JSON acima) como estrutura. Para compatibilidade com scripts de preparação mais antigos que omitem TASKS_TEMPLATE_CONTENT, leia TASKS_TEMPLATE em seu lugar. Preencha com:
   - O nome correto da funcionalidade a partir de plan.md
   - Fase 1: tarefas de Preparação (inicialização do projeto)
   - Fase 2: tarefas Fundacionais (pré-requisitos bloqueantes para todas as histórias de usuário)
   - Fase 3+: uma fase por história de usuário (em ordem de prioridade de spec.md)
   - Cada fase inclui: objetivo da história, critérios de teste independente, testes (se solicitados), tarefas de implementação
   - Fase Final: Acabamento e preocupações transversais
   - Todas as tarefas devem seguir o formato rigoroso de checklist (veja as Regras de Geração de Tarefas abaixo)
   - Caminhos de arquivo claros para cada tarefa
   - Seção de Dependências mostrando a ordem de conclusão das histórias
   - Exemplos de execução paralela por história
   - Seção de estratégia de implementação (MVP primeiro, entrega incremental)

## Hooks Obrigatórios Pós-Execução

**Você DEVE concluir esta seção antes de relatar a conclusão ao usuário.**

Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se não existir, ou se nenhum hook estiver registrado em `hooks.after_tasks`, vá direto para o Relatório de Conclusão.
- Se existir, leia-o e procure entradas na chave `hooks.after_tasks`.
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue para o Relatório de Conclusão.
- Filtre os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar expressões `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir um `condition` não vazio, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hifens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a saída a seguir conforme o seu flag `optional`:
  - **Hook obrigatório** (`optional: false`) — **Você DEVE emitir `EXECUTE_COMMAND:` para cada hook obrigatório**:
    ```
    ## Hooks de Extensão

    **Hook Automático**: {extension}
    Executando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Depois de emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que você executaria o comando por conta própria neste agente/sessão (a invocação pode diferir do id literal `{command}` exibido acima, por exemplo, um agente em modo de skills o executa como `/skill:speckit-...` ou `$speckit-...`). Apenas emitir o bloco não executa o hook.
  - **Hook opcional** (`optional: true`):
    ```
    ## Hooks de Extensão

    **Hook Opcional**: {extension}
    Comando: `/{command}`
    Descrição: {description}

    Prompt: {prompt}
    Para executar: `/{command}`
    ```

## Relatório de Conclusão

Informe o caminho do tasks.md gerado e um resumo:
- Contagem total de tarefas
- Contagem de tarefas por história de usuário
- Oportunidades de paralelismo identificadas
- Critérios de teste independente de cada história
- Escopo de MVP sugerido (tipicamente apenas a História de Usuário 1)
- Validação de formato: confirme que TODAS as tarefas seguem o formato de checklist (caixa de seleção, ID, rótulos, caminhos de arquivo)

Contexto para a geração de tarefas: $ARGUMENTS

O tasks.md deve ser imediatamente executável — cada tarefa deve ser específica o bastante para que um LLM possa concluí-la sem contexto adicional.

## Regras de Geração de Tarefas

**CRÍTICO**: As tarefas DEVEM ser organizadas por história de usuário para permitir implementação e teste independentes.

**Testes são OPCIONAIS**: Gere tarefas de teste somente se solicitado explicitamente na especificação da funcionalidade ou se o usuário pedir a abordagem TDD.

### Formato de Checklist (OBRIGATÓRIO)

Toda tarefa DEVE seguir estritamente este formato:

```text
- [ ] [TaskID] [P?] [Story?] Descrição com caminho do arquivo
```

**Componentes do Formato**:

1. **Caixa de seleção**: SEMPRE comece com `- [ ]` (caixa de seleção markdown)
2. **ID da Tarefa**: número sequencial (T001, T002, T003...) na ordem de execução
3. **Marcador [P]**: inclua SOMENTE se a tarefa for paralelizável (arquivos diferentes, sem dependências de tarefas incompletas)
4. **Rótulo [Story]**: OBRIGATÓRIO somente para tarefas de fases de história de usuário
   - Formato: [US1], [US2], [US3] etc. (mapeia para as histórias de usuário de spec.md)
   - Fase de Preparação: SEM rótulo de história
   - Fase Fundacional: SEM rótulo de história
   - Fases de História de Usuário: DEVEM ter rótulo de história
   - Fase de Acabamento: SEM rótulo de história
5. **Descrição**: ação clara com o caminho exato do arquivo

**Exemplos**:

- ✅ CORRETO: `- [ ] T001 Criar a estrutura do projeto conforme o plano de implementação`
- ✅ CORRETO: `- [ ] T005 [P] Implementar o middleware de autenticação em src/middleware/auth.py`
- ✅ CORRETO: `- [ ] T012 [P] [US1] Criar o modelo User em src/models/user.py`
- ✅ CORRETO: `- [ ] T014 [US1] Implementar o UserService em src/services/user_service.py`
- ❌ ERRADO: `- [ ] Criar o modelo User` (falta o ID e o rótulo de história)
- ❌ ERRADO: `T001 [US1] Criar o modelo` (falta a caixa de seleção)
- ❌ ERRADO: `- [ ] [US1] Criar o modelo User` (falta o ID da tarefa)
- ❌ ERRADO: `- [ ] T001 [US1] Criar o modelo` (falta o caminho do arquivo)

### Organização das Tarefas

1. **A partir das Histórias de Usuário (spec.md)** - ORGANIZAÇÃO PRINCIPAL:
   - Cada história de usuário (P1, P2, P3...) recebe sua própria fase
   - Mapeie todos os componentes relacionados à sua história:
     - Modelos necessários para essa história
     - Serviços necessários para essa história
     - Interfaces/UI necessárias para essa história
     - Se testes forem solicitados: testes específicos dessa história
   - Marque as dependências entre histórias (a maioria das histórias deve ser independente)

2. **A partir dos Contratos**:
   - Mapeie cada contrato de interface → para a história de usuário que ele atende
   - Se testes forem solicitados: cada contrato de interface → tarefa de teste de contrato [P] antes da implementação na fase dessa história

3. **A partir do Modelo de Dados**:
   - Mapeie cada entidade para a(s) história(s) de usuário que a necessitam
   - Se a entidade atender a várias histórias: coloque-a na primeira história ou na fase de Preparação
   - Relacionamentos → tarefas da camada de serviço na fase de história apropriada
   - Para cada campo com restrições em data-model.md (tamanho máximo, nulável/obrigatório, valores de enum, regras de validação), cite a restrição literalmente na descrição da tarefa para que ela não fique a critério do momento da implementação

4. **A partir da Preparação/Infraestrutura**:
   - Infraestrutura compartilhada → fase de Preparação (Fase 1)
   - Tarefas fundacionais/bloqueantes → fase Fundacional (Fase 2)
   - Preparação específica de uma história → dentro da fase dessa história

### Estrutura das Fases

- **Fase 1**: Preparação (inicialização do projeto)
- **Fase 2**: Fundacional (pré-requisitos bloqueantes — DEVEM ser concluídos antes das histórias de usuário)
- **Fase 3+**: Histórias de Usuário em ordem de prioridade (P1, P2, P3...)
  - Dentro de cada história: Testes (se solicitados) → Modelos → Serviços → Endpoints → Integração
  - Cada fase deve ser um incremento completo e testável de forma independente
- **Fase Final**: Acabamento e Preocupações Transversais

## Concluído Quando

- [ ] tasks.md gerado com todas as fases, IDs de tarefas e caminhos de arquivos
- [ ] Hooks de extensão despachados ou ignorados conforme as regras em Hooks Obrigatórios Pós-Execução acima
- [ ] Conclusão relatada ao usuário com a contagem de tarefas, o detalhamento por história e o escopo de MVP
