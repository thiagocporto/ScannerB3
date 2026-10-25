# -*- coding: utf-8 -*-
import json
import os
import time
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf

# Item E: Caminhos absolutos blindados via Path(__file__)
BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_UNIVERSO = BASE_DIR / "universo_b3.json"
ARQUIVO_FALLBACK = BASE_DIR / "ibrx100_tickers.json"
ARQUIVO_SAIDA_CSV = BASE_DIR / "scanner_fechamento.csv"

JANELA_SMA_LONGA = 200
JANELA_SMA_CURTA = 5
JANELA_BOLLINGER = 20
N_RSI_CURTO = 2
N_RSI_CRSI_PRECO = 3
N_RSI_CRSI_STREAK = 2
N_PERCENT_RANK = 100

def carregar_catalogo_ativos():
    if ARQUIVO_UNIVERSO.exists():
        try:
            with open(ARQUIVO_UNIVERSO, "r", encoding="utf-8") as f:
                dados = json.load(f)
                catalogo = []
                for item in dados:
                    if isinstance(item, dict):
                        catalogo.append(item)
                    else:
                        t_str = str(item).replace(".SA", "").strip()
                        catalogo.append({"ticker": t_str, "tipo": "ACAO", "nome": t_str})
                print(f"[CATALOGO] Carregados {len(catalogo)} ativos de '{ARQUIVO_UNIVERSO.name}'.")
                return catalogo
        except Exception as e:
            print(f"[AVISO] Falha ao ler {ARQUIVO_UNIVERSO.name}: {e}")

    if ARQUIVO_FALLBACK.exists():
        try:
            with open(ARQUIVO_FALLBACK, "r", encoding="utf-8") as f:
                tickers = json.load(f)
                catalogo = []
                for t in tickers:
                    if isinstance(t, dict):
                        catalogo.append(t)
                    else:
                        t_str = str(t).replace(".SA", "").strip()
                        catalogo.append({"ticker": t_str, "tipo": "ACAO", "nome": t_str})
                print(f"[CATALOGO] Fallback: {len(catalogo)} ativos de '{ARQUIVO_FALLBACK.name}'.")
                return catalogo
        except Exception as e:
            print(f"[AVISO] Falha ao ler {ARQUIVO_FALLBACK.name}: {e}")

    return [
        {"ticker": "PETR4", "tipo": "ACAO", "nome": "Petrobras PN"},
        {"ticker": "VALE3", "tipo": "ACAO", "nome": "Vale ON"},
        {"ticker": "ITUB4", "tipo": "ACAO", "nome": "Itau Unibanco PN"},
        {"ticker": "HGLG11", "tipo": "FII", "nome": "CSHG Logistica"},
        {"ticker": "IVVB11", "tipo": "ETF", "nome": "iShares S&P 500"}
    ]

# Item D: Semente Aritmetica Exata de Wilder no RSI
def calcular_rsi(serie: pd.Series, periodo: int = 2) -> pd.Series:
    delta = serie.diff()
    ganho = delta.where(delta > 0, 0.0).values
    perda = (-delta).where(delta < 0, 0.0).values
    tam = len(serie)
    rsi = np.full(tam, np.nan)

    if tam <= periodo:
        return pd.Series(rsi, index=serie.index)

    mg = np.mean(ganho[1 : periodo + 1])
    mp = np.mean(perda[1 : periodo + 1])

    if mp == 0.0:
        rsi[periodo] = 100.0 if mg > 0.0 else 50.0
    else:
        rsi[periodo] = 100.0 - (100.0 / (1.0 + mg / mp))

    alpha = 1.0 / periodo
    for i in range(periodo + 1, tam):
        mg = (mg * (periodo - 1) + ganho[i]) * alpha
        mp = (mp * (periodo - 1) + perda[i]) * alpha
        if mp == 0.0:
            rsi[i] = 100.0 if mg > 0.0 else 50.0
        else:
            rsi[i] = 100.0 - (100.0 / (1.0 + mg / mp))

    return pd.Series(rsi, index=serie.index)

def calcular_streak(series_close: pd.Series) -> pd.Series:
    streak = [0]
    for i in range(1, len(series_close)):
        diff = series_close.iloc[i] - series_close.iloc[i-1]
        if diff > 0:
            streak.append(streak[-1] + 1 if streak[-1] > 0 else 1)
        elif diff < 0:
            streak.append(streak[-1] - 1 if streak[-1] < 0 else -1)
        else:
            streak.append(0)
    return pd.Series(streak, index=series_close.index)

