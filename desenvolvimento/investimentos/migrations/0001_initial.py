# Generated by Django 5.1.5 on 2025-01-31 15:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Ativo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(max_length=100, verbose_name="Nome do Ativo"),
                ),
                (
                    "classe",
                    models.CharField(
                        choices=[
                            ("Renda Fixa", "Renda Fixa"),
                            ("Renda Variável", "Renda Variável"),
                        ],
                        max_length=20,
                        verbose_name="Classe do Ativo",
                    ),
                ),
                (
                    "subclasse",
                    models.CharField(
                        choices=[
                            ("CDB", "CDB"),
                            ("Tesouro Direto", "Tesouro Direto"),
                            ("Fundo de Renda Fixa", "Fundo de Renda Fixa"),
                            ("Ações", "Ações"),
                            ("FII", "FII"),
                            ("Criptomoeda", "Criptomoeda"),
                            ("Fundos no Exterior", "Fundos no Exterior"),
                        ],
                        max_length=50,
                        verbose_name="Subclasse do Ativo",
                    ),
                ),
                ("banco", models.CharField(max_length=50, verbose_name="Banco")),
                (
                    "valor_inicial",
                    models.DecimalField(
                        decimal_places=2, max_digits=15, verbose_name="Valor Inicial"
                    ),
                ),
                ("data_aquisicao", models.DateField(verbose_name="Data de Aquisição")),
                (
                    "observacoes",
                    models.TextField(blank=True, null=True, verbose_name="Observações"),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "ativos",
                "verbose_name_plural": "ativos",
                "db_table": "ativos",
            },
        ),
        migrations.CreateModel(
            name="Operacao",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("compra", "Compra"),
                            ("venda", "Venda"),
                            ("atualizacao", "Atualização"),
                        ],
                        max_length=15,
                    ),
                ),
                ("valor", models.DecimalField(decimal_places=2, max_digits=15)),
                ("data", models.DateField()),
                (
                    "ativo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operacoes",
                        to="investimentos.ativo",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "operação",
                "verbose_name_plural": "operações",
                "db_table": "operacoes",
            },
        ),
    ]
