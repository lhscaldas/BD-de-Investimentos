import os
import django
import random
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password

# Configurar o Django para rodar fora do manage.py shell
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sgpi.settings")  
django.setup()

from django.contrib.auth.models import User
from investimentos.models import Ativo, Operacao

nome_dummy = "dummy"
senha_dummy = "du123456"

# Excluir o usuário 'dummy' se ele já existir
User.objects.filter(username=nome_dummy).delete()

# Criar ou obter usuário 'dummy'
user, created = User.objects.get_or_create(
    username=nome_dummy,
    defaults={
        "first_name": "Dummy",
        "last_name": "User",
        "password": make_password(senha_dummy)  # Garante que a senha seja criptografada
    }
)

# Lista de ativos para criar
ativos_data = [
    {"nome": "Tesouro IPCA+", "classe": "Renda Fixa", "subclasse": "Tesouro Direto", "banco": "Banco do Brasil", "valor_inicial": 1000},
    {"nome": "Ações Petrobras", "classe": "Renda Variável", "subclasse": "Ações", "banco": "XP Investimentos", "valor_inicial": 5000},
    {"nome": "Criptomoeda Bitcoin", "classe": "Renda Variável", "subclasse": "Criptomoeda", "banco": "Binance", "valor_inicial": 30000},
    {"nome": "Fundo Imobiliário XPML11", "classe": "Renda Variável", "subclasse": "FII", "banco": "Rico", "valor_inicial": 1500},
]

# Criar os ativos
ativos = []
for ativo_data in ativos_data:
    ativo, created = Ativo.objects.get_or_create(
        usuario=user,
        nome=ativo_data["nome"],
        classe=ativo_data["classe"],
        subclasse=ativo_data["subclasse"],
        banco=ativo_data["banco"],
        valor_inicial=ativo_data["valor_inicial"],
        data_aquisicao=datetime(2024, 1, random.randint(1, 31)).date(),
    )
    ativos.append(ativo)

# Criar operações para cada ativo
for ativo in ativos:
    operacoes = []
    valor_atual = ativo.valor_inicial

    # Parâmetros de variação por classe
    if ativo.classe == "Renda Fixa":
        crescimento_anual = 0.06  # Crescimento médio de 6% ao ano
        variacao_mensal = (crescimento_anual / 12)  # Crescimento constante por mês
        volatilidade = 0.01  # Pouca variação

    elif ativo.subclasse in ["Ações", "FII"]:
        crescimento_anual = 0.10  # Crescimento médio de 10% ao ano
        variacao_mensal = (crescimento_anual / 12)
        volatilidade = 0.05  # Oscilação moderada

    elif ativo.subclasse == "Criptomoeda":
        crescimento_anual = 0.20  # Expectativa de maior crescimento (20% ao ano)
        variacao_mensal = (crescimento_anual / 12)
        volatilidade = 0.15  # Alta volatilidade

    else:
        crescimento_anual = 0.08
        variacao_mensal = (crescimento_anual / 12)
        volatilidade = 0.03  # Default para outros ativos

    # 4 operações de compra
    for _ in range(4):
        valor = valor_atual * (1 + variacao_mensal + random.uniform(-volatilidade, volatilidade))
        operacoes.append(Operacao(
            usuario=user,
            ativo=ativo,
            tipo="compra",
            valor=valor,
            data=ativo.data_aquisicao + timedelta(days=random.randint(1, 100)),
        ))
        valor_atual = valor

    # 4 operações de venda
    for _ in range(4):
        valor = valor_atual * (1 - variacao_mensal + random.uniform(-volatilidade, volatilidade))
        operacoes.append(Operacao(
            usuario=user,
            ativo=ativo,
            tipo="venda",
            valor=valor,
            data=ativo.data_aquisicao + timedelta(days=random.randint(1, 100)),
        ))
        valor_atual = valor

    # 12 operações de atualização (uma por mês)
    for i in range(12):
        valor = valor_atual * (1 + variacao_mensal + random.uniform(-volatilidade, volatilidade))
        operacoes.append(Operacao(
            usuario=user,
            ativo=ativo,
            tipo="atualizacao",
            valor=valor,
            data=ativo.data_aquisicao + timedelta(days=30 * (i + 1)),
        ))
        valor_atual = valor

    # Salvar todas as operações no banco
    Operacao.objects.bulk_create(operacoes)

print("População inicial do banco de dados concluída com sucesso!")
