# -*- coding: utf-8 -*-
import json
import os
import time
import pandas as pd
import numpy as np
import yfinance as yf

ARQUIVO_UNIVERSO = "universo_b3.json"
ARQUIVO_FALLBACK = "universo_b3.json"
ARQUIVO_SAIDA_CSV = "scanner_fechamento.csv"

def carregar_catalogo_ativos():
    """Carrega o catálogo completo de ativos da B3 (prioriza universo_b3.json)."""
    if os.path.exists(ARQUIVO_UNIVERSO):
        try:
            with open(ARQUIVO_UNIVERSO, "r", encoding="utf-8") as f:
                catalogo = json.load(f)
                print(f"[CATÁLOGO] Carregados {len(catalogo)} ativos de '{ARQUIVO_UNIVERSO}'.")
                return catalogo
        except Exception as e:
            print(f"[AVISO] Falha ao ler {ARQUIVO_UNIVERSO}: {e}")

    if os.path.exists(ARQUIVO_FALLBACK):
        try:
            with open(ARQUIVO_FALLBACK, "r", encoding="utf-8") as f:
                tickers = json.load(f)
                return [{"ticker": t.replace(".SA", "").strip(), "tipo": "ACAO", "nome": t} for t in tickers]
        except Exception:
            pass

    # Fallback de contingência mínima
    return [
        {"ticker": "PETR4", "tipo": "ACAO", "nome": "Petrobras PN"},
        {"ticker": "VALE3", "tipo": "ACAO", "nome": "Vale ON"},
        {"ticker": "ITUB4", "tipo": "ACAO", "nome": "Itaú Unibanco PN"},
        {"ticker": "HGLG11", "tipo": "FII", "nome": "CSHG Logística"},
        {"ticker": "IVVB11", "tipo": "ETF", "nome": "iShares S&P 500"}
    ]

def calcular_indicadores_tecnicos(df_d, df_w):
    """Calcula indicadores clássicos e de reversão à média (Larry Connors)."""
    fechamento = df_d["Close"]
    preco_atual = float(fechamento.iloc[-1])

    # SMA 200 (tendência primária)
    sma200 = float(fechamento.rolling(window=200, min_periods=10).mean().iloc[-1])
    if np.isnan(sma200):
        sma200 = float(fechamento.mean())

    # SMA 5 (alvo de reversão curta)
    sma5 = float(fechamento.rolling(window=5, min_periods=2).mean().iloc[-1])

    # IFR(2) - Índice de Força Relativa de 2 períodos
    delta = fechamento.diff()
    ganho = delta.where(delta > 0, 0.0)
    perda = -delta.where(delta < 0, 0.0)
    media_ganho = ganho.rolling(window=2, min_periods=2).mean()
    media_perda = perda.rolling(window=2, min_periods=2).mean()

    # Proteção de divisão por zero
    denominador = media_perda.iloc[-1]
    if denominador == 0.0 or np.isnan(denominador):
        rsi2 = 100.0 if media_ganho.iloc[-1] > 0 else 50.0
    else:
        rs = media_ganho.iloc[-1] / denominador
        rsi2 = float(100.0 - (100.0 / (1.0 + rs)))

    if np.isnan(rsi2):
        rsi2 = 50.0

    # Bandas de Bollinger (%b de 20 períodos)
    sma20 = fechamento.rolling(window=20, min_periods=5).mean()
    std20 = fechamento.rolling(window=20, min_periods=5).std()
    banda_superior = sma20 + (2.0 * std20)
    banda_inferior = sma20 - (2.0 * std20)

    bs_val = float(banda_superior.iloc[-1])
    bi_val = float(banda_inferior.iloc[-1])
    if bs_val != bi_val and not np.isnan(bs_val) and not np.isnan(bi_val):
        pct_b = float((preco_atual - bi_val) / (bs_val - bi_val))
    else:
        pct_b = 0.5

    # Classificação de Swing Trade
    if preco_atual > sma200 and rsi2 <= 15:
        fase = "Sobrevendido (Oportunidade)"
    elif preco_atual > sma200 and rsi2 >= 85:
        fase = "Sobrecomprado (Risco)"
    elif preco_atual > sma200:
        fase = "Tendência de Alta Forte"
    elif preco_atual < sma200 and rsi2 <= 15:
        fase = "Sobrevendido em Tendência Baixa"
    elif preco_atual < sma200:
        fase = "Tendência de Baixa"
    else:
        fase = "Lateralização / Neutro"

    return {
        "Preço (R$)": round(preco_atual, 2),
        "SMA 200": round(sma200, 2),
        "SMA 5": round(sma5, 2),
        "RSI(2)": round(rsi2, 1),
        "ConnorsRSI": round(rsi2, 1),
        "Percent_B": round(pct_b, 2),
        "Swing Trade": fase
    }

