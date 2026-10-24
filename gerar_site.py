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

def classificar_botao_tese(ticker, teses):
    if ticker not in teses or not teses[ticker].get("parecer"):
        return (
            "Pendente",
            "background-color: #1e293b; color: #94a3b8; border: 1px solid #334155;",
            "background-color: #64748b;"
        )
    
    parecer = str(teses[ticker].get("parecer", "")).lower()
    
    termos_vermelho = ["desfavorável", "desfavoravel", "venda", "alto risco", "deterioração", "desinvestir", "evitar", "pessimista"]
    termos_verde = ["favorável", "favoravel", "compra", "acumular", "acumulação", "positivo", "oportunidade", "atrativo", "alta convicção"]
    
    if any(p in parecer for p in termos_vermelho):
        # Vermelho / Desfavorável
        return (
            "Desfavorável",
            "background-color: rgba(225, 29, 72, 0.2); color: #fda4af; border: 1px solid #f43f5e;",
            "background-color: #f43f5e; box-shadow: 0 0 6px #f43f5e;"
        )
    elif any(p in parecer for p in termos_verde):
        # Verde / Favorável
        return (
            "Favorável",
            "background-color: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981;",
            "background-color: #10b981; box-shadow: 0 0 6px #10b981;"
        )
    else:
        # Amarelo / Cautela / Regular
        return (
            "Cautela",
            "background-color: rgba(245, 158, 11, 0.2); color: #fde68a; border: 1px solid #f59e0b;",
            "background-color: #f59e0b; box-shadow: 0 0 6px #f59e0b;"
        )

def formatar_badge_swing(valor):
    v = str(valor).lower()
    if "🔥 compra" in v:
        return f'<span class="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-500 text-slate-950 shadow-sm">{valor}</span>'
    elif "pullback em alta" in v or "atenção" in v:
        return f'<span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-900/40 text-amber-300 border border-amber-500/40">{valor}</span>'
    elif "alta forte" in v:
        return f'<span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-900/40 text-emerald-300 border border-emerald-500/40">{valor}</span>'
    elif "sobrecomprado" in v:
        return f'<span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-purple-900/40 text-purple-300 border border-purple-500/40">{valor}</span>'
    elif "baixa" in v:
        return f'<span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-900/40 text-rose-300 border border-rose-500/40">{valor}</span>'
    else:
        return f'<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-800 text-slate-400 border border-slate-700">{valor}</span>'

def formatar_badge_score(score_raw):
    score_str = str(score_raw)
    if "Excelente" in score_str or "Bom" in score_str:
        return f'<span class="px-2.5 py-0.5 text-xs font-bold rounded bg-emerald-900/30 text-emerald-300 border border-emerald-500/30">{score_str}</span>'
    elif "Regular" in score_str:
        return f'<span class="px-2.5 py-0.5 text-xs font-semibold rounded bg-amber-900/30 text-amber-300 border border-amber-500/30">{score_str}</span>'
    elif "Fraco" in score_str:
        return f'<span class="px-2.5 py-0.5 text-xs font-medium rounded bg-rose-900/30 text-rose-300 border border-rose-500/30">{score_str}</span>'
    else:
        return f'<span class="text-xs text-slate-400">{score_str}</span>'

