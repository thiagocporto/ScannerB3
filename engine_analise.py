# -*- coding: utf-8 -*-
import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import yfinance as yf

ARQUIVO_UNIVERSO = "universo_b3.json"
ARQUIVO_FALLBACK = "ibrx100_tickers.json"
ARQUIVO_SAIDA_CSV = "scanner_fechamento.csv"

JANELA_SMA_LONGA = 200
JANELA_SMA_CURTA = 5
JANELA_BOLLINGER = 20
N_RSI_CURTO = 2
N_RSI_CRSI_PRECO = 3
N_RSI_CRSI_STREAK = 2
N_PERCENT_RANK = 100

def carregar_catalogo_ativos():
    if os.path.exists(ARQUIVO_UNIVERSO):
        try:
            with open(ARQUIVO_UNIVERSO, "r", encoding="utf-8") as f:
                catalogo = json.load(f)
                print(f"[CAT?LOGO] Carregados {len(catalogo)} ativos de '{ARQUIVO_UNIVERSO}'.")
                return catalogo
        except Exception as e:
            print(f"[AVISO] Falha ao ler {ARQUIVO_UNIVERSO}: {e}")

    if os.path.exists(ARQUIVO_FALLBACK):
        try:
            with open(ARQUIVO_FALLBACK, "r", encoding="utf-8") as f:
                tickers = json.load(f)
                catalogo = []
                for t in tickers:
                    if isinstance(t, dict):
                        catalogo.append(t)
                    else:
                        catalogo.append({
                            "ticker": str(t).replace(".SA", "").strip(),
                            "tipo": "ACAO",
                            "nome": str(t)
                        })
                print(f"[CAT?LOGO] Fallback: {len(catalogo)} ativos de '{ARQUIVO_FALLBACK}'.")
                return catalogo
        except Exception as e:
            print(f"[AVISO] Falha ao ler {ARQUIVO_FALLBACK}: {e}")

    return [
        {"ticker": "PETR4", "tipo": "ACAO", "nome": "Petrobras PN"},
        {"ticker": "VALE3", "tipo": "ACAO", "nome": "Vale ON"},
        {"ticker": "ITUB4", "tipo": "ACAO", "nome": "Ita? Unibanco PN"},
        {"ticker": "HGLG11", "tipo": "FII", "nome": "CSHG Log?stica"},
        {"ticker": "IVVB11", "tipo": "ETF", "nome": "iShares S&P 500"}
    ]

# 1. RSI COM SUAVIZA??O DE WILDER (alpha = 1/n)
def rsi_wilder(serie, n):
    delta = serie.diff()
    ganho = delta.clip(lower=0.0)
    perda = (-delta).clip(lower=0.0)
    media_ganho = ganho.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    media_perda = perda.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()

    mg = media_ganho.values
    mp = media_perda.values
    rsi = np.full(len(serie), np.nan)
    valido = ~(np.isnan(mg) | np.isnan(mp))
    perda_zero = valido & (mp == 0.0)
    normal = valido & (mp != 0.0)

    rsi[normal] = 100.0 - (100.0 / (1.0 + mg[normal] / mp[normal]))
    rsi[perda_zero & (mg > 0.0)] = 100.0
    rsi[perda_zero & (mg == 0.0)] = 50.0
    return pd.Series(rsi, index=serie.index)

# 2. CONNORS RSI MATEM?TICO (Pre?o + Streak + PercentRank)
def calcular_streak(fechamento):
    v = fechamento.values
    out = np.zeros(len(v))
    for i in range(1, len(v)):
        if v[i] > v[i - 1]:
            out[i] = out[i - 1] + 1 if out[i - 1] > 0 else 1
        elif v[i] < v[i - 1]:
            out[i] = out[i - 1] - 1 if out[i - 1] < 0 else -1
        else:
            out[i] = 0
    return pd.Series(out, index=fechamento.index)

