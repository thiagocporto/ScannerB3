import pandas as pd
import datetime

def gerar_dashboard_html():
    try:
        df = pd.read_csv("scanner_fechamento.csv")
    except Exception:
        print("Arquivo scanner_fechamento.csv não encontrado!")
        return

    data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")

    # Linhas da tabela
    linhas = []
    for _, row in df.iterrows():
        # Destaque visual para gatilho conservador
        if "COMPRA" in str(row["Swing Trade"]):
            badge_swing = f'<span class="bg-emerald-100 text-emerald-800 font-bold px-2.5 py-0.5 rounded text-xs">{row["Swing Trade"]}</span>'
        elif "Alta" in str(row["Swing Trade"]):
            badge_swing = f'<span class="bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded text-xs">{row["Swing Trade"]}</span>'
        else:
            badge_swing = f'<span class="bg-gray-100 text-gray-700 px-2.5 py-0.5 rounded text-xs">{row["Swing Trade"]}</span>'

        # Badge Fundamentalista
        score_fund = row.get("Score_Fund", 0)
        if score_fund >= 70:
            badge_fund = f'<span class="bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded text-xs">{score_fund}/100</span>'
        elif score_fund >= 45:
            badge_fund = f'<span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-xs">{score_fund}/100</span>'
        else:
            badge_fund = f'<span class="bg-rose-100 text-rose-800 px-2 py-0.5 rounded text-xs">{score_fund}/100</span>'

        linhas.append(f"""
        <tr>
            <td class="font-bold text-gray-900 px-4 py-3">{row['Ticker']}</td>
            <td class="px-4 py-3 text-right">R$ {row['Preço (R$)']:.2f}</td>
            <td class="px-4 py-3 text-center font-mono">{row['RSI(2)']}</td>
            <td class="px-4 py-3 text-center">{badge_swing}</td>
            <td class="px-4 py-3 text-center text-xs">{row['Position Trade']}</td>
            <td class="px-4 py-3 text-center">{badge_fund}</td>
            <td class="px-4 py-3 text-right font-mono">{row['P/L']}</td>
            <td class="px-4 py-3 text-right font-mono">{row['DY (%)']}%</td>
            <td class="px-4 py-3 text-right font-mono">{row['ROE (%)']}%</td>
        </tr>
        """)

    tabela_linhas_str = "\n".join(linhas)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scanner B3 | IBrX 100</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <style>
        .dataTables_wrapper .dataTables_filter input {{
            border: 1px solid #d1d5db;
            border-radius: 0.375rem;
            padding: 0.25rem 0.5rem;
            margin-bottom: 0.75rem;
        }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 font-sans antialiased min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-extrabold text-slate-900 tracking-tight">Scanner B3 — IBrX 100</h1>
            <p class="text-sm text-slate-500 mt-1">Análise Quantitativa Multi-Horizonte (Swing Trade, Position Trade & Fundamentos)</p>
            <p class="text-xs text-slate-400 mt-0.5">Última atualização: {data_atual}</p>
        </header>

        <main class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 overflow-x-auto">
            <table id="tabelaScanner" class="w-full text-sm text-left">
                <thead class="text-xs uppercase bg-slate-100 text-slate-600">
                    <tr>
                        <th class="px-4 py-3">Ticker</th>
                        <th class="px-4 py-3 text-right">Preço</th>
                        <th class="px-4 py-3 text-center">IFR(2)</th>
                        <th class="px-4 py-3 text-center">Swing Trade</th>
                        <th class="px-4 py-3 text-center">Position Trade</th>
                        <th class="px-4 py-3 text-center">Score Fund.</th>
                        <th class="px-4 py-3 text-right">P/L</th>
                        <th class="px-4 py-3 text-right">DY (%)</th>
                        <th class="px-4 py-3 text-right">ROE (%)</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    {tabela_linhas_str}
                </tbody>
            </table>
        </main>
    </div>

    <script>
        $(document).ready(function() {{
            $('#tabelaScanner').DataTable({{
                pageLength: 25,
                language: {{
                    url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/pt-BR.json'
                }},
                order: [[5, 'desc']] // Inicia ordenado pelo Score Fundamentalista
            }});
        }});
    </script>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Site estático gerado com sucesso em 'index.html'!")

if __name__ == "__main__":
    gerar_dashboard_html()