def calcular_percent_rank(series_retorno: pd.Series, periodo: int = 100) -> pd.Series:
    def rank_func(window):
        val_atual = window[-1]
        menores = np.sum(window[:-1] < val_atual)
        return (menores / (len(window) - 1)) * 100.0 if len(window) > 1 else 50.0
    return series_retorno.rolling(window=periodo + 1).apply(rank_func, raw=True)

def calcular_connors_rsi(series_close: pd.Series) -> pd.Series:
    rsi_preco = calcular_rsi(series_close, periodo=3)
    streak = calcular_streak(series_close)
    rsi_streak = calcular_rsi(streak, periodo=2)
    retorno_diario = series_close.pct_change()
    prank = calcular_percent_rank(retorno_diario, periodo=100)
    return (rsi_preco + rsi_streak + prank) / 3.0

def calcular_bollinger_percent_b(series_close: pd.Series, periodo: int = 20, desvios: float = 2.0) -> pd.Series:
    media = series_close.rolling(window=periodo).mean()
    desvio = series_close.rolling(window=periodo).std()
    banda_superior = media + (desvios * desvio)
    banda_inferior = media - (desvios * desvio)
    largura = banda_superior - banda_inferior
    percent_b = np.where(largura == 0, 0.5, (series_close - banda_inferior) / largura)
    return pd.Series(percent_b, index=series_close.index)

def _num(info, chave):
    v = info.get(chave)
    if isinstance(v, (int, float, np.number)) and not isinstance(v, bool) and not np.isnan(v):
        return float(v)
    return None

def _escala(x, x_ruim, x_bom):
    if x is None or np.isnan(x) or x_bom == x_ruim:
        return None
    p = (x - x_ruim) / (x_bom - x_ruim) * 100.0
    return float(min(max(p, 0.0), 100.0))

def _media(valores):
    v = [x for x in valores if x is not None and not np.isnan(x)]
    return float(np.mean(v)) if v else None

def _rotulo(score):
    if score >= 80:
        return "Excelente"
    elif score >= 65:
        return "Bom"
    elif score >= 45:
        return "Regular"
    return "Fraco"

# Item C: Sanitizacao de unidades (DY, ROE, Margem, D/PL) e mapeamento setorial financeiro
def calcular_score_fundamentalista(info: dict) -> str:
    if not info or not isinstance(info, dict):
        return "N/D"

    pontos = 0
    dados_encontrados = 0

    roe = info.get("returnOnEquity")
    if roe is not None and not np.isnan(roe):
        if abs(roe) > 2.0:
            roe = roe / 100.0
        dados_encontrados += 1
        if roe >= 0.20:
            pontos += 25
        elif roe >= 0.12:
            pontos += 18
        elif roe > 0:
            pontos += 10

    margem = info.get("profitMargins")
    if margem is not None and not np.isnan(margem):
        if abs(margem) > 2.0:
            margem = margem / 100.0
        dados_encontrados += 1
        if margem >= 0.15:
            pontos += 25
        elif margem >= 0.08:
            pontos += 18
        elif margem > 0:
            pontos += 10

    setor = str(info.get("sector") or "").lower()
    industria = str(info.get("industry") or "").lower()
    texto_setor = f"{setor} {industria}"
    termos_fin = ["financial", "bank", "insurance", "segur", "credito", "asset management", "capital markets"]

    if any(f in texto_setor for f in termos_fin):
        dados_encontrados += 1
        pontos += 25  # Atribui pontuação neutra/saudável robusta para bancos/seguradoras sem penalizar endividamento
    else:
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity is not None and not np.isnan(debt_to_equity):
            if debt_to_equity > 5.0:
                debt_to_equity = debt_to_equity / 100.0
            dados_encontrados += 1
            if debt_to_equity < 0.80:
                pontos += 25
            elif debt_to_equity <= 1.40:
                pontos += 18
            elif debt_to_equity <= 2.00:
                pontos += 10

    pe = info.get("trailingPE")
    pb = info.get("priceToBook")
    if pe is not None and not np.isnan(pe) and pe > 0:
        dados_encontrados += 1
        if 3.0 <= pe <= 12.0:
            pontos += 25
        elif 12.0 < pe <= 18.0:
            pontos += 18
        elif pe <= 25.0:
            pontos += 10
    elif pb is not None and not np.isnan(pb) and pb > 0:
        dados_encontrados += 1
        if pb <= 1.5:
            pontos += 20
        elif pb <= 2.5:
            pontos += 12

    if dados_encontrados == 0:
        return "N/D"

    if pontos >= 80:
        return f"{pontos} (Excelente)"
    elif pontos >= 60:
        return f"{pontos} (Bom)"
    elif pontos >= 40:
        return f"{pontos} (Regular)"
    else:
        return f"{pontos} (Fraco)"

