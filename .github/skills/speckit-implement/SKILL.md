---
name: "speckit-implement"
description: "Executa o plano de implementação processando e executando todas as tarefas definidas em tasks.md"
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/implement.md"
---


## Entrada do Usuário

```text
$ARGUMENTS
```

Você **DEVE** considerar a entrada do usuário antes de prosseguir (se não estiver vazia).

## Verificações Pré-Execução

**Verifique a existência de hooks de extensão (antes da implementação)**:
- Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas na chave `hooks.before_implement`
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

1. Execute `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` a partir da raiz do repositório e interprete FEATURE_DIR e a lista AVAILABLE_DOCS. Todos os caminhos devem ser absolutos. Para aspas simples em argumentos como "I'm Groot", use a sintaxe de escape: por exemplo, 'I'\''m Groot' (ou aspas duplas, se possível: "I'm Groot").

2. **Verifique o status dos checklists** (se FEATURE_DIR/checklists/ existir):
   - Trate os marcadores dos checklists como um portão (gate) somente leitura: examine o estado das caixas de seleção, relate o status e pergunte antes de prosseguir quando necessário; NÃO modifique arquivos ou marcadores de checklist
   - `checklists/requirements.md` é o checklist interno de qualidade da especificação mantido por `/speckit-specify` e `/speckit-clarify`; checklists personalizados gerados por `/speckit-checklist` são artefatos de revisão de qualidade de requisitos pertencentes ao revisor
   - Em checklists personalizados, `[x]` significa que o revisor determinou que o critério de qualidade de requisitos foi satisfeito; NÃO significa que o trabalho de implementação está concluído
   - Examine todos os arquivos de checklist no diretório checklists/
   - Para cada checklist, conte:
     - Total de itens: todas as linhas que correspondem a `- [ ]` ou `- [X]` ou `- [x]`
     - Itens marcados: linhas que correspondem a `- [X]` ou `- [x]`
     - Itens desmarcados: linhas que correspondem a `- [ ]`
   - Crie uma tabela de status:

     ```text
     | Checklist | Total | Marcados | Desmarcados | Status |
     |-----------|-------|----------|-------------|--------|
     | ux.md     | 12    | 12       | 0           | ✓ APROVADO |
     | test.md   | 8     | 5        | 3           | ✗ REPROVADO |
     | security.md | 6   | 6        | 0           | ✓ APROVADO |
     ```

   - Calcule o status geral:
     - **APROVADO**: todos os checklists têm 0 itens desmarcados
     - **REPROVADO**: um ou mais checklists têm itens desmarcados

   - **Se algum checklist tiver itens desmarcados**:
     - Exiba a tabela com as contagens de itens desmarcados
     - **PARE** e pergunte: "Alguns checklists têm itens desmarcados. Deseja prosseguir com a implementação mesmo assim? (sim/não)"
     - Aguarde a resposta do usuário antes de continuar
     - Se o usuário disser "não", "espere" ou "pare" (ou "no", "wait", "stop"), interrompa a execução
     - Se o usuário disser "sim", "prossiga" ou "continue" (ou "yes", "proceed", "continue"), prossiga para a etapa 3

   - **Se todos os checklists estiverem marcados**:
     - Exiba a tabela mostrando que todos os checklists foram aprovados
     - Prossiga automaticamente para a etapa 3

3. Carregue e analise o contexto de implementação:
   - **OBRIGATÓRIO**: Leia tasks.md para a lista completa de tarefas e o plano de execução
   - **OBRIGATÓRIO**: Leia plan.md para a stack tecnológica, a arquitetura e a estrutura de arquivos
   - **SE EXISTIR**: Leia data-model.md para entidades e relacionamentos
   - **SE EXISTIR**: Leia contracts/ para especificações de API e requisitos de teste
   - **SE EXISTIR**: Leia research.md para decisões técnicas e restrições
   - **SE EXISTIR**: Leia .specify/memory/constitution.md para restrições de governança
   - **SE EXISTIR**: Leia quickstart.md para cenários de integração

