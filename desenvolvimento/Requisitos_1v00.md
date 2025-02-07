# Requisitos do Sistema de Gerenciamento de Portfólio de Investimentos

## Banco de Dados
- ~~**[BD_01]** O banco de dados deverá ser capaz de registrar informações detalhadas de cada ativo, incluindo:~~
   - Usuário.
   - Nome do ativo.
   - Classe e subclasse.
   - Banco em que está registrado.
   - Valor inicial.
   - Data de aquisição inicial.
   - Observações opcionais.
- ~~**[BD_02]** O banco de dados deverá ser capaz de armazenar operações realizadas para cada ativo, incluindo:~~
   - Usuário.
   - Nome do ativo.
   - Tipo de operação (compra, venda ou atualização).
   - Valor da operação.
   - Data da operação.
1. **(Sprint+7):**
- **[BD_03]** O banco de dados deverá garantir que os dados sejam criptografados, impedindo acesso direto, inclusive para o administrador.

---

## Funcionalidades para o Usuário
- ~~**[USER_01]** O sistema deverá permitir o registro manual de um ativo com todos os seus detalhes iniciais (nome, classe, subclasse, banco, valor inicial, data e observações).~~
- ~~**[USER_02]** O sistema deverá permitir a edição ou remoção de um ativo registrado, incluindo alterações no nome, banco, valor inicial, data de aquisição e observações.~~
- ~~**[USER_03]** O sistema deverá permitir o registro manual de uma operação (compra, venda ou atualização) para ativos já criados.~~

-  ~~**[USER_04]** O sistema deverá permitir o upload de um arquivo CSV para registrar múltiplas operações de compra, venda ou atualização de ativos já criados. O arquivo deverá seguir um formato pré-definido pelo sistema, incluindo os seguintes campos:~~
   - Nome do ativo.
   - Tipo de operação (compra, venda ou atualização).
   - Valor da operação.
   - Data da operação.
-  ~~**[USER_05]** O sistema deverá permitir o upload de um arquivo CSV para registrar múltiplas criações de ativos. O arquivo deverá seguir um formato pré-definido pelo sistema, incluindo os seguintes campos:~~
   - Nome do ativo.
   - Classe e subclasse.
   - Banco em que está registrado.
   - Valor inicial.
   - Data de aquisição inicial.
   - Observações opcionais.

- ~~**[USER_06]** O sistema deverá validar o formato dos arquivos de CSV antes de processar as operações.~~
- ~~**[USER_07]** O sistema deverá permitir que o administrador crie, edite e desative contas de usuários.~~
- ~~**[USER_08]** O sistema deverá implementar autenticação por usuário e senha para acesso ao sistema.~~

---

## Interface (Resumo)
1. **(Sprint+1):**
   - ~~**[UI_01]** A interface deverá exibir o nome do ativo.~~
   - ~~**[UI_02]** A interface deverá exibir a classe e subclasse do ativo.~~
   - ~~**[UI_03]** A interface deverá exibir o banco em que o ativo está registrado.~~
   - ~~**[UI_04]** A interface deverá exibir o valor atual do ativo, calculado com base nas operações registradas.~~
   - ~~**[UI_05]** A interface deverá exibir as observações relacionadas ao ativo, quando fornecidas.~~
   - ~~**[UI_06]** A interface deverá incluir botões para:~~
      - Registrar novos ativos.
      - Registrar novas operações (compra, venda ou atualização) para ativos existentes.

2. **(Sprint+2):**
   - ~~**[UI_07]** A interface deverá permitir filtros por:~~
      - Classe.
      - Subclasse.
      - Banco.

3. **(Sprint+3):**
   - **[UI_08]** A interface deverá exibir o total do patrimônio, considerando os filtros aplicados.
   - **[UI_09]** A interface deverá exibir o total das rentabilidades, considerando os filtros aplicados.
   - **[UI_10]** A interface deverá exibir o ganho ou prejuízo mensal por ativo, em:
      - Valor absoluto (R$).
      - Rentabilidade percentual.

4. **(Sprint+4):**
   - **[UI_11]** A interface deverá incluir um gráfico de rendimento:
      - Exibindo rendimento com base nos filtros aplicados.
      - Comparando o rendimento total com índices de referência (CDI ou IBOVESPA), selecionáveis pelo usuário.

5. **(Sprint+5):**
   - **[UI_12]** A interface deverá incluir um gráfico de alocação em formato de pizza:
      - Exibindo inicialmente a distribuição por classes.
      - Possibilitando detalhar por subclasses ao clicar em uma classe.
      - Possibilitando detalhar por ativos ao clicar em uma subclasse.

6. **(Sprint+6):**
   - **[UI_13]** O sistema deverá permitir que o usuário exporte os dados atuais para um arquivo CSV, incluindo:
      - Nome dos ativos.
      - Classe dos ativos.
      - Subclasse dos ativos.
      - Banco onde estão registrados.
      - Valor atual dos ativos.
      - Rentabilidades calculadas.
      - Observações relacionadas aos ativos.
      - Filtros aplicados no momento da exportação.

