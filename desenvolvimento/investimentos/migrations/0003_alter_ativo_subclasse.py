# Generated by Django 5.1.5 on 2025-01-31 19:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("investimentos", "0002_alter_ativo_subclasse"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ativo",
            name="subclasse",
            field=models.CharField(
                choices=[
                    (
                        "Renda Fixa",
                        [
                            ("CDB", "CDB"),
                            ("Tesouro Direto", "Tesouro Direto"),
                            ("Fundo de Renda Fixa", "Fundo de Renda Fixa"),
                        ],
                    ),
                    (
                        "Renda Variável",
                        [
                            ("Ações", "Ações"),
                            ("Fundos de Ações", "Fundos de Ações"),
                            ("Fundos Multimercado", "Fundos Multimercado"),
                            ("FII", "FII"),
                            ("Criptomoeda", "Criptomoeda"),
                            ("Fundos no Exterior", "Fundos no Exterior"),
                        ],
                    ),
                ],
                max_length=50,
                verbose_name="Subclasse do Ativo",
            ),
        ),
    ]
