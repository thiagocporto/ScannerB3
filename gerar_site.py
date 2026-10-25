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

def escapar_json_script(objeto: dict) -> str:
    """Serializa JSON com escape rigoroso de tags HTML para mitigar injeção de script (XSS)."""
    bruto = json.dumps(objeto, ensure_ascii=False)
    return bruto.replace("<", "\\u003c").replace(">", "\\u003e")

def construir_painel():
    if not os.path.exists('scanner_fechamento.csv'):
        print("Erro: CSV de fechamento não encontrado.")
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
            "tese_texto": str(tese_obj.get("parecer", "Análise em processamento...")),
            "sinal_ia": sinal_ia 
        })

    dados_injetados = {
        "atualizacao": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        "total_ativos": len(ativos_front),
        "grafico_tendencias": contagem_tendencias,
        "ativos": ativos_front
    }
    
    json_seguro = escapar_json_script(dados_injetados)
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' data:; img-src 'self' data:; connect-src 'self';">
    <title>WF Investimentos | Scanner Quantitativo</title>
    <!-- Folha Estatica Pre-compilada Tailwind (Sem JIT de terceiros) -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" crossorigin="anonymous">
    <!-- Chart.js 4.4.1 Oficial Versao Fixada -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" crossorigin="anonymous"></script>
    <style>
        body {{ background-color: #0f172a; color: #cbd5e1; font-family: ui-sans-serif, system-ui, sans-serif; }}
        .bg-card {{ background-color: #1e293b; }}
        .border-card {{ border-color: #334155; }}
        .border-gold {{ border-color: #f59e0b; }}
        .text-gold {{ color: #fbbf24; }}
        .btn-compra {{ background-color: rgba(6, 78, 59, 0.4); color: #34d399; border-color: rgba(52, 211, 153, 0.4); }}
        .btn-compra:hover {{ background-color: rgba(6, 78, 59, 0.7); }}
        .led-compra {{ background-color: #34d399; }}
        .btn-alerta {{ background-color: rgba(120, 53, 15, 0.4); color: #fbbf24; border-color: rgba(251, 191, 36, 0.4); }}
        .btn-alerta:hover {{ background-color: rgba(120, 53, 15, 0.7); }}
        .led-alerta {{ background-color: #fbbf24; }}
        .btn-venda {{ background-color: rgba(136, 19, 55, 0.4); color: #fb7185; border-color: rgba(251, 113, 133, 0.4); }}
        .btn-venda:hover {{ background-color: rgba(136, 19, 55, 0.7); }}
        .led-venda {{ background-color: #fb7185; }}
        .btn-neutro {{ background-color: #1e293b; color: #94a3b8; border-color: #475569; }}
        .btn-neutro:hover {{ background-color: #334155; }}
        .led-neutro {{ background-color: #64748b; }}
    </style>
</head>
<body class="min-h-screen flex flex-col antialiased">
    <!-- Header Oficial WF -->
    <header class="bg-card border-b-2 border-gold shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-4">
                <div class="w-12 h-12 rounded-full bg-slate-900 border border-gold flex items-center justify-center text-gold font-bold text-xl shadow">WF</div>
                <div>
                    <h1 class="text-2xl font-black tracking-wider text-white">WF INVESTIMENTOS</h1>
                    <p class="text-xs text-gold font-semibold tracking-widest uppercase">Avaliação Institucional &amp; Scanner B3</p>
                </div>
            </div>
            <div class="text-right">
                <p class="text-sm font-medium text-slate-300" id="data-hora"></p>
                <p class="text-xs text-slate-400">Universo: B3 IBrX 100 • <span id="qtd-ativos">100</span> Ações</p>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8 flex-1 w-full space-y-8">
        <!-- Gráficos Analíticos -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-card rounded-xl p-6 border border-card shadow-lg">
                <h3 class="text-sm font-bold text-white mb-4 flex items-center space-x-2">
                    <span class="text-gold">📊</span>
                    <span>DISTRIBUIÇÃO DE TENDÊNCIAS</span>
                </h3>
                <div class="relative h-64 w-full flex justify-center items-center">
                    <canvas id="graficoTendencias"></canvas>
                </div>
            </div>
            <div class="bg-card rounded-xl p-6 border border-card shadow-lg">
                <h3 class="text-sm font-bold text-white mb-4 flex items-center space-x-2">
                    <span class="text-gold">📈</span>
                    <span>RADAR IFR(2) - TOP 8 MENORES</span>
                </h3>
                <div class="relative h-64 w-full">
                    <canvas id="graficoIfr"></canvas>
                </div>
            </div>
        </div>

        <!-- Tabela -->
        <div class="bg-card rounded-xl border border-card shadow-lg overflow-hidden">
            <div class="p-6 border-b border-card flex flex-col sm:flex-row justify-between items-center gap-4">
                <h2 class="text-xl font-bold text-white">Matriz de Ativos B3</h2>
                <input type="text" id="busca-ticker" placeholder="Pesquisar Ticker (ex: VALE3)..." class="bg-slate-900 border border-slate-600 text-white text-sm rounded-lg p-2.5 w-full sm:w-72 focus:outline-none focus:border-amber-500">
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left text-slate-300">
                    <thead class="text-xs uppercase bg-slate-900 text-slate-400 border-b border-card">
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
                    <tbody id="tabela-corpo" class="divide-y divide-slate-800"></tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Modal Institucional -->
    <div id="modal-tese" class="hidden fixed inset-0 z-50 bg-black bg-opacity-75 flex items-center justify-center p-4">
        <div class="bg-card w-full max-w-2xl rounded-2xl border border-slate-600 shadow-2xl overflow-hidden" id="modal-box">
            <div class="bg-slate-900 px-6 py-4 border-b border-card flex justify-between items-center">
                <h3 class="text-lg font-bold text-white flex items-center space-x-2">
                    <span class="text-gold">📊</span>
                    <span>Tese Institucional: <span id="modal-ticker" class="text-emerald-400"></span></span>
                </h3>
                <button type="button" id="btn-fechar-x" class="text-slate-400 hover:text-white text-2xl font-bold leading-none">&times;</button>
            </div>
            <div class="p-6">
                <p id="modal-texto" class="text-slate-200 whitespace-pre-line leading-relaxed text-sm"></p>
            </div>
            <div class="bg-slate-900 px-6 py-4 border-t border-card flex justify-end">
                <button type="button" id="btn-fechar" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium">Fechar</button>
            </div>
        </div>
    </div>

    <!-- Script de Dados Protegido contra quebra de tag -->
    <script id="dados-iniciais" type="application/json">{json_seguro}</script>

    <!-- JavaScript com Event Delegation e Renderização Segura via DOM -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const rawElement = document.getElementById('dados-iniciais');
            const db = JSON.parse(rawElement.textContent);
            
            document.getElementById('data-hora').textContent = 'Atualizado em: ' + db.atualizacao;
            document.getElementById('qtd-ativos').textContent = db.total_ativos;
            
            const tbody = document.getElementById('tabela-corpo');
            let ativosVisiveis = [...db.ativos];

            const temaIA = {{
                "compra": {{ classe: "btn-compra", led: "led-compra", label: "Favorável" }},
                "alerta": {{ classe: "btn-alerta", led: "led-alerta", label: "Cautela" }},
                "venda": {{ classe: "btn-venda", led: "led-venda", label: "Desfavorável" }},
                "neutro": {{ classe: "btn-neutro", led: "led-neutro", label: "Neutro" }}
            }};

            function renderizarTabela(lista) {{
                tbody.textContent = '';
                lista.forEach((ativo, idx) => {{
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-slate-800 transition-colors';

                    const tdTicker = document.createElement('td');
                    tdTicker.className = 'px-6 py-4 font-bold text-white';
                    tdTicker.textContent = ativo.ticker;

                    const tdPreco = document.createElement('td');
                    tdPreco.className = 'px-6 py-4 text-right font-medium text-slate-200';
                    tdPreco.textContent = ativo.preco_br;

                    const tdSma = document.createElement('td');
                    tdSma.className = 'px-6 py-4 text-right text-slate-400';
                    tdSma.textContent = ativo.sma200_br;

                    const tdIfr = document.createElement('td');
                    tdIfr.className = 'px-6 py-4 text-right font-mono text-slate-300';
                    tdIfr.textContent = ativo.rsi2;

                    const tdFase = document.createElement('td');
                    tdFase.className = 'px-6 py-4 text-center';
                    const spanFase = document.createElement('span');
                    spanFase.className = 'px-2.5 py-1 text-xs border border-slate-600 rounded bg-slate-900 text-slate-300';
                    spanFase.textContent = ativo.fase;
                    tdFase.appendChild(spanFase);

                    const tdScore = document.createElement('td');
                    tdScore.className = 'px-6 py-4 text-center text-slate-300 font-medium';
                    tdScore.textContent = ativo.score_fund;

                    const tdBtn = document.createElement('td');
                    tdBtn.className = 'px-6 py-4 text-center';

                    const conf = temaIA[ativo.sinal_ia] || temaIA["neutro"];
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'btn-parecer px-3 py-1 rounded-lg border text-xs font-semibold uppercase tracking-wider inline-flex items-center space-x-2 ' + conf.classe;
                    btn.dataset.index = idx;

                    const led = document.createElement('span');
                    led.className = 'w-2 h-2 rounded-full inline-block ' + conf.led;
                    btn.appendChild(led);

                    const txtLabel = document.createTextNode(' ' + conf.label);
                    btn.appendChild(txtLabel);
                    tdBtn.appendChild(btn);

                    tr.append(tdTicker, tdPreco, tdSma, tdIfr, tdFase, tdScore, tdBtn);
                    tbody.appendChild(tr);
                }});
            }}

            renderizarTabela(ativosVisiveis);

            document.getElementById('busca-ticker').addEventListener('input', (e) => {{
                const termo = e.target.value.toUpperCase();
                ativosVisiveis = db.ativos.filter(a => a.ticker.includes(termo));
                renderizarTabela(ativosVisiveis);
            }});

            tbody.addEventListener('click', (e) => {{
                const botao = e.target.closest('.btn-parecer');
                if (!botao) return;
                
                const idx = parseInt(botao.dataset.index, 10);
                const ativo = ativosVisiveis[idx];
                if (ativo) {{
                    document.getElementById('modal-ticker').textContent = ativo.ticker;
                    document.getElementById('modal-texto').textContent = ativo.tese_texto;
                    document.getElementById('modal-tese').classList.remove('hidden');
                }}
            }});

            const modal = document.getElementById('modal-tese');
            const fecharModal = () => modal.classList.add('hidden');
            document.getElementById('btn-fechar').addEventListener('click', fecharModal);
            document.getElementById('btn-fechar-x').addEventListener('click', fecharModal);
            modal.addEventListener('click', (e) => {{ if (e.target === modal) fecharModal(); }});
            document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') fecharModal(); }});

            const c = db.grafico_tendencias;
            new Chart(document.getElementById('graficoTendencias').getContext('2d'), {{
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

            const topSobrevendidos = [...db.ativos]
                .filter(a => !isNaN(parseFloat(a.rsi2)))
                .sort((a, b) => parseFloat(a.rsi2) - parseFloat(b.rsi2))
                .slice(0, 8);

            new Chart(document.getElementById('graficoIfr').getContext('2d'), {{
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
    print("Sucesso: index.html regerado com layout seguro, CSP e sem inline handlers!")

if __name__ == "__main__":
    construir_painel()
