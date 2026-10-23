import json
import numpy as np
import pandas as pd
import yfinance as yf


def calcular_rsi(series, periodo=2):
  """Calcula o Índice de Força Relativa (IFR / RSI)."""
  delta = series.diff()
  ganho = delta.where(delta > 0, 0.0)
  perda = -delta.where(delta < 0, 0.0)

  media_ganho = ganho.ewm(alpha=1 / periodo, min_periods=periodo).mean()
  media_perda = perda.ewm(alpha=1 / periodo, min_periods=periodo).mean()

  rs = media_ganho / media_perda
  rsi = 100 - (100 / (1 + rs))
  return rsi


def calcular_score_fundamentalista(info):
  """Calcula um Score Fundamentalista de 0 a 100 baseado em múltiplos contábeis.

  Pilares (25 pts cada): 1. Rentabilidade (ROE > 15%) 2. Margem Líquida (> 10%)
  3. Alavancagem (Dívida Líquida / EBITDA < 2.5x) 4. Valuation (P/L entre 0 e 15
  ou P/VP razoável)
  """
  pontos = 0
  dados_validos = 0

  # 1. Rentabilidade: ROE (Return on Equity)
  roe = info.get("returnOnEquity")
  if roe is not None and not np.isnan(roe):
    dados_validos += 1
    if roe >= 0.20:
      pontos += 25
    elif roe >= 0.12:
      pontos += 18
    elif roe > 0:
      pontos += 10

  # 2. Eficiência: Margem Líquida (Profit Margins)
  margem = info.get("profitMargins")
  if margem is not None and not np.isnan(margem):
    dados_validos += 1
    if margem >= 0.15:
      pontos += 25
    elif margem >= 0.08:
      pontos += 18
    elif margem > 0:
      pontos += 10

  # 3. Endividamento: Dívida Líquida / EBITDA (ou Dívida Total / Patrimônio)
  # yfinance traz frequentemente 'debtToEquity' (percentual)
  debt_to_equity = info.get("debtToEquity")
  if debt_to_equity is not None and not np.isnan(debt_to_equity):
    dados_validos += 1
    # D/E < 80% é muito saudável; > 150% é alto
    if debt_to_equity < 80:
      pontos += 25
    elif debt_to_equity <= 140:
      pontos += 18
    elif debt_to_equity <= 200:
      pontos += 10
  else:
    # Caso seja instituição financeira (bancos não usam D/E ou EBITDA padrão)
    pontos += 15

  # 4. Valuation: P/L (Trailing P/E) ou P/VP (Price to Book)
  pe = info.get("trailingPE")
  pb = info.get("priceToBook")
  if pe is not None and not np.isnan(pe) and pe > 0:
    dados_validos += 1
    if 3.0 <= pe <= 12.0:
      pontos += 25
    elif 12.0 < pe <= 18.0:
      pontos += 18
    elif pe <= 25.0:
      pontos += 10
  elif pb is not None and not np.isnan(pb) and pb > 0:
    dados_validos += 1
    if pb <= 1.5:
      pontos += 20
    elif pb <= 2.5:
      pontos += 12

  # Se a empresa não tiver dados suficientes auditados no Yahoo Finance
  if dados_validos == 0:
    return "N/D"

  # Classificação em Selos/Notas
  if pontos >= 80:
    rating = f"{pontos} (Excelente)"
  elif pontos >= 60:
    rating = f"{pontos} (Bom)"
  elif pontos >= 40:
    rating = f"{pontos} (Regular)"
  else:
    rating = f"{pontos} (Fraco)"

  return rating


