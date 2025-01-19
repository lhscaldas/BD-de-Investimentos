# Lista de Sprints com Tags dos Requisitos Associados

## **Sprint 1: Configuração Inicial**
1. ~~Configurar o ambiente de desenvolvimento local. *(Sem tag específica - pré-requisito técnico).*~~  
2. ~~Criar o repositório no GitHub. *(Sem tag específica - pré-requisito técnico).*~~  
3. ~~Configurar a hospedagem na plataforma gratuita. *(Sem tag específica - pré-requisito técnico).*~~

4. ~~Criar a estrutura inicial do projeto (frontend e backend separados). *(Sem tag específica - pré-requisito técnico).*~~
5. Configurar o banco de dados com conexão básica. *(Sem tag específica - pré-requisito técnico).*

---

## **Sprint 2: Estruturação do Banco de Dados**
**Objetivo:** Implementar a estrutura do banco de dados para ativos e operações.
1. Criar a tabela **Ativos** com as colunas: Nome, classe, subclasse, banco, valor inicial, data de aquisição, observações. *(BD_01)*  
2. Criar a tabela **Operações** com as colunas: Tipo (compra, venda ou atualização), valor, data, referência ao ativo. *(BD_02)*  
3. Configurar criptografia no banco de dados. *(BD_03)*  
4. Testar o banco de dados com registros fictícios. *(Sem tag específica - teste técnico).*

---

## **Sprint 3: Backend - Cadastro de Ativos**
**Objetivo:** Implementar APIs para gerenciar ativos.
1. Criar endpoint para registrar ativos. *(USER_01)*  
2. Criar endpoint para editar ativos. *(USER_02)*  
3. Criar endpoint para listar ativos com filtros básicos (classe e banco). *(UI_11)*  

---

## **Sprint 4: Backend - Registro de Operações**
**Objetivo:** Implementar APIs para gerenciar operações.
1. Criar endpoint para registrar operações manualmente. *(USER_03)*  
2. Criar endpoint para editar e remover operações. *(USER_05)*  
3. Criar endpoint para listar operações vinculadas a ativos. *(Sem tag específica - funcionalidade implícita para complementar USER_03 e UI_11).*

---

## **Sprint 5: Upload de CSV**
**Objetivo:** Adicionar funcionalidade para upload de arquivos CSV.
1. Implementar endpoint para validar e processar o upload de CSV. *(USER_04)*  
2. Configurar regras de validação do formato do CSV. *(USER_05)*  
3. Testar processamento de múltiplas operações a partir de CSV. *(USER_04)*  

---

## **Sprint 6: Frontend - Interface Básica**
**Objetivo:** Criar a interface para cadastro e exibição de ativos.
1. Criar página para cadastro e edição de ativos. *(UI_01, UI_02, UI_03, UI_05)*  
2. Criar lista de ativos com filtros básicos (classe, banco). *(UI_11)*  
3. Exibir informações detalhadas de cada ativo (nome, banco, valor inicial, observações). *(UI_01, UI_02, UI_03, UI_04, UI_05)*  

---

## **Sprint 7: Frontend - Registro de Operações**
**Objetivo:** Criar a interface para registro e gerenciamento de operações.
1. Criar formulário para registrar operações manuais (compra, venda, atualização). *(USER_03, UI_12)*  
2. Criar lista de operações vinculadas a um ativo. *(Sem tag específica - funcionalidade implícita para complementar UI_12).*  
3. Adicionar funcionalidade para editar e remover operações. *(USER_05)*  

---

## **Sprint 8: Gráficos Interativos**
**Objetivo:** Implementar gráficos de alocação e rendimento.
1. Criar gráfico de alocação em formato de pizza com:
   - Exibição inicial por classes. *(UI_09)*  
   - Detalhamento por subclasses ao clicar em uma classe. *(UI_09)*  
   - Detalhamento por ativos ao clicar em uma subclasse. *(UI_09)*  
2. Criar gráfico de rendimento:
   - Exibição com base nos filtros aplicados. *(UI_10)*  
   - Comparação com índices de referência (CDI ou IBOVESPA). *(UI_10)*  

---

## **Sprint 9: Segurança e Gerenciamento de Usuários**
**Objetivo:** Adicionar autenticação e gerenciamento de usuários.
1. Implementar autenticação com usuário e senha. *(USER_07)*  
2. Criar funcionalidades para o administrador gerenciar contas de usuários (criar, editar, desativar). *(USER_06)*  
3. Testar acesso e permissões. *(USER_06, USER_07)*  

---

## **Sprint 10: Exportação e Relatórios**
**Objetivo:** Finalizar funcionalidades de exportação e análises.
1. Implementar exportação de dados filtrados para CSV. *(EXP_01)*  
2. Adicionar tabela secundária com ganho/prejuízo mensal por ativo. *(UI_08)*  
3. Testar relatórios e validações. *(EXP_01, UI_08)*  

---

## **Sprint 11: Refinamento e Ajustes Finais**
**Objetivo:** Garantir que o sistema está pronto para uso pessoal.
1. Testar todas as funcionalidades de ponta a ponta. *(Sem tag específica - validação geral).*  
2. Corrigir bugs e ajustar melhorias na interface. *(Sem tag específica - refinamento técnico).*  
3. Configurar deploy final na plataforma escolhida. *(Sem tag específica - etapa técnica).*  