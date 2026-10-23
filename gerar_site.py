import os
import json
from datetime import datetime
import pandas as pd

def formatar_badge_swing(valor):
    val_str = str(valor).strip()
    val_upper = val_str.upper()
    if "ALTA FORTE" in val_upper or "COMPRA" in val_upper:
        return f'<span class="badge badge-trend-alta">{val_str}</span>'
    elif "PULLBACK" in val_upper:
        return f'<span class="badge badge-pullback">{val_str}</span>'
    elif "LATERAL" in val_upper or "NEUTRO" in val_upper:
        return f'<span class="badge badge-lateral">{val_str}</span>'
    elif "SOBRECOMPRADO" in val_upper:
        return f'<span class="badge badge-sobrecomprado">{val_str}</span>'
    elif "BAIXA" in val_upper:
        return f'<span class="badge badge-baixa">{val_str}</span>'
    return f'<span class="badge bg-secondary">{val_str}</span>'

def formatar_badge_pos(valor):
    val_str = str(valor).strip()
    if "Alta" in val_str:
        return f'<span class="badge badge-pos-alta">{val_str}</span>'
    elif "Baixa" in val_str or "Abaixo" in val_str:
        return f'<span class="badge badge-pos-baixa">{val_str}</span>'
    return f'<span class="badge bg-secondary">{val_str}</span>'

