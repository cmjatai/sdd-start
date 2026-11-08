---
name: "speckit-clarify"
description: "Identifica áreas subespecificadas na especificação da funcionalidade atual fazendo até 5 perguntas de esclarecimento altamente direcionadas e registrando as respostas de volta na especificação."
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/clarify.md"
---


## Entrada do Usuário

```text
$ARGUMENTS
```

Você **DEVE** considerar a entrada do usuário antes de prosseguir (se não estiver vazia).

## Verificações Pré-Execução

**Verifique se há hooks de extensão (antes do esclarecimento)**:
- Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se existir, leia-o e procure entradas sob a chave `hooks.before_clarify`
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

Objetivo: Detectar e reduzir ambiguidades ou pontos de decisão ausentes na especificação da funcionalidade ativa e registrar os esclarecimentos diretamente no arquivo da especificação.

Nota: Espera-se que este fluxo de esclarecimento seja executado (e concluído) ANTES de invocar `/speckit-plan`. Se o usuário declarar explicitamente que está pulando o esclarecimento (por exemplo, um spike exploratório), você pode prosseguir, mas deve avisar que o risco de retrabalho posterior aumenta.

Etapas de execução:

1. Execute `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` a partir da raiz do repositório **uma única vez** (modo combinado `--json --paths-only` / `-Json -PathsOnly`). Interprete os campos mínimos do payload JSON:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Opcionalmente capture `IMPL_PLAN`, `TASKS` para fluxos encadeados futuros.)
   - Se a interpretação do JSON falhar, aborte e instrua o usuário a executar novamente `/speckit-specify` ou a verificar o ambiente da branch da funcionalidade.
   - Para aspas simples em argumentos como "I'm Groot", use a sintaxe de escape: por exemplo 'I'\''m Groot' (ou aspas duplas, se possível: "I'm Groot").

2. **SE EXISTIR**: Carregue `.specify/memory/constitution.md` para obter os princípios do projeto e as restrições de governança.

3. Carregue o arquivo da especificação atual. Execute uma varredura estruturada de ambiguidade e cobertura usando esta taxonomia. Para cada categoria, marque o status: Claro / Parcial / Ausente. Produza um mapa de cobertura interno usado para priorização (não exiba o mapa bruto, a menos que nenhuma pergunta vá ser feita).

   Escopo Funcional e Comportamento:
   - Objetivos centrais do usuário e critérios de sucesso
   - Declarações explícitas de fora do escopo
   - Diferenciação de papéis / personas de usuário

   Domínio e Modelo de Dados:
   - Entidades, atributos, relacionamentos
   - Regras de identidade e unicidade
   - Ciclo de vida / transições de estado
   - Premissas de volume / escala de dados

   Fluxo de Interação e UX:
   - Jornadas / sequências críticas do usuário
   - Estados de erro/vazio/carregamento
   - Notas de acessibilidade ou localização

   Atributos de Qualidade Não Funcionais:
   - Desempenho (latência, metas de vazão)
   - Escalabilidade (horizontal/vertical, limites)
   - Confiabilidade e disponibilidade (uptime, expectativas de recuperação)
   - Observabilidade (sinais de logging, métricas, tracing)
   - Segurança e privacidade (autenticação/autorização, proteção de dados, premissas de ameaça)
   - Restrições de conformidade / regulatórias (se houver)

   Integração e Dependências Externas:
   - Serviços/APIs externos e modos de falha
   - Formatos de importação/exportação de dados
   - Premissas de protocolo/versionamento

   Casos de Borda e Tratamento de Falhas:
   - Cenários negativos
   - Limitação de taxa / throttling
   - Resolução de conflitos (por exemplo, edições concorrentes)

   Restrições e Trade-offs:
   - Restrições técnicas (linguagem, armazenamento, hospedagem)
   - Trade-offs explícitos ou alternativas rejeitadas

   Terminologia e Consistência:
   - Termos canônicos do glossário
   - Sinônimos evitados / termos obsoletos

   Sinais de Conclusão:
   - Testabilidade dos critérios de aceitação
   - Indicadores mensuráveis no estilo Definição de Pronto

   Diversos / Placeholders:
   - Marcadores TODO / decisões não resolvidas
   - Adjetivos ambíguos ("robusto", "intuitivo") sem quantificação

   Para cada categoria com status Parcial ou Ausente, adicione uma oportunidade de pergunta candidata, a menos que:
   - O esclarecimento não altere materialmente a estratégia de implementação ou de validação
   - O item trate especificamente de método de implementação, comparação de stack tecnológica ou decomposição de tarefas (anote internamente)

