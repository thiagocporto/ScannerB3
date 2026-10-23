import json
import re
from datetime import datetime
import pandas as pd


def formatar_badge_swing(valor):
  v = str(valor).lower()
  if "🔥 compra" in v:
    return (
        '<span class="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-500'
        f' text-white shadow-sm">{valor}</span>'
    )
  elif "pullback em alta" in v or "atenção" in v:
    return (
        '<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100'
        f' text-amber-800 border border-amber-300">{valor}</span>'
    )
  elif "alta forte" in v:
    return (
        '<span class="px-2 py-0.5 text-xs font-medium rounded-full'
        ' bg-emerald-100 text-emerald-800 border'
        f' border-emerald-300">{valor}</span>'
    )
  elif "sobrecomprado" in v:
    return (
        '<span class="px-2 py-0.5 text-xs font-medium rounded-full'
        ' bg-purple-100 text-purple-800 border'
        f' border-purple-300">{valor}</span>'
    )
  elif "baixa" in v:
    return (
        '<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-rose-100'
        f' text-rose-800 border border-rose-300">{valor}</span>'
    )
  else:
    return (
        '<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-100'
        f' text-slate-600 border border-slate-300">{valor}</span>'
    )


def formatar_badge_score(score_raw):
  score_str = str(score_raw)
  if "Excelente" in score_str or "Bom" in score_str:
    return (
        '<span class="px-2.5 py-1 text-xs font-bold rounded bg-emerald-50'
        f' text-emerald-700 border border-emerald-300">{score_str}</span>'
    )
  elif "Regular" in score_str:
    return (
        '<span class="px-2.5 py-1 text-xs font-semibold rounded bg-amber-50'
        f' text-amber-700 border border-amber-300">{score_str}</span>'
    )
  elif "Fraco" in score_str:
    return (
        '<span class="px-2.5 py-1 text-xs font-medium rounded bg-rose-50'
        f' text-rose-700 border border-rose-300">{score_str}</span>'
    )
  else:
    return (
        f'<span class="text-xs text-slate-400 font-medium">{score_str}</span>'
    )


def extrair_valor_score(score_raw):
  """Extrai o número de 0 a 100 para ordenação matemática correta."""
  score_str = str(score_raw)
  m = re.search(r"\d+", score_str)
  return int(m.group()) if m else -1


