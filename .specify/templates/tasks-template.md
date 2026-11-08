---

description: "Modelo de lista de tarefas para implementação de funcionalidade"
---

# Tarefas: [NOME DA FUNCIONALIDADE]

**Entrada**: Documentos de design em `/specs/[###-nome-da-funcionalidade]/`

**Pré-requisitos**: plan.md (obrigatório), spec.md (obrigatório para histórias de usuário), research.md, data-model.md, contracts/

**Testes**: Os exemplos abaixo incluem tarefas de teste. Os testes são OPCIONAIS - inclua-os somente se solicitados explicitamente na especificação da funcionalidade.

**Organização**: As tarefas são agrupadas por história de usuário para permitir a implementação e o teste independentes de cada história.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: Pode ser executada em paralelo (arquivos diferentes, sem dependências)
- **[História]**: A qual história de usuário esta tarefa pertence (ex.: US1, US2, US3)
- Inclua os caminhos exatos dos arquivos nas descrições

## Convenções de Caminhos

- **Projeto único**: `src/`, `tests/` na raiz do repositório
- **Aplicação web**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` ou `android/src/`
- Os caminhos mostrados abaixo assumem projeto único - ajuste com base na estrutura do plan.md

<!--
  ============================================================================
  IMPORTANTE: As tarefas abaixo são TAREFAS DE EXEMPLO, apenas para fins de ilustração.

  O comando /speckit-tasks DEVE substituí-las por tarefas reais com base em:
  - Histórias de usuário do spec.md (com suas prioridades P1, P2, P3...)
  - Requisitos da funcionalidade do plan.md
  - Entidades do data-model.md
  - Endpoints de contracts/

  As tarefas DEVEM ser organizadas por história de usuário para que cada história possa ser:
  - Implementada de forma independente
  - Testada de forma independente
  - Entregue como um incremento do MVP

  NÃO mantenha estas tarefas de exemplo no arquivo tasks.md gerado.
  ============================================================================
-->

## Fase 1: Preparação (Infraestrutura Compartilhada)

**Propósito**: Inicialização do projeto e estrutura básica

- [ ] T001 Criar a estrutura do projeto conforme o plano de implementação
- [ ] T002 Inicializar o projeto [linguagem] com as dependências do [framework]
- [ ] T003 [P] Configurar as ferramentas de lint e formatação

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Propósito**: Infraestrutura central que DEVE estar concluída antes que QUALQUER história de usuário possa ser implementada

**⚠️ CRÍTICO**: Nenhum trabalho de história de usuário pode começar até que esta fase esteja concluída

Exemplos de tarefas fundacionais (ajuste conforme o seu projeto):

- [ ] T004 Configurar o esquema do banco de dados e o framework de migrações
- [ ] T005 [P] Implementar o framework de autenticação/autorização
- [ ] T006 [P] Configurar o roteamento da API e a estrutura de middleware
- [ ] T007 Criar os modelos/entidades base dos quais todas as histórias dependem
- [ ] T008 Configurar a infraestrutura de tratamento de erros e logging
- [ ] T009 Configurar o gerenciamento de configuração de ambiente

**Ponto de Controle**: Fundação pronta - a implementação das histórias de usuário agora pode começar em paralelo

---

## Fase 3: História de Usuário 1 - [Título] (Prioridade: P1) 🎯 MVP

**Objetivo**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar que esta história funciona por conta própria]

### Testes da História de Usuário 1 (OPCIONAL - somente se testes forem solicitados) ⚠️

> **NOTA: Escreva estes testes PRIMEIRO e garanta que FALHEM antes da implementação**

- [ ] T010 [P] [US1] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T011 [P] [US1] Teste de integração para [jornada do usuário] em tests/integration/test_[nome].py

### Implementação da História de Usuário 1

- [ ] T012 [P] [US1] Criar o modelo [Entidade1] em src/models/[entidade1].py
- [ ] T013 [P] [US1] Criar o modelo [Entidade2] em src/models/[entidade2].py
- [ ] T014 [US1] Implementar [Serviço] em src/services/[servico].py (depende de T012, T013)
- [ ] T015 [US1] Implementar [endpoint/funcionalidade] em src/[local]/[arquivo].py
- [ ] T016 [US1] Adicionar validação e tratamento de erros
- [ ] T017 [US1] Adicionar logging para as operações da história de usuário 1

**Ponto de Controle**: Neste ponto, a História de Usuário 1 deve estar totalmente funcional e testável de forma independente

---

## Fase 4: História de Usuário 2 - [Título] (Prioridade: P2)

**Objetivo**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar que esta história funciona por conta própria]

### Testes da História de Usuário 2 (OPCIONAL - somente se testes forem solicitados) ⚠️

- [ ] T018 [P] [US2] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T019 [P] [US2] Teste de integração para [jornada do usuário] em tests/integration/test_[nome].py

### Implementação da História de Usuário 2

- [ ] T020 [P] [US2] Criar o modelo [Entidade] em src/models/[entidade].py
- [ ] T021 [US2] Implementar [Serviço] em src/services/[servico].py
- [ ] T022 [US2] Implementar [endpoint/funcionalidade] em src/[local]/[arquivo].py
- [ ] T023 [US2] Integrar com os componentes da História de Usuário 1 (se necessário)

**Ponto de Controle**: Neste ponto, as Histórias de Usuário 1 E 2 devem funcionar de forma independente

---

## Fase 5: História de Usuário 3 - [Título] (Prioridade: P3)

**Objetivo**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar que esta história funciona por conta própria]

### Testes da História de Usuário 3 (OPCIONAL - somente se testes forem solicitados) ⚠️

- [ ] T024 [P] [US3] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T025 [P] [US3] Teste de integração para [jornada do usuário] em tests/integration/test_[nome].py

### Implementação da História de Usuário 3

- [ ] T026 [P] [US3] Criar o modelo [Entidade] em src/models/[entidade].py
- [ ] T027 [US3] Implementar [Serviço] em src/services/[servico].py
- [ ] T028 [US3] Implementar [endpoint/funcionalidade] em src/[local]/[arquivo].py

**Ponto de Controle**: Todas as histórias de usuário agora devem ser funcionais de forma independente

---

[Adicione mais fases de histórias de usuário conforme necessário, seguindo o mesmo padrão]

---

## Fase N: Acabamento e Preocupações Transversais

**Propósito**: Melhorias que afetam várias histórias de usuário

- [ ] TXXX [P] Atualizações de documentação em docs/
- [ ] TXXX Limpeza e refatoração de código
- [ ] TXXX Otimização de desempenho em todas as histórias
- [ ] TXXX [P] Testes unitários adicionais (se solicitados) em tests/unit/
- [ ] TXXX Reforço de segurança
- [ ] TXXX Executar a validação do quickstart.md

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Preparação (Fase 1)**: Sem dependências - pode começar imediatamente
- **Fundacional (Fase 2)**: Depende da conclusão da Preparação - BLOQUEIA todas as histórias de usuário
- **Histórias de Usuário (Fase 3+)**: Todas dependem da conclusão da fase Fundacional
  - As histórias de usuário podem então prosseguir em paralelo (se houver equipe)
  - Ou sequencialmente, em ordem de prioridade (P1 → P2 → P3)
- **Acabamento (Fase Final)**: Depende de todas as histórias de usuário desejadas estarem concluídas

### Dependências entre Histórias de Usuário

- **História de Usuário 1 (P1)**: Pode começar após a Fundacional (Fase 2) - Sem dependências de outras histórias
- **História de Usuário 2 (P2)**: Pode começar após a Fundacional (Fase 2) - Pode integrar com a US1, mas deve ser testável de forma independente
- **História de Usuário 3 (P3)**: Pode começar após a Fundacional (Fase 2) - Pode integrar com a US1/US2, mas deve ser testável de forma independente

### Dentro de Cada História de Usuário

- Os testes (se incluídos) DEVEM ser escritos e FALHAR antes da implementação
- Modelos antes dos serviços
- Serviços antes dos endpoints
- Implementação central antes da integração
- História concluída antes de passar para a próxima prioridade

### Oportunidades de Paralelismo

- Todas as tarefas de Preparação marcadas com [P] podem ser executadas em paralelo
- Todas as tarefas Fundacionais marcadas com [P] podem ser executadas em paralelo (dentro da Fase 2)
- Depois que a fase Fundacional for concluída, todas as histórias de usuário podem começar em paralelo (se a capacidade da equipe permitir)
- Todos os testes de uma história de usuário marcados com [P] podem ser executados em paralelo
- Modelos dentro de uma história marcados com [P] podem ser executados em paralelo
- Histórias de usuário diferentes podem ser trabalhadas em paralelo por membros diferentes da equipe

---

## Exemplo de Paralelismo: História de Usuário 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Estratégia de Implementação

### MVP Primeiro (Somente a História de Usuário 1)

1. Concluir a Fase 1: Preparação
2. Concluir a Fase 2: Fundacional (CRÍTICO - bloqueia todas as histórias)
3. Concluir a Fase 3: História de Usuário 1
4. **PARAR e VALIDAR**: Testar a História de Usuário 1 de forma independente
5. Implantar/demonstrar, se estiver pronta

### Entrega Incremental

1. Concluir Preparação + Fundacional → Fundação pronta
2. Adicionar a História de Usuário 1 → Testar de forma independente → Implantar/Demonstrar (MVP!)
3. Adicionar a História de Usuário 2 → Testar de forma independente → Implantar/Demonstrar
4. Adicionar a História de Usuário 3 → Testar de forma independente → Implantar/Demonstrar
5. Cada história agrega valor sem quebrar as histórias anteriores

### Estratégia de Equipe em Paralelo

Com vários desenvolvedores:

1. A equipe conclui Preparação + Fundacional em conjunto
2. Quando a Fundacional estiver concluída:
   - Desenvolvedor A: História de Usuário 1
   - Desenvolvedor B: História de Usuário 2
   - Desenvolvedor C: História de Usuário 3
3. As histórias são concluídas e integradas de forma independente

---

## Notas

- Tarefas [P] = arquivos diferentes, sem dependências
- O rótulo [História] associa a tarefa a uma história de usuário específica para rastreabilidade
- Cada história de usuário deve poder ser concluída e testada de forma independente
- Verifique se os testes falham antes de implementar
- Faça commit após cada tarefa ou grupo lógico
- Pare em qualquer ponto de controle para validar a história de forma independente
- Evite: tarefas vagas, conflitos no mesmo arquivo, dependências entre histórias que quebrem a independência