4. Gere (internamente) uma fila priorizada de perguntas de esclarecimento candidatas (máximo de 5). NÃO as exiba todas de uma vez. Aplique estas restrições:
    - Máximo de 5 perguntas no total em toda a sessão.
    - Cada pergunta deve ser respondível com UMA das opções:
       - Uma seleção curta de múltipla escolha (2–5 opções distintas e mutuamente exclusivas), OU
       - Uma resposta de uma palavra / frase curta (restrinja explicitamente: "Responda em <=5 palavras").
    - Inclua apenas perguntas cujas respostas impactem materialmente arquitetura, modelagem de dados, decomposição de tarefas, design de testes, comportamento de UX, prontidão operacional ou validação de conformidade.
    - Garanta o equilíbrio de cobertura entre categorias: tente cobrir primeiro as categorias não resolvidas de maior impacto; evite fazer duas perguntas de baixo impacto quando uma única área de alto impacto (por exemplo, postura de segurança) estiver sem resolução.
    - Exclua perguntas já respondidas, preferências estilísticas triviais ou detalhes de execução em nível de plano (a menos que bloqueiem a correção).
    - Favoreça esclarecimentos que reduzam o risco de retrabalho posterior ou evitem testes de aceitação desalinhados.
    - Se mais de 5 categorias permanecerem sem resolução, selecione as 5 principais pela heurística (Impacto * Incerteza).

5. Laço de perguntas sequencial (interativo):
    - Apresente EXATAMENTE UMA pergunta por vez.
    - **Qualidade da redação das perguntas (aplica-se a todas as perguntas, de múltipla escolha ou resposta curta):**
       - Comece com `**Pergunta:**` seguido de uma frase interrogativa completa que termine com `?`. O texto da pergunta antes do `?` deve fazer sentido por si só.
       - NUNCA use um rótulo de tópico, título de seção ou id de requisito como a própria pergunta. Por exemplo, `Matriz de dispositivos/runtime de aceitação (FR-023)` é INVÁLIDO — é um rótulo, não uma pergunta.
       - Após o `?`, o único sufixo permitido é um id de requisito/pergunta opcional entre parênteses. Formato exato: `**Pergunta:** <interrogativa>?` ou `**Pergunta:** <interrogativa>? (FR-023)`. Nunca coloque o id antes do `?` e nunca use o id (sozinho ou com um rótulo de tópico) como o prompt inteiro.
       - Imediatamente após a linha da pergunta, adicione uma frase em linguagem simples "Por que isso importa" (o que está em jogo para a aceitação ou a entrega) antes da recomendação/opções.
       - Use palavras do dia a dia; introduza jargão somente se for definido na mesma frase. Autoverificação: um leitor que não conhece o Spec Kit deve conseguir responder apenas a partir da linha da Pergunta. Ser conciso é aceitável; rótulos enigmáticos não.
    - Para perguntas de múltipla escolha:
       - **Analise todas as opções** e determine a **opção mais adequada** com base em:
          - Melhores práticas para o tipo de projeto
          - Padrões comuns em implementações semelhantes
          - Redução de risco (segurança, desempenho, manutenibilidade)
          - Alinhamento com quaisquer objetivos ou restrições explícitos do projeto visíveis na especificação
       - Apresente sua **opção recomendada em destaque** no topo, com justificativa clara (1-2 frases explicando por que é a melhor escolha).
       - Formato: `**Recomendada:** Opção [X] - <justificativa>`
       - Em seguida, renderize todas as opções como uma tabela Markdown:

       | Opção | Descrição |
       |--------|-------------|
       | A | <Descrição da Opção A> |
       | B | <Descrição da Opção B> |
       | C | <Descrição da Opção C> (adicione D/E conforme necessário, até 5) |
       | Curta | Forneça uma resposta curta diferente (<=5 palavras) (Inclua somente se uma alternativa de resposta livre for apropriada) |

       - Após a tabela, adicione: `Você pode responder com a letra da opção (por exemplo, "A"), aceitar a recomendação dizendo "sim" ou "recomendada", ou fornecer sua própria resposta curta.`
    - Para o estilo de resposta curta (sem opções discretas significativas):
       - Forneça sua **resposta sugerida** com base em melhores práticas e no contexto.
       - Formato: `**Sugerida:** <sua resposta proposta> - <breve justificativa>`
       - Em seguida, exiba: `Formato: Resposta curta (<=5 palavras). Você pode aceitar a sugestão dizendo "sim" ou "sugerida", ou fornecer sua própria resposta.`
    - Depois que o usuário responder:
       - Se o usuário responder "sim", "recomendada" ou "sugerida", use a recomendação/sugestão que você declarou anteriormente como a resposta.
       - Caso contrário, valide se a resposta corresponde a uma das opções ou se respeita a restrição de <=5 palavras.
       - Se for ambígua, peça uma desambiguação rápida (a contagem continua pertencendo à mesma pergunta; não avance).
       - Quando satisfatória, registre-a na memória de trabalho (ainda não grave em disco) e passe para a próxima pergunta da fila.
    - Pare de fazer novas perguntas quando:
       - Todas as ambiguidades críticas forem resolvidas cedo (os itens restantes da fila se tornam desnecessários), OU
       - O usuário sinalizar conclusão ("pronto", "bom", "chega", "sem mais"), OU
       - Você atingir 5 perguntas feitas.
    - Nunca revele antecipadamente as perguntas futuras da fila.
    - Se não existirem perguntas válidas no início, informe imediatamente que não há ambiguidades críticas.

