# Generated by Django 5.1.5 on 2025-01-31 19:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("investimentos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ativo",
            name="subclasse",
            field=models.CharField(
                choices=[
                    ("CDB", "CDB"),
                    ("Tesouro Direto", "Tesouro Direto"),
                    ("Fundo de Renda Fixa", "Fundo de Renda Fixa"),
                    ("Ações", "Ações"),
                    ("Fundos de Ações", "Fundos de Ações"),
                    ("Fundos Multimercado", "Fundos Multimercad"),
                    ("FII", "FII"),
                    ("Criptomoeda", "Criptomoeda"),
                    ("Fundos no Exterior", "Fundos no Exterior"),
                ],
                max_length=50,
                verbose_name="Subclasse do Ativo",
            ),
        ),
    ]
