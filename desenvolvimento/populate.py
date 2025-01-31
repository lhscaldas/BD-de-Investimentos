import os
import django
import random
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password

# Configurar o Django para rodar fora do manage.py shell
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sgpi.settings")  # Substitua "sgpi" pelo nome do seu projeto
django.setup()

from django.contrib.auth.models import User
from investimentos.models import Ativo, Operacao

nome_dummy = "dummy"
senha_dummy = "du123456"

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
        data_aquisicao=datetime.today().date(),
    )
    ativos.append(ativo)

# Criar operações para cada ativo
for ativo in ativos:
    operacoes = []

    # 2 operações de compra
    for _ in range(2):
        operacoes.append(Operacao(
            usuario=user,
            ativo=ativo,
            tipo="compra",
            valor=random.randint(100, 5000),
            data=datetime.today().date() - timedelta(days=random.randint(10, 100)),
        ))

    # 2 operações de venda
    for _ in range(2):
        operacoes.append(Operacao(
            usuario=user,
            ativo=ativo,
            tipo="venda",
            valor=random.randint(100, 5000),
            data=datetime.today().date() - timedelta(days=random.randint(5, 90)),
        ))

    # 6 operações de atualização (uma por mês)
    for i in range(6):
        operacoes.append(Operacao(
            usuario=user,
            ativo=ativo,
            tipo="atualizacao",
            valor=random.randint(100, 5000),
            data=(datetime.today() - timedelta(days=30 * (i + 1))).date(),
        ))

    # Salvar todas as operações no banco
    Operacao.objects.bulk_create(operacoes)

print("População inicial do banco de dados concluída com sucesso!")
