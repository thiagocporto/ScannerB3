import os
import json
from datetime import datetime
import pandas as pd

def formatar_badge_swing(valor):
    val_str = str(valor).upper().strip()
    if "COMPRA" in val_str or "GATILHO" in val_str:
        return f'<span class="badge bg-success">{valor}</span>'
    elif "OBSERVAR" in val_str or "ATENÇÃO" in val_str:
        return f'<span class="badge bg-warning text-dark">{valor}</span>'
    elif "NEUTRO" in val_str:
        return f'<span class="badge bg-secondary">{valor}</span>'
    return f'<span class="badge bg-light text-dark">{valor}</span>'

def formatar_badge_score(score_raw):
    try:
        score = int(str(score_raw).split()[0])
        if score >= 70:
            return f'<span class="badge bg-success">{score_raw}</span>'
        elif score >= 50:
            return f'<span class="badge bg-primary">{score_raw}</span>'
        else:
            return f'<span class="badge bg-secondary">{score_raw}</span>'
    except Exception:
        return str(score_raw)

def gerar_dashboard_html(caminho_csv="scanner_fechamento.csv", caminho_saida="index.html"):
    df = pd.DataFrame()
    if os.path.exists(caminho_csv):
        try:
            df = pd.read_csv(caminho_csv)
        except Exception:
            pass

    # Carregar alertas intraday de hoje
    oportunidades = []
    if os.path.exists("oportunidades_hoje.json"):
        try:
            with open("oportunidades_hoje.json", "r", encoding="utf-8") as f:
                oportunidades = json.load(f)
        except Exception:
            oportunidades = []

    # Construir Cards de Oportunidades Intraday
    cards_html = ""
    if oportunidades:
        cards_html += """
        <div class="row mb-4">
            <div class="col-12">
                <div class="card border-success shadow-sm">
                    <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
                        <span class="fw-bold"><i class="bi bi-lightning-charge-fill"></i> 🔥 OPORTUNIDADES DETECTADAS HOJE (INTRADAY)</span>
                        <span class="badge bg-light text-success fw-bold">Ao Vivo</span>
                    </div>
                    <div class="card-body">
                        <div class="row g-3">
        """
        for op in oportunidades:
            cards_html += f"""
                            <div class="col-md-4 col-sm-6">
                                <div class="p-3 border rounded bg-light border-2 border-success position-relative">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <h4 class="fw-bold text-dark m-0">#{op.get('ticker')}</h4>
                                        <span class="badge bg-dark">{op.get('regime')}</span>
                                    </div>
                                    <div class="fs-5 fw-bold text-success mb-1">R$ {op.get('preco', 0.0):.2f}</div>
                                    <div class="small text-muted mb-1"><strong>RSI(2):</strong> <span class="badge bg-danger">{op.get('rsi2', 0.0):.2f}</span></div>
                                    <div class="small text-muted mb-1"><strong>MM200:</strong> R$ {op.get('mm200', 0.0):.2f}</div>
                                    <div class="small text-muted"><strong>Fundamentos:</strong> {op.get('score', '-')}</div>
                                    <div class="text-end text-muted mt-2" style="font-size: 0.75rem;">Detectado às {op.get('hora', '-')}</div>
                                </div>
                            </div>
            """
        cards_html += """
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    else:
        cards_html = """
        <div class="alert alert-info border-0 shadow-sm mb-4 d-flex align-items-center" role="alert">
            <i class="bi bi-info-circle me-2 fs-5"></i>
            <div>Nenhum papel acionou sobrevenda extrema de Larry Connors no pregão até o momento. O radar segue monitorando o IBrX-100 a cada 15 min.</div>
        </div>
        """

    # Gerar linhas da tabela geral se existir CSV
    tabela_linhas = ""
    if not df.empty:
        colunas_esperadas = ["Ticker", "Preço (R$)", "RSI(2)", "SMA 200", "Volume > Média", "Score Fundamentalista", "Swing Trade"]
        colunas_ativas = [c for c in colunas_esperadas if c in df.columns]
        
        for _, row in df.iterrows():
            tabela_linhas += "<tr>"
            for col in colunas_ativas:
                val = row[col]
                if col == "Swing Trade":
                    tabela_linhas += f"<td>{formatar_badge_swing(val)}</td>"
                elif col == "Score Fundamentalista":
                    tabela_linhas += f"<td>{formatar_badge_score(val)}</td>"
                elif col in ["Preço (R$)", "SMA 200"]:
                    try:
                        tabela_linhas += f"<td>R$ {float(val):.2f}</td>"
                    except Exception:
                        tabela_linhas += f"<td>{val}</td>"
                elif col == "RSI(2)":
                    try:
                        v_rsi = float(val)
                        badge_c = "bg-danger" if v_rsi <= 15 else ("bg-warning text-dark" if v_rsi <= 25 else "bg-light text-dark")
                        tabela_linhas += f'<td><span class="badge {badge_c}">{v_rsi:.1f}</span></td>'
                    except Exception:
                        tabela_linhas += f"<td>{val}</td>"
                else:
                    tabela_linhas += f"<td>{val}</td>"
            tabela_linhas += "</tr>\n"

    data_agora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>WF Investimentos - Radar Quantitativo B3</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        body {{ background-color: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .card {{ border-radius: 10px; }}
        .table-hover tbody tr:hover {{ background-color: #e9ecef; }}
    </style>
</head>
<body class="py-4">
    <div class="container-fluid px-4">
        <header class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
            <div>
                <h2 class="fw-bold text-dark m-0"><i class="bi bi-graph-up-arrow text-primary"></i> WF Investimentos • Radar B3</h2>
                <div class="text-muted small">Estratégia Quantitativa Larry Connors RSI(2) & Regimes de Mercado</div>
            </div>
            <div class="text-end">
                <span class="badge bg-dark">Atualizado: {data_agora}</span>
            </div>
        </header>

        {cards_html}

        <div class="card shadow-sm border-0 mb-4">
            <div class="card-header bg-white fw-bold py-3">
                <i class="bi bi-table"></i> Panorama Consolidado de Ativos
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0 text-center">
                        <thead class="table-dark">
                            <tr>
                                <th>Ticker</th>
                                <th>Preço (R$)</th>
                                <th>RSI(2)</th>
                                <th>SMA 200</th>
                                <th>Volume > Média</th>
                                <th>Score Fund.</th>
                                <th>Sinal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tabela_linhas}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer class="text-center text-muted small py-3 border-top mt-4">
            WF Investimentos • Automação Quantitativa Integrada • Dados B3 via yfinance
        </footer>
    </div>
</body>
</html>
"""

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html_completo)

if __name__ == "__main__":
    gerar_dashboard_html()
