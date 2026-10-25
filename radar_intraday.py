import os
import sys
import json
import time
import requests
from datetime import datetime
import yfinance as yf
from engine_analise import analisar_ativo

# Importa o módulo macro leve
from monitor_macro import atualizar_cenario_macro, ARQUIVO_MACRO

# Configurações de Notificação WhatsApp
URL_WPP = "http://localhost:21465/api/wf-investimentos/send-message"
GRUPO_WHATSAPP = "120363410136539471@g.us"

ARQUIVO_DISPARADOS = r"D:\ScannerB3\disparos_hoje.json"

# Controlo de execução das 3 chamadas diárias de macro
MACRO_EXECUTADO = {
    "data": "",
    "PRE_MARKET": False,
    "MEIO_PREGAO": False,
    "FECHAMENTO": False
}

def resetar_travas_se_novo_dia():
    hoje = datetime.now().strftime("%Y-%m-%d")
    if MACRO_EXECUTADO["data"] != hoje:
        MACRO_EXECUTADO["data"] = hoje
        MACRO_EXECUTADO["PRE_MARKET"] = False
        MACRO_EXECUTADO["MEIO_PREGAO"] = False
        MACRO_EXECUTADO["FECHAMENTO"] = False

def verificar_e_atualizar_macro_automatico():
    """Garante a execução nas 3 janelas horárias com apenas 1 chamada por janela."""
    resetar_travas_se_novo_dia()
    agora = datetime.now()
    hm = (agora.hour, agora.minute)

    # Janela 1: Pré-Market (08:50 às 09:20)
    if (8, 50) <= hm <= (9, 20) and not MACRO_EXECUTADO["PRE_MARKET"]:
        print("\n🌐 [MACRO] A disparar leitura matinal de Pré-Market...")
        atualizar_cenario_macro("PRE_MARKET")
        MACRO_EXECUTADO["PRE_MARKET"] = True

    # Janela 2: Meio do Pregão (12:45 às 13:20)
    elif (12, 45) <= hm <= (13, 20) and not MACRO_EXECUTADO["MEIO_PREGAO"]:
        print("\n🌐 [MACRO] A atualizar leitura de Meio-Pregão...")
        atualizar_cenario_macro("MEIO_PREGAO")
        MACRO_EXECUTADO["MEIO_PREGAO"] = True

    # Janela 3: Fechamento (17:45 às 18:15)
    elif (17, 45) <= hm <= (18, 15) and not MACRO_EXECUTADO["FECHAMENTO"]:
        print("\n🌐 [MACRO] A consolidar leitura de Fechamento do dia...")
        atualizar_cenario_macro("FECHAMENTO")
        MACRO_EXECUTADO["FECHAMENTO"] = True

def obter_resumo_macro_local():
    """Lê o diagnóstico em disco sem gastar tokens."""
    try:
        if os.path.exists(ARQUIVO_MACRO):
            with open(ARQUIVO_MACRO, "r", encoding="utf-8") as f:
                d = json.load(f)
                clima = d.get("clima", "Neutro")
                risco = d.get("risco_fiscal", "Moderado")
                setores = d.get("setores", "Geral")
                return f"\n🌐 *Cenário Externo/Macro:* {clima} | Risco Fiscal: {risco}\n⚠️ *Foco Setorial:* {setores}"
    except Exception:
        pass
    return ""

def enviar_alerta_whatsapp(mensagem: str):
    try:
        payload = {"phone": GRUPO_WHATSAPP, "message": mensagem, "isGroup": True}
        headers = {"Content-Type": "application/json"}
        res = requests.post(URL_WPP, json=payload, headers=headers, timeout=10)
        return res.status_code in [200, 201]
    except Exception as e:
        print(f"[ERRO WHATSAPP] Falha no envio: {e}")
        return False

def executar_radar_loop():
    print("=" * 60)
    print("WF INVESTIMENTOS | RADAR CONTÍNUO COM SUPORTE MACRO INTEGRADO")
    print("=" * 60)

    while True:
        # 1. Verifica se está na hora de rodar alguma das 3 chamadas macro
        verificar_e_atualizar_macro_automatico()

        # 2. Carrega lista do IBrX 100
        try:
            with open("ibrx100_tickers.json", "r", encoding="utf-8") as f:
                tickers = json.load(f)
        except Exception:
            tickers = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "WEGE3"]

        hora_atual = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{hora_atual}] A varrer mercado para oportunidades de assimetria...")

        texto_macro = obter_resumo_macro_local()

        for ticker in tickers:
            t_clean = str(ticker).replace(".SA", "").strip().upper()
            try:
                ativo = yf.Ticker(f"{t_clean}.SA")
                df_d = ativo.history(period="1y", interval="1d")
                df_w = ativo.history(period="2y", interval="1wk")

                if df_d.empty or len(df_d) < 150:
                    continue

                analise = analisar_ativo(df_d, df_w, info=ativo.info or {})

                if analise.get("Gatilho_Swing"):
                    preco = analise.get("Preço (R$)", 0)
                    alvo = analise.get("Alvo SMA 5", 0)
                    upside = analise.get("Upside (%)", 0)
                    score_f = analise.get("Score Fundamentalista", "N/D")
                    crsi = analise.get("ConnorsRSI", 0)
                    ifr2 = analise.get("IFR(2)", 0)

                    msg = (
                        f"🏆 *RADAR JANELA DE OURO (INSTITUCIONAL)*\n\n"
                        f"📌 *Ativo:* #{t_clean}\n"
                        f"💵 *Preço de Entrada:* R$ {preco:.2f}\n"
                        f"🎯 *Preço-Alvo (SMA 5):* R$ {alvo:.2f} (+{upside:.1f}%)\n"
                        f"📊 *IFR(2):* {ifr2:.1f} | *ConnorsRSI:* {crsi:.1f}\n"
                        f"🏢 *Score Fundamentalista:* {score_f}\n"
                        f"{texto_macro}\n\n"
                        f"🕒 {hora_atual}"
                    )
                    
                    print(f"🔥 GATILHO DETETADO: {t_clean}! A disparar alerta...")
                    enviar_alerta_whatsapp(msg)
                    time.sleep(2)

            except Exception:
                continue

        # Intervalo entre varreduras técnicas normais (15 minutos)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo concluído. Próxima checagem em 15 minutos...")
        time.sleep(900)

if __name__ == "__main__":
    executar_radar_loop()
