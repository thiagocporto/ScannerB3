import os
import json
from datetime import datetime
import pandas as pd
import html

ARQUIVO_CSV = r"D:\ScannerB3\scanner_fechamento.csv"
ARQUIVO_TESES = r"D:\ScannerB3\teses_qualitativas.json"
ARQUIVO_SAIDA_JSON = r"D:\ScannerB3\banco_painel.json"

OBRIGATORIOS = {"ticker", "preco", "sma200", "ifr2", "connors", "fase_codigo", "fase_label", "score", "score_label", "sinal_ia", "parecer_ia"}

def validar_lote(ativos):
    erros = []
    for a in ativos:
        t = a.get("ticker", "?")
        faltam = OBRIGATORIOS - set(a.keys())
        if faltam:
            erros.append(f"{t}: campos ausentes {sorted(faltam)}")
        ifr2 = a.get("ifr2", -1)
        if not (0 <= ifr2 <= 100):
            erros.append(f"{t}: IFR(2) fora do range 0-100: {ifr2}")
    if ativos and all(a.get("ifr2") == 0 for a in ativos):
        erros.append("CRITICO: IFR(2) = 0 em todo o universo. Verifique a coleta.")
    return erros

def ler_teses():
    if os.path.exists(ARQUIVO_TESES):
        try:
            with open(ARQUIVO_TESES, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def classificar_fase(fase_texto):
    f = str(fase_texto).lower()
    if "alta forte" in f: return "alta_forte", "Tendência de Alta Forte"
    if "pullback" in f: return "pullback", "Pullback em Alta"
    if "sobrecomprado" in f: return "sobrecomprado", "Sobrecomprado (Risco)"
    if "sobrevendido" in f: return "sobrevendido", "Sobrevendido (Oportunidade)"
    if "baixa" in f: return "baixa", "Tendência de Baixa"
    return "neutro", "Lateralização / Neutro"

def compilar_banco_final():
    if not os.path.exists(ARQUIVO_CSV):
        print(f"[ERRO] CSV nao encontrado: {ARQUIVO_CSV}")
        return
    df = pd.read_csv(ARQUIVO_CSV)
    teses = ler_teses()
    ativos = []
    for _, row in df.iterrows():
        ticker = str(row.get("Ticker", "")).strip().upper()
        preco = float(pd.to_numeric(row.get("Preço (R$)", 0.0), errors="coerce") or 0.0)
        sma200 = float(pd.to_numeric(row.get("SMA 200", 0.0), errors="coerce") or 0.0)
        
        ifr_raw = row.get("RSI(2)", row.get("IFR(2)", 50.0))
        ifr2 = float(pd.to_numeric(ifr_raw, errors="coerce"))
        if pd.isna(ifr2): ifr2 = 50.0
        
        crsi = float(pd.to_numeric(row.get("ConnorsRSI", ifr2), errors="coerce") or ifr2)
        score_texto = str(row.get("Score Fundamentalista", "Regular"))
        fase_cod, fase_lbl = classificar_fase(row.get("Swing Trade", ""))
        
        score_num = 50
        score_lbl = "Regular"
        if "Excelente" in score_texto: score_num, score_lbl = 85, "Excelente"
        elif "Bom" in score_texto: score_num, score_lbl = 70, "Bom"
        elif "Fraco" in score_texto: score_num, score_lbl = 30, "Fraco"

        tese_obj = teses.get(ticker, {})
        texto_parecer = tese_obj.get("parecer", "")
        sinal = "NEUTRO"
        if "favorável" in texto_parecer.lower() and "não é" not in texto_parecer.lower():
            sinal = "COMPRA"
        elif "desfavorável" in texto_parecer.lower() or "evitar" in texto_parecer.lower() or "venda" in texto_parecer.lower():
            sinal = "VENDA"
            
        texto_limpo = html.escape(texto_parecer).replace("**", "")
        ativos.append({
            "ticker": ticker, "preco": round(preco, 2), "sma200": round(sma200, 2),
            "ifr2": round(ifr2, 1), "connors": round(crsi, 1), "fase_codigo": fase_cod,
            "fase_label": fase_lbl, "score": score_num, "score_label": score_lbl,
            "sinal_ia": sinal, "parecer_ia": texto_limpo
        })

    erros = validar_lote(ativos)
    if erros:
        print("⚠ ALERTAS NO LOTE (Verifique o CSV e o Coletor):")
        for e in erros[:5]: print(" -", e)

    dados_finais = {"atualizacao": datetime.now().isoformat(), "total": len(ativos), "ativos": ativos}
    with open(ARQUIVO_SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(dados_finais, f, ensure_ascii=False, indent=2)
    print("✅ banco_painel.json gerado de forma limpa e segura!")

if __name__ == "__main__":
    compilar_banco_final()