def formatar_badge_score(score_raw):
    s = str(score_raw).strip()
    try:
        val = int(s.split()[0])
        if val >= 80:
            return f'<span class="badge badge-score-exc">{s}</span>'
        elif val >= 60:
            return f'<span class="badge badge-score-bom">{s}</span>'
        elif val >= 40:
            return f'<span class="badge badge-score-reg">{s}</span>'
        else:
            return f'<span class="badge badge-score-fra">{s}</span>'
    except Exception:
        return f'<span class="badge bg-secondary">{s}</span>'

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
                <div class="card card-custom border-1 border-warning">
                    <div class="card-header bg-dark d-flex justify-content-between align-items-center border-bottom border-warning">
                        <span class="fw-bold text-warning"><i class="bi bi-lightning-charge-fill"></i> 🔥 OPORTUNIDADES DETECTADAS HOJE (INTRADAY)</span>
                        <span class="badge bg-success text-white fw-bold">Ao Vivo</span>
                    </div>
                    <div class="card-body">
                        <div class="row g-3">
        """
        for op in oportunidades:
            cards_html += f"""
                            <div class="col-md-4 col-sm-6">
                                <div class="p-3 rounded bg-dark border border-success position-relative">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <h4 class="fw-bold text-white m-0">#{op.get('ticker')}</h4>
                                        <span class="badge bg-primary">{op.get('regime')}</span>
                                    </div>
                                    <div class="fs-4 fw-bold text-success mb-1">R$ {op.get('preco', 0.0):.2f}</div>
                                    <div class="small text-muted mb-1"><strong>RSI(2):</strong> <span class="badge bg-danger fs-6">{op.get('rsi2', 0.0):.2f}</span></div>
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

    # Montar tabela e dados para gráficos
    tabela_linhas = ""
    dist_swing = {}
    menores_ifr = []

    if not df.empty:
        # Gráficos
        if "Swing Trade" in df.columns:
            dist_swing = df["Swing Trade"].value_counts().to_dict()

        if "IFR(2)" in df.columns or "RSI(2)" in df.columns:
            col_rsi = "IFR(2)" if "IFR(2)" in df.columns else "RSI(2)"
            df_sorted = df.dropna(subset=[col_rsi]).sort_values(by=col_rsi).head(8)
            for _, r in df_sorted.iterrows():
                menores_ifr.append({"ticker": str(r.get("Ticker", "")), "ifr": float(r.get(col_rsi, 0))})

        for _, row in df.iterrows():
            t = str(row.get("Ticker", ""))
            p = row.get("Preço (R$)", 0.0)
            mm = row.get("SMA 200", 0.0)
            ifr = row.get("IFR(2)", row.get("RSI(2)", 0.0))
            sw = row.get("Swing Trade", "-")
            pos = row.get("Position (Semanal)", "-")
            sc = row.get("Score Fund.", row.get("Score Fundamentalista", "-"))

            ifr_color = "text-danger fw-bold" if float(ifr) <= 15 else ("text-warning" if float(ifr) <= 25 else "text-muted")

            tabela_linhas += f"""
            <tr>
                <td class="fw-bold text-white">{t}</td>
                <td>R$ {float(p):.2f}</td>
                <td>R$ {float(mm):.2f}</td>
                <td class="{ifr_color}">{float(ifr):.1f}</td>
                <td>{formatar_badge_swing(sw)}</td>
                <td>{formatar_badge_pos(pos)}</td>
                <td>{formatar_badge_score(sc)}</td>
            </tr>
            """

    data_agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    total_ativos = len(df) if not df.empty else 83

    # Dados Chart JS
    chart_labels = json.dumps(list(dist_swing.keys()))
    chart_values = json.dumps(list(dist_swing.values()))
    bar_labels = json.dumps([x["ticker"] for x in menores_ifr])
    bar_values = json.dumps([x["ifr"] for x in menores_ifr])

    html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>WF Investimentos - Avaliação de Ativos & Mercado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            background-color: #0b132b;
            color: #e0e6ed;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .navbar-custom {{
            background-color: #1c2541;
            border-bottom: 2px solid #3a506b;
            padding: 12px 24px;
        }}
        .card-custom {{
            background-color: #1c2541;
            border: 1px solid #3a506b;
            border-radius: 10px;
        }}
        .table-custom {{
            color: #d1d5db;
        }}
        .table-custom th {{
            background-color: #0f172a !important;
            color: #94a3b8;
            font-size: 0.85rem;
            text-transform: uppercase;
            border-bottom: 2px solid #3a506b;
        }}
        .table-custom td {{
            background-color: transparent !important;
            border-bottom: 1px solid #1e293b;
            font-size: 0.9rem;
        }}
        .table-hover tbody tr:hover td {{
            background-color: #233152 !important;
        }}
        /* Badges Temáticas WF */
        .badge-trend-alta {{ background-color: #10b981; color: white; }}
        .badge-pullback {{ background-color: #ec4899; color: white; }}
        .badge-lateral {{ background-color: #8b5cf6; color: white; }}
        .badge-sobrecomprado {{ background-color: #f59e0b; color: white; }}
        .badge-baixa {{ background-color: #ef4444; color: white; }}
        .badge-pos-alta {{ background-color: transparent; border: 1px solid #10b981; color: #10b981; }}
        .badge-pos-baixa {{ background-color: transparent; border: 1px solid #ef4444; color: #ef4444; }}
        .badge-score-exc {{ background-color: transparent; border: 1px solid #10b981; color: #10b981; }}
        .badge-score-bom {{ background-color: transparent; border: 1px solid #3b82f6; color: #3b82f6; }}
        .badge-score-reg {{ background-color: transparent; border: 1px solid #f59e0b; color: #f59e0b; }}
        .badge-score-fra {{ background-color: transparent; border: 1px solid #ef4444; color: #ef4444; }}
        .search-box {{
            background-color: #0f172a;
            border: 1px solid #3a506b;
            color: white;
        }}
        .search-box:focus {{
            background-color: #0f172a;
            color: white;
            border-color: #60a5fa;
            box-shadow: none;
        }}
    </style>
</head>
<body class="pb-5">

    <!-- Top Navbar -->
    <nav class="navbar navbar-custom mb-4">
        <div class="container-fluid d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
                <div class="rounded-circle d-flex align-items-center justify-content-center me-3 border border-warning" style="width: 48px; height: 48px; background-color: #0b132b;">
                    <span class="fw-bold text-warning" style="font-size: 1.1rem;">WF</span>
                </div>
                <div>
                    <h4 class="fw-bold text-white m-0">WF INVESTIMENTOS</h4>
                    <span class="text-warning small text-uppercase" style="letter-spacing: 1px; font-size: 0.75rem;">Avaliação de Ativos & Mercado</span>
                </div>
            </div>
            <div class="text-end text-muted small">
                <div><i class="bi bi-clock me-1 text-primary"></i> Atualizado em: <strong class="text-white">{data_agora}</strong></div>
                <div>Universo: <strong class="text-white">{total_ativos} IBrX 100</strong></div>
            </div>
        </div>
    </nav>

    <div class="container-fluid px-4">

        <!-- Banner Intraday -->
        {cards_html}

        <!-- Gráficos -->
        <div class="row g-4 mb-4">
            <div class="col-lg-6">
                <div class="card card-custom p-3 h-100 shadow-sm">
                    <h6 class="fw-bold text-warning mb-3"><i class="bi bi-pie-chart-fill me-2"></i> DISTRIBUIÇÃO DE TENDÊNCIAS (SWING TRADE)</h6>
                    <div style="position: relative; height: 260px;">
                        <canvas id="chartTendencias"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="card card-custom p-3 h-100 shadow-sm">
                    <h6 class="fw-bold text-warning mb-3"><i class="bi bi-bar-chart-fill me-2"></i> RADAR IFR(2) - MENORES NÍVEIS (PULLBACKS)</h6>
                    <div style="position: relative; height: 260px;">
                        <canvas id="chartIfr"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tabela -->
        <div class="card card-custom shadow-sm">
            <div class="card-header bg-transparent d-flex justify-content-between align-items-center py-3 border-bottom border-secondary">
                <div>
                    <h5 class="fw-bold text-white m-0">Scanner Consolidado de Ativos</h5>
                    <div class="text-muted small">Clique no cabeçalho das colunas para ordenar</div>
                </div>
                <div class="w-25">
                    <input type="text" id="filtroTicker" class="form-control form-control-sm search-box" placeholder="🔍 Pesquisar Ticker (ex: VALE3)...">
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-custom table-hover align-middle mb-0 text-center" id="tabelaScanner">
                        <thead>
                            <tr>
                                <th>TICKER ⇕</th>
                                <th>PREÇO ⇕</th>
                                <th>SMA 200 ⇕</th>
                                <th>IFR(2) ⇕</th>
                                <th>SWING TRADE ⇕</th>
                                <th>POSITION (SEMANAL) ⇕</th>
                                <th>SCORE FUND. ⇕</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tabela_linhas}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer class="text-center text-muted small py-4 mt-4 border-top border-secondary">
            WF Investimentos • Automação Quantitativa Integrada • Dados B3 via yfinance
        </footer>
    </div>

    <script>
        // Gráfico Rosca
        const ctxPie = document.getElementById('chartTendencias').getContext('2d');
        new Chart(ctxPie, {{
            type: 'doughnut',
            data: {{
                labels: {chart_labels},
                datasets: [{{
                    data: {chart_values},
                    backgroundColor: ['#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#3b82f6', '#ec4899', '#06b6d4'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }}
                }}
            }}
        }});

        // Gráfico Barras
        const ctxBar = document.getElementById('chartIfr').getContext('2d');
        new Chart(ctxBar, {{
            type: 'bar',
            data: {{
                labels: {bar_labels},
                datasets: [{{
                    label: 'IFR(2)',
                    data: {bar_values},
                    backgroundColor: '#d97706',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ min: 0, max: 100, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
                    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});

        // Filtro de Busca
        document.getElementById('filtroTicker').addEventListener('keyup', function() {{
            const val = this.value.toUpperCase();
            const trs = document.querySelectorAll('#tabelaScanner tbody tr');
            trs.forEach(tr => {{
                const td = tr.querySelector('td');
                if (td) {{
                    tr.style.display = td.innerText.toUpperCase().indexOf(val) > -1 ? '' : 'none';
                }}
            }});
        }});
    </script>
</body>
</html>
"""

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html_completo)

if __name__ == "__main__":
    gerar_dashboard_html()
