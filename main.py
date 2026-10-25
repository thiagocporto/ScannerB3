import sys
from engine_analise import executar_scanner
from gerar_site import gerar_dashboard_html

def main():
    print("=" * 60)
    print("WF INVESTIMENTOS | INICIANDO PIPELINE DIARIO B3")
    print("=" * 60)
    
    try:
        executar_scanner()
    except Exception as e:
        print(f"[ERRO CRITICO] Falha no motor de analise: {e}")
        sys.exit(1)
        
    try:
        gerar_dashboard_html()
    except Exception as e:
        print(f"[ERRO CRITICO] Falha ao compilar dashboard: {e}")
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("=== PIPELINE FINALIZADO COM SUCESSO ===")
    print("=" * 60)

if __name__ == "__main__":
    main()