6. Integração após CADA resposta aceita (abordagem de atualização incremental):
    - Mantenha uma representação em memória da especificação (carregada uma vez no início) mais o conteúdo bruto do arquivo.
    - Para a primeira resposta integrada nesta sessão:
       - Garanta que exista uma seção `## Esclarecimentos` (crie-a logo após a seção contextual/de visão geral de nível mais alto, conforme o template da especificação, se estiver ausente).
       - Sob ela, crie (se não existir) um subtítulo `### Sessão AAAA-MM-DD` para hoje.
    - Acrescente uma linha de marcador imediatamente após a aceitação: `- P: <pergunta> → R: <resposta final>`.
    - Em seguida, aplique imediatamente o esclarecimento à(s) seção(ões) mais apropriada(s):
       - Ambiguidade funcional → Atualize ou adicione um marcador em Requisitos Funcionais.
       - Interação do usuário / distinção de atores → Atualize as Histórias de Usuário ou a subseção de Atores (se presente) com o papel, a restrição ou o cenário esclarecido.
       - Formato de dados / entidades → Atualize o Modelo de Dados (adicione campos, tipos, relacionamentos) preservando a ordem; anote as restrições adicionadas de forma sucinta.
       - Restrição não funcional → Adicione/modifique critérios mensuráveis em Critérios de Sucesso > Resultados Mensuráveis (converta adjetivos vagos em métrica ou meta explícita).
       - Caso de borda / fluxo negativo → Adicione um novo marcador em Casos de Borda / Tratamento de Erros (ou crie essa subseção se o template fornecer um placeholder para ela).
       - Conflito de terminologia → Normalize o termo em toda a especificação; mantenha o original somente se necessário, adicionando `(anteriormente chamado de "X")` uma única vez.
    - Se o esclarecimento invalidar uma afirmação ambígua anterior, substitua essa afirmação em vez de duplicá-la; não deixe texto obsoleto e contraditório.
    - Salve o arquivo da especificação APÓS cada integração para minimizar o risco de perda de contexto (sobrescrita atômica).
    - Preserve a formatação: não reordene seções não relacionadas; mantenha a hierarquia de títulos intacta.
    - Mantenha cada esclarecimento inserido mínimo e testável (evite divagação narrativa).