def analisar_ativo(df_diario: pd.DataFrame, df_semanal: pd.DataFrame, info: dict = None) -> dict:
    # Item A: Consistencia de base unica usando Close puro (sem misturar com Adj Close)
    fechamento_d = df_diario["Close"].dropna()
    volume_d = df_diario["Volume"]

    # Médias diárias
    sma200_d = fechamento_d.rolling(window=200, min_periods=10).mean()
    ema50_d = fechamento_d.ewm(span=50, adjust=False).mean()
    ema21_d = fechamento_d.ewm(span=21, adjust=False).mean()
    sma5_d = fechamento_d.rolling(window=5, min_periods=2).mean()
    vol_medio20_d = volume_d.rolling(window=20, min_periods=5).mean()

    # Indicadores Quantitativos
    rsi2_series = calcular_rsi(fechamento_d, periodo=2)
    crsi_series = calcular_connors_rsi(fechamento_d)
    percent_b_series = calcular_bollinger_percent_b(fechamento_d, periodo=20, desvios=2.0)

    # Semanal
    fechamento_w = df_semanal["Close"]
    sma20_w = fechamento_w.rolling(window=20, min_periods=5).mean()

    preco_atual = float(fechamento_d.iloc[-1])
    sma200_val = float(sma200_d.iloc[-1]) if not pd.isna(sma200_d.iloc[-1]) else np.nan
    ema50_val = float(ema50_d.iloc[-1]) if not pd.isna(ema50_d.iloc[-1]) else preco_atual
    ema21_val = float(ema21_d.iloc[-1]) if not pd.isna(ema21_d.iloc[-1]) else preco_atual
    sma5_val = float(sma5_d.iloc[-1]) if not pd.isna(sma5_d.iloc[-1]) else preco_atual
    
    rsi2_val = float(rsi2_series.iloc[-1]) if not pd.isna(rsi2_series.iloc[-1]) else 50.0
    crsi_val = float(crsi_series.iloc[-1]) if not pd.isna(crsi_series.iloc[-1]) else 50.0
    percent_b_val = float(percent_b_series.iloc[-1]) if not pd.isna(percent_b_series.iloc[-1]) else 0.5
    sma20_w_val = float(sma20_w.iloc[-1]) if len(sma20_w.dropna()) > 0 else preco_atual

    vol_atual = float(volume_d.iloc[-1]) if not pd.isna(volume_d.iloc[-1]) else 0
    vol_medio_val = float(vol_medio20_d.iloc[-1]) if not pd.isna(vol_medio20_d.iloc[-1]) else 1
    volume_acima_media = vol_atual > vol_medio_val

    # Item B: Protecao contra NaN na SMA 200 (nao joga ativos novos em Tendencia de Baixa)
    if np.isnan(sma200_val):
        sma200_efetiva = preco_atual
        alta_macro = False
        baixa_macro = False
    else:
        sma200_efetiva = sma200_val
        alta_macro = (preco_atual > sma200_efetiva) and (preco_atual > ema50_val)
        baixa_macro = (preco_atual < sma200_efetiva) and (preco_atual < ema50_val)

    em_pullback = preco_atual < ema21_val
    sobrevendido_raro = (rsi2_val <= 15.0) or (crsi_val <= 15.0)
    bollinger_esticado = percent_b_val <= 0.20
    sobrecomprado = (rsi2_val >= 85.0) or (crsi_val >= 85.0)

    upside_sma5 = ((sma5_val - preco_atual) / preco_atual) * 100.0 if preco_atual > 0 else 0.0

    gatilho_swing = False
    if np.isnan(sma200_val):
        status_swing = "Lateralização / Neutro"
    elif alta_macro and em_pullback and sobrevendido_raro and bollinger_esticado:
        status_swing = "🔥 COMPRA ALTA PROBABILIDADE"
        gatilho_swing = True
    elif alta_macro and sobrevendido_raro:
        status_swing = "Atenção: Sobrevendido em Alta"
    elif alta_macro and sobrecomprado:
        status_swing = "Sobrecomprado (Risco de Correção)"
    elif alta_macro and em_pullback:
        status_swing = "Pullback em Alta (Aguardando Gatilho)"
    elif alta_macro:
        status_swing = "Tendência de Alta Forte"
    elif baixa_macro and sobrevendido_raro:
        status_swing = "Tendência de Baixa (Sobrevendido)"
    elif baixa_macro:
        status_swing = "Tendência de Baixa"
    else:
        status_swing = "Lateralização / Neutro"

    status_position = "Alta Estrutural (Semanal)" if preco_atual > sma20_w_val else "Abaixo da Média Semanal"
    score_fund = calcular_score_fundamentalista(info)

    return {
        "Preço (R$)": round(preco_atual, 2),
        "SMA 200": round(sma200_efetiva, 2),
        "Alvo SMA 5": round(sma5_val, 2),
        "Upside (%)": round(upside_sma5, 2),
        "IFR(2)": round(rsi2_val, 1),
        "ConnorsRSI": round(crsi_val, 1),
        "%b Bollinger": round(percent_b_val, 2),
        "Swing Trade": status_swing,
        "Position Trade": status_position,
        "Gatilho_Swing": gatilho_swing,
        "Score Fundamentalista": score_fund,
    }