def gerar_dashboard_html():
    if not os.path.exists(ARQUIVO_CSV):
        print(f"[ERRO] {ARQUIVO_CSV} não encontrado.")
        return

    df = pd.read_csv(ARQUIVO_CSV)
    teses = carregar_teses()
    data_atualizacao = datetime.now().strftime("%d/%m/%Y às %H:%M")

    dist_swing = df["Swing Trade"].value_counts().to_dict()
    labels_donut = list(dist_swing.keys())
    valores_donut = list(dist_swing.values())

    df_sorted_rsi = df.sort_values(by="RSI(2)").head(8)
    labels_bar = df_sorted_rsi["Ticker"].tolist()
    valores_bar = df_sorted_rsi["RSI(2)"].tolist()

    linhas_tabela = ""
    for _, row in df.iterrows():
        ticker = str(row.get("Ticker", "")).strip().upper()
        preco = float(row.get("Preço (R$)", 0.0))
        sma200 = float(row.get("SMA 200", 0.0))
        rsi_val = float(row.get("RSI(2)", 0.0))
        swing = row.get("Swing Trade", "-")
        pos_trade = row.get("Position Trade", "-")
        score = row.get("Score Fundamentalista", "N/D")

        badge_sw = formatar_badge_swing(swing)
        badge_sc = formatar_badge_score(score)
        cor_pos = "text-emerald-400 font-semibold" if "Alta" in str(pos_trade) else "text-slate-400"
        cor_rsi = "text-emerald-400 font-bold" if rsi_val <= 15 else ("text-rose-400 font-bold" if rsi_val >= 85 else "text-slate-200")

        nome_tom, estilo_btn, estilo_led = classificar_botao_tese(ticker, teses)
        btn_tese = f'''<button onclick="abrirModalTese('{ticker}')" style="{estilo_btn}" class="px-2.5 py-1 text-xs font-bold rounded-lg cursor-pointer transition-transform hover:scale-105 inline-flex items-center gap-1.5 shadow-sm">
            <span style="{estilo_led}" class="w-2 h-2 rounded-full inline-block"></span>
            Tese IA
        </button>'''

        linhas_tabela += f"""
        <tr class="hover:bg-slate-800/60 border-b border-slate-800 transition-colors">
            <td class="px-4 py-3 font-bold text-white tracking-wide">{ticker}</td>
            <td class="px-4 py-3 text-right font-medium text-slate-100">R$ {preco:.2f}</td>
            <td class="px-4 py-3 text-right text-slate-300">R$ {sma200:.2f}</td>
            <td class="px-4 py-3 text-right {cor_rsi}">{rsi_val:.1f}</td>
            <td class="px-4 py-3 text-center">{badge_sw}</td>
            <td class="px-4 py-3 text-center text-xs {cor_pos}">{pos_trade}</td>
            <td class="px-4 py-3 text-center">{badge_sc}</td>
            <td class="px-4 py-3 text-center">{btn_tese}</td>
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
        .gold-border {{ border-color: #c5a059; }}
        .gold-text {{ color: #d4af37; }}
    </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen flex flex-col">

    <!-- Header Dark Navy -->
    <header class="bg-slate-900 border-b-2 gold-border shadow-xl">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-4">
                <img src="logo.png" alt="WF Investimentos" class="w-14 h-14 rounded-full border border-amber-500/40 object-cover bg-slate-950" onerror="this.style.display='none'">
                <div>
                    <h1 class="text-xl sm:text-2xl font-black tracking-wider uppercase text-white flex items-center gap-2">
                        <span>WF INVESTIMENTOS</span>
                    </h1>
                    <p class="text-xs gold-text uppercase tracking-widest font-semibold">Avaliação Institucional & Scanner B3</p>
                </div>
            </div>
            <div class="text-right text-xs text-slate-300">
                <p><i class="fa-regular fa-clock mr-1 gold-text"></i> Atualizado em: <span class="font-bold text-white">{data_atualizacao}</span></p>
                <p class="text-slate-400">Universo: B3 IBrX 100 • Teses Qualitativas IA</p>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">

        <!-- Barra de Legenda do Termômetro IA -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs shadow-md">
            <span class="font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <i class="fa-solid fa-brain gold-text"></i> Termômetro das Teses IA (Semafórico):
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

        <!-- Gráficos -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-lg">
                <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-chart-pie gold-text"></i> Distribuição de Fases (Swing Trade)
                </h3>
                <div class="relative h-56">
                    <canvas id="chartDonut"></canvas>
                </div>
            </div>

            <div class="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-lg">
                <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-chart-bar gold-text"></i> Radar IFR(2) - Menores Níveis (Pullbacks)
                </h3>
                <div class="relative h-56">
                    <canvas id="chartBar"></canvas>
                </div>
            </div>
        </div>

        <!-- Tabela -->
        <div class="bg-slate-900 rounded-xl border border-slate-800 shadow-xl overflow-hidden">
            <div class="p-4 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-900/60">
                <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <i class="fa-solid fa-layer-group gold-text"></i> Scanner Consolidado IBrX 100
                </h2>
                <div class="relative w-full sm:w-72">
                    <input type="text" id="filtroTicker" placeholder="Pesquisar Ticker (ex: VALE3)..." class="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-950 border border-slate-700 text-white rounded-lg focus:outline-none focus:border-amber-400">
                    <i class="fa-solid fa-search absolute left-3 top-2.5 text-slate-500 text-xs"></i>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm" id="tabelaDados">
                    <thead class="bg-slate-950 text-slate-300 text-xs uppercase tracking-wider border-b border-slate-800">
                        <tr>
                            <th class="px-4 py-3">Ticker</th>
                            <th class="px-4 py-3 text-right">Preço</th>
                            <th class="px-4 py-3 text-right">SMA 200</th>
                            <th class="px-4 py-3 text-right">IFR(2)</th>
                            <th class="px-4 py-3 text-center">Swing Trade</th>
                            <th class="px-4 py-3 text-center">Position (Sem.)</th>
                            <th class="px-4 py-3 text-center">Score Fund.</th>
                            <th class="px-4 py-3 text-center">Parecer IA</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800 text-slate-200">
                        {linhas_tabela}
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <!-- Modal Dark Navy para Tese Institucional -->
    <div id="modalTese" class="fixed inset-0 bg-slate-950/85 backdrop-blur-sm hidden items-center justify-center p-4 z-50">
        <div class="bg-slate-900 border-2 gold-border rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                <div class="flex items-center gap-3">
                    <span class="w-3 h-3 rounded-full bg-amber-400 shadow-[0_0_8px_#f59e0b]"></span>
                    <h3 id="modalTitulo" class="text-lg font-black text-white tracking-wide uppercase">Tese Institucional</h3>
                </div>
                <button onclick="fecharModalTese()" class="text-slate-400 hover:text-white text-2xl font-bold cursor-pointer transition-colors">&times;</button>
            </div>
            
            <div id="modalCorpo" class="text-xs sm:text-sm text-slate-200 space-y-3 whitespace-pre-line leading-relaxed max-h-[65vh] overflow-y-auto pr-2">
            </div>

            <div class="border-t border-slate-800 pt-3 flex justify-between items-center text-xs text-slate-500">
                <span>WF Investimentos • Inteligência Gemini</span>
                <button onclick="fecharModalTese()" class="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg cursor-pointer transition-colors">Fechar</button>
            </div>
        </div>
    </div>

    <footer class="bg-slate-950 text-slate-400 py-4 text-center text-xs border-t border-slate-800">
        <p>© {datetime.now().year} WF Investimentos. Análise quantitativa e qualitativa automatizada para apoio decisório.</p>
    </footer>

    <script>
        const BANCO_TESES = {json.dumps(teses, ensure_ascii=False)};

        function abrirModalTese(ticker) {{
            const modal = document.getElementById('modalTese');
            const titulo = document.getElementById('modalTitulo');
            const corpo = document.getElementById('modalCorpo');

            titulo.innerText = 'PARECER INSTITUCIONAL #' + ticker;

            if (BANCO_TESES[ticker] && BANCO_TESES[ticker].parecer) {{
                corpo.innerText = BANCO_TESES[ticker].parecer;
            }} else {{
                corpo.innerText = 'Tese institucional em processamento pelo motor analítico da WF.';
            }}

            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }}

        function fecharModalTese() {{
            const modal = document.getElementById('modalTese');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }}

        window.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') fecharModalTese(); }});
        document.getElementById('modalTese').addEventListener('click', (e) => {{
            if (e.target.id === 'modalTese') fecharModalTese();
        }});

        document.getElementById('filtroTicker').addEventListener('keyup', function() {{
            let filter = this.value.toUpperCase();
            let rows = document.querySelectorAll('#tabelaDados tbody tr');
            rows.forEach(row => {{
                let ticker = row.cells[0].innerText;
                row.style.display = ticker.toUpperCase().includes(filter) ? '' : 'none';
            }});
        }});

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
    print(f"✅ Dashboard gerado com sucesso em '{ARQUIVO_HTML}'!")

if __name__ == "__main__":
    gerar_dashboard_html()
