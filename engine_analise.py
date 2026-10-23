import json
import time
import numpy as np
import pandas as pd
import yfinance as yf


def calcular_rsi(series: pd.Series, periodo: int = 2) -> pd.Series:
  """Calcula o Índice de Força Relativa (IFR / RSI) de Larry Connors."""
  delta = series.diff()
  ganho = delta.where(delta > 0, 0.0)
  perda = -delta.where(delta < 0, 0.0)

  media_ganho = ganho.ewm(alpha=1 / periodo, min_periods=periodo).mean()
  media_perda = perda.ewm(alpha=1 / periodo, min_periods=periodo).mean()

  rs = media_ganho / media_perda
  rsi = 100 - (100 / (1 + rs))
  return rsi


def calcular_score_fundamentalista(info: dict) -> str:
  """Calcula um Score Fundamentalista de 0 a 100 baseado em balanços auditados.

  Pilares (25 pts cada):
  1. Rentabilidade (ROE >= 12% a 20%)
  2. Margem Líquida (Margem >= 8% a 15%)
  3. Alavancagem e Endividamento (Dívida/Patrimônio saudável)
  4. Valuation (P/L justo entre 3x e 18x ou P/VP baixo)
  """
  if not info or not isinstance(info, dict):
    return "N/D"

  pontos = 0
  dados_encontrados = 0

  # 1. Rentabilidade: ROE (Return on Equity)
  roe = info.get("returnOnEquity")
  if roe is not None and not np.isnan(roe):
    dados_encontrados += 1
    if roe >= 0.20:
      pontos += 25
    elif roe >= 0.12:
      pontos += 18
    elif roe > 0:
      pontos += 10

  # 2. Eficiência Operacional: Margem Líquida (Profit Margins)
  margem = info.get("profitMargins")
  if margem is not None and not np.isnan(margem):
    dados_encontrados += 1
    if margem >= 0.15:
      pontos += 25
    elif margem >= 0.08:
      pontos += 18
    elif margem > 0:
      pontos += 10

  # 3. Endividamento: Debt to Equity
  debt_to_equity = info.get("debtToEquity")
  if debt_to_equity is not None and not np.isnan(debt_to_equity):
    dados_encontrados += 1
    if debt_to_equity < 80:
      pontos += 25
    elif debt_to_equity <= 140:
      pontos += 18
    elif debt_to_equity <= 200:
      pontos += 10
  else:
    # Setor financeiro (bancos/seguradoras) opera sem essa métrica convencional
    pontos += 15

  # 4. Valuation: Preço / Lucro (P/E) ou Preço / Valor Patrimonial (P/B)
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

  # Classificação por Faixas
  if pontos >= 80:
    return f"{pontos} (Excelente)"
  elif pontos >= 60:
    return f"{pontos} (Bom)"
  elif pontos >= 40:
    return f"{pontos} (Regular)"
  else:
    return f"{pontos} (Fraco)"


def analisar_ativo(
    df_diario: pd.DataFrame, df_semanal: pd.DataFrame, info: dict = None
) -> dict:
  """Executa a triagem técnica e consolida com o score fundamentalista."""
  fechamento_d = df_diario["Close"]

  # Médias diárias
  sma200_d = fechamento_d.rolling(window=200).mean()
  ema50_d = fechamento_d.ewm(span=50, adjust=False).mean()
  ema21_d = fechamento_d.ewm(span=21, adjust=False).mean()

  # IFR(2)
  rsi2 = calcular_rsi(fechamento_d, periodo=2)

  # Semanal (Position Trade)
  fechamento_w = df_semanal["Close"]
  sma20_w = fechamento_w.rolling(window=20).mean()

  preco_atual = float(fechamento_d.iloc[-1])
  sma200_val = (
      float(sma200_d.iloc[-1])
      if not pd.isna(sma200_d.iloc[-1])
      else preco_atual
  )
  ema50_val = (
      float(ema50_d.iloc[-1]) if not pd.isna(ema50_d.iloc[-1]) else preco_atual
  )
  ema21_val = (
      float(ema21_d.iloc[-1]) if not pd.isna(ema21_d.iloc[-1]) else preco_atual
  )
  rsi2_val = float(rsi2.iloc[-1]) if not pd.isna(rsi2.iloc[-1]) else 50.0
  sma20_w_val = (
      float(sma20_w.iloc[-1]) if len(sma20_w.dropna()) > 0 else preco_atual
  )

  # Lógica Técnica
  alta_macro = (preco_atual > sma200_val) and (preco_atual > ema50_val)
  baixa_macro = (preco_atual < sma200_val) and (preco_atual < ema50_val)
  em_pullback = preco_atual < ema21_val
  sobrevendido_raro = rsi2_val <= 15.0
  sobrecomprado = rsi2_val >= 85.0

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

  score_fund = calcular_score_fundamentalista(info)

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
  """Lê a lista do IBrX 100, sanitiza os tickers e processa cotações e fundamentos."""
  print("=== INICIANDO MOTOR QUANTITATIVO & FUNDAMENTALISTA ===")

  try:
    with open("ibrx100_tickers.json", "r", encoding="utf-8") as f:
      tickers = json.load(f)
  except FileNotFoundError:
    print(
        "Arquivo 'ibrx100_tickers.json' não encontrado. Utilizando cesta"
        " padrão."
    )
    tickers = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "WEGE3", "RENT3"]

  resultados = []
  total = len(tickers)

  for i, ticker in enumerate(tickers, 1):
    # Higienização contra '.SA.SA' ou espaços acidentais
    ticker_limpo = (
        str(ticker).replace(".SA", "").replace(".sa", "").strip().upper()
    )
    simbolo_yf = f"{ticker_limpo}.SA"

    print(f"[{i:03d}/{total:03d}] Processando {ticker_limpo} ({simbolo_yf})...")

    try:
      ativo = yf.Ticker(simbolo_yf)

      # 1. Cotações históricas diárias e semanais
      df_d = ativo.history(period="1y", interval="1d")
      df_w = ativo.history(period="2y", interval="1wk")

      if df_d.empty or len(df_d) < 30:
        print(f"  [AVISO] Dados históricos insuficientes para {ticker_limpo}.")
        continue

      # 2. Fundamentos da empresa
      info = {}
      try:
        info = ativo.info or {}
      except Exception:
        info = {}

      # 3. Análise quantitativa
      analise = analisar_ativo(df_d, df_w, info=info)
      analise["Ticker"] = ticker_limpo
      resultados.append(analise)

      # Pausa suave para evitar restrição de taxa da API
      time.sleep(0.2)

    except Exception as e:
      print(f"  [ERRO] Falha ao processar {ticker_limpo}: {e}")
      continue

  if resultados:
    df_final = pd.DataFrame(resultados)
    colunas_ordenadas = [
        "Ticker",
        "Preço (R$)",
        "SMA 200",
        "RSI(2)",
        "Swing Trade",
        "Position Trade",
        "Score Fundamentalista",
        "Gatilho_Swing",
    ]
    df_final = df_final[
        [c for c in colunas_ordenadas if c in df_final.columns]
    ]
    df_final.to_csv("scanner_fechamento.csv", index=False, encoding="utf-8")
    print(
        f"\nBase salva em 'scanner_fechamento.csv' com {len(df_final)} ativos"
        " analisados com sucesso."
    )
  else:
    print("\nNenhum dado pôde ser compilado.")


if __name__ == "__main__":
  executar_scanner()