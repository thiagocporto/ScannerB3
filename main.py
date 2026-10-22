import coletor_ibrx100
import engine_analise
import gerar_site

def executar_pipeline_completo():
    print("=== 1/3: Atualizando lista IBrX 100 ===")
    coletor_ibrx100.obter_carteira_ibrx100()

    print("\n=== 2/3: Executando análise técnica e fundamentalista ===")
    engine_analise.executar_scanner()

    print("\n=== 3/3: Gerando painel web (index.html) ===")
    gerar_site.gerar_dashboard_html()
    
    print("\n Pipeline concluído com sucesso!")

if __name__ == "__main__":
    executar_pipeline_completo()