---
name: "speckit-specify"
description: "Cria ou atualiza a especificação da funcionalidade a partir de uma descrição em linguagem natural."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/specify.md"
---


## Entrada do Usuário

```text
$ARGUMENTS
```

Você **DEVE** considerar a entrada do usuário antes de prosseguir (se não estiver vazia).

## Verificações Pré-Execução

**Verifique hooks de extensão (antes da especificação)**:
- Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas sob a chave `hooks.before_specify`
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

O texto que o usuário digitou após `/speckit-specify` na mensagem que disparou o comando **é** a descrição da funcionalidade. Presuma que você sempre a tem disponível nesta conversa, mesmo que `$ARGUMENTS` apareça literalmente abaixo. Não peça ao usuário para repeti-la, a menos que ele tenha fornecido um comando vazio.

Dada essa descrição da funcionalidade, faça o seguinte:

1. **Gere um nome curto e conciso** (2-4 palavras) para a funcionalidade:
   - Analise a descrição da funcionalidade e extraia as palavras-chave mais significativas
   - Crie um nome curto de 2-4 palavras que capture a essência da funcionalidade
   - Use o formato ação-substantivo quando possível (ex.: "adicionar-autenticacao", "corrigir-bug-pagamento")
   - Preserve termos técnicos e siglas (OAuth2, API, JWT etc.)
   - Mantenha-o conciso, mas descritivo o bastante para entender a funcionalidade num relance
   - Exemplos:
     - "Quero adicionar autenticação de usuário" → "autenticacao-usuario"
     - "Implementar integração OAuth2 para a API" → "integracao-oauth2-api"
     - "Criar um dashboard de análises" → "dashboard-analises"
     - "Corrigir bug de timeout no processamento de pagamento" → "corrigir-timeout-pagamento"

2. **Criação do branch** (opcional, via hook):

   Se um hook `before_specify` foi executado com sucesso nas Verificações Pré-Execução acima, ele terá criado/trocado para um branch git e produzido um JSON contendo `BRANCH_NAME` e `FEATURE_NUM`. Anote esses valores para referência, mas o nome do branch **não** dita o nome do diretório da especificação.

   Se o usuário forneceu explicitamente `GIT_BRANCH_NAME`, repasse-o ao hook para que o script de branch use exatamente esse valor como nome do branch (ignorando toda geração de prefixo/sufixo).

3. **Crie o diretório da especificação da funcionalidade**:

   As especificações ficam no diretório padrão `specs/`, a menos que o usuário forneça explicitamente `SPECIFY_FEATURE_DIRECTORY`.

   **Ordem de resolução de `SPECIFY_FEATURE_DIRECTORY`**:
   1. Se o usuário forneceu explicitamente `SPECIFY_FEATURE_DIRECTORY` (por exemplo, via variável de ambiente, argumento ou configuração), use-o como está
   2. Caso contrário, gere-o automaticamente sob `specs/`:
      - Verifique `.specify/init-options.json` em busca de `feature_numbering` (preferido) ou `branch_numbering` (obsoleto, apenas para migração — será removido em uma versão futura)
      - Se `"timestamp"`: o prefixo é `YYYYMMDD-HHMMSS` (timestamp atual)
      - Se `"sequential"` ou ausente: o prefixo é `NNN` (próximo número de 3 dígitos disponível após examinar os diretórios existentes em `specs/`)
      - Construa o nome do diretório: `<prefix>-<short-name>` (ex.: `003-user-auth` ou `20260319-143022-user-auth`)
      - Defina `SPECIFY_FEATURE_DIRECTORY` como `specs/<directory-name>`
      - Se `branch_numbering` foi usado (e `feature_numbering` estava ausente), emita um aviso de uma linha: "⚠️ `branch_numbering` em init-options.json está obsoleto. Renomeie para `feature_numbering`."

   **Crie o diretório e o arquivo da especificação**:
   - Execute `.specify/scripts/bash/resolve-template.sh spec-template --json` a partir da raiz do repositório e interprete `TEMPLATE_CONTENT` como o `spec-template` ativo. O resolvedor compartilhado compõe sobrescritas do projeto, camadas de presets e camadas de extensões sobre o template base, incluindo as estratégias `append`, `prepend` e `wrap`. Se falhar, pare e reporte o erro de resolução; não continue com apenas uma das camadas de template contribuintes.
   - `mkdir -p SPECIFY_FEATURE_DIRECTORY`
   - Escreva `TEMPLATE_CONTENT` em `SPECIFY_FEATURE_DIRECTORY/spec.md` como ponto de partida. Não copie um arquivo de template do disco no lugar disso: quando um preset compõe `spec-template`, nenhum arquivo único contém o template completo.
   - Defina `SPEC_FILE` como `SPECIFY_FEATURE_DIRECTORY/spec.md`
   - Persista o caminho resolvido em `.specify/feature.json`:
     ```json
     {
       "feature_directory": "<resolved feature dir>"
     }
     ```
     Escreva o valor real do caminho do diretório resolvido (por exemplo, `specs/003-user-auth`), não a string literal `SPECIFY_FEATURE_DIRECTORY`.
     Isso permite que comandos subsequentes (`/speckit-plan`, `/speckit-tasks` etc.) localizem o diretório da funcionalidade sem depender de convenções de nome de branch git.

   **IMPORTANTE**:
   - Você deve criar apenas uma funcionalidade por invocação de `/speckit-specify`
   - O nome do diretório da especificação e o nome do branch git são independentes — podem ser iguais, mas isso é escolha do usuário
   - O diretório e o arquivo da especificação são sempre criados por este comando, nunca pelo hook

