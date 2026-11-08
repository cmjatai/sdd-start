---
name: "speckit-constitution"
description: "Cria ou atualiza a constituição do projeto a partir de princípios informados de forma interativa ou fornecidos pelo usuário."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/constitution.md"
---


## Entrada do Usuário

```text
$ARGUMENTS
```

Você **DEVE** considerar a entrada do usuário antes de prosseguir (se não estiver vazia).

## Proteção de Escopo

O trabalho deste comando se limita a atualizar a própria constituição do projeto. Templates e comandos
dependentes leem a constituição em tempo de execução e não são modificados aqui.

- Classifique cada parte da entrada do usuário como conteúdo da constituição ou como uma intenção
  separada, não relacionada à governança.
- Se a entrada incluir pedidos de implementação de funcionalidade, geração de código, refatoração,
  build ou deploy, você **NÃO DEVE** executá-los. Extraia-os como intenções adiadas.
- Você **NÃO DEVE** criar, modificar ou excluir arquivos de código-fonte da aplicação, rotas de
  funcionalidades, componentes, testes, arquivos de deploy ou outros artefatos não relacionados ao
  fluxo de trabalho da constituição.
- Se não estiver claro se uma instrução é conteúdo da constituição, peça esclarecimento antes de
  fazer qualquer alteração.
- Após concluir a atualização da constituição, inclua uma seção `Próximas Ações` para cada intenção
  adiada. Liste a intenção original e sugira o comando de acompanhamento apropriado do Spec Kit,
  como `/speckit-specify`, sem invocá-lo.
- Se não houver intenções não relacionadas à governança, omita a seção `Próximas Ações`.

## Verificações Pré-Execução

**Verifique se há hooks de extensão (antes da atualização da constituição)**:
- Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas sob a chave `hooks.before_constitution`
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue normalmente
- Ignore os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar as expressões de `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir uma `condition` não vazia, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hífens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a saída a seguir de acordo com o flag `optional`:
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

    Aguarde o resultado do comando do hook antes de prosseguir para o Esboço.
    ```
    Após emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que executaria o comando por conta própria neste agente/sessão (a invocação pode diferir do id literal `{command}` mostrado acima, por exemplo, um agente em modo skills o executa como `/skill:speckit-...` ou `$speckit-...`). Apenas emitir o bloco não executa o hook.
- Se nenhum hook estiver registrado ou `.specify/extensions.yml` não existir, ignore silenciosamente

## Esboço

Você está atualizando a constituição do projeto em `.specify/memory/constitution.md`. O scaffold ativo
da constituição é resolvido em tempo de execução a partir de `constitution-template` por meio da
pilha de resolução de presets/templates do Spec Kit.

Siga este fluxo de execução:

1. Execute `.specify/scripts/bash/resolve-template.sh constitution-template --json` a partir da raiz do repositório e interprete `TEMPLATE_CONTENT` como o template ativo.
   - O resolvedor compartilhado aplica as sobreposições do projeto, as camadas de presets de composição e as camadas de extensões
     antes do fallback para o template principal. Ele DEVE ter sucesso antes de continuar.
   - Se falhar, pare e relate o erro de resolução; não continue com apenas uma camada de
     template contribuinte.
   - Se `.specify/memory/constitution.md` existir, carregue-o como fonte dos valores e emendas
     atuais específicos do projeto. Preserve as informações que ainda são aplicáveis ao aplicar o
     scaffold recém-resolvido.
   - Se não existir, use o template resolvido como documento inicial.
   - Não grave de volta em nenhuma camada de template versionada.
   - Identifique todo token de placeholder no formato `[IDENTIFICADOR_EM_MAIUSCULAS]`.
   **IMPORTANTE**: O usuário pode querer menos ou mais princípios do que os usados no template. Se um número for especificado, respeite-o - siga o template geral. Você atualizará o documento de acordo.

