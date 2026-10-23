import sys
from engine_analise import executar_scanner
from gerar_site import gerar_dashboard_html
from alertas_telegram import enviar_alerta_telegram

def main():
    print("=" * 60)
    print("WF INVESTIMENTOS | INICIANDO PIPELINE DIÁRIO B3")
    print("=" * 60)
    
    # 1. Executa a análise quantitativa e fundamentalista
    try:
        executar_scanner()
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha no motor de análise: {e}")
        sys.exit(1)
        
    # 2. Compila o index.html com os gráficos e ordenação
    try:
        gerar_dashboard_html()
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha ao compilar o dashboard: {e}")
        sys.exit(1)
        
    # 3. Dispara o relatório executivo para o seu Telegram
    try:
        print("\nEnviando resumo para o Telegram...")
        enviar_alerta_telegram()
    except Exception as e:
        print(f"[AVISO] Não foi possível enviar para o Telegram: {e}")
        
    print("\n" + "=" * 60)
    print("=== PIPELINE FINALIZADO COM SUCESSO ===")
    print("=" * 60)

if __name__ == "__main__":
    main()