4. Use `TEMPLATE_CONTENT` para entender as seções obrigatórias.

5. **SE EXISTIR**: Carregue `.specify/memory/constitution.md` para os princípios do projeto e restrições de governança.

6. Siga este fluxo de execução:
    1. Interprete a descrição do usuário a partir dos argumentos
       Se vazia: ERRO "Nenhuma descrição de funcionalidade fornecida"
    2. Extraia os conceitos-chave da descrição
       Identifique: atores, ações, dados, restrições
    3. Para aspectos pouco claros:
       - Faça suposições fundamentadas com base no contexto e nos padrões do mercado
       - Marque com [PRECISA DE ESCLARECIMENTO: pergunta específica] somente se:
         - A escolha impacta significativamente o escopo da funcionalidade ou a experiência do usuário
         - Existem múltiplas interpretações razoáveis com implicações diferentes
         - Não existe um padrão razoável
       - **LIMITE: no máximo 3 marcadores [PRECISA DE ESCLARECIMENTO] no total**
       - Priorize os esclarecimentos por impacto: escopo > segurança/privacidade > experiência do usuário > detalhes técnicos
    4. Preencha a seção Cenários de Usuário e Testes
       Se não houver fluxo de usuário claro: ERRO "Não foi possível determinar os cenários de usuário"
    5. Gere os Requisitos Funcionais
       Cada requisito deve ser testável
       Use padrões razoáveis para detalhes não especificados (documente as premissas na seção Premissas)
    6. Defina os Critérios de Sucesso
       Crie resultados mensuráveis e agnósticos de tecnologia
       Inclua métricas quantitativas (tempo, desempenho, volume) e medidas qualitativas (satisfação do usuário, conclusão de tarefas)
       Cada critério deve ser verificável sem detalhes de implementação
    7. Identifique as Entidades-Chave (se houver dados envolvidos)
    8. Retorne: SUCESSO (especificação pronta para o planejamento)

7. Escreva a especificação em SPEC_FILE usando a estrutura do template, substituindo os placeholders por detalhes concretos derivados da descrição da funcionalidade (argumentos) e preservando a ordem e os títulos das seções.

