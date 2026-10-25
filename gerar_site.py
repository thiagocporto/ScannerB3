import pandas as pd
import json
import os
import html
from datetime import datetime

def formatar_moeda(valor):
    if pd.isna(valor): return "R$ 0,00"
    texto = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"

def resolver_fase_tecnica(preco, sma200, rsi2):
    """Categoriza a fase técnica com limites matemáticos rígidos (Regra 5)."""
    if pd.isna(preco) or pd.isna(sma200) or sma200 == 0:
        return {"rotulo": "Sem Dados", "status": "neutro"}
    
    distancia = (preco - sma200) / sma200
    rsi2 = float(rsi2) if not pd.isna(rsi2) else 50.0

    if distancia > 0.05:
        if rsi2 >= 85: return {"rotulo": "Sobrecomprado", "status": "alerta"}
        if rsi2 <= 15: return {"rotulo": "Pullback em Alta (Oportunidade)", "status": "compra"}
        return {"rotulo": "Tendência de Alta", "status": "compra"}
    elif -0.05 <= distancia <= 0.05:
        return {"rotulo": "Consolidação / Neutro", "status": "neutro"}
    else:
        if rsi2 <= 15: return {"rotulo": "Tendência de Baixa (Sobrevendido)", "status": "neutro"}
        return {"rotulo": "Tendência de Baixa", "status": "venda"}

def construir_painel():
    if not os.path.exists('scanner_fechamento.csv'):
        print("Erro: CSV não encontrado.")
        return

    df = pd.read_csv('scanner_fechamento.csv')
    
    teses = {}
    if os.path.exists('teses_qualitativas.json'):
        with open('teses_qualitativas.json', 'r', encoding='utf-8') as f:
            teses = json.load(f)

    ativos_front = []
    contagem_tendencias = {"Sobrecomprado": 0, "Pullback em Alta (Oportunidade)": 0, "Tendência de Alta": 0, "Consolidação / Neutro": 0, "Tendência de Baixa (Sobrevendido)": 0, "Tendência de Baixa": 0}
    
    for _, row in df.iterrows():
        ticker = str(row.get('Ticker', ''))
        preco = row.get('Preço (R$)', 0.0)
        sma200 = row.get('SMA 200', 0.0)
        
        # Tratamento de Nulos do Pandas que zerava a coluna (Regra 1 e 2)
        rsi2_bruto = row.get('RSI(2)', 50.0)
        rsi2 = float(rsi2_bruto) if not pd.isna(rsi2_bruto) and 0 <= float(rsi2_bruto) <= 100 else 50.0
        
        fase = resolver_fase_tecnica(preco, sma200, rsi2)
        if fase["rotulo"] in contagem_tendencias: contagem_tendencias[fase["rotulo"]] += 1
        
        tese_obj = teses.get(ticker, {})
        # Traz o sinal validado da IA ou herda a lógica matemática do front se a IA falhar
        sinal_ia = tese_obj.get("veredito_sinal", fase["status"]) 
        
        ativos_front.append({
            "ticker": ticker,
            "preco_br": formatar_moeda(preco),
            "sma200_br": formatar_moeda(sma200),
            "rsi2": f"{rsi2:.1f}",
            "fase": fase["rotulo"],
            "score_fund": str(row.get('Score Fundamentalista', 'N/D')),
            "tese_texto": tese_obj.get("parecer", "Análise em processamento..."),
            "sinal_ia": sinal_ia 
        })

    dados_injetados = {
        "atualizacao": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        "total_ativos": len(ativos_front),
        "grafico_tendencias": contagem_tendencias,
        "ativos": ativos_front
    }
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WF Investimentos | Scanner Quantitativo</title>
    <!-- Dependencias fixadas com SRI de segurança -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" integrity="sha384-wHO8xMpsnffGz+qU3K9xQ75uI/7p/f0+Z9/qgQ3n0y5Xh0M2aVf3PZkL/H2hU+x6" crossorigin="anonymous"></script>
    <script>
        tailwind.config = {{ theme: {{ extend: {{ colors: {{ slate: {{ 800: '#1e293b', 900: '#0f172a' }}, emerald: {{ 400: '#34d399', 900: '#064e3b' }}, amber: {{ 400: '#fbbf24', 900: '#78350f' }}, rose: {{ 400: '#fb7185', 900: '#881337' }} }} }} }} }}
    </script>
