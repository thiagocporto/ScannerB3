import sys
from coletor_ibrx100 import obter_carteira_ibrx100
from engine_analise import executar_scanner
from gerar_site import gerar_dashboard_html

def rodar_pipeline_completo():
    print("=== INICIANDO PIPELINE QUANTITATIVO B3 ===")
    
    # 1. Coleta da carteira teórica e atualização do ibrx100_tickers.json
    tickers = obter_carteira_ibrx100()
    print(f"Total de ativos capturados: {len(tickers)}")
    
    # 2. Execução do motor de análise técnica e fundamentalista
    # (Lê internamente a lista salva em ibrx100_tickers.json)
    executar_scanner()
    
    # 3. Compilação do dashboard com a marca WF Investimentos e gráficos interativos
    print("Compilando dashboard visual...")
    gerar_dashboard_html(
        caminho_csv="scanner_fechamento.csv",
        caminho_saida="index.html"
    )
    print("=== PIPELINE FINALIZADO COM SUCESSO ===")

if __name__ == "__main__":
    rodar_pipeline_completo()