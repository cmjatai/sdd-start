# Plano de Implementação: [FUNCIONALIDADE]

**Branch**: `[###-nome-da-funcionalidade]` | **Data**: [DATA] | **Especificação**: [link]

**Entrada**: Especificação da funcionalidade em `/specs/[###-nome-da-funcionalidade]/spec.md`

**Nota**: Este template é preenchido pelo comando `/speckit-plan`; sua definição descreve o fluxo de execução.

## Resumo

[Extraia da especificação da funcionalidade: requisito principal + abordagem técnica da pesquisa]

## Contexto Técnico

<!--
  AÇÃO NECESSÁRIA: Substitua o conteúdo desta seção pelos detalhes técnicos
  do projeto. A estrutura aqui é apresentada em caráter consultivo para guiar
  o processo de iteração.
-->

**Linguagem/Versão**: [ex.: Python 3.11, Swift 5.9, Rust 1.75 ou PRECISA DE ESCLARECIMENTO]

**Dependências Principais**: [ex.: FastAPI, UIKit, LLVM ou PRECISA DE ESCLARECIMENTO]

**Armazenamento**: [se aplicável, ex.: PostgreSQL, CoreData, arquivos ou N/A]

**Testes**: [ex.: pytest, XCTest, cargo test ou PRECISA DE ESCLARECIMENTO]

**Plataforma Alvo**: [ex.: servidor Linux, iOS 15+, WASM ou PRECISA DE ESCLARECIMENTO]

**Tipo de Projeto**: [ex.: biblioteca/cli/serviço-web/app-mobile/compilador/app-desktop ou PRECISA DE ESCLARECIMENTO]

**Metas de Desempenho**: [específicas do domínio, ex.: 1000 req/s, 10k linhas/s, 60 fps ou PRECISA DE ESCLARECIMENTO]

**Restrições**: [específicas do domínio, ex.: <200ms p95, <100MB de memória, funcionar offline ou PRECISA DE ESCLARECIMENTO]

**Escala/Escopo**: [específicos do domínio, ex.: 10k usuários, 1M LOC, 50 telas ou PRECISA DE ESCLARECIMENTO]

## Verificação da Constituição

*PORTÃO (gate): Deve passar antes da pesquisa da Fase 0. Reverifique após o design da Fase 1.*

[Portões (gates) determinados com base no arquivo da constituição]

## Estrutura do Projeto

### Documentação (desta funcionalidade)

```text
specs/[###-funcionalidade]/
├── plan.md              # Este arquivo (saída do comando /speckit-plan)
├── research.md          # Saída da Fase 0 (comando /speckit-plan)
├── data-model.md        # Saída da Fase 1 (comando /speckit-plan)
├── quickstart.md        # Saída da Fase 1 (comando /speckit-plan)
├── contracts/           # Saída da Fase 1 (comando /speckit-plan)
└── tasks.md             # Saída da Fase 2 (comando /speckit-tasks - NÃO é criado por /speckit-plan)
```

### Código-Fonte (raiz do repositório)
<!--
  AÇÃO NECESSÁRIA: Substitua a árvore de placeholder abaixo pelo layout concreto
  desta funcionalidade. Exclua as opções não utilizadas e expanda a estrutura escolhida com
  caminhos reais (ex.: apps/admin, packages/algo). O plano entregue
  não deve incluir rótulos de Opção.
-->

```text
# [REMOVA SE NÃO USAR] Opção 1: Projeto único (PADRÃO)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVA SE NÃO USAR] Opção 2: Aplicação web (quando "frontend" + "backend" detectados)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVA SE NÃO USAR] Opção 3: Mobile + API (quando "iOS/Android" detectados)
api/
└── [igual ao backend acima]

ios/ ou android/
└── [estrutura específica da plataforma: módulos da funcionalidade, fluxos de UI, testes da plataforma]
```

**Decisão de Estrutura**: [Documente a estrutura selecionada e referencie os
diretórios reais capturados acima]

## Rastreamento de Complexidade

> **Preencha SOMENTE se a Verificação da Constituição tiver violações que precisem ser justificadas**

| Violação | Por que é Necessária | Alternativa Mais Simples Rejeitada Porque |
|-----------|------------|-------------------------------------|
| [ex.: 4º projeto] | [necessidade atual] | [por que 3 projetos são insuficientes] |
| [ex.: padrão Repository] | [problema específico] | [por que o acesso direto ao banco é insuficiente] |