8. **Validação de Qualidade da Especificação**: Após escrever a especificação inicial, valide-a contra os critérios de qualidade:

   a. **Crie o Checklist de Qualidade da Especificação**: Gere um arquivo de checklist em `SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md` usando a estrutura do template de checklist com estes itens de validação:

      ```markdown
      # Checklist de Qualidade da Especificação: [NOME DA FUNCIONALIDADE]

      **Propósito**: Validar a completude e a qualidade da especificação antes de prosseguir para o planejamento
      **Criado em**: [DATA]
      **Funcionalidade**: [Link para spec.md]

      ## Qualidade do Conteúdo

      - [ ] Sem detalhes de implementação (linguagens, frameworks, APIs)
      - [ ] Focada no valor para o usuário e nas necessidades do negócio
      - [ ] Escrita para stakeholders não técnicos
      - [ ] Todas as seções obrigatórias preenchidas

      ## Completude dos Requisitos

      - [ ] Nenhum marcador [PRECISA DE ESCLARECIMENTO] permanece
      - [ ] Requisitos são testáveis e não ambíguos
      - [ ] Critérios de sucesso são mensuráveis
      - [ ] Critérios de sucesso são agnósticos de tecnologia (sem detalhes de implementação)
      - [ ] Todos os cenários de aceitação estão definidos
      - [ ] Casos de borda estão identificados
      - [ ] O escopo está claramente delimitado
      - [ ] Dependências e premissas estão identificadas

      ## Prontidão da Funcionalidade

      - [ ] Todos os requisitos funcionais têm critérios de aceitação claros
      - [ ] Os cenários de usuário cobrem os fluxos principais
      - [ ] A funcionalidade atende aos resultados mensuráveis definidos nos Critérios de Sucesso
      - [ ] Nenhum detalhe de implementação vaza para a especificação

      ## Notas

      - Itens marcados como incompletos exigem atualização da especificação antes de `/speckit-clarify` ou `/speckit-plan`
      ```

   b. **Execute a Verificação de Validação**: Revise a especificação contra cada item do checklist:
      - Para cada item, determine se passa ou falha
      - Documente os problemas específicos encontrados (cite as seções relevantes da especificação)

   c. **Trate os Resultados da Validação**:

      - **Se todos os itens passarem**: Marque o checklist como completo e prossiga para a seção Hooks Obrigatórios Pós-Execução

      - **Se itens falharem (excluindo [PRECISA DE ESCLARECIMENTO])**:
        1. Liste os itens que falharam e os problemas específicos
        2. Atualize a especificação para tratar cada problema
        3. Reexecute a validação até que todos os itens passem (máx. 3 iterações)
        4. Se ainda falhar após 3 iterações, documente os problemas restantes nas notas do checklist e avise o usuário

      - **Se marcadores [PRECISA DE ESCLARECIMENTO] permanecerem**:
        1. Extraia todos os marcadores [PRECISA DE ESCLARECIMENTO: ...] da especificação
        2. **VERIFICAÇÃO DE LIMITE**: Se existirem mais de 3 marcadores, mantenha apenas os 3 mais críticos (por impacto em escopo/segurança/UX) e faça suposições fundamentadas para o restante
        3. Para cada esclarecimento necessário (máx. 3), apresente opções ao usuário neste formato:

           ```markdown
           ## Pergunta [N]: [Tópico]

           **Contexto**: [Cite a seção relevante da especificação]

           **O que precisamos saber**: [Pergunta específica do marcador PRECISA DE ESCLARECIMENTO]

           **Respostas Sugeridas**:

           | Opção | Resposta | Implicações |
           |--------|--------|--------------|
           | A      | [Primeira resposta sugerida] | [O que isso significa para a funcionalidade] |
           | B      | [Segunda resposta sugerida] | [O que isso significa para a funcionalidade] |
           | C      | [Terceira resposta sugerida] | [O que isso significa para a funcionalidade] |
           | Personalizada | Forneça sua própria resposta | [Explique como fornecer uma resposta personalizada] |

           **Sua escolha**: _[Aguarde a resposta do usuário]_
           ```

        4. **CRÍTICO - Formatação de Tabelas**: Garanta que as tabelas markdown estejam formatadas corretamente:
           - Use espaçamento consistente com os pipes alinhados
           - Cada célula deve ter espaços ao redor do conteúdo: `| Conteúdo |` e não `|Conteúdo|`
           - O separador do cabeçalho deve ter pelo menos 3 hifens: `|--------|`
           - Teste se a tabela é renderizada corretamente na pré-visualização markdown
        5. Numere as perguntas sequencialmente (Q1, Q2, Q3 - máx. 3 no total)
        6. Apresente todas as perguntas juntas antes de aguardar as respostas
        7. Aguarde o usuário responder com suas escolhas para todas as perguntas (ex.: "Q1: A, Q2: Personalizada - [detalhes], Q3: B")
        8. Atualize a especificação substituindo cada marcador [PRECISA DE ESCLARECIMENTO] pela resposta escolhida ou fornecida pelo usuário
        9. Reexecute a validação depois que todos os esclarecimentos forem resolvidos

   d. **Atualize o Checklist**: Após cada iteração de validação, atualize o arquivo de checklist com o status atual de aprovado/reprovado

## Hooks Obrigatórios Pós-Execução

**Você DEVE concluir esta seção antes de reportar a conclusão ao usuário.**

Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se não existir, ou se nenhum hook estiver registrado sob `hooks.after_specify`, vá direto para o Relatório de Conclusão.
- Se existir, leia-o e procure entradas sob a chave `hooks.after_specify`.
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