4. **Verificação da Preparação do Projeto**:
   - **OBRIGATÓRIO**: Crie/verifique arquivos de ignore com base na configuração real do projeto:

   **Lógica de Detecção e Criação**:
   - Verifique se o comando a seguir tem sucesso para determinar se o repositório é um repositório git (crie/verifique .gitignore em caso afirmativo):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Verifique se Dockerfile* existe ou se há Docker em plan.md → crie/verifique .dockerignore
   - Verifique se .eslintrc* existe → crie/verifique .eslintignore
   - Verifique se eslint.config.* existe → garanta que as entradas `ignores` da configuração cubram os padrões necessários
   - Verifique se .prettierrc* existe → crie/verifique .prettierignore
   - Verifique se .npmrc ou package.json existe → crie/verifique .npmignore (se for publicar)
   - Verifique se existem arquivos terraform (*.tf) → crie/verifique .terraformignore
   - Verifique se .helmignore é necessário (charts helm presentes) → crie/verifique .helmignore

   **Se o arquivo de ignore já existir**: Verifique se contém os padrões essenciais; acrescente apenas os padrões críticos ausentes
   **Se o arquivo de ignore estiver ausente**: Crie-o com o conjunto completo de padrões para a tecnologia detectada

   **Padrões Comuns por Tecnologia** (da stack tecnológica de plan.md):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `*.dll`, `autom4te.cache/`, `config.status`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Padrões Específicos de Ferramentas**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. Interprete a estrutura de tasks.md e extraia:
   - **Fases das tarefas**: Preparação, Testes, Núcleo, Integração, Acabamento
   - **Dependências das tarefas**: regras de execução sequencial vs paralela
   - **Detalhes das tarefas**: ID, descrição, caminhos de arquivos, marcadores de paralelismo [P]
   - **Fluxo de execução**: requisitos de ordem e dependência

6. Execute a implementação seguindo o plano de tarefas:
   - **Execução fase a fase**: conclua cada fase antes de passar para a próxima
   - **Respeite as dependências**: execute as tarefas sequenciais em ordem; as tarefas paralelas [P] podem ser executadas juntas
   - **Siga a abordagem TDD**: execute as tarefas de teste antes das tarefas de implementação correspondentes
   - **Coordenação baseada em arquivos**: tarefas que afetam os mesmos arquivos devem ser executadas sequencialmente
   - **Pontos de validação**: verifique a conclusão de cada fase antes de prosseguir

7. Regras de execução da implementação:
   - **Preparação primeiro**: inicialize a estrutura do projeto, as dependências e a configuração
   - **Testes antes do código**: se você precisar escrever testes para contratos, entidades e cenários de integração
   - **Desenvolvimento do núcleo**: implemente modelos, serviços, comandos de CLI, endpoints
   - **Trabalho de integração**: conexões com banco de dados, middleware, logging, serviços externos
   - **Acabamento e validação**: testes unitários, otimização de desempenho, documentação

8. Acompanhamento de progresso e tratamento de erros:
   - Relate o progresso após cada tarefa concluída
   - Interrompa a execução se qualquer tarefa não paralela falhar
   - Para tarefas paralelas [P], continue com as bem-sucedidas e relate as que falharam
   - Forneça mensagens de erro claras com contexto para depuração
   - Sugira os próximos passos se a implementação não puder prosseguir
   - **IMPORTANTE** Para as tarefas concluídas, certifique-se de marcá-las como [X] no arquivo de tarefas.

9. Validação da conclusão:
   - Verifique se todas as tarefas necessárias foram concluídas
   - Confira se as funcionalidades implementadas correspondem à especificação original
   - Valide se os testes passam e se a cobertura atende aos requisitos
   - Confirme se a implementação segue o plano técnico

Observação: Este comando pressupõe que exista um detalhamento completo de tarefas em tasks.md. Se as tarefas estiverem incompletas ou ausentes, sugira executar `/speckit-tasks` primeiro para regenerar a lista de tarefas.

## Hooks Obrigatórios Pós-Execução

**Você DEVE concluir esta seção antes de relatar a conclusão ao usuário.**

Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se não existir, ou se nenhum hook estiver registrado em `hooks.after_implement`, vá direto para o Relatório de Conclusão.
- Se existir, leia-o e procure entradas na chave `hooks.after_implement`.
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

Relate o status final com um resumo do trabalho concluído.

## Concluído Quando

- [ ] Todas as tarefas em tasks.md concluídas e marcadas como `[X]`
- [ ] Implementação validada em relação à especificação, ao plano e à cobertura de testes
- [ ] Hooks de extensão despachados ou ignorados conforme as regras em Hooks Obrigatórios Pós-Execução acima
- [ ] Conclusão relatada ao usuário com um resumo do trabalho concluído