def executar_scanner():
    print("=== MOTOR QUANTITATIVO: WILDER EXATO + CLOSE UNIFICADO + SANITIZAÇÃO ===")
    if ARQUIVO_UNIVERSO.exists():
        caminho_ativo = ARQUIVO_UNIVERSO
    elif ARQUIVO_FALLBACK.exists():
        caminho_ativo = ARQUIVO_FALLBACK
    else:
        caminho_ativo = None

    tickers = []
    if caminho_ativo:
        try:
            with open(caminho_ativo, "r", encoding="utf-8") as f:
                dados = json.load(f)
                for item in dados:
                    if isinstance(item, dict):
                        tickers.append(item.get("ticker", ""))
                    else:
                        tickers.append(str(item))
        except Exception:
            pass

    if not tickers:
        tickers = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "WEGE3", "RENT3"]

    resultados = []
    total = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        ticker_limpo = str(ticker).replace(".SA", "").replace(".sa", "").strip().upper()
        if not ticker_limpo:
            continue
        simbolo_yf = f"{ticker_limpo}.SA"
        print(f"[{i:03d}/{total:03d}] Analisando {ticker_limpo}...")
        try:
            ativo = yf.Ticker(simbolo_yf)
            df_d = ativo.history(period="2y", interval="1d")
            df_w = ativo.history(period="2y", interval="1wk")

            if df_d.empty or len(df_d) < 10:
                continue

            info = {}
            try:
                info = ativo.info or {}
            except Exception:
                pass

            analise = analisar_ativo(df_d, df_w, info=info)
            analise["Ticker"] = ticker_limpo
            resultados.append(analise)
            time.sleep(0.1)
        except Exception:
            continue

    if resultados:
        df_final = pd.DataFrame(resultados)
        colunas_ordenadas = [
            "Ticker", "Preço (R$)", "SMA 200", "Alvo SMA 5", "Upside (%)",
            "IFR(2)", "ConnorsRSI", "%b Bollinger",
            "Swing Trade", "Position Trade", "Score Fundamentalista", "Gatilho_Swing"
        ]
        df_final = df_final[[c for c in colunas_ordenadas if c in df_final.columns]]
        df_final.to_csv(ARQUIVO_SAIDA_CSV, index=False, encoding="utf-8-sig")
        print(f"\n✅ Base salva com sucesso em '{ARQUIVO_SAIDA_CSV.name}' ({len(df_final)} ativos).")
    else:
        print("\nNenhum dado pôde ser compilado.")

if __name__ == "__main__":
    executar_scanner()
