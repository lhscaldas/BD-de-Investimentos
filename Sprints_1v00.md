# Lista de Sprints

## **Sprint 1: Configuração Inicial**
**Objetivo:** Preparar o ambiente e estabelecer a base do projeto.
1. Configurar o ambiente de desenvolvimento local.
2. Criar o repositório no GitHub.
3. Configurar a hospedagem na plataforma gratuita.
4. Criar a estrutura inicial do projeto (frontend e backend separados).
5. Configurar o banco de dados com conexão básica.

---

## **Sprint 2: Estruturação do Banco de Dados**
**Objetivo:** Implementar a estrutura do banco de dados para ativos e operações.
1. Criar a tabela **Ativos** com as colunas: Nome, classe, subclasse, banco, valor inicial, data de aquisição, observações.
2. Criar a tabela **Operações** com as colunas: Tipo (compra, venda ou atualização), valor, data, referência ao ativo.
3. Configurar criptografia no banco de dados.
4. Testar o banco de dados com registros fictícios.

---

## **Sprint 3: Backend - Cadastro de Ativos**
**Objetivo:** Implementar APIs para gerenciar ativos.
1. Criar endpoint para registrar ativos.
2. Criar endpoint para editar ativos.
3. Criar endpoint para listar ativos com filtros básicos (classe e banco).

---

## **Sprint 4: Backend - Registro de Operações**
**Objetivo:** Implementar APIs para gerenciar operações.
1. Criar endpoint para registrar operações manualmente.
2. Criar endpoint para editar e remover operações.
3. Criar endpoint para listar operações vinculadas a ativos.

---

## **Sprint 5: Upload de CSV**
**Objetivo:** Adicionar funcionalidade para upload de arquivos CSV.
1. Implementar endpoint para validar e processar o upload de CSV.
2. Configurar regras de validação do formato do CSV.
3. Testar processamento de múltiplas operações a partir de CSV.

---

## **Sprint 6: Frontend - Interface Básica**
**Objetivo:** Criar a interface para cadastro e exibição de ativos.
1. Criar página para cadastro e edição de ativos.
2. Criar lista de ativos com filtros básicos (classe, banco).
3. Exibir informações detalhadas de cada ativo (nome, banco, valor inicial, observações).

---

## **Sprint 7: Frontend - Registro de Operações**
**Objetivo:** Criar a interface para registro e gerenciamento de operações.
1. Criar formulário para registrar operações manuais (compra, venda, atualização).
2. Criar lista de operações vinculadas a um ativo.
3. Adicionar funcionalidade para editar e remover operações.

---

## **Sprint 8: Gráficos Interativos**
**Objetivo:** Implementar gráficos de alocação e rendimento.
1. Criar gráfico de alocação em formato de pizza com:
   - Exibição inicial por classes.
   - Detalhamento por subclasses ao clicar em uma classe.
   - Detalhamento por ativos ao clicar em uma subclasse.
2. Criar gráfico de rendimento:
   - Exibição com base nos filtros aplicados.
   - Comparação com índices de referência (CDI ou IBOVESPA).

---

## **Sprint 9: Segurança e Gerenciamento de Usuários**
**Objetivo:** Adicionar autenticação e gerenciamento de usuários.
1. Implementar autenticação com usuário e senha.
2. Criar funcionalidades para o administrador gerenciar contas de usuários (criar, editar, desativar).
3. Testar acesso e permissões.

---

## **Sprint 10: Exportação e Relatórios**
**Objetivo:** Finalizar funcionalidades de exportação e análises.
1. Implementar exportação de dados filtrados para CSV.
2. Adicionar tabela secundária com ganho/prejuízo mensal por ativo.
3. Testar relatórios e validações.

---

## **Sprint 11: Refinamento e Ajustes Finais**
**Objetivo:** Garantir que o sistema está pronto para uso pessoal.
1. Testar todas as funcionalidades de ponta a ponta.
2. Corrigir bugs e ajustar melhorias na interface.
3. Configurar deploy final na plataforma escolhida.
