import os
import pandas as pd
import requests

# Credenciais configuradas
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8615383070:AAFJNFACdTpxGilf8bneLyxuCLwKMo4fv2Q")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8965739506")

def formatar_mensagem(caminho_csv="scanner_fechamento.csv") -> str:
    """Filtra oportunidades de Swing Trade e monta o relatório executivo WF."""
    if not os.path.exists(caminho_csv):
        return ""
    
    df = pd.read_csv(caminho_csv)
    
    # Filtra oportunidades em sobrevenda ou compras de alta probabilidade
    compras = df[df["Swing Trade"].str.contains("COMPRA|Sobrevendido", case=False, na=False)]
    
    if compras.empty:
        return (
            "🏛️ *WF INVESTIMENTOS | RADAR B3*\n\n"
            "Nenhum ativo acionou sobrevenda extrema hoje.\n\n"
            "🔗 *Painel Geral:* https://thiagocporto.github.io/ScannerB3/"
        )
    
    msg = "🏛️ *WF INVESTIMENTOS | RADAR B3*\n"
    msg += "🎯 *Oportunidades de Reversão / Swing Trade:*\n\n"
    
    for _, row in compras.iterrows():
        ticker = row.get("Ticker", "-")
        preco = row.get("Preço (R$)", 0.0)
        rsi = row.get("RSI(2)", 0.0)
        status = row.get("Swing Trade", "-")
        score = row.get("Score Fundamentalista", "-")
        
        msg += (
            f"• *{ticker}* | R$ {preco:.2f}\n"
            f"  IFR(2): `{rsi:.1f}` | Status: {status}\n"
            f"  Fundamentos: *{score}*\n\n"
        )
    
    msg += "📊 *Painel Interativo:* https://thiagocporto.github.io/ScannerB3/"
    return msg

def enviar_alerta_telegram():
    """Envia o alerta formatado via API oficial do Telegram."""
    texto = formatar_mensagem()
    if not texto:
        print("[AVISO] Nenhum dado para enviar.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ Alerta enviado com sucesso para o Telegram!")
            return True
        else:
            print(f"❌ Erro API Telegram: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Falha de conexão: {e}")
        return False

if __name__ == "__main__":
    enviar_alerta_telegram()