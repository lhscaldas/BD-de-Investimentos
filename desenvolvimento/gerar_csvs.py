import csv
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Lista de ativos a serem gerados
ativos = [
    {"nome": "Tesouro IPCA+", "classe": "Renda Fixa", "subclasse": "Tesouro Direto", "banco": "Banco do Brasil", "valor_inicial": 1000.00},
    {"nome": "Ações Petrobras", "classe": "Renda Variável", "subclasse": "Ações", "banco": "XP Investimentos", "valor_inicial": 5000.00},
    {"nome": "Criptomoeda Bitcoin", "classe": "Renda Variável", "subclasse": "Criptomoeda", "banco": "Binance", "valor_inicial": 30000.00},
    {"nome": "Fundo Imobiliário XPML11", "classe": "Renda Variável", "subclasse": "FII", "banco": "Rico", "valor_inicial": 1500.00},
    {"nome": "CDB Banco Inter", "classe": "Renda Fixa", "subclasse": "CDB", "banco": "Banco Inter", "valor_inicial": 5000.00},
    {"nome": "Ações Vale", "classe": "Renda Variável", "subclasse": "Ações", "banco": "Clear", "valor_inicial": 7000.00},
    {"nome": "Criptomoeda Ethereum", "classe": "Renda Variável", "subclasse": "Criptomoeda", "banco": "Binance", "valor_inicial": 1500.00},
    {"nome": "Fundo Multimercado XP", "classe": "Renda Variável", "subclasse": "Fundos Multimercado", "banco": "XP Investimentos", "valor_inicial": 4000.00},
    {"nome": "Tesouro Selic", "classe": "Renda Fixa", "subclasse": "Tesouro Direto", "banco": "Banco do Brasil", "valor_inicial": 2000.00},
    {"nome": "FII HGLG11", "classe": "Renda Variável", "subclasse": "FII", "banco": "BTG Pactual", "valor_inicial": 2500.00},
]

# Definição da data de aquisição inicial (janeiro de 2023)
data_inicio = datetime(2023, 1, 1)

# Gerar ativos.csv
with open("ativos.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, delimiter=";")
    writer.writerow(["Nome", "Classe", "Subclasse", "Banco", "Valor Inicial", "Data de Aquisição", "Observações"])

    for ativo in ativos:
        data_aquisicao = data_inicio + timedelta(days=random.randint(0, 30))  # Distribui a aquisição ao longo do mês
        writer.writerow([ativo["nome"], ativo["classe"], ativo["subclasse"], ativo["banco"], ativo["valor_inicial"], data_aquisicao.date(), ""])

# Gerar operacoes.csv
with open("operacoes.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, delimiter=";")
    writer.writerow(["Ativo", "Tipo", "Data", "Valor"])

    for ativo in ativos:
        data_atual = data_inicio
        valor_atual = ativo["valor_inicial"]

        while data_atual <= datetime(2025, 2, 1):
            # Gera uma operação de atualização mensal
            if ativo["classe"] == "Renda Fixa":
                valor_atual *= 1 + random.uniform(0.002, 0.005)  # Crescimento estável de 0.2% a 0.5% ao mês
            elif ativo["classe"] == "Renda Variável":
                valor_atual *= 1 + random.uniform(-0.05, 0.07)  # Oscilação entre -5% e +7%
            
            writer.writerow([ativo["nome"], "atualizacao", data_atual.date(), round(valor_atual, 2)])

            # Adiciona algumas compras e vendas aleatórias
            if random.random() < 0.3:  # 30% de chance de uma compra no mês
                compra_valor = random.uniform(0.5, 1.5) * ativo["valor_inicial"]
                writer.writerow([ativo["nome"], "compra", data_atual.date(), round(compra_valor, 2)])

            if random.random() < 0.2:  # 20% de chance de uma venda no mês
                venda_valor = random.uniform(0.5, 1.2) * ativo["valor_inicial"]
                writer.writerow([ativo["nome"], "venda", data_atual.date(), round(venda_valor, 2)])

            # Avança para o próximo mês
            data_atual += relativedelta(months=1)

print("Arquivos ativos.csv e operacoes.csv gerados com sucesso!")