2. Colete/derive os valores dos placeholders:
   - Se a entrada do usuário (conversa) fornecer um valor, use-o.
   - Caso contrário, infira a partir do contexto existente do repositório (README, docs, versões anteriores da constituição, se embutidas).
   - Para datas de governança: `RATIFICATION_DATE` é a data original de adoção (se desconhecida, pergunte ou marque como TODO), `LAST_AMENDED_DATE` é hoje se houver alterações, caso contrário mantenha a anterior.
   - `CONSTITUTION_VERSION` deve ser incrementada de acordo com as regras de versionamento semântico:
     - MAJOR: remoções ou redefinições de governança/princípios incompatíveis com versões anteriores.
     - MINOR: novo princípio/seção adicionado ou orientação materialmente expandida.
     - PATCH: esclarecimentos, redação, correções de erros de digitação, refinamentos não semânticos.
   - Se o tipo de incremento de versão for ambíguo, proponha o raciocínio antes de finalizar.

3. Redija o conteúdo atualizado da constituição usando o template resolvido como a estrutura obrigatória:
   - Substitua todo placeholder por texto concreto (nenhum token entre colchetes deve permanecer, exceto slots do template intencionalmente mantidos porque o projeto optou por ainda não defini-los—justifique explicitamente qualquer um deixado).
   - Preserve a hierarquia de títulos; os comentários podem ser removidos depois de substituídos, a menos que ainda agreguem orientação esclarecedora.
   - Garanta que cada seção de Princípio tenha: uma linha de nome sucinta, um parágrafo (ou lista de marcadores) com as regras inegociáveis e uma justificativa explícita se não for óbvia.
   - Garanta que a seção de Governança liste o procedimento de emenda, a política de versionamento e as expectativas de revisão de conformidade.

4. Produza um Relatório de Impacto da Sincronização como comentário HTML no topo do arquivo da constituição após a atualização.
   Este relatório é material de rascunho temporário para revisão humana da emenda, não conteúdo
   de governança; espera-se que seja removido antes de o arquivo da constituição emendada ser commitado.
   - Mudança de versão: antiga → nova
   - Lista de princípios modificados (título antigo → título novo, se renomeado)
   - Seções adicionadas
   - Seções removidas
   - TODOs de acompanhamento, se algum placeholder foi intencionalmente adiado.

5. Validação antes da saída final:
   - Nenhum token entre colchetes sem explicação deve permanecer.
   - A linha de versão corresponde ao relatório.
   - Datas em formato ISO YYYY-MM-DD.
   - Os princípios são declarativos, testáveis e livres de linguagem vaga ("deveria" → substituir por DEVE/DEVERIA com justificativa, quando apropriado).

6. Grave a constituição concluída de volta em `.specify/memory/constitution.md` (sobrescrevendo).

7. Produza um resumo final para o usuário com:
   - Nova versão e justificativa do incremento.
   - Quaisquer placeholders TODO ou itens adiados que exijam acompanhamento manual.
   - Mensagem de commit sugerida (por exemplo, `docs: amend constitution to vX.Y.Z (principle additions + governance update)`).
   - Uma seção `Próximas Ações` para quaisquer intenções adiadas não relacionadas à governança.

Requisitos de Formatação e Estilo:

- Use os títulos Markdown exatamente como no template (não rebaixe/promova níveis).
- Quebre linhas longas de justificativa para manter a legibilidade (<100 caracteres idealmente), mas sem impor quebras artificiais.
- Mantenha uma única linha em branco entre as seções.
- Evite espaços em branco ao final das linhas.

Se o usuário fornecer atualizações parciais (por exemplo, apenas a revisão de um princípio), ainda assim execute as etapas de validação e de decisão de versão.

Se faltarem informações críticas (por exemplo, a data de ratificação realmente desconhecida), insira `TODO(<NOME_DO_CAMPO>): explicação` e inclua no Relatório de Impacto da Sincronização, nos itens adiados.

Grave somente `.specify/memory/constitution.md`; não crie nem modifique arquivos-fonte de template.

## Verificações Pós-Execução

**Verifique se há hooks de extensão (após a atualização da constituição)**:
Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas sob a chave `hooks.after_constitution`
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue normalmente
- Ignore os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar as expressões de `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir uma `condition` não vazia, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hífens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a saída a seguir de acordo com o flag `optional`:
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
    Após emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que executaria o comando por conta própria neste agente/sessão (a invocação pode diferir do id literal `{command}` mostrado acima, por exemplo, um agente em modo skills o executa como `/skill:speckit-...` ou `$speckit-...`). Apenas emitir o bloco não executa o hook.
- Se nenhum hook estiver registrado ou `.specify/extensions.yml` não existir, ignore silenciosamente
