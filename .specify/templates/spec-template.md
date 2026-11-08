# Especificação da Funcionalidade: [NOME DA FUNCIONALIDADE]

**Branch da Funcionalidade**: `[###-nome-da-funcionalidade]`

**Criado em**: [DATA]

**Status**: Rascunho

**Entrada**: Descrição do usuário: "$ARGUMENTS"

## Cenários de Usuário e Testes *(obrigatório)*

<!--
  IMPORTANTE: As histórias de usuário devem ser PRIORIZADAS como jornadas de usuário ordenadas por importância.
  Cada história/jornada de usuário deve ser TESTÁVEL DE FORMA INDEPENDENTE - ou seja, se você implementar apenas UMA delas,
  ainda deve ter um MVP (Produto Mínimo Viável) que entregue valor.

  Atribua prioridades (P1, P2, P3, etc.) a cada história, onde P1 é a mais crítica.
  Pense em cada história como uma fatia autônoma de funcionalidade que pode ser:
  - Desenvolvida de forma independente
  - Testada de forma independente
  - Implantada de forma independente
  - Demonstrada aos usuários de forma independente
-->

### História de Usuário 1 - [Título Breve] (Prioridade: P1)

[Descreva esta jornada de usuário em linguagem simples]

**Por que esta prioridade**: [Explique o valor e por que ela tem este nível de prioridade]

**Teste Independente**: [Descreva como isto pode ser testado de forma independente - ex.: "Pode ser totalmente testado por [ação específica] e entrega [valor específico]"]

**Cenários de Aceitação**:

1. **Dado** [estado inicial], **Quando** [ação], **Então** [resultado esperado]
2. **Dado** [estado inicial], **Quando** [ação], **Então** [resultado esperado]

---

### História de Usuário 2 - [Título Breve] (Prioridade: P2)

[Descreva esta jornada de usuário em linguagem simples]

**Por que esta prioridade**: [Explique o valor e por que ela tem este nível de prioridade]

**Teste Independente**: [Descreva como isto pode ser testado de forma independente]

**Cenários de Aceitação**:

1. **Dado** [estado inicial], **Quando** [ação], **Então** [resultado esperado]

---

### História de Usuário 3 - [Título Breve] (Prioridade: P3)

[Descreva esta jornada de usuário em linguagem simples]

**Por que esta prioridade**: [Explique o valor e por que ela tem este nível de prioridade]

**Teste Independente**: [Descreva como isto pode ser testado de forma independente]

**Cenários de Aceitação**:

1. **Dado** [estado inicial], **Quando** [ação], **Então** [resultado esperado]

---

[Adicione mais histórias de usuário conforme necessário, cada uma com uma prioridade atribuída]

### Casos de Borda

<!--
  AÇÃO NECESSÁRIA: O conteúdo desta seção representa placeholders.
  Preencha-os com os casos de borda adequados.
-->

- O que acontece quando [condição limite]?
- Como o sistema trata [cenário de erro]?

## Requisitos *(obrigatório)*

<!--
  AÇÃO NECESSÁRIA: O conteúdo desta seção representa placeholders.
  Preencha-os com os requisitos funcionais adequados.
-->

### Requisitos Funcionais

- **FR-001**: O sistema DEVE [capacidade específica, ex.: "permitir que usuários criem contas"]
- **FR-002**: O sistema DEVE [capacidade específica, ex.: "validar endereços de e-mail"]
- **FR-003**: Os usuários DEVEM poder [interação principal, ex.: "redefinir sua senha"]
- **FR-004**: O sistema DEVE [requisito de dados, ex.: "persistir as preferências do usuário"]
- **FR-005**: O sistema DEVE [comportamento, ex.: "registrar em log todos os eventos de segurança"]

*Exemplo de marcação de requisitos pouco claros:*

- **FR-006**: O sistema DEVE autenticar usuários via [PRECISA DE ESCLARECIMENTO: método de autenticação não especificado - e-mail/senha, SSO, OAuth?]
- **FR-007**: O sistema DEVE reter os dados do usuário por [PRECISA DE ESCLARECIMENTO: período de retenção não especificado]

### Entidades-Chave *(incluir se a funcionalidade envolver dados)*

- **[Entidade 1]**: [O que ela representa, atributos principais sem detalhes de implementação]
- **[Entidade 2]**: [O que ela representa, relacionamentos com outras entidades]

## Critérios de Sucesso *(obrigatório)*

<!--
  AÇÃO NECESSÁRIA: Defina critérios de sucesso mensuráveis.
  Eles devem ser agnósticos quanto à tecnologia e mensuráveis.
-->

### Resultados Mensuráveis

- **SC-001**: [Métrica mensurável, ex.: "Os usuários conseguem concluir a criação de conta em menos de 2 minutos"]
- **SC-002**: [Métrica mensurável, ex.: "O sistema suporta 1000 usuários simultâneos sem degradação"]
- **SC-003**: [Métrica de satisfação do usuário, ex.: "90% dos usuários concluem a tarefa principal com sucesso na primeira tentativa"]
- **SC-004**: [Métrica de negócio, ex.: "Reduzir em 50% os chamados de suporte relacionados a [X]"]

## Premissas

<!--
  AÇÃO NECESSÁRIA: O conteúdo desta seção representa placeholders.
  Preencha-os com as premissas adequadas, com base em padrões razoáveis
  escolhidos quando a descrição da funcionalidade não especificou certos detalhes.
-->

- [Premissa sobre os usuários-alvo, ex.: "Os usuários têm conexão estável com a internet"]
- [Premissa sobre os limites do escopo, ex.: "Suporte a dispositivos móveis está fora do escopo da v1"]
- [Premissa sobre dados/ambiente, ex.: "O sistema de autenticação existente será reutilizado"]
- [Dependência de sistema/serviço existente, ex.: "Requer acesso à API de perfil de usuário existente"]