Reporte a conclusão ao usuário com:
- `SPECIFY_FEATURE_DIRECTORY` — o caminho do diretório da funcionalidade
- `SPEC_FILE` — o caminho do arquivo da especificação
- Resumo dos resultados do checklist
- Prontidão para a próxima fase (`/speckit-clarify` ou `/speckit-plan`)

**NOTA:** A criação do branch é tratada pelo hook `before_specify` (extensão git). A criação do diretório e do arquivo da especificação é sempre tratada por este comando principal.

## Diretrizes Rápidas

- Foque no **O QUÊ** os usuários precisam e **POR QUÊ**.
- Evite o COMO implementar (sem stack tecnológica, APIs, estrutura de código).
- Escrita para stakeholders de negócio, não para desenvolvedores.
- NÃO crie checklists embutidos na especificação. Isso será um comando separado.

### Requisitos das Seções

- **Seções obrigatórias**: Devem ser preenchidas para toda funcionalidade
- **Seções opcionais**: Inclua apenas quando relevantes para a funcionalidade
- Quando uma seção não se aplica, remova-a por completo (não deixe como "N/A")

### Para Geração por IA

Ao criar esta especificação a partir de um prompt do usuário:

1. **Faça suposições fundamentadas**: Use contexto, padrões do mercado e padrões comuns para preencher lacunas
2. **Documente as premissas**: Registre padrões razoáveis na seção Premissas
3. **Limite os esclarecimentos**: No máximo 3 marcadores [PRECISA DE ESCLARECIMENTO] — use apenas para decisões críticas que:
   - Impactam significativamente o escopo da funcionalidade ou a experiência do usuário
   - Têm múltiplas interpretações razoáveis com implicações diferentes
   - Não têm nenhum padrão razoável
4. **Priorize os esclarecimentos**: escopo > segurança/privacidade > experiência do usuário > detalhes técnicos
5. **Pense como um testador**: Todo requisito vago deve falhar no item de checklist "testável e não ambíguo"
6. **Áreas comuns que precisam de esclarecimento** (somente se não houver padrão razoável):
   - Escopo e limites da funcionalidade (incluir/excluir casos de uso específicos)
   - Tipos de usuário e permissões (se houver múltiplas interpretações conflitantes)
   - Requisitos de segurança/conformidade (quando legal/financeiramente significativos)

**Exemplos de padrões razoáveis** (não pergunte sobre estes):

- Retenção de dados: práticas padrão do mercado para o domínio
- Metas de desempenho: expectativas padrão de aplicações web/mobile, salvo indicação em contrário
- Tratamento de erros: mensagens amigáveis ao usuário com alternativas apropriadas
- Método de autenticação: baseado em sessão padrão ou OAuth2 para aplicações web
- Padrões de integração: use padrões apropriados ao projeto (REST/GraphQL para serviços web, chamadas de função para bibliotecas, argumentos de CLI para ferramentas etc.)

### Diretrizes para Critérios de Sucesso

Os critérios de sucesso devem ser:

1. **Mensuráveis**: Incluir métricas específicas (tempo, porcentagem, contagem, taxa)
2. **Agnósticos de tecnologia**: Sem menção a frameworks, linguagens, bancos de dados ou ferramentas
3. **Focados no usuário**: Descrever resultados da perspectiva do usuário/negócio, não de internos do sistema
4. **Verificáveis**: Podem ser testados/validados sem conhecer detalhes de implementação

**Bons exemplos**:

- "Usuários conseguem concluir a compra em menos de 3 minutos"
- "O sistema suporta 10.000 usuários simultâneos"
- "95% das buscas retornam resultados em menos de 1 segundo"
- "A taxa de conclusão de tarefas melhora em 40%"

**Maus exemplos** (focados em implementação):

- "O tempo de resposta da API é inferior a 200ms" (técnico demais, use "Usuários veem os resultados instantaneamente")
- "O banco de dados suporta 1000 TPS" (detalhe de implementação, use uma métrica voltada ao usuário)
- "Componentes React renderizam de forma eficiente" (específico de framework)
- "A taxa de acerto do cache Redis acima de 80%" (específico de tecnologia)

## Concluído Quando

- [ ] Especificação escrita em `SPEC_FILE` e validada contra o checklist de qualidade
- [ ] Hooks de extensão despachados ou ignorados conforme as regras em Hooks Obrigatórios Pós-Execução acima
- [ ] Conclusão reportada ao usuário com o diretório da funcionalidade, o caminho do arquivo da especificação e os resultados do checklist
