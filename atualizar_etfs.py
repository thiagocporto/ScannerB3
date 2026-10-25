import json
import os

ARQUIVO = "universo_b3.json"

# Carrega base existente para preservar Acoes, FIIs e BDRs
dados = []
if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        dados = json.load(f)

# Remove ETFs antigos para reescrever a cesta oficial dos 20
dados = [item for item in dados if item.get("tipo") != "ETF"]

top_20_etfs = [
    {"ticker": "BOVA11", "tipo": "ETF", "nome": "iShares Ibovespa"},
    {"ticker": "BRAX11", "tipo": "ETF", "nome": "iShares IBrX 100"},
    {"ticker": "SMAL11", "tipo": "ETF", "nome": "iShares Small Cap"},
    {"ticker": "NDIV11", "tipo": "ETF", "nome": "Nu Ibov Smart Dividendos"},
    {"ticker": "DIVO11", "tipo": "ETF", "nome": "It Now IDIV Dividendos"},
    {"ticker": "FIND11", "tipo": "ETF", "nome": "iShares Setor Financeiro"},
    {"ticker": "MATB11", "tipo": "ETF", "nome": "iShares Materiais Basicos"},
    {"ticker": "IVVB11", "tipo": "ETF", "nome": "iShares S&P 500"},
    {"ticker": "SPXI11", "tipo": "ETF", "nome": "It Now S&P 500"},
    {"ticker": "NASD11", "tipo": "ETF", "nome": "Trend Nasdaq 100"},
    {"ticker": "ACWI11", "tipo": "ETF", "nome": "Trend MSCI ACWI Global"},
    {"ticker": "XINA11", "tipo": "ETF", "nome": "Trend MSCI China"},
    {"ticker": "GOLD11", "tipo": "ETF", "nome": "Trend Ouro Fixo"},
    {"ticker": "HASH11", "tipo": "ETF", "nome": "Hashdex Nasdaq Crypto"},
    {"ticker": "QBTC11", "tipo": "ETF", "nome": "QR CME CF Bitcoin"},
    {"ticker": "QETH11", "tipo": "ETF", "nome": "QR CME CF Ether"},
    {"ticker": "B5P211", "tipo": "ETF", "nome": "It Now IMA-B 5 P2"},
    {"ticker": "IMAB11", "tipo": "ETF", "nome": "It Now IMA-B Geral"},
    {"ticker": "IB5M11", "tipo": "ETF", "nome": "It Now IMA-B 5+"},
    {"ticker": "LFTS11", "tipo": "ETF", "nome": "Investo Teva Tesouro Selic"}
]

dados.extend(top_20_etfs)

with open(ARQUIVO, "w", encoding="utf-8") as f:
    json.dump(dados, f, indent=4, ensure_ascii=False)

print(f"Sucesso: universo_b3.json atualizado com os 20 Top ETFs da B3 (Total: {len(dados)} ativos)!")
