import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import yfinance as yf

def calcular_rsi(series: pd.Series, periodo: int) -> pd.Series:
    delta = series.diff()
    ganho = delta.where(delta > 0, 0.0)
    perda = -delta.where(delta < 0, 0.0)
    media_ganho = ganho.ewm(alpha=1 / periodo, min_periods=periodo).mean()
    media_perda = perda.ewm(alpha=1 / periodo, min_periods=periodo).mean()
    rs = np.where(media_perda == 0, 100.0, media_ganho / media_perda)
    return pd.Series(100.0 - (100.0 / (1.0 + rs)), index=series.index)

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
    crsi = (rsi_preco + rsi_streak + prank) / 3.0
    return crsi

print("A analisar dados para comparar IFR(2) vs ConnorsRSI (CRSI)...")
for ticker in ["PETR4.SA", "VALE3.SA", "BRAP4.SA"]:
    df = yf.Ticker(ticker).history(period="1y")
    fechamento = df["Close"]
    
    ifr2 = calcular_rsi(fechamento, periodo=2).iloc[-1]
    crsi = calcular_connors_rsi(fechamento).iloc[-1]
    preco = fechamento.iloc[-1]
    
    print(f"\nAtivo: #{ticker.replace('.SA', '')} | Preço Atual: R$ {preco:.2f}")
    print(f"  • IFR(2) Tradicional : {ifr2:.1f}")
    print(f"  • ConnorsRSI (CRSI)   : {crsi:.1f}")