def calcular_connors_rsi(fechamento):
    if len(fechamento) < 5:
        return np.nan

    rsi_preco = rsi_wilder(fechamento, N_RSI_CRSI_PRECO).iloc[-1]
    streak = calcular_streak(fechamento)
    rsi_streak = rsi_wilder(streak, N_RSI_CRSI_STREAK).iloc[-1]

    roc = fechamento.pct_change()
    janela = roc.iloc[-(N_PERCENT_RANK + 1):]
    if len(janela) < (N_PERCENT_RANK + 1) or janela.isna().any():
        percent_rank = 50.0
    else:
        atual = janela.iloc[-1]
        anteriores = janela.iloc[:-1]
        percent_rank = float((anteriores < atual).sum()) / N_PERCENT_RANK * 100.0

    componentes = [rsi_preco, rsi_streak, percent_rank]
    comp_validos = [c for c in componentes if not np.isnan(c)]
    if not comp_validos:
        return np.nan
    return float(np.mean(comp_validos))

# 3. TRATAMENTO CONT?NUO E 4. ISOLAMENTO DO SETOR FINANCEIRO
def _num(info, chave):
    v = info.get(chave)
    if isinstance(v, (int, float)) and not isinstance(v, bool) and not np.isnan(v):
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

def avaliar_saude_fundamentalista(info, tipo_ativo):
    if tipo_ativo in ["FII", "FIAGRO"]:
        p_vp = _num(info, "priceToBook")
        dy = _num(info, "dividendYield")
        s_dy = _escala(dy, 0.04, 0.12)

        if p_vp is None:
            s_pvp = None
        elif 0.85 <= p_vp <= 1.05:
            s_pvp = 100.0
        elif p_vp < 0.85:
            s_pvp = _escala(p_vp, 0.50, 0.85)
        else:
            s_pvp = _escala(p_vp, 1.50, 1.05)

        score = _media([s_dy, s_pvp])
        if score is None:
            return 50, "Regular"
        s_int = int(round(score))
        return s_int, _rotulo(s_int)

    if tipo_ativo == "ETF":
        return 50, "Regular"

    roe = _num(info, "returnOnEquity")
    margem = _num(info, "profitMargins")
    setor = str(info.get("sector") or "")

    eixo_rent = _escala(roe, 0.0, 0.20)
    eixo_efic = _escala(margem, 0.0, 0.15)

    # 4. Isolamento do setor financeiro: omite alavancagem em bancos e seguradoras
    eixo_solv = None
    if not any(f in setor.lower() for f in ["financial", "bank", "segur"]):
        d_pl = _num(info, "debtToEquity")
        if d_pl is not None:
            d_pl = d_pl / 100.0
        divida = _num(info, "totalDebt")
        caixa = _num(info, "totalCash")
        ebitda = _num(info, "ebitda")
        div_liq_ebitda = None
        if divida is not None and caixa is not None and ebitda is not None and ebitda > 0:
            div_liq_ebitda = (divida - caixa) / ebitda
        eixo_solv = _media([_escala(d_pl, 2.0, 0.0), _escala(div_liq_ebitda, 4.0, 0.0)])

    pl = _num(info, "trailingPE")
    p_vp = _num(info, "priceToBook")
    s_pl = 0.0 if (pl is not None and pl <= 0) else _escala(pl, 25.0, 8.0)
    eixo_val = _media([s_pl, _escala(p_vp, 3.0, 1.0)])

    eixos = [eixo_rent, eixo_efic, eixo_solv, eixo_val]
    eixos_validos = [e for e in eixos if e is not None]
    if not eixos_validos:
        return 50, "Regular"

    score = int(round(_media(eixos_validos)))
    return score, _rotulo(score)

