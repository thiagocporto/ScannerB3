# -*- coding: utf-8 -*-
import json
import os
import time
import pandas as pd
from google import genai
from google.genai import types

def carregar_dados():
    csv_file = "scanner_fechamento.csv"
    if not os.path.exists(csv_file):
        print("Aviso: scanner_fechamento.csv nao encontrado.")
        return []
    
    df = pd.read_csv(csv_file)
    
    tipos_map = {}
    if os.path.exists("universo_b3.json"):
        with open("universo_b3.json", "r", encoding="utf-8") as f:
            for item in json.load(f):
                tipos_map[item["ticker"]] = {
                    "tipo": item.get("tipo", "ACAO"),
                    "nome": item.get("nome", item["ticker"])
                }
    
    ativos = []
    for _, row in df.iterrows():
        t = str(row.get("Ticker", "")).strip().upper()
        if not t or t == "NAN": 
            continue
        
        info = tipos_map.get(t, {"tipo": "ACAO", "nome": t})
        ativos.append({
            "ticker": t,
            "tipo": info["tipo"],
            "nome": info["nome"],
            "preco": row.get("Preco (R$)", row.get("Preço (R$)", 0.0)),
            "sma200": row.get("SMA 200", 0.0),
            "rsi2": row.get("RSI(2)", 50.0),
            "score": row.get("Score Fundamentalista", 50)
        })
    return ativos

def executar_analise_ia():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Erro: Variavel GEMINI_API_KEY nao encontrada no ambiente.")
        return

    client = genai.Client(api_key=api_key)
    ARQUIVO_TESES = "teses_qualitativas.json"
    
    teses = {}
    if os.path.exists(ARQUIVO_TESES):
        try:
            with open(ARQUIVO_TESES, "r", encoding="utf-8") as f:
                teses = json.load(f)
        except Exception:
            teses = {}

    ativos = carregar_dados()
    pendentes = [a for a in ativos if a["ticker"] not in teses]
    total = len(pendentes)
    
    print(f"\nIniciando Varredura Qualitativa da IA ({total} pendentes de {len(ativos)} ativos)...")

    for i, a in enumerate(pendentes, 1):
        ticker = a["ticker"]
        tipo = a["tipo"]
        nome = a["nome"]
        
        print(f"[{i}/{total}] Analisando {ticker} ({tipo} - {nome})...", end="", flush=True)

        prompt = f"""Voce e o Analista-Chefe da WF Investimentos.
Analise o ativo '{ticker}' ({nome}), classe: {tipo}.
Dados Quantitativos:
- Preco Atual: R$ {a['preco']}
- SMA 200: R$ {a['sma200']}
- IFR(2) Larry Connors: {a['rsi2']}
- Score de Saude: {a['score']}/100

Diretrizes para {tipo}:
- Se ACAO ou BDR: analise valuation, solidez financeira e risco macro/politico.
- Se FII ou FIAGRO: analise dividend yield, vacancia/credito e sensibilidade a taxa Selic.
- Se ETF: analise a tese do indice replicado, risco sistemico e momento de reversao a media.

Retorne EXCLUSIVAMENTE um JSON valido no seguinte formato:
{{
    "veredito_sinal": "compra" | "alerta" | "venda" | "neutro",
    "parecer": "1. VISAO FUNDAMENTALISTA / MACRO:\\n...\\n\\n2. TIMING QUANTITATIVO (IFR2 & MEDIAS):\\n...\\n\\n3. DIRETRIZ INSTITUCIONAL WF:\\n..."
}}
"""
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            res_json = json.loads(response.text)
            teses[ticker] = {
                "veredito_sinal": res_json.get("veredito_sinal", "neutro"),
                "parecer": res_json.get("parecer", "Parecer em analise.")
            }
            
            with open(ARQUIVO_TESES, "w", encoding="utf-8") as f:
                json.dump(teses, f, indent=4, ensure_ascii=False)
            
            print(f" OK ({res_json.get('veredito_sinal')})")
            time.sleep(4.2)
            
        except Exception as e:
            print(f" Erro: {e}")
            time.sleep(2)

    print("\nVarredura qualitativa concluida com sucesso!")

if __name__ == "__main__":
    executar_analise_ia()
