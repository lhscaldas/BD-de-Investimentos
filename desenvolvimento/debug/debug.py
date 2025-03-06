import pandas as pd

def load_data(folder='debug/'):
    # Carregar os datasets
    carteira = pd.read_csv(folder + 'carteira.csv', sep=';')
    ipca = pd.read_csv(folder + 'ipca.csv', sep=';')
    petro = pd.read_csv(folder + 'petro.csv', sep=';')
    bitcoin = pd.read_csv(folder + 'bitcoin.csv', sep=';')

    # Exibir as primeiras linhas dos DataFrames
    print("=== Primeiras linhas da carteira ===")
    print(carteira.head(), "\n")

    print("=== Primeiras linhas do IPCA ===")
    print(ipca.head(), "\n")

    print("=== Primeiras linhas do PETRO ===")
    print(petro.head(), "\n")

    print("=== Primeiras linhas do BITCOIN ===")
    print(bitcoin.head(), "\n")

    return carteira, ipca, petro, bitcoin

def check_data(carteira, ipca, petro, bitcoin):
    carteira['Soma Componentes'] = ipca['Valor'] + petro['Valor'] + bitcoin['Valor']
    carteira['Diferença'] = carteira['Valor da Carteira'] - carteira['Soma Componentes']
    
    print("=== Diferenças entre Valor da Carteira e soma das componentes ===")
    print(carteira[['Data Referência', 'Valor da Carteira', 'Soma Componentes', 'Diferença']].head())

    return carteira['Diferença'].abs().sum() < 1e-6

def check_data2(carteira, ipca, petro, bitcoin):
    carteira['Soma Rentabilidade Absoluta'] = ipca['Rentabilidade Absoluta'] + petro['Rentabilidade Absoluta'] + bitcoin['Rentabilidade Absoluta']
    carteira['Diferença Rentabilidade Absoluta'] = carteira['Rentabilidade Absoluta'] - carteira['Soma Rentabilidade Absoluta']
    
    print("=== Diferenças entre Rentabilidade Absoluta e soma das componentes ===")
    print(carteira[['Data Referência', 'Rentabilidade Absoluta', 'Soma Rentabilidade Absoluta', 'Diferença Rentabilidade Absoluta']].head())

    return carteira['Diferença Rentabilidade Absoluta'].abs().sum() < 1e-6

def check_data3(carteira):
    carteira['Calculado'] = carteira['Rentabilidade Absoluta'] / carteira['Valor da Carteira'] * 100
    carteira['Diferença Percentual'] = carteira['Rentabilidade Percentual'] - carteira['Calculado']
    
    print("=== Diferenças entre Rentabilidade Percentual calculada e original ===")
    print(carteira[['Data Referência', 'Rentabilidade Percentual', 'Calculado', 'Diferença Percentual']].head())

    return carteira['Diferença Percentual'].abs().sum() < 1e-1

# Verifica a rentabilidade absoluta da carteira 1m, 1a e total, pegando a rentabilidade abs do penultimo mês, a soma dos últimos 13 meses e a soma total
def check_data4(carteira):
    Rentabilidade_1m = carteira['Rentabilidade Absoluta'].iloc[-2]
    Rentabilidade_1a = carteira['Rentabilidade Absoluta'].iloc[-13:].sum()
    Rentabilidade_Total = carteira['Rentabilidade Absoluta'].sum()

    return Rentabilidade_1m, Rentabilidade_1a, Rentabilidade_Total

# Verifica a rentabilidade percentual da carteira 1m, 1a e total, pegando a rentabilidade abs do périodo e dividindo pelo valor da carteira no inicio do período
def check_data5(carteira):
    Rentabilidade_1m = carteira['Rentabilidade Absoluta'].iloc[-2]
    Rentabilidade_1a = carteira['Rentabilidade Absoluta'].iloc[-13:].sum()
    Rentabilidade_Total = carteira['Rentabilidade Absoluta'].sum()

    Rentabilidade_1m_perc = Rentabilidade_1m / carteira['Valor da Carteira'].iloc[-2] * 100
    Rentabilidade_1a_perc = Rentabilidade_1a / carteira['Valor da Carteira'].iloc[-13] * 100
    Rentabilidade_Total_perc = Rentabilidade_Total / carteira['Valor da Carteira'].iloc[0] * 100

    return Rentabilidade_1m_perc, Rentabilidade_1a_perc, Rentabilidade_Total_perc
    

# Executar o código
carteira, ipca, petro, bitcoin = load_data()
print("Check 1 (Soma dos Valores):", check_data(carteira, ipca, petro, bitcoin), "\n")
print("Check 2 (Soma Rentabilidade Absoluta):", check_data2(carteira, ipca, petro, bitcoin), "\n")
print("Check 3 (Cálculo da Rentabilidade Percentual):", check_data3(carteira), "\n")
print("Check 4 (Rentabilidades Absolutas da carteira):")
Rentabilidade_1m, Rentabilidade_1a, Rentabilidade_Total = check_data4(carteira)
print("Rentabilidade 1m:", Rentabilidade_1m)   
print("Rentabilidade 1a:", Rentabilidade_1a)
print("Rentabilidade Total:", Rentabilidade_Total, "\n")
print("Check 5 (Rentabilidades Percentuais da carteira):")
Rentabilidade_1m_perc, Rentabilidade_1a_perc, Rentabilidade_Total_perc = check_data5(carteira)
print("Rentabilidade 1m:", Rentabilidade_1m_perc)
print("Rentabilidade 1a:", Rentabilidade_1a_perc)
print("Rentabilidade Total:", Rentabilidade_Total_perc)

