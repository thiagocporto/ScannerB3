import json
import os
import time
import pandas as pd
import yfinance as yf

def calcular_rsi(serie, periodos=2):
    delta = serie.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    
    media_ganho = ganho.ewm(alpha=1/periodos, adjust=False).mean()
    media_perda = perda.ewm(alpha=1/periodos, adjust=False).mean()
    
    rs = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_score_fundamentalista(info, tipo="AÇÃO"):
    if tipo == "ETF":
        return 80  # Score padrão institucional para cesta de índices
    
    score = 0
    try:
        # 1. Rentabilidade / Retorno
        roe = info.get("returnOnEquity")
        if roe and roe > 0.12: score += 25
        elif roe and roe > 0: score += 15
        
        # 2. Margens
        margem = info.get("profitMargins")
        if margem and margem > 0.10: score += 25
        elif margem and margem > 0: score += 15
        
        # 3. Alavancagem
        divida = info.get("debtToEquity")
        if divida and divida < 150: score += 25
        elif divida is None: score += 15
        
        # 4. Valuation
        pl = info.get("trailingPE")
        pvp = info.get("priceToBook")
        if pl and 0 < pl < 20: score += 25
        elif pvp and 0 < pvp < 2.5: score += 20
        else: score += 10
    except Exception:
        score = 50
    return min(score, 100)

def executar_scanner():
    print("Iniciando motor analítico com Universo B3 Ampliado...")
    
    arquivo_universo = "universo_b3.json"
    if os.path.exists(arquivo_universo):
        with open(arquivo_universo, "r", encoding="utf-8") as f:
            catalogo = json.load(f)
    else:
        print("Erro: universo_b3.json não encontrado.")
        return

    resultados = []
    total = len(catalogo)

    for i, item in enumerate(catalogo, 1):
        ticker = str(item.get("ticker", "")).strip().upper()
        tipo = item.get("tipo", "AÇÃO")
        simbolo_yf = f"{ticker}.SA"

        print(f"[{i}/{total}] Analisando {ticker} ({tipo})...", end="", flush=True)

        try:
            ativo = yf.Ticker(simbolo_yf)
            df_d = ativo.history(period="1y", interval="1d")

            if df_d.empty or len(df_d) < 30:
                print(" -> Dados insuficientes no Yahoo Finance.")
                continue

            preco_atual = float(df_d["Close"].iloc[-1])
            sma200 = float(df_d["Close"].rolling(200).mean().iloc[-1]) if len(df_d) >= 200 else float(df_d["Close"].rolling(len(df_d)).mean().iloc[-1])
            
            rsi2_series = calcular_rsi(df_d["Close"], periodos=2)
            rsi2 = float(rsi2_series.iloc[-1])

            # Fundamentos
            info = {}
            if tipo != "ETF":
                try:
                    info = ativo.info or {}
                except Exception:
                    info = {}
            
            score_num = calcular_score_fundamentalista(info, tipo=tipo)

            resultados.append({
                "Ticker": ticker,
                "Preço (R$)": round(preco_atual, 2),
                "SMA 200": round(sma200, 2),
                "RSI(2)": round(rsi2, 1),
                "Score Fundamentalista": score_num
            })
            print(f" OK (R$ {preco_atual:.2f} | IFR2: {rsi2:.1f})")
            time.sleep(0.2)

        except Exception as e:
            print(f" -> Erro: {e}")
            continue

    if resultados:
        df_final = pd.DataFrame(resultados)
        df_final.to_csv("scanner_fechamento.csv", index=False)
        print(f"\nSucesso: scanner_fechamento.csv regerado com {len(df_final)} ativos!")
    else:
        print("Erro: Nenhum ativo pôde ser processado.")

if __name__ == "__main__":
    executar_scanner()
