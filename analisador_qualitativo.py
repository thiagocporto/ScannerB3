import os
import json
import time
from datetime import datetime
import pandas as pd
import requests

ARQUIVO_CSV = r"D:\ScannerB3\scanner_fechamento.csv"
ARQUIVO_TESES = r"D:\ScannerB3\teses_qualitativas.json"

# 1. Carrega a chave diretamente do .env ou ficheiros de texto locais
API_KEY = None
for nome_arq in [".env", "chave.txt", "api_key.txt"]:
    if os.path.exists(nome_arq):
        with open(nome_arq, "r", encoding="utf-8") as f:
            for linha in f.read().splitlines():
                if "API_KEY" in linha or "AIza" in linha:
                    parte = linha.split("=")[-1].strip().strip('"').strip("'")
                    if parte:
                        API_KEY = parte
                        break
        if API_KEY:
            break

if not API_KEY:
    API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""

MODELO_HOMOLOGADO = "gemini-flash-lite-latest"
URL_GENERATE = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_HOMOLOGADO}:generateContent?key={API_KEY}"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

def gerar_tese_estruturada(ticker, preco, sma200, rsi2, fase, score):
    prompt = f"""
Atue como Analista Quant da WF Investimentos. Avalie {ticker}.
DADOS: Preço: R$ {preco:.2f} | Média 200: R$ {sma200:.2f} | IFR(2): {rsi2}
CENÁRIO: {fase} | FUNDAMENTOS: {score}

Sintetize a tese sem fantasiar preços-alvo que não estão nos dados. Justifique o risco e a saúde financeira com os números acima.
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "veredito_sinal": {
                        "type": "STRING",
                        "enum": ["compra", "alerta", "venda", "neutro"],
                        "description": "Cor que ditará o botão da IA na tabela."
                    },
                    "parecer_limpo": {
                        "type": "STRING",
                        "description": "Texto em 3 parágrafos curtos diretos (Balanço, Macro, Veredito). Sem uso de asteriscos. Max 400 caracteres."
                    }
                },
                "required": ["veredito_sinal", "parecer_limpo"]
            },
            "maxOutputTokens": 400,
            "temperature": 0.0
        }
    }

    for tentativa in range(3):
        try:
            resp = session.post(URL_GENERATE, json=payload, timeout=20)
            if resp.status_code == 200:
                texto_json = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(texto_json)
            elif resp.status_code == 429:
                time.sleep(6)
            elif resp.status_code == 503:
                time.sleep(4)
        except Exception:
            time.sleep(2)
    return None

def executar_varredura():
    print("=== MOTOR QUALITATIVO SEGURO (MODELO FLASH-LITE) ===")
    if not os.path.exists(ARQUIVO_CSV):
        print("Erro: CSV de fechamento não encontrado.")
        return

    df = pd.read_csv(ARQUIVO_CSV)
    
    teses = {}
    if os.path.exists(ARQUIVO_TESES):
        with open(ARQUIVO_TESES, "r", encoding="utf-8") as f:
            teses = json.load(f)

    hoje_str = datetime.now().strftime("%Y-%m-%d")
    total = len(df)
    concluidos = 0
    
    for idx, row in df.iterrows():
        ticker = str(row.get("Ticker", "")).strip().upper()
        if not ticker or ticker == "NAN": continue
        
        # Só processa se não existir ou se faltar a chave veredito_sinal
        if ticker not in teses or "veredito_sinal" not in teses.get(ticker, {}):
            print(f"[{idx+1}/{total}] A gerar JSON para #{ticker}...", end="", flush=True)
            
            preco = float(row.get("Preço (R$)", 0.0))
            sma200 = float(row.get("SMA 200", 0.0))
            rsi2 = row.get("RSI(2)", 0.0)
            fase = row.get("Swing Trade", "Neutro")
            score = row.get("Score Fundamentalista", "Regular")
            
            res = gerar_tese_estruturada(ticker, preco, sma200, rsi2, fase, score)
            
            if res:
                teses[ticker] = {
                    "data": hoje_str,
                    "parecer": res["parecer_limpo"].replace("**", ""),
                    "veredito_sinal": res["veredito_sinal"]
                }
                with open(ARQUIVO_TESES, "w", encoding="utf-8") as f:
                    json.dump(teses, f, indent=4, ensure_ascii=False)
                print(f" OK ({res['veredito_sinal']})")
                concluidos += 1
            else:
                print(" Falha")
            
            # Intervalo para respeitar os limites de requisições por minuto
            time.sleep(4.2)
        else:
            concluidos += 1

    print(f"\nConcluído com sucesso! {concluidos}/{total} teses consolidadas.")

if __name__ == "__main__":
    executar_varredura()
