import os
import django
import csv
import io
from datetime import datetime
from django.contrib.auth.hashers import make_password

# Configurar o Django para rodar fora do manage.py shell
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sgpi.settings")
django.setup()

from django.contrib.auth.models import User
from investimentos.models import Ativo, Operacao

# Nome e senha do usuário dummy
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

# Caminhos dos arquivos CSV
ativos_csv_path = "ativos.csv"
operacoes_csv_path = "operacoes.csv"

# Limpa os dados existentes
Ativo.objects.filter(usuario=user).delete()
Operacao.objects.filter(usuario=user).delete()

# Importa os ativos do CSV
try:
    with open(ativos_csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            nome = row["Nome"]
            classe = row["Classe"]
            subclasse = row["Subclasse"]
            banco = row["Banco"]
            valor_inicial = float(row["Valor Inicial"])
            data_aquisicao = datetime.strptime(row["Data de Aquisição"], "%Y-%m-%d").date()

            # Criar o ativo no banco de dados
            Ativo.objects.create(
                usuario=user,
                nome=nome,
                classe=classe,
                subclasse=subclasse,
                banco=banco,
                valor_inicial=valor_inicial,
                data_aquisicao=data_aquisicao
            )

    print("Ativos importados com sucesso!")
except Exception as e:
    print(f"Erro ao importar ativos: {e}")

# Importa as operações do CSV
try:
    with open(operacoes_csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")

        operacoes = []
        for row in reader:
            ativo_nome = row["Ativo"]
            tipo = row["Tipo"]
            data = datetime.strptime(row["Data"], "%Y-%m-%d").date()
            valor = float(row["Valor"])

            # Verifica se o ativo existe
            ativo = Ativo.objects.filter(nome=ativo_nome, usuario=user).first()
            if not ativo:
                print(f"Ativo '{ativo_nome}' não encontrado. Operação ignorada.")
                continue  # Pula esta linha se o ativo não for encontrado

            # Criar a operação no banco de dados
            operacoes.append(
                Operacao(
                    usuario=user,
                    ativo=ativo,
                    tipo=tipo,
                    data=data,
                    valor=valor
                )
            )

        # Salvar todas as operações em batch para otimizar a inserção
        Operacao.objects.bulk_create(operacoes)
    print("Operações importadas com sucesso!")
except Exception as e:
    print(f"Erro ao importar operações: {e}")

print("População inicial do banco de dados concluída com sucesso!")
