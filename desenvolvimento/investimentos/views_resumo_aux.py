from datetime import datetime
from collections import defaultdict
import json
import requests
import numpy as np
import yfinance as yf
import os

CACHE_FILE = "indices_cache.json"

def carregar_cache():
    """Carrega o cache do arquivo, se existir."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def salvar_cache(dados):
    """Salva os dados no arquivo de cache."""
    with open(CACHE_FILE, "w") as f:
        json.dump(dados, f)

def obter_indices_historicos(data_inicio, data_fim):
    try:
        # Carregar cache
        cache = carregar_cache()
        hoje = datetime.today().strftime("%Y-%m-%d")

        # Se já buscamos os dados hoje, retornamos do cache
        if cache.get("data_atualizacao") == hoje:
            print("Retornando dados do cache.")
            return cache.get("indices", {})

        # Converter datas para o formato YYYY-MM-DD
        data_inicio_iso = datetime.strptime(data_inicio, "%d/%m/%Y").strftime("%Y-%m-%d")
        data_fim_iso = datetime.strptime(data_fim, "%d/%m/%Y").strftime("%Y-%m-%d")

        # Baixar os dados do IBOVESPA via Yahoo Finance
        ibov = yf.Ticker("^BVSP")
        historico_ibov = ibov.history(start=data_inicio_iso, end=data_fim_iso, interval="1mo")

        ibov_mensal = {}
        if not historico_ibov.empty:
            ibov_por_mes = defaultdict(list)
            for data, row in historico_ibov.iterrows():
                mes_ano = data.strftime("%Y-%m")
                ibov_por_mes[mes_ano].append(row["Close"])

            meses_ordenados = sorted(ibov_por_mes.keys())
            for i in range(1, len(meses_ordenados)):
                mes_atual = meses_ordenados[i]
                mes_anterior = meses_ordenados[i - 1]

                valor_atual = ibov_por_mes[mes_atual][0]
                valor_anterior = ibov_por_mes[mes_anterior][0]

                if valor_anterior > 0:
                    ibov_mensal[mes_atual] = ((valor_atual / valor_anterior) - 1) * 100  # Percentual

        # Baixar os dados do CDI via API do Banco Central
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={data_inicio}&dataFinal={data_fim}"
        resposta = requests.get(url)
        cdi_mensal = {}

        if resposta.status_code == 200:
            dados_cdi = resposta.json()
            cdi_por_mes = defaultdict(list)
            for entrada in dados_cdi:
                data = datetime.strptime(entrada["data"], "%d/%m/%Y").date()
                mes_ano = data.strftime("%Y-%m")
                cdi_por_mes[mes_ano].append(float(entrada["valor"]) / 100)  # Convertendo para decimal

            cdi_mensal = {mes: (np.prod([1 + taxa for taxa in valores]) - 1) * 100 for mes, valores in cdi_por_mes.items()}

        # Salvar no cache
        indices = {
            "IBOVESPA": ibov_mensal,
            "CDI": cdi_mensal
        }
        cache = {
            "data_atualizacao": hoje,
            "indices": indices
        }
        salvar_cache(cache)

        return indices

    except Exception as e:
        print(f"Erro ao obter índices históricos: {e}")
        return {}
    
def calcular_indices_acumulados(meses_ordenados):
    # Carregar cache do arquivo JSON
        indices_historicos = {}
        if os.path.exists("indices_cache.json"):
            with open("indices_cache.json", "r") as f:
                try:
                    indices_historicos = json.load(f).get("indices", {})
                except json.JSONDecodeError:
                    indices_historicos = {}

        # Determinar período desejado
        data_inicio = meses_ordenados[0].strftime("%d/%m/%Y")
        data_fim = meses_ordenados[-1].strftime("%d/%m/%Y")

        # Converter datas para o formato YYYY-MM para comparação
        data_inicio_fmt = datetime.strptime(data_inicio, "%d/%m/%Y").strftime("%Y-%m")
        data_fim_fmt = datetime.strptime(data_fim, "%d/%m/%Y").strftime("%Y-%m")

        # Filtrar diretamente na view
        cdi_mensal_historico = {
            mes: valor for mes, valor in indices_historicos.get("CDI", {}).items()
            if data_inicio_fmt <= mes <= data_fim_fmt
        }

        ibov_mensal_historico = {
            mes: valor for mes, valor in indices_historicos.get("IBOVESPA", {}).items()
            if data_inicio_fmt <= mes <= data_fim_fmt
        }


        data_cdi = [1]  # CDI começa em 1 (100% do investimento inicial)
        data_ibov = [1]  # IBOVESPA começa em 1 (100% do investimento inicial)

        for i in range(1, len(meses_ordenados)):
            mes_atual = meses_ordenados[i]
            mes_atual_str = mes_atual.strftime("%Y-%m")

            # Obter CDI e IBOV mensal
            cdi_mensal = cdi_mensal_historico.get(mes_atual_str, 0)
            ibov_mensal = ibov_mensal_historico.get(mes_atual_str, 0)

            # Acumular CDI e IBOV
            cdi_acumulado = data_cdi[-1] * (1 + cdi_mensal / 100)
            ibov_acumulado = data_ibov[-1] * (1 + ibov_mensal / 100)

            data_cdi.append(cdi_acumulado)
            data_ibov.append(ibov_acumulado)

        # Converter para percentual antes de exibir no gráfico
        data_cdi_percentual = [(valor - 1) * 100 for valor in data_cdi]
        data_ibov_percentual = [(valor - 1) * 100 for valor in data_ibov]

        return data_cdi_percentual, data_ibov_percentual