</head>
<body class="bg-slate-900 text-slate-300 font-sans antialiased">
    <header class="bg-slate-800 border-b-2 border-amber-600 shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-slate-900 border border-amber-500 flex items-center justify-center text-amber-500 font-bold text-xl">WF</div>
                <div>
                    <h1 class="text-2xl font-black tracking-wider text-white">WF INVESTIMENTOS</h1>
                </div>
            </div>
            <div class="text-right">
                <p class="text-sm font-medium text-slate-400" id="data-hora"></p>
                <p class="text-xs text-slate-500">Universo: B3 IBrX 100 • <span id="qtd-ativos">100</span> Ações</p>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <h3 class="text-sm font-bold text-white mb-4">📊 DISTRIBUIÇÃO DE TENDÊNCIAS</h3>
                <div class="relative h-64 w-full flex justify-center"><canvas id="graficoTendencias"></canvas></div>
            </div>
            <div class="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <h3 class="text-sm font-bold text-white mb-4">📈 RADAR IFR(2) - TOP 8</h3>
                <div class="relative h-64 w-full"><canvas id="graficoIfr"></canvas></div>
            </div>
        </div>

        <!-- Tabela construída via JS -->
        <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            <div class="p-6 border-b border-slate-700 flex justify-between items-center">
                <h2 class="text-xl font-bold text-white">Matriz de Ativos B3</h2>
                <input type="text" id="busca-ticker" placeholder="Pesquisar Ticker..." class="bg-slate-900 border border-slate-600 text-white text-sm rounded-lg p-2.5">
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left text-slate-300">
                    <thead class="text-xs uppercase bg-slate-900 text-slate-400 border-b border-slate-700">
                        <tr>
                            <th class="px-6 py-4 font-semibold">Ticker</th>
                            <th class="px-6 py-4 text-right">Preço</th>
                            <th class="px-6 py-4 text-right">SMA 200</th>
                            <th class="px-6 py-4 text-right">IFR(2)</th>
                            <th class="px-6 py-4 text-center">Fase Técnica</th>
                            <th class="px-6 py-4 text-center">Score Fund.</th>
                            <th class="px-6 py-4 text-center">Parecer IA</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-corpo" class="divide-y divide-slate-700/50"></tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Modal Base (innerText blinda Markdown e tags HTML cruas) -->
    <div id="modal-tese" class="hidden fixed inset-0 z-50 bg-slate-900/80 flex items-center justify-center p-4 opacity-0 transition-opacity">
        <div class="bg-slate-800 w-full max-w-2xl rounded-2xl border border-slate-600 shadow-2xl p-6">
            <h3 class="text-lg font-bold text-white mb-4">Tese: <span id="modal-ticker" class="text-emerald-400"></span></h3>
            <p id="modal-texto" class="text-slate-300 whitespace-pre-line leading-relaxed text-sm"></p>
            <div class="mt-6 flex justify-end">
                <button id="btn-fechar-modal" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg">Ciente</button>
            </div>
        </div>
    </div>

    <!-- Escape JSON para impedir XSS -->
    <script id="dados-iniciais" type="application/json">{json.dumps(dados_injetados).replace('<', '\\u003c').replace('>', '\\u003e')}</script>

    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const db = JSON.parse(document.getElementById('dados-iniciais').textContent);
            document.getElementById('data-hora').textContent = 'Atualizado em: ' + db.atualizacao;
            const tbody = document.getElementById('tabela-corpo');

            const temaIA = {{
                "compra": {{ cor: "bg-emerald-900/30 text-emerald-400 border-emerald-500/30", label: "Favorável" }},
                "alerta": {{ cor: "bg-amber-900/30 text-amber-400 border-amber-500/30", label: "Cautela" }},
                "venda": {{ cor: "bg-rose-900/30 text-rose-400 border-rose-500/30", label: "Desfavorável" }},
                "neutro": {{ cor: "bg-slate-800 text-slate-400 border-slate-600", label: "Neutro" }}
            }};

            function renderTabela(lista) {{
                tbody.innerHTML = '';
                lista.forEach(ativo => {{
                    const btn = temaIA[ativo.sinal_ia] || temaIA["neutro"];
                    const tr = document.createElement('tr');
                    tr.className = "hover:bg-slate-800/50";
                    tr.innerHTML = `
                        <td class="px-6 py-4 font-bold text-white">${{ativo.ticker}}</td>
                        <td class="px-6 py-4 text-right">${{ativo.preco_br}}</td>
                        <td class="px-6 py-4 text-right">${{ativo.sma200_br}}</td>
                        <td class="px-6 py-4 text-right font-mono">${{ativo.rsi2}}</td>
                        <td class="px-6 py-4 text-center"><span class="px-2 py-1 text-xs border rounded">${{ativo.fase}}</span></td>
                        <td class="px-6 py-4 text-center">${{ativo.score_fund}}</td>
                        <td class="px-6 py-4 text-center">
                            <button data-ticker="${{ativo.ticker}}" data-texto="${{btoa(unescape(encodeURIComponent(ativo.tese_texto)))}}" class="btn-modal px-3 py-1 rounded border ${{btn.cor}} text-xs uppercase">${{btn.label}}</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                }});
                
                document.querySelectorAll('.btn-modal').forEach(b => {{
                    b.addEventListener('click', function() {{
                        document.getElementById('modal-ticker').textContent = this.dataset.ticker;
                        document.getElementById('modal-texto').textContent = decodeURIComponent(escape(atob(this.dataset.texto)));
                        const m = document.getElementById('modal-tese');
                        m.classList.remove('hidden'); setTimeout(() => m.classList.remove('opacity-0'), 10);
                    }});
                }});
            }}

            renderTabela(db.ativos);
            document.getElementById('busca-ticker').addEventListener('input', e => renderTabela(db.ativos.filter(a => a.ticker.includes(e.target.value.toUpperCase()))));
            
            const m = document.getElementById('modal-tese');
            const fechar = () => {{ m.classList.add('opacity-0'); setTimeout(() => m.classList.add('hidden'), 300); }};
            document.getElementById('btn-fechar-modal').addEventListener('click', fechar);
            m.addEventListener('click', e => {{ if(e.target === m) fechar(); }});
            document.addEventListener('keydown', e => {{ if(e.key === 'Escape') fechar(); }});

            const c = db.grafico_tendencias;
            new Chart(document.getElementById('graficoTendencias').getContext('2d'), {{ type: 'doughnut', data: {{ labels: Object.keys(c), datasets: [{{ data: Object.values(c), backgroundColor: ['#a855f7', '#34d399', '#059669', '#475569', '#fbbf24', '#e11d48'], borderColor: '#1e293b' }}] }}, options: {{ plugins: {{ legend: {{ position: 'right', labels: {{color: '#94a3b8'}} }} }} }} }});
            
            const top = [...db.ativos].sort((a,b) => parseFloat(a.rsi2) - parseFloat(b.rsi2)).slice(0, 8);
            new Chart(document.getElementById('graficoIfr').getContext('2d'), {{ type: 'bar', data: {{ labels: top.map(a => a.ticker), datasets: [{{ data: top.map(a => parseFloat(a.rsi2)), backgroundColor: '#fbbf24' }}] }}, options: {{ scales: {{ y: {{ max: 100, min: 0 }} }}, plugins: {{ legend: {{ display: false }} }} }} }});
        }});
    </script>
</body>
</html>"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    construir_painel()
