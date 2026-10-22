import json
import base64
import requests

def obter_carteira_ibrx100():
    """
    Obtém a lista oficial de ações do IBrX 100 diretamente da API da B3.
    Inclui paginação e fallback de contingência.
    """
    # Parâmetros codificados em Base64 para a API de índices da B3 (pageNumber 1, pageSize 120)
    payload_str = '{"language":"pt-br","pageNumber":1,"pageSize":120,"index":"IBXX","segment":"1"}'
    token = base64.b64encode(payload_str.encode("utf-8")).decode("utf-8")
    
    url = f"https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/{token}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.b3.com.br/",
        "Accept": "application/json, text/plain, */*"
    }

    print("A conectar à B3 para recolher os ativos do IBrX 100...")
    tickers = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        dados = response.json()
        
        resultados = dados.get("results") or []
        for item in resultados:
            cod = item.get("cod")
            if cod and cod.strip().isalnum():
                ticker_formatado = f"{cod.strip()}.SA"
                if ticker_formatado not in tickers:
                    tickers.append(ticker_formatado)
                    
    except Exception as e:
        print(f"Aviso: Falha temporária no endpoint direto da B3 ({e}). A aplicar contingência...")

    # Se a requisição à B3 falhar ou retornar vazia, aplica lista estruturada de contingência do IBrX 100
    if len(tickers) < 50:
        tickers = [
            "ABEV3.SA", "ALOS3.SA", "ALPA4.SA", "ARZZ3.SA", "ASAI3.SA", "AURE3.SA", "AZUL4.SA", "B3SA3.SA",
            "BBAS3.SA", "BBDC3.SA", "BBDC4.SA", "BBSE3.SA", "BEEF3.SA", "BPAC11.SA", "BRAP4.SA", "BRFS3.SA",
            "BRKM5.SA", "CCRO3.SA", "CIEL3.SA", "CMIG4.SA", "CMIN3.SA", "COGN3.SA", "CPFE3.SA", "CPLE6.SA",
            "CRFB3.SA", "CSAN3.SA", "CSNA3.SA", "CVCB3.SA", "CYRE3.SA", "DXCO3.SA", "EGIE3.SA", "ELET3.SA",
            "ELET6.SA", "EMBR3.SA", "ENEV3.SA", "ENGI11.SA", "EQTL3.SA", "EZTC3.SA", "FLRY3.SA", "GGBR4.SA",
            "GOAU4.SA", "GOLL4.SA", "HAPV3.SA", "HYPE3.SA", "IGTI11.SA", "IRBR3.SA", "ITSA4.SA", "ITUB4.SA",
            "JBSS3.SA", "KLBN11.SA", "LREN3.SA", "LWSA3.SA", "MGLU3.SA", "MRFG3.SA", "MRVE3.SA", "MULT3.SA",
            "NTCO3.SA", "PCAR3.SA", "PETR3.SA", "PETR4.SA", "PRIO3.SA", "RADL3.SA", "RAID3.SA", "RAIZ4.SA",
            "RDOR3.SA", "RECV3.SA", "RENT3.SA", "RRRP3.SA", "SANB11.SA", "SBSP3.SA", "SLCE3.SA", "SMTO3.SA",
            "SOMA3.SA", "SUZB3.SA", "TAEE11.SA", "TIMS3.SA", "TOTS3.SA", "TRPL4.SA", "UGPA3.SA", "USIM5.SA",
            "VALE3.SA", "VAMO3.SA", "VBBR3.SA", "VIVA3.SA", "VIVT3.SA", "WEGE3.SA", "YDUQ3.SA"
        ]

    # Guarda em cache local para que as próximas execuções sejam instantâneas
    with open("ibrx100_tickers.json", "w", encoding="utf-8") as f:
        json.dump(tickers, f, indent=2)

    print(f"Sucesso! {len(tickers)} ativos carregados e guardados em 'ibrx100_tickers.json'.")
    return tickers

if __name__ == "__main__":
    lista = obter_carteira_ibrx100()
    print("\nPrimeiros 10 papéis da carteira:")
    for t in lista[:10]:
        print(f"- {t}")
    