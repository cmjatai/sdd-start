# Constituição de [PROJECT_NAME]
<!-- Exemplo: Constituição do Spec, Constituição do TaskFlow, etc. -->

## Princípios Fundamentais

### [PRINCIPLE_1_NAME]
<!-- Exemplo: I. Biblioteca Primeiro -->
[PRINCIPLE_1_DESCRIPTION]
<!-- Exemplo: Toda funcionalidade começa como uma biblioteca autônoma; as bibliotecas devem ser autocontidas, testáveis de forma independente e documentadas; propósito claro é obrigatório - nada de bibliotecas apenas organizacionais -->

### [PRINCIPLE_2_NAME]
<!-- Exemplo: II. Interface CLI -->
[PRINCIPLE_2_DESCRIPTION]
<!-- Exemplo: Toda biblioteca expõe funcionalidade via CLI; protocolo de texto entrada/saída: stdin/args → stdout, erros → stderr; suporte a JSON + formatos legíveis por humanos -->

### [PRINCIPLE_3_NAME]
<!-- Exemplo: III. Test-First (INEGOCIÁVEL) -->
[PRINCIPLE_3_DESCRIPTION]
<!-- Exemplo: TDD obrigatório: testes escritos → aprovados pelo usuário → testes falham → só então implementar; ciclo Red-Green-Refactor rigorosamente aplicado -->

### [PRINCIPLE_4_NAME]
<!-- Exemplo: IV. Testes de Integração -->
[PRINCIPLE_4_DESCRIPTION]
<!-- Exemplo: Áreas que exigem testes de integração: testes de contrato de novas bibliotecas, mudanças de contrato, comunicação entre serviços, esquemas compartilhados -->

### [PRINCIPLE_5_NAME]
<!-- Exemplo: V. Observabilidade, VI. Versionamento e Mudanças Incompatíveis, VII. Simplicidade -->
[PRINCIPLE_5_DESCRIPTION]
<!-- Exemplo: E/S em texto garante depuração; log estruturado obrigatório; ou: formato MAJOR.MINOR.BUILD; ou: comece simples, princípios YAGNI -->

## [SECTION_2_NAME]
<!-- Exemplo: Restrições Adicionais, Requisitos de Segurança, Padrões de Desempenho, etc. -->

[SECTION_2_CONTENT]
<!-- Exemplo: Requisitos de stack tecnológico, padrões de conformidade, políticas de implantação, etc. -->

## [SECTION_3_NAME]
<!-- Exemplo: Fluxo de Desenvolvimento, Processo de Revisão, Portões (gates) de Qualidade, etc. -->

[SECTION_3_CONTENT]
<!-- Exemplo: Requisitos de revisão de código, portões (gates) de testes, processo de aprovação de implantação, etc. -->

## Governança
<!-- Exemplo: A Constituição prevalece sobre todas as outras práticas; emendas exigem documentação, aprovação e plano de migração -->

[GOVERNANCE_RULES]
<!-- Exemplo: Todos os PRs/revisões devem verificar a conformidade; a complexidade deve ser justificada; use [GUIDANCE_FILE] para orientações de desenvolvimento em tempo de execução -->

**Versão**: [CONSTITUTION_VERSION] | **Ratificada em**: [RATIFICATION_DATE] | **Última Alteração**: [LAST_AMENDED_DATE]
<!-- Exemplo: Versão: 2.1.1 | Ratificada em: 2025-06-13 | Última Alteração: 2025-07-16 -->
