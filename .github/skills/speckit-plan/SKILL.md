---
name: "speckit-plan"
description: "Executa o fluxo de planejamento de implementação usando o template de plano para gerar os artefatos de design."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/plan.md"
---


## Entrada do Usuário

```text
$ARGUMENTS
```

Você **DEVE** considerar a entrada do usuário antes de prosseguir (se não estiver vazia).

## Verificações Pré-Execução

**Verifique hooks de extensão (antes do planejamento)**:
- Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas sob a chave `hooks.before_plan`
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue normalmente
- Descarte os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar expressões de `condition` do hook:
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

    Aguarde o resultado do comando do hook antes de prosseguir para o Resumo do Fluxo.
    ```
    Depois de emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que você executaria o comando nesta sessão/agente (a invocação pode diferir do id literal `{command}` mostrado acima; por exemplo, um agente em modo skills o executa como `/skill:speckit-...` ou `$speckit-...`). Emitir apenas o bloco não executa o hook.
- Se nenhum hook estiver registrado ou `.specify/extensions.yml` não existir, ignore silenciosamente

## Resumo do Fluxo

1. **Preparação**: Execute `.specify/scripts/bash/setup-plan.sh --json` a partir da raiz do repositório e interprete o JSON para obter FEATURE_SPEC, IMPL_PLAN, FEATURE_DIR, BRANCH. Para aspas simples em argumentos como "I'm Groot", use a sintaxe de escape: por exemplo 'I'\''m Groot' (ou aspas duplas, se possível: "I'm Groot").

2. **Carregar contexto**: Leia FEATURE_SPEC e `.specify/memory/constitution.md`. Carregue o template IMPL_PLAN (já copiado).

3. **Executar o fluxo do plano**: Siga a estrutura do template IMPL_PLAN para:
   - Preencher o Contexto Técnico (marque incógnitas como "PRECISA DE ESCLARECIMENTO")
   - Preencher a seção Verificação da Constituição a partir da constituição
   - Avaliar os portões (gates) (ERRO se houver violações sem justificativa)
   - Fase 0: Gerar research.md (resolver todos os PRECISA DE ESCLARECIMENTO)
   - Fase 1: Gerar data-model.md, contracts/, quickstart.md
   - Reavaliar a Verificação da Constituição após o design

## Hooks Obrigatórios Pós-Execução

**Você DEVE concluir esta seção antes de reportar a conclusão ao usuário.**

Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se não existir, ou se nenhum hook estiver registrado sob `hooks.after_plan`, vá direto para o Relatório de Conclusão.
- Se existir, leia-o e procure entradas sob a chave `hooks.after_plan`.
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue para o Relatório de Conclusão.
- Descarte os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar expressões de `condition` do hook:
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
    Depois de emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que você executaria o comando nesta sessão/agente (a invocação pode diferir do id literal `{command}` mostrado acima; por exemplo, um agente em modo skills o executa como `/skill:speckit-...` ou `$speckit-...`). Emitir apenas o bloco não executa o hook.
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

O comando termina após o design da Fase 1. Reporte o branch, o caminho de IMPL_PLAN e os artefatos gerados.

## Fases

### Fase 0: Esboço e Pesquisa

1. **Extraia as incógnitas do Contexto Técnico** acima:
   - Para cada PRECISA DE ESCLARECIMENTO → tarefa de pesquisa
   - Para cada dependência → tarefa de melhores práticas
   - Para cada integração → tarefa de padrões

2. **Gere e despache agentes de pesquisa**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolide os achados** em `research.md` usando o formato:
   - Decisão: [o que foi escolhido]
   - Justificativa: [por que foi escolhido]
   - Alternativas consideradas: [o que mais foi avaliado]

**Saída**: research.md com todos os PRECISA DE ESCLARECIMENTO resolvidos

### Fase 1: Design e Contratos

**Pré-requisitos:** `research.md` concluído

1. **Extraia as entidades da especificação da funcionalidade** → `data-model.md`:
   - Nome da entidade, campos, relacionamentos
   - Regras de validação derivadas dos requisitos
   - Transições de estado, se aplicável

2. **Defina os contratos de interface** (se o projeto tiver interfaces externas) → `/contracts/`:
   - Identifique quais interfaces o projeto expõe a usuários ou a outros sistemas
   - Documente o formato de contrato apropriado ao tipo de projeto
   - Exemplos: APIs públicas para bibliotecas, esquemas de comandos para ferramentas CLI, endpoints para serviços web, gramáticas para parsers, contratos de UI para aplicações
   - Ignore se o projeto for puramente interno (scripts de build, ferramentas pontuais etc.)

3. **Crie o guia de validação de início rápido** → `quickstart.md`:
   - Documente cenários de validação executáveis que provem que a funcionalidade funciona de ponta a ponta
   - Inclua pré-requisitos, comandos de preparação, comandos de teste/execução e resultados esperados
   - Use links ou referências aos contratos e aos detalhes do modelo de dados em vez de duplicá-los
   - Não inclua código completo de implementação, corpos de model/service/controller, migrações ou suítes de testes completas
   - Mantenha este artefato como um guia de validação/execução; detalhes de implementação pertencem a `tasks.md` e à fase de implementação

**Saída**: data-model.md, /contracts/*, quickstart.md

## Regras principais

- Use caminhos absolutos para operações no sistema de arquivos; use caminhos relativos ao projeto para referências na documentação
- ERRO em falhas de portão (gate) ou esclarecimentos não resolvidos

## Concluído Quando

- [ ] Fluxo do plano executado e artefatos de design gerados
- [ ] Hooks de extensão despachados ou ignorados conforme as regras em Hooks Obrigatórios Pós-Execução acima
- [ ] Conclusão reportada ao usuário com branch, caminho do plano e artefatos gerados
