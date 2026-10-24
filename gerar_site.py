import os
import json
from datetime import datetime
import pandas as pd

ARQUIVO_CSV = r"D:\ScannerB3\scanner_fechamento.csv"
ARQUIVO_TESES = r"D:\ScannerB3\teses_qualitativas.json"
ARQUIVO_HTML = r"D:\ScannerB3\index.html"

def carregar_teses():
    if os.path.exists(ARQUIVO_TESES):
        try:
            with open(ARQUIVO_TESES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def classificar_estilo_botao(ticker, teses):
    if ticker not in teses or not teses[ticker].get("parecer"):
        return (
            "border: 1px solid #475569; color: #94a3b8; background-color: rgba(30, 41, 59, 0.6);",
            "background-color: #64748b;"
        )
    
    parecer = str(teses[ticker].get("parecer", "")).lower()
    termos_vermelho = ["desfavorável", "desfavoravel", "venda", "alto risco", "deterioração", "desinvestir", "evitar", "pessimista"]
    termos_verde = ["favorável", "favoravel", "compra", "acumular", "acumulação", "positivo", "oportunidade", "atrativo", "alta convicção"]
    
    if any(p in parecer for p in termos_vermelho):
        return (
            "border: 1px solid #f43f5e; color: #fda4af; background-color: rgba(225, 29, 72, 0.25); box-shadow: 0 0 8px rgba(244, 63, 94, 0.25);",
            "background-color: #f43f5e; box-shadow: 0 0 6px #f43f5e;"
        )
    elif any(p in parecer for p in termos_verde):
        return (
            "border: 1px solid #10b981; color: #6ee7b7; background-color: rgba(16, 185, 129, 0.25); box-shadow: 0 0 8px rgba(16, 185, 129, 0.25);",
            "background-color: #10b981; box-shadow: 0 0 6px #10b981;"
        )
    else:
        return (
            "border: 1px solid #f59e0b; color: #fde68a; background-color: rgba(245, 158, 11, 0.25); box-shadow: 0 0 8px rgba(245, 158, 11, 0.25);",
            "background-color: #f59e0b; box-shadow: 0 0 6px #f59e0b;"
        )

def gerar_dashboard_html():
    if not os.path.exists(ARQUIVO_CSV):
        print(f"[ERRO] {ARQUIVO_CSV} nao encontrado.")
        return

    df = pd.read_csv(ARQUIVO_CSV)
    teses = carregar_teses()
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # 1. Gráficos Analíticos Superiores (Chart.js)
    col_swing = "Swing Trade" if "Swing Trade" in df.columns else df.columns[4]
    dist_swing = df[col_swing].value_counts().to_dict()
    labels_donut = list(dist_swing.keys())
    valores_donut = list(dist_swing.values())

    col_rsi = "RSI(2)" if "RSI(2)" in df.columns else df.columns[3]
    df_temp = df.copy()
    df_temp[col_rsi] = pd.to_numeric(df_temp[col_rsi], errors="coerce").fillna(50.0)
    df_sorted_rsi = df_temp.sort_values(by=col_rsi).head(8)
    labels_bar = df_sorted_rsi["Ticker"].tolist()
    valores_bar = [round(float(v), 1) for v in df_sorted_rsi[col_rsi].tolist()]

    # 2. Tabela Consolidada Dark Navy
    linhas_tabela = ""
    for _, row in df.iterrows():
        ticker = str(row.get("Ticker", "")).strip().upper()
        preco = float(pd.to_numeric(row.get("Preço (R$)", 0.0), errors="coerce") or 0.0)
        sma200 = float(pd.to_numeric(row.get("SMA 200", 0.0), errors="coerce") or 0.0)
        rsi2 = float(pd.to_numeric(row.get("RSI(2)", 0.0), errors="coerce") or 0.0)
        crsi = float(pd.to_numeric(row.get("ConnorsRSI", rsi2), errors="coerce") or rsi2)
        fase = str(row.get("Swing Trade", "Neutro"))
        score = str(row.get("Score Fundamentalista", "Regular"))

        badge_fase = f'<span class="px-3 py-1 text-xs font-medium rounded-full bg-slate-800/80 text-blue-300 border border-blue-500/30">{fase}</span>'

        if "Excelente" in score or "Bom" in score:
            badge_score = f'<span class="text-xs font-semibold text-emerald-400">{score}</span>'
        elif "Fraco" in score:
            badge_score = f'<span class="text-xs font-semibold text-rose-400">{score}</span>'
        else:
            badge_score = f'<span class="text-xs font-semibold text-amber-400">{score}</span>'

        cor_rsi = "text-emerald-400 font-bold" if rsi2 <= 15 else ("text-rose-400 font-bold" if rsi2 >= 85 else "text-slate-300")

        estilo_btn, estilo_led = classificar_estilo_botao(ticker, teses)
        btn_tese = f'''<button onclick="abrirModal('{ticker}')" style="{estilo_btn}" class="px-3 py-1 text-xs font-bold rounded cursor-pointer transition-transform hover:scale-105 inline-flex items-center gap-1.5">
            <span style="{estilo_led}" class="w-2 h-2 rounded-full inline-block"></span>
            Tese IA
        </button>'''

        linhas_tabela += f"""
        <tr class="border-b border-slate-800 hover:bg-slate-800/40 transition-colors">
            <td class="px-4 py-3.5 font-bold text-white tracking-wide">{ticker}</td>
            <td class="px-4 py-3.5 text-right font-medium text-slate-100">R$ {preco:.2f}</td>
            <td class="px-4 py-3.5 text-right text-slate-400">R$ {sma200:.2f}</td>
            <td class="px-4 py-3.5 text-right {cor_rsi}">{rsi2:.1f}</td>
            <td class="px-4 py-3.5 text-right font-semibold text-amber-400">{crsi:.1f}</td>
            <td class="px-4 py-3.5 text-center">{badge_fase}</td>
            <td class="px-4 py-3.5 text-center">{badge_score}</td>
            <td class="px-4 py-3.5 text-center">{btn_tese}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WF Investimentos | Scanner Quantitativo B3</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .gold-gradient {{ background: linear-gradient(135deg, #1b263b 0%, #0d1b2a 100%); }}
        .gold-border {{ border-color: #c5a059; }}
        .gold-text {{ color: #d4af37; }}
    </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen flex flex-col">

    <!-- Top Header Institucional WF Investimentos -->
    <header class="gold-gradient text-white border-b-4 gold-border shadow-xl">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-4">
                <img src="logo.png" alt="WF Investimentos" class="w-14 h-14 rounded-full border-2 gold-border shadow-md object-cover bg-slate-900" onerror="this.style.display='none'">
                <div>
                    <h1 class="text-2xl font-black tracking-wider uppercase flex items-center gap-2">
                        <span>WF INVESTIMENTOS</span>
                    </h1>
                    <p class="text-xs gold-text uppercase tracking-widest font-semibold">Avaliação Institucional & Scanner B3</p>
                </div>
            </div>
            <div class="text-right text-xs text-slate-300">
                <p><i class="fa-regular fa-clock mr-1 gold-text"></i> Atualizado em: <span class="font-bold text-white">{agora_str}</span></p>
                <p class="text-slate-400">Universo: B3 IBrX 100 • {len(df)} Ações</p>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">

        <!-- Barra de Termômetro Semafórico das Teses IA -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs shadow-md">
            <span class="font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <i class="fa-solid fa-brain gold-text"></i> Termômetro das Teses IA:
            </span>
            <div class="flex items-center gap-4">
                <span class="inline-flex items-center gap-1.5 font-medium text-emerald-300">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#10b981]"></span> Parecer Favorável
                </span>
                <span class="inline-flex items-center gap-1.5 font-medium text-amber-300">
                    <span class="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-[0_0_8px_#f59e0b]"></span> Cautela / Regular
                </span>
                <span class="inline-flex items-center gap-1.5 font-medium text-rose-300">
                    <span class="w-2.5 h-2.5 rounded-full bg-rose-400 shadow-[0_0_8px_#f43f5e]"></span> Desfavorável
                </span>
            </div>
        </div>

        <!-- Seção Superior de Cards Analíticos (Restauração dos Gráficos) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Gráfico 1: Tendências e Fases -->
            <div class="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-lg">
                <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-chart-pie gold-text"></i> Distribuição de Tendências (Swing Trade)
                </h3>
                <div class="relative h-56">
                    <canvas id="chartDonut"></canvas>
                </div>
            </div>

            <!-- Gráfico 2: Menores IFR(2) (Radar Larry Connors) -->
            <div class="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-lg">
                <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-chart-bar gold-text"></i> Radar IFR(2) - Menores Níveis (Pullbacks)
                </h3>
                <div class="relative h-56">
                    <canvas id="chartBar"></canvas>
                </div>
            </div>
        </div>

        <!-- Tabela Consolidada Dark Navy com Busca -->
        <div class="bg-slate-900 rounded-xl border border-slate-800 shadow-2xl overflow-hidden">
            <div class="p-4 sm:p-5 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60">
                <div>
                    <h2 class="text-base sm:text-lg font-bold text-white tracking-wide">Matriz de Ativos B3 (IBrX 100)</h2>
                    <p class="text-xs text-slate-400">Total: {len(df)} ações monitoradas</p>
                </div>
                <div class="relative w-full sm:w-72">
                    <input type="text" id="filtroTicker" placeholder="Pesquisar Ticker (ex: VALE3)..." class="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-950 border border-slate-700 text-white rounded-lg focus:outline-none focus:border-amber-400">
                    <i class="fa-solid fa-search absolute left-3 top-2.5 text-slate-500 text-xs"></i>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs sm:text-sm" id="tabelaDados">
                    <thead class="bg-slate-950/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                        <tr>
                            <th class="px-4 py-3.5">TICKER</th>
                            <th class="px-4 py-3.5 text-right">PREÇO</th>
                            <th class="px-4 py-3.5 text-right">SMA 200</th>
                            <th class="px-4 py-3.5 text-right">IFR(2)</th>
                            <th class="px-4 py-3.5 text-right">CONNORSISI</th>
                            <th class="px-4 py-3.5 text-center">FASE TÉCNICA</th>
                            <th class="px-4 py-3.5 text-center">SCORE FUND.</th>
                            <th class="px-4 py-3.5 text-center">PARECER IA</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60">
                        {linhas_tabela}
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <!-- Modal Dark Navy da Tese Institucional -->
    <div id="modalBox" class="fixed inset-0 bg-slate-950/85 backdrop-blur-sm hidden items-center justify-center p-4 z-50">
        <div class="bg-slate-900 border-2 gold-border rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 id="modalTitulo" class="text-base font-bold text-white flex items-center gap-2">
                    📊 Tese Institucional
                </h3>
                <button onclick="fecharModal()" class="text-slate-400 hover:text-white text-2xl font-bold cursor-pointer transition-colors">&times;</button>
            </div>
            
            <div id="modalTexto" class="text-xs sm:text-sm text-slate-200 whitespace-pre-line leading-relaxed max-h-[60vh] overflow-y-auto pr-2">
            </div>

            <div class="border-t border-slate-800 pt-3 flex justify-between items-center text-xs text-slate-500">
                <span>WF Investimentos • Motor Analítico Gemini</span>
                <button onclick="fecharModal()" class="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg cursor-pointer transition-colors">Fechar</button>
            </div>
        </div>
    </div>

    <footer class="bg-slate-950 text-slate-400 py-4 text-center text-xs border-t border-slate-800">
        <p>© {datetime.now().year} WF Investimentos. Análise quantitativa e qualitativa automatizada para apoio decisório.</p>
    </footer>

    <script>
        const TESES = {json.dumps(teses, ensure_ascii=False)};

        function abrirModal(ticker) {{
            const modal = document.getElementById('modalBox');
            const tit = document.getElementById('modalTitulo');
            const txt = document.getElementById('modalTexto');

            if (TESES[ticker] && TESES[ticker].parecer) {{
                const item = TESES[ticker];
                tit.innerHTML = '📊 Tese Institucional: #' + ticker + ' <span class="text-xs text-slate-400 font-normal">(' + (item.data || '') + ' às ' + (item.hora || '') + ')</span>';
                txt.innerText = item.parecer;
            }} else {{
                tit.innerText = '📊 Tese Institucional: #' + ticker;
                txt.innerText = 'Parecer técnico em elaboração pelo motor analítico.';
            }}

            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }}

        function fecharModal() {{
            const modal = document.getElementById('modalBox');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }}

        window.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') fecharModal(); }});
        document.getElementById('modalBox').addEventListener('click', (e) => {{
            if (e.target.id === 'modalBox') fecharModal();
        }});

        // Filtro em tempo real
        document.getElementById('filtroTicker').addEventListener('keyup', function() {{
            let filter = this.value.toUpperCase();
            let rows = document.querySelectorAll('#tabelaDados tbody tr');
            rows.forEach(row => {{
                let ticker = row.cells[0].innerText;
                row.style.display = ticker.toUpperCase().includes(filter) ? '' : 'none';
            }});
        }});

        // Gráfico 1: Tendências (Donut)
        new Chart(document.getElementById('chartDonut'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(labels_donut)},
                datasets: [{{
                    data: {json.dumps(valores_donut)},
                    backgroundColor: ['#10b981', '#f59e0b', '#a855f7', '#f43f5e', '#64748b', '#38bdf8', '#fb7185'],
                    borderColor: '#0f172a',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{ boxWidth: 10, font: {{ size: 10 }}, color: '#cbd5e1' }}
                    }}
                }}
            }}
        }});

        // Gráfico 2: Radar Menores Níveis IFR(2)
        new Chart(document.getElementById('chartBar'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(labels_bar)},
                datasets: [{{
                    label: 'IFR(2)',
                    data: {json.dumps(valores_bar)},
                    backgroundColor: '#d4af37',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, max: 100, grid: {{ color: '#1e293b' }}, ticks: {{ color: '#94a3b8' }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ color: '#cbd5e1' }} }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
    </script>
</body>
</html>
"""
    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Sucesso: index.html regerado com layout completo às {agora_str}!")

if __name__ == "__main__":
    gerar_dashboard_html()
