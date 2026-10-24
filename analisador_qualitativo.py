import os
import json
import time
from datetime import datetime
import pandas as pd
import requests

ARQUIVO_CSV = r"D:\ScannerB3\scanner_fechamento.csv"
ARQUIVO_TESES = r"D:\ScannerB3\teses_qualitativas.json"
ARQUIVO_CONTROLE = r"D:\ScannerB3\controle_quota.json"

API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
MODELO_HOMOLOGADO = "gemini-flash-lite-latest"
URL_GENERATE = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_HOMOLOGADO}:generateContent?key={API_KEY}"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

LIMITE_DIARIO_SEGURO = 1000

def checar_e_incrementar_quota():
    hoje = datetime.now().strftime("%Y-%m-%d")
    dados = {"data": hoje, "consumo": 0}
    if os.path.exists(ARQUIVO_CONTROLE):
        try:
            with open(ARQUIVO_CONTROLE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if d.get("data") == hoje:
                    dados = d
        except Exception:
            pass

    if dados["consumo"] >= LIMITE_DIARIO_SEGURO:
        print(f"\n[TRAVA DE COTA] Limite diário atingido.")
        return False

    dados["consumo"] += 1
    with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2)
    return True

def carregar_teses_existentes():
    if os.path.exists(ARQUIVO_TESES):
        try:
            with open(ARQUIVO_TESES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_teses(teses):
    with open(ARQUIVO_TESES, "w", encoding="utf-8") as f:
        json.dump(teses, f, indent=4, ensure_ascii=False)

def gerar_tese_ativo(ticker, preco, sma200, rsi2, crsi, swing, score):
    prompt_texto = f"""
Atue como estrategista-chefe da WF Investimentos. Ativo #{ticker} da B3.
Preço: R$ {preco} | SMA 200: R$ {sma200} | IFR(2): {rsi2} | ConnorsRSI: {crsi} | Fase: {swing} | Score: {score}

Redija em exatas 3 seções concisas e diretas:
1. VALUATION & BALANÇO: (Saúde financeira e múltiplos)
2. RISCO MACRO/SETORIAL: (Sensibilidade a juros, commodities e regulação)
3. VEREDITO INSTITUCIONAL: (Diretriz para o investidor da WF)
"""
    payload = {
        "contents": [{
            "parts": [{"text": prompt_texto}]
        }],
        "generationConfig": {
            "maxOutputTokens": 350,
            "temperature": 0.1
        }
    }

    for tentativa in range(2):
        try:
            resp = session.post(URL_GENERATE, json=payload, timeout=20)
            if resp.status_code == 200:
                dados = resp.json()
                return dados["candidates"][0]["content"]["parts"][0]["text"].strip()
            elif resp.status_code == 429:
                time.sleep(2.0)
            elif resp.status_code == 503:
                time.sleep(3.0)
        except Exception as e:
            if tentativa == 0:
                time.sleep(1.5)
    return None

def executar_varredura_qualitativa(forcar_todos=False, max_repescagens=2):
    print("=" * 65)
    print("WF INVESTIMENTOS | MOTOR DE TESES QUALITATIVAS")
    print(f"Modelo: {MODELO_HOMOLOGADO} | Repescagem Automática")
    print("=" * 65)

    if not os.path.exists(ARQUIVO_CSV):
        print(f"[ERRO] {ARQUIVO_CSV} não encontrado.")
        return

    df = pd.read_csv(ARQUIVO_CSV)
    hoje_str = datetime.now().strftime("%Y-%m-%d")

    for rodada in range(max_repescagens + 1):
        teses = carregar_teses_existentes()
        tickers_pendentes = []
        for idx, row in df.iterrows():
            ticker = str(row.get("Ticker", "")).strip().upper()
            if not ticker or ticker == "NAN":
                continue
            if forcar_todos or ticker not in teses or teses[ticker].get("data") != hoje_str:
                tickers_pendentes.append((idx + 1, row))

        if not tickers_pendentes:
            print("\n🎉 Todas as 100 teses estão consolidadas com sucesso!")
            break

        print(f"\n🔄 Processando {len(tickers_pendentes)} papéis pendentes...")

        for num_ativo, row in tickers_pendentes:
            ticker = str(row.get("Ticker", "")).strip().upper()
            if not checar_e_incrementar_quota():
                return

            preco = row.get("Preço (R$)", 0.0)
            sma200 = row.get("SMA 200", 0.0)
            rsi2 = row.get("RSI(2)", 0.0)
            crsi = row.get("ConnorsRSI", rsi2)
            swing = row.get("Swing Trade", "Neutro")
            score = row.get("Score Fundamentalista", "Regular")

            print(f"[{num_ativo}/100] Repescando #{ticker}...", end="", flush=True)
            t_inicio = time.time()
            parecer = gerar_tese_ativo(ticker, preco, sma200, rsi2, crsi, swing, score)
            duracao = time.time() - t_inicio

            if parecer:
                teses[ticker] = {
                    "ticker": ticker,
                    "data": hoje_str,
                    "hora": datetime.now().strftime("%H:%M"),
                    "parecer": parecer,
                    "preco_base": preco,
                    "fase": swing,
                    "score": score
                }
                salvar_teses(teses)
                print(f" Concluído em {duracao:.1f}s.")
            else:
                print(" Falhou.")

            time.sleep(4.2)

    print("\n✅ Base de teses finalizada com sucesso.")

if __name__ == "__main__":
    executar_varredura_qualitativa()