7. Validação (executada após CADA gravação, além de uma passagem final):
   - A sessão de Esclarecimentos contém exatamente um marcador por resposta aceita (sem duplicatas).
   - Total de perguntas feitas (aceitas) ≤ 5.
   - As seções atualizadas não contêm placeholders vagos remanescentes que a nova resposta deveria resolver.
   - Nenhuma afirmação anterior contraditória permanece (verifique se escolhas alternativas agora inválidas foram removidas).
   - Estrutura Markdown válida; os únicos novos títulos permitidos: `## Esclarecimentos`, `### Sessão AAAA-MM-DD`.
   - Consistência de terminologia: o mesmo termo canônico é usado em todas as seções atualizadas.

8. Grave a especificação atualizada de volta em `FEATURE_SPEC`.

9. **Revalide o Checklist de Qualidade da Especificação** (se existir):
   - Verifique se `FEATURE_DIR/checklists/requirements.md` existe.
   - Se NÃO existir, ignore esta etapa silenciosamente.
   - Se existir:
     1. Leia o arquivo de checklist.
     2. Identifique todas as linhas de checkbox de lista de tarefas do GitHub — linhas que correspondam a `- [ ]`, `- [x]` ou `- [X]` (sem diferenciar maiúsculas de minúsculas, tolerando espaços iniciais para itens aninhados) fora de blocos de código. Ignore todo o outro conteúdo (títulos, notas, marcadores que não sejam checkbox, metadados).
     3. Para cada linha de checkbox, registre o estado atual do marcador (marcado ou desmarcado) e o texto do item em uma lista de snapshot anterior.
     4. Reavalie cada item de checkbox em relação à especificação **atualizada** (a versão que acabou de ser salva na etapa 7).
     5. Para cada item de checkbox, atualize somente se o estado marcado/desmarcado de fato mudar:
        - Se o item agora passa e estava desmarcado: altere `[ ]` para `[x]`.
        - Se o item agora falha e estava marcado: altere `[x]`/`[X]` para `[ ]`.
        - Se o estado não mudou: deixe o marcador como está (preserve a caixa original para evitar diffs cosméticos).
     6. Salve o arquivo de checklist atualizado. **Alterne somente a parte do marcador `[ ]`/`[x]` das linhas de checkbox cujo estado mudou.** Todo o outro conteúdo do arquivo — títulos, metadados, notas, ordem das linhas, espaçamento — deve permanecer inalterado para evitar diffs ruidosos.
     7. Compare o snapshot anterior com o estado atual para calcular três listas para o Relatório de Conclusão:
        - **Passaram agora**: itens que mudaram de desmarcado para marcado.
        - **Regressões**: itens que mudaram de marcado para desmarcado.
        - **Ainda desmarcados**: itens que permanecem desmarcados.
     8. Registre as contagens de aprovação antes/depois como marcados/total de itens de checkbox (por exemplo, "12/16 → 15/16 itens aprovados").

Regras de comportamento:

- Se nenhuma ambiguidade significativa for encontrada (ou todas as perguntas potenciais forem de baixo impacto), responda: "Nenhuma ambiguidade crítica detectada que justifique um esclarecimento formal." e sugira prosseguir.
- Se o arquivo da especificação estiver ausente, instrua o usuário a executar `/speckit-specify` primeiro (não crie uma nova especificação aqui).
- Nunca exceda 5 perguntas feitas no total (novas tentativas de esclarecimento para uma única pergunta não contam como novas perguntas).
- Evite perguntas especulativas sobre a stack tecnológica, a menos que sua ausência bloqueie a clareza funcional.
- Respeite os sinais de encerramento antecipado do usuário ("pare", "pronto", "prossiga").
- Se nenhuma pergunta for feita por cobertura completa, exiba um resumo compacto de cobertura (todas as categorias Claras) e sugira avançar.
- Se a cota for atingida com categorias de alto impacto ainda sem resolução, sinalize-as explicitamente em Adiadas, com a justificativa.