def gerar_dashboard_html(
    caminho_csv="scanner_fechamento.csv", caminho_saida="index.html"
):
  df = pd.read_csv(caminho_csv)
  data_atualizacao = datetime.now().strftime("%d/%m/%Y às %H:%M")

  # 1. Gráficos Chart.js
  distribuicao_swing = df["Swing Trade"].value_counts().to_dict()
  labels_chart_donut = list(distribuicao_swing.keys())
  valores_chart_donut = list(distribuicao_swing.values())

  df_sorted_rsi = df.sort_values(by="RSI(2)").head(8)
  labels_chart_bar = df_sorted_rsi["Ticker"].tolist()
  valores_chart_bar = df_sorted_rsi["RSI(2)"].tolist()

  # 2. Montagem das Linhas com data-val para ordenação nativa
  linhas_tabela = ""
  for _, row in df.iterrows():
    ticker = str(row.get("Ticker", "-"))
    preco = float(row.get("Preço (R$)", 0.0))
    sma200 = float(row.get("SMA 200", 0.0))
    rsi_val = float(row.get("RSI(2)", 0.0))
    swing_val = str(row.get("Swing Trade", "-"))
    pos_trade = str(row.get("Position Trade", "-"))
    score_raw = str(row.get("Score Fundamentalista", "N/D"))
    score_num = extrair_valor_score(score_raw)

    badge_swing = formatar_badge_swing(swing_val)
    badge_score = formatar_badge_score(score_raw)

    badge_position = (
        "text-emerald-600 font-semibold"
        if "Alta" in pos_trade
        else "text-slate-500"
    )
    cor_rsi = (
        "text-emerald-700 font-bold"
        if rsi_val <= 15
        else ("text-rose-700 font-bold" if rsi_val >= 85 else "text-slate-700")
    )

    linhas_tabela += f"""
        <tr class="hover:bg-slate-50 border-b border-slate-200 transition-colors">
            <td class="px-4 py-3 font-bold text-slate-900" data-val="{ticker}">{ticker}</td>
            <td class="px-4 py-3 text-right text-slate-800 font-medium" data-val="{preco}">R$ {preco:.2f}</td>
            <td class="px-4 py-3 text-right text-slate-600" data-val="{sma200}">R$ {sma200:.2f}</td>
            <td class="px-4 py-3 text-right {cor_rsi}" data-val="{rsi_val}">{rsi_val:.1f}</td>
            <td class="px-4 py-3 text-center" data-val="{swing_val}">{badge_swing}</td>
            <td class="px-4 py-3 text-center text-xs {badge_position}" data-val="{pos_trade}">{pos_trade}</td>
            <td class="px-4 py-3 text-center" data-val="{score_num}">{badge_score}</td>
        </tr>
        """

  html_template = f"""<!DOCTYPE html>
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
        th.sortable {{ cursor: pointer; user-select: none; transition: background-color 0.2s; }}
        th.sortable:hover {{ background-color: #1e293b; color: #d4af37; }}
    </style>
</head>
<body class="bg-slate-100 text-slate-800 font-sans min-h-screen flex flex-col">

    <!-- Top Header WF Investimentos -->
    <header class="gold-gradient text-white border-b-4 gold-border shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-4">
                <img src="logo.png" alt="WF Investimentos" class="w-16 h-16 rounded-full border-2 gold-border shadow-md object-cover bg-slate-900" onerror="this.style.display='none'">
                <div>
                    <h1 class="text-2xl font-black tracking-wider uppercase flex items-center gap-2">
                        <span>WF INVESTIMENTOS</span>
                    </h1>
                    <p class="text-xs gold-text uppercase tracking-widest font-semibold">Avaliação de Ativos & Mercado</p>
                </div>
            </div>
            <div class="text-right text-xs text-slate-300">
                <p><i class="fa-regular fa-clock mr-1"></i> Atualizado em: <span class="font-bold text-white">{data_atualizacao}</span></p>
                <p class="text-slate-400">Universo: B3 IBrX 100</p>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">

        <!-- Gráficos -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
                <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-chart-pie gold-text"></i> Distribuição de Tendências (Swing Trade)
                </h3>
                <div class="relative h-56">
                    <canvas id="chartDonut"></canvas>
                </div>
            </div>

            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
                <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-chart-bar gold-text"></i> Radar IFR(2) - Menores Níveis (Pullbacks)
                </h3>
                <div class="relative h-56">
                    <canvas id="chartBar"></canvas>
                </div>
            </div>
        </div>

        <!-- Tabela com Ordenação Dinâmica -->
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="p-4 border-b border-slate-200 flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-50">
                <div>
                    <h2 class="text-base font-bold text-slate-800">Scanner Consolidado de Ativos</h2>
                    <p class="text-xs text-slate-500">Clique no cabeçalho das colunas para ordenar</p>
                </div>
                <div class="relative w-full sm:w-72">
                    <input type="text" id="filtroTicker" placeholder="Pesquisar Ticker (ex: VALE3)..." class="w-full pl-9 pr-4 py-1.5 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500">
                    <i class="fa-solid fa-search absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm" id="tabelaDados">
                    <thead class="bg-slate-900 text-white text-xs uppercase tracking-wider">
                        <tr>
                            <th class="px-4 py-3 sortable" onclick="ordenarTabela(0, 'str')">Ticker <i class="fa-solid fa-sort ml-1 text-slate-400"></i></th>
                            <th class="px-4 py-3 text-right sortable" onclick="ordenarTabela(1, 'num')">Preço <i class="fa-solid fa-sort ml-1 text-slate-400"></i></th>
                            <th class="px-4 py-3 text-right sortable" onclick="ordenarTabela(2, 'num')">SMA 200 <i class="fa-solid fa-sort ml-1 text-slate-400"></i></th>
                            <th class="px-4 py-3 text-right sortable" onclick="ordenarTabela(3, 'num')">IFR(2) <i class="fa-solid fa-sort ml-1 text-slate-400"></i></th>
                            <th class="px-4 py-3 text-center sortable" onclick="ordenarTabela(4, 'str')">Swing Trade <i class="fa-solid fa-sort ml-1 text-slate-400"></i></th>
                            <th class="px-4 py-3 text-center sortable" onclick="ordenarTabela(5, 'str')">Position (Semanal) <i class="fa-solid fa-sort ml-1 text-slate-400"></i></th>
                            <th class="px-4 py-3 text-center sortable" onclick="ordenarTabela(6, 'num')">Score Fund. <i class="fa-solid fa-sort ml-1 text-slate-400"></i></th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        {linhas_tabela}
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <footer class="bg-slate-900 text-slate-400 py-4 text-center text-xs border-t gold-border">
        <p>© {datetime.now().year} WF Investimentos. Análise quantitativa automatizada para apoio decisório.</p>
    </footer>

    <script>
        // Filtro em tempo real de Ticker
        document.getElementById('filtroTicker').addEventListener('keyup', function() {{
            let filter = this.value.toUpperCase();
            let rows = document.querySelectorAll('#tabelaDados tbody tr');
            rows.forEach(row => {{
                let ticker = row.cells[0].innerText;
                row.style.display = ticker.toUpperCase().includes(filter) ? '' : 'none';
            }});
        }});

        // Gráfico Donut
        new Chart(document.getElementById('chartDonut'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(labels_chart_donut)},
                datasets: [{{
                    data: {json.dumps(valores_chart_donut)},
                    backgroundColor: ['#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#64748b', '#3b82f6', '#ec4899'],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{ boxWidth: 12, font: {{ size: 10 }} }}
                    }}
                }}
            }}
        }});

        // Gráfico IFR(2)
        new Chart(document.getElementById('chartBar'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(labels_chart_bar)},
                datasets: [{{
                    label: 'IFR(2)',
                    data: {json.dumps(valores_chart_bar)},
                    backgroundColor: '#d4af37',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, max: 100, grid: {{ color: '#f1f5f9' }} }},
                    x: {{ grid: {{ display: false }} }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});

        // Motor de Ordenação Dinâmica
        let direcaoOrdenacao = {{}};
        function ordenarTabela(colIndex, tipo) {{
            const tabela = document.getElementById('tabelaDados');
            const tbody = tabela.querySelector('tbody');
            const linhas = Array.from(tbody.querySelectorAll('tr'));
            
            // Alterna ascendente e descendente
            const ascendente = !direcaoOrdenacao[colIndex];
            direcaoOrdenacao = {{}}; // reseta outros
            direcaoOrdenacao[colIndex] = ascendente;

            linhas.sort((a, b) => {{
                let valA = a.cells[colIndex].getAttribute('data-val') || a.cells[colIndex].innerText.trim();
                let valB = b.cells[colIndex].getAttribute('data-val') || b.cells[colIndex].innerText.trim();

                if (tipo === 'num') {{
                    valA = parseFloat(valA) || 0;
                    valB = parseFloat(valB) || 0;
                    return ascendente ? valA - valB : valB - valA;
                }} else {{
                    return ascendente ? valA.localeCompare(valB) : valB.localeCompare(valA);
                }}
            }});

            // Atualiza ícones dos cabeçalhos
            const headers = tabela.querySelectorAll('th i');
            headers.forEach(i => i.className = 'fa-solid fa-sort ml-1 text-slate-400');
            const iconeAtivo = tabela.querySelectorAll('th')[colIndex].querySelector('i');
            iconeAtivo.className = ascendente ? 'fa-solid fa-sort-up ml-1 text-amber-400' : 'fa-solid fa-sort-down ml-1 text-amber-400';

            linhas.forEach(linha => tbody.appendChild(linha));
        }}
    </script>
</body>
</html>
"""
  with open(caminho_saida, "w", encoding="utf-8") as f:
    f.write(html_template)
  print(f"Dashboard interativo com ordenação gerado com sucesso em '{caminho_saida}'.")


if __name__ == "__main__":
  gerar_dashboard_html()