def analisar_ativo(df_diario, df_semanal, info_fundamentalista=None):
  """Aplica a classificação quantitativa técnica e fundamentalista completa."""
  fechamento_d = df_diario["Close"]

  # Médias diárias
  sma200_d = fechamento_d.rolling(window=200).mean()
  ema50_d = fechamento_d.ewm(span=50, adjust=False).mean()
  ema21_d = fechamento_d.ewm(span=21, adjust=False).mean()

  # IFR de 2 períodos
  rsi2 = calcular_rsi(fechamento_d, periodo=2)

  # Position (Semanal)
  fechamento_w = df_semanal["Close"]
  sma20_w = fechamento_w.rolling(window=20).mean()

  preco_atual = float(fechamento_d.iloc[-1])
  sma200_val = float(sma200_d.iloc[-1])
  ema50_val = float(ema50_d.iloc[-1])
  ema21_val = float(ema21_d.iloc[-1])
  rsi2_val = float(rsi2.iloc[-1]) if not pd.isna(rsi2.iloc[-1]) else 50.0
  sma20_w_val = (
      float(sma20_w.iloc[-1]) if len(sma20_w.dropna()) > 0 else preco_atual
  )

  # Condições Técnicas
  alta_macro = (preco_atual > sma200_val) and (preco_atual > ema50_val)
  baixa_macro = (preco_atual < sma200_val) and (preco_atual < ema50_val)
  em_pullback = preco_atual < ema21_val
  sobrevendido_raro = rsi2_val <= 15.0
  sobrecomprado = rsi2_val >= 85.0

  # Classificação de Swing Trade
  gatilho_swing = False
  if alta_macro and em_pullback and sobrevendido_raro:
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

  status_position = (
      "Alta Estrutural (Semanal)"
      if preco_atual > sma20_w_val
      else "Abaixo da Média Semanal"
  )

  # Score Fundamentalista
  score_fund = (
      calcular_score_fundamentalista(info_fundamentalista)
      if info_fundamentalista
      else "N/D"
  )

  return {
      "Preço (R$)": round(preco_atual, 2),
      "SMA 200": round(sma200_val, 2),
      "RSI(2)": round(rsi2_val, 1),
      "Swing Trade": status_swing,
      "Position Trade": status_position,
      "Gatilho_Swing": gatilho_swing,
      "Score Fundamentalista": score_fund,
  }


def executar_scanner():
  """Lê a lista de tickers do IBrX 100, captura cotações e fundamentos, e exporta para CSV."""
  print("Iniciando motor de análise técnica e fundamentalista...")

  try:
    with open("ibrx100_tickers.json", "r", encoding="utf-8") as f:
      tickers = json.load(f)
  except FileNotFoundError:
    print(
        "Arquivo 'ibrx100_tickers.json' não encontrado. Usando lista padrão."
    )
    tickers = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "WEGE3", "RENT3"]

  resultados = []
  total = len(tickers)

  for i, ticker in enumerate(tickers, 1):
    simbolo_yf = f"{ticker}.SA"
    print(f"[{i}/{total}] Analisando {ticker}...")

    try:
      ativo = yf.Ticker(simbolo_yf)

      # 1. Histórico para médias e IFR
      df_d = ativo.history(period="1y", interval="1d")
      df_w = ativo.history(period="2y", interval="1wk")

      if df_d.empty or len(df_d) < 50:
        continue

      # 2. Fundamentos da empresa
      try:
        info = ativo.info
      except Exception:
        info = {}

      analise = analisar_ativo(df_d, df_w, info_fundamentalista=info)
      analise["Ticker"] = ticker
      resultados.append(analise)

    except Exception as e:
      print(f"Erro ao processar {ticker}: {e}")
      continue

  if resultados:
    df_final = pd.DataFrame(resultados)
    # Ordenar colunas para a tabela
    colunas = [
        "Ticker",
        "Preço (R$)",
        "SMA 200",
        "RSI(2)",
        "Swing Trade",
        "Position Trade",
        "Score Fundamentalista",
        "Gatilho_Swing",
    ]
    df_final = df_final[[c for c in colunas if c in df_final.columns]]
    df_final.to_csv("scanner_fechamento.csv", index=False)
    print(
        f"\nBase consolidada atualizada em 'scanner_fechamento.csv' com"
        f" {len(df_final)} ativos."
    )
  else:
    print("Nenhum dado pôde ser processado.")


if __name__ == "__main__":
  executar_scanner()