def avaliar_saude_fundamentalista(info, tipo_ativo):
    """Estima score de 0 a 100 de acordo com a classe de ativo."""
    if tipo_ativo in ["FII", "FIAGRO"]:
        dy = info.get("dividendYield", 0) or 0
        p_vp = info.get("priceToBook", 1.0) or 1.0
        score = 65
        if dy >= 0.09: score += 15
        if 0.85 <= p_vp <= 1.05: score += 15
        return min(max(score, 40), 95), "Bom" if score >= 75 else "Regular"

    if tipo_ativo == "ETF":
        return 75, "Bom"

    # Ações e BDRs
    roe = info.get("returnOnEquity", 0) or 0
    margem = info.get("profitMargins", 0) or 0
    score = 50
    if roe > 0.15: score += 20
    elif roe > 0.08: score += 10
    if margem > 0.10: score += 15
    elif margem > 0.05: score += 5

    if score >= 80:
        return score, "Excelente"
    elif score >= 65:
        return score, "Bom"
    return score, "Regular"

def executar_scanner():
    catalogo = carregar_catalogo_ativos()
    total = len(catalogo)
    print(f"\n[SCANNER] Iniciando processamento quantitativo de {total} ativos...")

    resultados = []
    for i, item in enumerate(catalogo, 1):
        t_raw = item.get("ticker", "").strip().upper().replace(".SA", "")
        tipo = item.get("tipo", "ACAO")
        nome = item.get("nome", t_raw)
        simbolo_yf = f"{t_raw}.SA"

        print(f"[{i}/{total}] Baixando {t_raw} ({tipo} - {nome})...", end="", flush=True)

        try:
            ativo = yf.Ticker(simbolo_yf)
            df_d = ativo.history(period="1y", interval="1d")

            if df_d.empty or len(df_d) < 3:
                print(" [SEM HISTÓRICO - PULADO]")
                continue

            ind = calcular_indicadores_tecnicos(df_d, None)
            
            # Tenta colher dados complementares com tolerância a falhas
            info = {}
            try:
                info = ativo.info or {}
            except Exception:
                pass

            score_num, score_lbl = avaliar_saude_fundamentalista(info, tipo)

            registro = {
                "Ticker": t_raw,
                "Tipo": tipo,
                "Nome": nome,
                "Preço (R$)": ind["Preço (R$)"],
                "SMA 200": ind["SMA 200"],
                "SMA 5": ind["SMA 5"],
                "RSI(2)": ind["RSI(2)"],
                "ConnorsRSI": ind["ConnorsRSI"],
                "Percent_B": ind["Percent_B"],
                "Swing Trade": ind["Swing Trade"],
                "Score Fundamentalista": f"{score_num} ({score_lbl})"
            }
            resultados.append(registro)
            print(" [OK]")
            time.sleep(0.15)  # Intervalo de segurança para requisições Yahoo Finance

        except Exception as e:
            print(f" [ERRO: {e}]")
            continue

    if resultados:
        df_final = pd.DataFrame(resultados)
        df_final.to_csv(ARQUIVO_SAIDA_CSV, index=False, encoding="utf-8-sig")
        print(f"\n[SUCESSO] Base consolidada com {len(df_final)} ativos em '{ARQUIVO_SAIDA_CSV}'!")
    else:
        print("\n[ERRO CRÍTICO] Nenhum ativo pôde ser consolidado.")

if __name__ == "__main__":
    executar_scanner()
