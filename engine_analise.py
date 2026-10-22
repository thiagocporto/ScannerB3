import json
import yfinance as yf
import pandas as pd
import numpy as np

def carregar_tickers():
    """Carrega os 100 ativos do IBrX 100 guardados no ficheiro JSON."""
    with open("ibrx100_tickers.json", "r", encoding="utf-8") as f:
        return json.load(f)

def calcular_rsi(serie_precos, periodo=2):
    """Calcula o RSI/IFR de período curto (default: 2 períodos)."""
    delta = serie_precos.diff()
    ganho = delta.where(delta > 0, 0.0)
    perda = -delta.where(delta < 0, 0.0)
    
    media_ganho = ganho.ewm(alpha=1/periodo, adjust=False).mean()
    media_perda = perda.ewm(alpha=1/periodo, adjust=False).mean()
    
    rs = media_ganho / (media_perda + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_score_fundamentalista(info):
    """
    Calcula um Score de 0 a 100 baseado em múltiplos de valor, rentabilidade e solvência.
    """
    pontos = 0
    
    pl = info.get("trailingPE")
    pvp = info.get("priceToBook")
    dy = info.get("dividendYield")
    roe = info.get("returnOnEquity")
    div_ebitda = info.get("debtToEquity") # Proxy de endividamento
    
    # 1. P/L (Até 25 pontos)
    if pl is not None and 0 < pl <= 15:
        pontos += 25
    elif pl is not None and 15 < pl <= 22:
        pontos += 15

    # 2. P/VP (Até 20 pontos)
    if pvp is not None and 0.5 <= pvp <= 2.2:
        pontos += 20
    elif pvp is not None and 2.2 < pvp <= 3.5:
        pontos += 10

    # 3. Dividend Yield (Até 25 pontos)
    if dy is not None and dy >= 0.06: # DY >= 6%
        pontos += 25
    elif dy is not None and dy >= 0.03: # DY >= 3%
        pontos += 15

    # 4. ROE (Até 20 pontos)
    if roe is not None and roe >= 0.15: # ROE >= 15%
        pontos += 20
    elif roe is not None and roe >= 0.08:
        pontos += 10

    # 5. Endividamento (Até 10 pontos)
    if div_ebitda is not None and div_ebitda <= 150: # Debt/Equity moderado
        pontos += 10

    # Classificação
    if pontos >= 70:
        classificacao = "💎 Sólida (Top Tier)"
    elif pontos >= 45:
        classificacao = "⚖️ Moderada / Aceitável"
    else:
        classificacao = "⚠️ Múltiplos Esticados / Arriscada"

    return {
        "Score_Fund": pontos,
        "Class_Fund": classificacao,
        "P/L": round(pl, 2) if pl else "-",
        "P/VP": round(pvp, 2) if pvp else "-",
        "DY (%)": round(dy * 100, 2) if dy else 0.0,
        "ROE (%)": round(roe * 100, 2) if roe else 0.0
    }

def analisar_ativo(df_diario, df_semanal):
    """Aplica os critérios de Swing Trade conservador e Position Trade."""
    fechamento_d = df_diario['Close']
    
    # Médias diárias
    sma200_d = fechamento_d.rolling(window=200).mean()
    ema50_d = fechamento_d.ewm(span=50, adjust=False).mean()
    ema21_d = fechamento_d.ewm(span=21, adjust=False).mean()
    
    # IFR de 2 períodos
    rsi2 = calcular_rsi(fechamento_d, periodo=2)
    
    # Position (Semanal)
    fechamento_w = df_semanal['Close']
    sma20_w = fechamento_w.rolling(window=20).mean()

    preco_atual = float(fechamento_d.iloc[-1])
    sma200_val = float(sma200_d.iloc[-1])
    ema50_val = float(ema50_d.iloc[-1])
    ema21_val = float(ema21_d.iloc[-1])
    rsi2_val = float(rsi2.iloc[-1]) if not pd.isna(rsi2.iloc[-1]) else 50.0
    sma20_w_val = float(sma20_w.iloc[-1]) if len(sma20_w.dropna()) > 0 else preco_atual

    # Filtros de Swing
    em_tendencia_macro = (preco_atual > sma200_val) and (preco_atual > ema50_val)
    em_pullback = preco_atual < ema21_val
    sobrevendido_raro = rsi2_val <= 15.0

    if em_tendencia_macro and em_pullback and sobrevendido_raro:
        status_swing = "🔥 COMPRA ALTA PROBABILIDADE"
        gatilho_swing = True
    elif em_tendencia_macro and sobrevendido_raro:
        status_swing = "Atenção: Sobrevendido em Alta"
        gatilho_swing = False
    elif em_tendencia_macro:
        status_swing = "Tendência de Alta Forte"
        gatilho_swing = False
    else:
        status_swing = "Fora do Filtro"
        gatilho_swing = False

    status_position = "Alta Estrutural (Semanal)" if preco_atual > sma20_w_val else "Abaixo da Média Semanal"

    return {
        "Preço (R$)": round(preco_atual, 2),
        "SMA 200": round(sma200_val, 2),
        "RSI(2)": round(rsi2_val, 1),
        "Swing Trade": status_swing,
        "Position Trade": status_position,
        "Gatilho_Swing": gatilho_swing
    }

def executar_scanner():
    tickers = carregar_tickers()
    print(f"Descarregando cotações históricas dos {len(tickers)} ativos...")

    dados_diarios = yf.download(tickers, period="2y", interval="1d", group_by='ticker', auto_adjust=True, threads=True)
    dados_semanais = yf.download(tickers, period="2y", interval="1wk", group_by='ticker', auto_adjust=True, threads=True)

    print("Calculando indicadores técnicos e capturando fundamentos...")
    relatorio = []

    for t in tickers:
        try:
            df_d = dados_diarios[t].dropna()
            df_w = dados_semanais[t].dropna()

            if len(df_d) >= 200 and len(df_w) >= 20:
                analise_tec = analisar_ativo(df_d, df_w)
                
                # Obter fundamentos via Ticker object
                tk = yf.Ticker(t)
                info = tk.info or {}
                fundamentos = calcular_score_fundamentalista(info)
                
                # Consolidação
                item_completo = {
                    "Ticker": t.replace(".SA", ""),
                    **analise_tec,
                    **fundamentos
                }
                relatorio.append(item_completo)
        except Exception:
            continue

    df_final = pd.DataFrame(relatorio)

    # 1. VISÃO SWING TRADE (GATILHOS DO DIA)
    oportunidades_swing = df_final[df_final["Gatilho_Swing"] == True]
    print("\n" + "="*70)
    print("🎯 OPORTUNIDADES CONSERVADORAS DE SWING TRADE")
    print("="*70)
    if not oportunidades_swing.empty:
        colunas_swing = ["Ticker", "Preço (R$)", "RSI(2)", "Position Trade", "Score_Fund", "Class_Fund"]
        print(oportunidades_swing[colunas_swing].to_string(index=False))
    else:
        print("Nenhum ativo preencheu os critérios estritos de Swing Trade conservador hoje.")

    # 2. VISÃO FUNDAMENTALISTA (TOP EMPRESAS DE LONGO PRAZO)
    top_fundamentais = df_final.sort_values(by="Score_Fund", ascending=False).head(10)
    print("\n" + "="*70)
    print("💎 TOP 10 EMPRESAS MAIS SÓLIDAS DO IBrX 100 (VISÃO FUNDAMENTALISTA)")
    print("="*70)
    colunas_fund = ["Ticker", "Preço (R$)", "P/L", "P/VP", "DY (%)", "ROE (%)", "Score_Fund", "Position Trade"]
    print(top_fundamentais[colunas_fund].to_string(index=False))

    # Guarda base consolidada completa em CSV
    df_final.to_csv("scanner_fechamento.csv", index=False, encoding="utf-8-sig")
    print("\nBase consolidada atualizada em 'scanner_fechamento.csv'.")

if __name__ == "__main__":
    executar_scanner()