Contexto para priorização: $ARGUMENTS

## Hooks Obrigatórios Pós-Execução

**Você DEVE concluir esta seção antes de relatar a conclusão ao usuário.**

Verifique se `.specify/extensions.yml` existe na raiz do projeto.
- Se não existir, ou se nenhum hook estiver registrado sob `hooks.after_clarify`, vá direto para o Relatório de Conclusão.
- Se existir, leia-o e procure entradas sob a chave `hooks.after_clarify`.
- Se o YAML não puder ser interpretado ou for inválido, não ignore silenciosamente: informe ao usuário que `.specify/extensions.yml` não pôde ser lido (inclua o erro do parser) e que nenhum hook foi verificado, incluindo quaisquer hooks obrigatórios (`optional: false`) registrados ali, e então continue para o Relatório de Conclusão.
- Ignore os hooks em que `enabled` seja explicitamente `false`. Trate hooks sem o campo `enabled` como habilitados por padrão.
- Para cada hook restante, **não** tente interpretar ou avaliar as expressões de `condition` do hook:
  - Se o hook não tiver o campo `condition`, ou ele for nulo/vazio, trate o hook como executável
  - Se o hook definir uma `condition` não vazia, ignore o hook e deixe a avaliação da condição para a implementação do HookExecutor
- Ao construir invocações de comando a partir dos nomes de comando dos hooks, substitua pontos (`.`) por hífens (`-`). Por exemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook executável, produza a saída a seguir de acordo com o flag `optional`:
  - **Hook obrigatório** (`optional: false`) — **Você DEVE emitir `EXECUTE_COMMAND:` para cada hook obrigatório**:
    ```
    ## Hooks de Extensão

    **Hook Automático**: {extension}
    Executando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Após emitir o bloco acima, você DEVE de fato invocar o hook e aguardar sua conclusão antes de continuar. Execute-o da mesma forma que executaria o comando por conta própria neste agente/sessão (a invocação pode diferir do id literal `{command}` mostrado acima, por exemplo, um agente em modo skills o executa como `/skill:speckit-...` ou `$speckit-...`). Apenas emitir o bloco não executa o hook.
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

Relate a conclusão (após o fim do laço de perguntas ou encerramento antecipado):
- Número de perguntas feitas e respondidas.
- Caminho da especificação atualizada.
- Seções alteradas (liste os nomes).
- Status do checklist de qualidade da especificação (se `FEATURE_DIR/checklists/requirements.md` foi revalidado): mostre as contagens de aprovação antes/depois (por exemplo, "Checklist de Qualidade da Especificação: 12/16 → 15/16 itens aprovados") e liste quaisquer itens que mudaram de estado — tanto os recém-marcados (desmarcado → marcado) quanto quaisquer regressões (marcado → desmarcado). Se algum item permanecer desmarcado, liste-o como área que precisa de atenção.
- Tabela de resumo de cobertura listando cada categoria da taxonomia com Status: Resolvida (estava Parcial/Ausente e foi tratada), Adiada (excede a cota de perguntas, ou o item restante trata especificamente de método de implementação, comparação de stack tecnológica ou decomposição de tarefas), Clara (já suficiente), Pendente (ainda Parcial/Ausente, mas de baixo impacto).
- Se restarem itens Pendentes ou Adiados, recomende se deve prosseguir para `/speckit-plan` ou executar `/speckit-clarify` novamente mais tarde, após o plano.
- Próximo comando sugerido.

## Concluído Quando

- [ ] Ambiguidades da especificação identificadas e esclarecimentos integrados ao arquivo da especificação
- [ ] Checklist de qualidade da especificação revalidado em relação à especificação atualizada (se `FEATURE_DIR/checklists/requirements.md` existir)
- [ ] Hooks de extensão despachados ou ignorados conforme as regras em Hooks Obrigatórios Pós-Execução acima
- [ ] Conclusão relatada ao usuário com as perguntas respondidas, seções alteradas, status do checklist e resumo de cobertura
