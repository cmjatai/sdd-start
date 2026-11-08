# Checklist de [TIPO DE CHECKLIST]: [NOME DA FUNCIONALIDADE]

**Propósito**: [Breve descrição do que este checklist cobre]
**Criado em**: [DATA]
**Funcionalidade**: [Link para spec.md ou documentação relevante]

**Nota**: Este checklist personalizado é gerado pelo comando `/speckit-checklist` com base no contexto e nos requisitos da funcionalidade.
**Responsabilidade da Revisão**: Este checklist é um artefato de revisão da qualidade dos requisitos, de responsabilidade do revisor. Marque um item como `[x]` somente quando o revisor determinar que o critério de qualidade dos requisitos foi satisfeito.
**Semântica das Marcações**: `[x]` significa que o critério foi revisado e satisfeito quanto à qualidade dos requisitos. Não significa que o trabalho de implementação esteja concluído.

<!--
  ============================================================================
  IMPORTANTE: Os itens do checklist abaixo são ITENS DE EXEMPLO, apenas para ilustração.

  O comando /speckit-checklist DEVE substituí-los por itens reais com base em:
  - Solicitação específica de checklist do usuário
  - Requisitos da funcionalidade em spec.md
  - Contexto técnico em plan.md
  - Detalhes de implementação em tasks.md

  NÃO mantenha estes itens de exemplo no arquivo de checklist gerado.
  ============================================================================
-->

## [Categoria 1]

- [ ] CHK001 Primeiro item do checklist com ação clara
- [ ] CHK002 Segundo item do checklist
- [ ] CHK003 Terceiro item do checklist

## [Categoria 2]

- [ ] CHK004 Outro item da categoria
- [ ] CHK005 Item com critérios específicos
- [ ] CHK006 Último item desta categoria

## Notas

- Marque os itens como `[x]` somente depois que a revisão confirmar que o critério de qualidade do requisito foi satisfeito
- Deixe os itens desmarcados quando ainda exigirem esclarecimento, correção ou avaliação do revisor
- `/speckit-implement` lê o estado das caixas de seleção do checklist como um portão (gate) e não deve modificar as marcações
- `checklists/requirements.md` tem um ciclo de vida próprio, embutido, mantido por `/speckit-specify` e `/speckit-clarify`
- Adicione comentários ou achados inline
- Inclua links para recursos ou documentação relevantes
- Os itens são numerados sequencialmente para facilitar a referência
