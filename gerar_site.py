import pandas as pd
import json
import os
from datetime import datetime

def formatar_moeda(valor):
    if pd.isna(valor): return "R$ 0,00"
    texto = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"

def resolver_fase_tecnica(preco, sma200, rsi2):
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
    contagem_tendencias = {
        "Sobrecomprado": 0,
        "Pullback em Alta (Oportunidade)": 0,
        "Tendência de Alta": 0,
        "Consolidação / Neutro": 0,
        "Tendência de Baixa (Sobrevendido)": 0,
        "Tendência de Baixa": 0
    }
    
    for _, row in df.iterrows():
        ticker = str(row.get('Ticker', '')).strip().upper()
        if not ticker or ticker == "NAN": continue
        
        preco = row.get('Preço (R$)', 0.0)
        sma200 = row.get('SMA 200', 0.0)
        
        rsi2_bruto = row.get('RSI(2)', 50.0)
        rsi2 = float(rsi2_bruto) if not pd.isna(rsi2_bruto) and 0 <= float(rsi2_bruto) <= 100 else 50.0
        
        fase = resolver_fase_tecnica(preco, sma200, rsi2)
        if fase["rotulo"] in contagem_tendencias:
            contagem_tendencias[fase["rotulo"]] += 1
        
        tese_obj = teses.get(ticker, {})
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
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js oficial estavel via CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        slate: {{ 800: '#1e293b', 900: '#0f172a' }},
                        emerald: {{ 400: '#34d399', 900: '#064e3b' }},
                        amber: {{ 400: '#fbbf24', 900: '#78350f' }},
                        rose: {{ 400: '#fb7185', 900: '#881337' }}
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="bg-slate-900 text-slate-300 font-sans antialiased min-h-screen flex flex-col">
    <!-- Header Oficial WF -->
    <header class="bg-slate-800 border-b-2 border-amber-500 shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-slate-900 border border-amber-500 flex items-center justify-center text-amber-500 font-bold text-xl shadow-[0_0_10px_rgba(245,158,11,0.2)]">WF</div>
                <div>
                    <h1 class="text-2xl font-black tracking-wider text-white">WF INVESTIMENTOS</h1>
                    <p class="text-xs text-amber-400 font-semibold tracking-widest uppercase">Avaliação Institucional & Scanner B3</p>
                </div>
            </div>
            <div class="text-right">
                <p class="text-sm font-medium text-slate-300" id="data-hora"></p>
                <p class="text-xs text-slate-500">Universo: B3 IBrX 100 • <span id="qtd-ativos">100</span> Ações</p>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8 flex-1 w-full space-y-8">
        <!-- Cards Analíticos do Topo -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
                <h3 class="text-sm font-bold text-white mb-4 flex items-center gap-2">
                    <span class="text-amber-500">📊</span> DISTRIBUIÇÃO DE TENDÊNCIAS
                </h3>
                <div class="relative h-64 w-full flex justify-center items-center">
                    <canvas id="graficoTendencias"></canvas>
                </div>
            </div>
            <div class="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
                <h3 class="text-sm font-bold text-white mb-4 flex items-center gap-2">
                    <span class="text-amber-500">📈</span> RADAR IFR(2) - TOP 8 MENORES
                </h3>
                <div class="relative h-64 w-full">
                    <canvas id="graficoIfr"></canvas>
                </div>
            </div>
        </div>

        <!-- Tabela Consolidada -->
        <div class="bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden">
            <div class="p-6 border-b border-slate-700 flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-800/60">
                <h2 class="text-xl font-bold text-white">Matriz de Ativos B3</h2>
                <input type="text" id="busca-ticker" placeholder="Pesquisar Ticker (ex: VALE3)..." class="bg-slate-900 border border-slate-600 text-white text-sm rounded-lg p-2.5 w-full sm:w-72 focus:outline-none focus:border-amber-500">
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left text-slate-300">
                    <thead class="text-xs uppercase bg-slate-900 text-slate-400 border-b border-slate-700">
                        <tr>
                            <th class="px-6 py-4 font-semibold">Ticker</th>
                            <th class="px-6 py-4 text-right font-semibold">Preço</th>
                            <th class="px-6 py-4 text-right font-semibold">SMA 200</th>
                            <th class="px-6 py-4 text-right font-semibold">IFR(2)</th>
                            <th class="px-6 py-4 text-center font-semibold">Fase Técnica</th>
                            <th class="px-6 py-4 text-center font-semibold">Score Fund.</th>
                            <th class="px-6 py-4 text-center font-semibold">Parecer IA</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-corpo" class="divide-y divide-slate-700/50"></tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Modal Institucional -->
    <div id="modal-tese" class="hidden fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center p-4 opacity-0 transition-opacity duration-200">
        <div class="bg-slate-800 w-full max-w-2xl rounded-2xl border border-slate-600 shadow-2xl overflow-hidden transform scale-95 transition-transform duration-200" id="modal-content">
            <div class="bg-slate-900 px-6 py-4 border-b border-slate-700 flex justify-between items-center">
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                    <span class="text-amber-500">📊</span> Tese Institucional: <span id="modal-ticker" class="text-emerald-400"></span>
                </h3>
                <button id="btn-fechar-modal-x" class="text-slate-400 hover:text-white transition-colors text-xl font-bold">&times;</button>
            </div>
            <div class="p-6">
                <p id="modal-texto" class="text-slate-200 whitespace-pre-line leading-relaxed text-sm"></p>
            </div>
            <div class="bg-slate-900/50 px-6 py-4 border-t border-slate-700 flex justify-end">
                <button id="btn-fechar-modal" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors">Fechar</button>
            </div>
        </div>
    </div>

    <!-- Script de Dados Embutido -->
    <script id="dados-iniciais" type="application/json">{json.dumps(dados_injetados).replace('<', '\\u003c').replace('>', '\\u003e')}</script>

    <!-- Lógica de Renderização e Gráficos -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const raw = document.getElementById('dados-iniciais').textContent;
            const db = JSON.parse(raw);
            
            document.getElementById('data-hora').textContent = 'Atualizado em: ' + db.atualizacao;
            document.getElementById('qtd-ativos').textContent = db.total_ativos;
            
            const tbody = document.getElementById('tabela-corpo');

            const temaIA = {{
                "compra": {{ cor: "bg-emerald-900/40 text-emerald-400 border-emerald-500/40 hover:bg-emerald-800/50", led: "bg-emerald-400", label: "Favorável" }},
                "alerta": {{ cor: "bg-amber-900/40 text-amber-400 border-amber-500/40 hover:bg-amber-800/50", led: "bg-amber-400", label: "Cautela" }},
                "venda": {{ cor: "bg-rose-900/40 text-rose-400 border-rose-500/40 hover:bg-rose-800/50", led: "bg-rose-400", label: "Desfavorável" }},
                "neutro": {{ cor: "bg-slate-800 text-slate-400 border-slate-600 hover:bg-slate-700", led: "bg-slate-500", label: "Neutro" }}
            }};

            function renderTabela(lista) {{
                tbody.innerHTML = '';
                lista.forEach(ativo => {{
                    const btn = temaIA[ativo.sinal_ia] || temaIA["neutro"];
                    const tr = document.createElement('tr');
                    tr.className = "hover:bg-slate-800/60 transition-colors";
                    tr.innerHTML = `
                        <td class="px-6 py-4 font-bold text-white">${{ativo.ticker}}</td>
                        <td class="px-6 py-4 text-right font-medium text-slate-200">${{ativo.preco_br}}</td>
                        <td class="px-6 py-4 text-right text-slate-400">${{ativo.sma200_br}}</td>
                        <td class="px-6 py-4 text-right font-mono text-slate-300">${{ativo.rsi2}}</td>
                        <td class="px-6 py-4 text-center">
                            <span class="px-2.5 py-1 text-xs border border-slate-600 rounded bg-slate-900/80 text-slate-300">${{ativo.fase}}</span>
                        </td>
                        <td class="px-6 py-4 text-center text-slate-300 font-medium">${{ativo.score_fund}}</td>
                        <td class="px-6 py-4 text-center">
                            <button data-ticker="${{ativo.ticker}}" data-texto="${{btoa(unescape(encodeURIComponent(ativo.tese_texto)))}}" class="btn-modal px-3 py-1 rounded-lg border ${{btn.cor}} text-xs font-semibold uppercase tracking-wider inline-flex items-center gap-2 transition-all">
                                <span class="w-2 h-2 rounded-full ${{btn.led}}"></span>
                                ${{btn.label}}
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                }});
                
                document.querySelectorAll('.btn-modal').forEach(b => {{
                    b.addEventListener('click', function() {{
                        const ticker = this.dataset.ticker;
                        const texto = decodeURIComponent(escape(atob(this.dataset.texto)));
                        abrirModal(ticker, texto);
                    }});
                }});
            }}

            renderTabela(db.ativos);

            // Filtro em tempo real
            document.getElementById('busca-ticker').addEventListener('input', e => {{
                const val = e.target.value.toUpperCase();
                renderTabela(db.ativos.filter(a => a.ticker.includes(val)));
            }});

            // Controle do Modal
            const modal = document.getElementById('modal-tese');
            const modalBox = document.getElementById('modal-content');
            
            function abrirModal(ticker, texto) {{
                document.getElementById('modal-ticker').textContent = ticker;
                document.getElementById('modal-texto').textContent = texto;
                modal.classList.remove('hidden');
                setTimeout(() => {{
                    modal.classList.remove('opacity-0');
                    modalBox.classList.remove('scale-95');
                }}, 10);
            }}

            function fecharModal() {{
                modal.classList.add('opacity-0');
                modalBox.classList.add('scale-95');
                setTimeout(() => modal.classList.add('hidden'), 200);
            }}

            document.getElementById('btn-fechar-modal').addEventListener('click', fecharModal);
            document.getElementById('btn-fechar-modal-x').addEventListener('click', fecharModal);
            modal.addEventListener('click', e => {{ if(e.target === modal) fecharModal(); }});
            document.addEventListener('keydown', e => {{ if(e.key === 'Escape') fecharModal(); }});

            // 1. Gráfico de Rosca (Distribuição de Tendências)
            const c = db.grafico_tendencias;
            const ctxDonut = document.getElementById('graficoTendencias').getContext('2d');
            new Chart(ctxDonut, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(c),
                    datasets: [{{
                        data: Object.values(c),
                        backgroundColor: ['#a855f7', '#34d399', '#059669', '#64748b', '#fbbf24', '#f43f5e'],
                        borderColor: '#1e293b',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'right',
                            labels: {{ color: '#cbd5e1', font: {{ size: 11 }} }}
                        }}
                    }}
                }}
            }});

            // 2. Gráfico de Barras (Top 8 Menores IFR)
            const topSobrevendidos = [...db.ativos]
                .filter(a => !isNaN(parseFloat(a.rsi2)))
                .sort((a,b) => parseFloat(a.rsi2) - parseFloat(b.rsi2))
                .slice(0, 8);

            const ctxBar = document.getElementById('graficoIfr').getContext('2d');
            new Chart(ctxBar, {{
                type: 'bar',
                data: {{
                    labels: topSobrevendidos.map(a => a.ticker),
                    datasets: [{{
                        label: 'IFR(2)',
                        data: topSobrevendidos.map(a => parseFloat(a.rsi2)),
                        backgroundColor: '#fbbf24',
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            max: 100,
                            min: 0,
                            grid: {{ color: '#334155' }},
                            ticks: {{ color: '#94a3b8' }}
                        }},
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ color: '#cbd5e1' }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Site com graficos Chart.js corrigidos gerado com sucesso!")

if __name__ == "__main__":
    construir_painel()