def calcular_indicadores_tecnicos(df_d):
    fechamento = df_d["Adj Close"] if "Adj Close" in df_d.columns else df_d["Close"]
    preco_atual = float(fechamento.iloc[-1])
    preco_exibicao = float(df_d["Close"].iloc[-1])

    # Amostragem tolerante para permitir ativos jovens sem descarte
    sma200 = float(fechamento.rolling(window=JANELA_SMA_LONGA, min_periods=10).mean().iloc[-1])
    sma5 = float(fechamento.rolling(window=JANELA_SMA_CURTA, min_periods=2).mean().iloc[-1])
    rsi2 = float(rsi_wilder(fechamento, N_RSI_CURTO).iloc[-1])
    crsi = calcular_connors_rsi(fechamento)

    sma20 = fechamento.rolling(window=JANELA_BOLLINGER, min_periods=5).mean()
    std20 = fechamento.rolling(window=JANELA_BOLLINGER, min_periods=5).std()
    bs = sma20 + (2.0 * std20)
    bi = sma20 - (2.0 * std20)

    bs_val = float(bs.iloc[-1])
    bi_val = float(bi.iloc[-1])
    pct_b = float((preco_atual - bi_val) / (bs_val - bi_val)) if (bs_val != bi_val and not np.isnan(bs_val) and not np.isnan(bi_val)) else 0.5

    # Enquadramento t?cnico consistente com gerar_site.py
    if preco_atual > sma200:
        if rsi2 <= 15:
            fase = "Sobrevendido (Oportunidade)"
        elif rsi2 >= 85:
            fase = "Sobrecomprado"
        else:
            fase = "Tend?ncia de Alta Forte"
    else:
        if rsi2 <= 15:
            fase = "Sobrevendido em Tend?ncia Baixa"
        elif rsi2 >= 85:
            fase = "Sobrecomprado"
        else:
            fase = "Tend?ncia de Baixa"

    return {
        "Pre?o (R$)": round(preco_exibicao, 2),
        "SMA 200": round(sma200, 2),
        "SMA 5": round(sma5, 2),
        "RSI(2)": round(rsi2, 1),
        "ConnorsRSI": round(crsi, 1) if not np.isnan(crsi) else 50.0,
        "%b Bollinger": round(pct_b, 2),
        "Swing Trade": fase,
        "Position Trade": "Estrutura Monitorada"
    }

def executar_scanner():
    catalogo = carregar_catalogo_ativos()
    total = len(catalogo)
    print(f"\n[SCANNER] Processando {total} ativos com Wilder, ConnorsRSI e Scoring Continuo...")

    resultados = []
    for i, item in enumerate(catalogo, 1):
        t_raw = item.get("ticker", "").strip().upper().replace(".SA", "")
        tipo = item.get("tipo", "ACAO")
        nome = item.get("nome", t_raw)
        simbolo_yf = f"{t_raw}.SA"

        print(f"[{i}/{total}] {t_raw} ({tipo})...", end="", flush=True)

        try:
            ativo = yf.Ticker(simbolo_yf)
            df_d = ativo.history(period="2y", interval="1d", auto_adjust=False)

            if df_d.empty or len(df_d) < 3:
                print(" [HIST?RICO CURTO - PULADO]")
                continue

            ind = calcular_indicadores_tecnicos(df_d)

            info = {}
            try:
                info = ativo.info or {}
            except Exception:
                pass

            score_num, score_lbl = avaliar_saude_fundamentalista(info, tipo)
            score_txt = f"{score_num} ({score_lbl})"

            registro = {
                "Ticker": t_raw,
                "Tipo": tipo,
                "Nome": nome,
                "Pre?o (R$)": ind["Pre?o (R$)"],
                "SMA 200": ind["SMA 200"],
                "SMA 5": ind["SMA 5"],
                "RSI(2)": ind["RSI(2)"],
                "ConnorsRSI": ind["ConnorsRSI"],
                "%b Bollinger": ind["%b Bollinger"],
                "Swing Trade": ind["Swing Trade"],
                "Position Trade": ind["Position Trade"],
                "Score Fundamentalista": score_txt
            }
            resultados.append(registro)
            print(" [OK]")
            time.sleep(0.08)

        except Exception as e:
            print(f" [ERRO: {e}]")
            continue

    if resultados:
        df_final = pd.DataFrame(resultados)
        df_final.to_csv(ARQUIVO_SAIDA_CSV, index=False, encoding="utf-8-sig")
        print(f"\n[SUCESSO] Base consolidada com {len(df_final)} ativos em '{ARQUIVO_SAIDA_CSV}'!")
    else:
        print("\n[ERRO CR?TICO] Nenhum ativo p?de ser consolidado.")

if __name__ == "__main__":
    executar_scanner()
