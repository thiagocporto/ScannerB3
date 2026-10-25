import pandas as pd
import json
import os
import re
from datetime import datetime

def formatar_moeda(valor):
    if pd.isna(valor): return "R$ 0,00"
    texto = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"

def extrair_score_numerico(score_raw):
    """Extrai estritamente o valor numérico do Score."""
    if pd.isna(score_raw): return None
    match = re.search(r"(\d+(\.\d+)?)", str(score_raw))
    return float(match.group(1)) if match else None

def resolver_codigo_fase(preco, sma200, rsi2):
    """Resolve a fase para um código canônico rigoroso."""
    if pd.isna(preco) or pd.isna(sma200) or sma200 <= 0:
        return "indefinido"
    
    distancia = (preco - sma200) / sma200
    rsi2 = float(rsi2) if not pd.isna(rsi2) else 50.0

    if distancia > 0.05:
        if rsi2 >= 85: return "alta_sobrecomprado"
        if rsi2 <= 15: return "alta_pullback"
        return "alta_forte"
    elif -0.05 <= distancia <= 0.05:
        return "lateral"
    else:
        if rsi2 <= 15: return "baixa_sobrevendido"
        return "baixa"

def escapar_json_script(objeto: dict) -> str:
    bruto = json.dumps(objeto, ensure_ascii=False)
    return bruto.replace("<", "\\u003c").replace(">", "\\u003e")

def construir_painel():
    if not os.path.exists('scanner_fechamento.csv'):
        print("Erro: CSV scanner_fechamento.csv não encontrado.")
        return

    df = pd.read_csv('scanner_fechamento.csv')
    
    teses = {}
    if os.path.exists('teses_qualitativas.json'):
        with open('teses_qualitativas.json', 'r', encoding='utf-8') as f:
            teses = json.load(f)

    ativos_front = []
    for _, row in df.iterrows():
        ticker = str(row.get('Ticker', '')).strip().upper()
        if not ticker or ticker == "NAN": continue
        
        preco = float(row.get('Preço (R$)', 0.0))
        sma200 = float(row.get('SMA 200', 0.0))
        
        rsi2_bruto = row.get('RSI(2)', 50.0)
        rsi2 = float(rsi2_bruto) if not pd.isna(rsi2_bruto) and 0 <= float(rsi2_bruto) <= 100 else 50.0
        
        fase_codigo = resolver_codigo_fase(preco, sma200, rsi2)
        score_num = extrair_score_numerico(row.get('Score Fundamentalista'))
        
        tese_obj = teses.get(ticker, {})
        sinal_ia = tese_obj.get("veredito_sinal", "neutro")
        
        ativos_front.append({
            "ticker": ticker,
            "preco": round(preco, 2),
            "preco_br": formatar_moeda(preco),
            "sma200": round(sma200, 2),
            "sma200_br": formatar_moeda(sma200),
            "rsi2": round(rsi2, 1),
            "fase_cod": fase_codigo,
            "score": score_num,
            "tese_texto": str(tese_obj.get("parecer", "Análise qualitativa em processamento...")),
            "sinal_ia": sinal_ia 
        })

    dados_injetados = {
        "atualizacao": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        "ano_corrente": datetime.now().year,
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
    <!-- Tailwind Estático Pré-Compilado -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" crossorigin="anonymous">
    <!-- Chart.js 4.4.1 Oficial com Versão Fixa -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" crossorigin="anonymous"></script>
    <style>
        body {{ background-color: #0f172a; color: #cbd5e1; font-family: ui-sans-serif, system-ui, sans-serif; }}
        .bg-card {{ background-color: #1e293b; }}
        .border-card {{ border-color: #334155; }}
        .border-gold {{ border-color: #f59e0b; }}
        .text-gold {{ color: #fbbf24; }}
        th.cursor-pointer:hover {{ color: #f59e0b; }}
        
        dialog {{
            background: #1e293b;
            color: #cbd5e1;
            border: 1px solid #475569;
            border-radius: 1rem;
            max-width: 42rem;
            width: 100%;
            padding: 0;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.75);
        }}
        dialog::backdrop {{
            background-color: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(4px);
        }}
    </style>
</head>
<body class="min-h-screen flex flex-col antialiased">
    <!-- Cabeçalho Oficial WF -->
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
                <p class="text-sm font-medium text-slate-300">Atualizado em: <span id="data-hora" class="font-bold text-white"></span></p>
                <p class="text-xs text-slate-400">Universo: B3 IBrX 100 • <span id="qtd-ativos" class="font-bold text-slate-200">0</span> Ações</p>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8 flex-1 w-full space-y-8">
        <!-- Gráficos Analíticos -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-card rounded-xl p-6 border border-card shadow-lg">
                <h3 class="text-sm font-bold text-white mb-4 flex items-center space-x-2">
                    <span class="text-gold">📊</span>
                    <span>DISTRIBUIÇÃO DE FASES TÉCNICAS</span>
                </h3>
                <div class="relative h-64 w-full flex justify-center items-center">
                    <canvas id="graficoTendencias"></canvas>
                </div>
            </div>
            <div class="bg-card rounded-xl p-6 border border-card shadow-lg">
                <h3 class="text-sm font-bold text-white mb-4 flex items-center space-x-2">
                    <span class="text-gold">📈</span>
                    <span>TOP 8 PULLBACKS - MENORES IFR(2)</span>
                </h3>
                <div class="relative h-64 w-full">
                    <canvas id="graficoIfr"></canvas>
                </div>
            </div>
        </div>

        <!-- Matriz de Ativos B3 -->
        <div class="bg-card rounded-xl border border-card shadow-lg overflow-hidden">
            <div class="p-6 border-b border-card flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-800/60">
                <div>
                    <h2 class="text-xl font-bold text-white">Matriz de Ativos B3</h2>
                    <p class="text-xs text-slate-400 mt-1">Dica: Clique nas colunas para ordenar os dados</p>
                </div>
                <input type="text" id="busca-ticker" placeholder="Pesquisar Ticker (ex: VALE3)..." class="bg-slate-900 border border-slate-600 text-white text-sm rounded-lg p-2.5 w-full sm:w-72 focus:outline-none focus:border-amber-500">
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left text-slate-300">
                    <thead class="text-xs uppercase bg-slate-900 text-slate-400 border-b border-card select-none">
                        <tr>
                            <th class="px-6 py-4 font-semibold cursor-pointer" data-campo="ticker">Ticker <span id="sort-ticker">↕</span></th>
                            <th class="px-6 py-4 text-right font-semibold cursor-pointer" data-campo="preco">Preço <span id="sort-preco">↕</span></th>
                            <th class="px-6 py-4 text-right font-semibold cursor-pointer" data-campo="sma200">SMA 200 <span id="sort-sma200">↕</span></th>
                            <th class="px-6 py-4 text-right font-semibold cursor-pointer" data-campo="rsi2">IFR(2) <span id="sort-rsi2">↕</span></th>
                            <th class="px-6 py-4 text-center font-semibold">Fase Técnica</th>
                            <th class="px-6 py-4 text-center font-semibold cursor-pointer" data-campo="score">Score Fund. <span id="sort-score">↕</span></th>
                            <th class="px-6 py-4 text-center font-semibold">Parecer IA</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-corpo" class="divide-y divide-slate-800">
                        <!-- Gerado 100% dinamicamente via JS seguro -->
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Modal com elemento nativo <dialog> -->
    <dialog id="modal-dialog" aria-labelledby="modal-titulo">
        <div class="bg-slate-900 px-6 py-4 border-b border-card flex justify-between items-center">
            <h3 id="modal-titulo" class="text-lg font-bold text-white flex items-center space-x-2">
                <span class="text-gold">📊</span>
                <span>Tese Institucional: <span id="modal-ticker" class="text-emerald-400 font-mono"></span></span>
            </h3>
            <button type="button" id="btn-dialog-close-x" class="text-slate-400 hover:text-white text-2xl font-bold leading-none" aria-label="Fechar modal">&times;</button>
        </div>
        <div class="p-6">
            <p id="modal-texto" class="text-slate-200 whitespace-pre-line leading-relaxed text-sm"></p>
        </div>
        <div class="bg-slate-900 px-6 py-4 border-t border-card flex justify-between items-center">
            <span class="text-[11px] text-slate-500">Uso interno de apoio decisório • WF Investimentos</span>
            <button type="button" id="btn-dialog-close" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors" aria-label="Fechar parecer">Fechar</button>
        </div>
    </dialog>

    <footer class="border-t border-card py-4 text-center text-xs text-slate-500">
        WF Investimentos &copy; <span id="ano-footer"></span> • Todos os direitos reservados.
    </footer>

    <!-- Dados Embutidos Escapados -->
    <script id="dados-iniciais" type="application/json">{json_seguro}</script>

    <!-- Aplicação JavaScript Completa e Reativa -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const db = JSON.parse(document.getElementById('dados-iniciais').textContent);
            
            // 1. Atualizações Reativas de Cabeçalho e Rodapé
            document.getElementById('data-hora').textContent = db.atualizacao;
            document.getElementById('qtd-ativos').textContent = db.ativos.length;
            document.getElementById('ano-footer').textContent = db.ano_corrente;
            
            // 2. Mapa Único de Fases (Centralizado)
            const MAPA_FASES = {{
                "alta_sobrecomprado": {{ rotulo: "Sobrecomprado", badge: "border-purple-500/40 text-purple-400 bg-purple-900/30" }},
                "alta_pullback": {{ rotulo: "Pullback em Alta", badge: "border-emerald-500/40 text-emerald-300 bg-emerald-900/40 font-bold" }},
                "alta_forte": {{ rotulo: "Tendência de Alta", badge: "border-emerald-500/30 text-emerald-400 bg-emerald-900/20" }},
                "lateral": {{ rotulo: "Consolidação / Neutro", badge: "border-slate-600 text-slate-300 bg-slate-800" }},
                "baixa_sobrevendido": {{ rotulo: "Tendência de Baixa (Sobrevendido)", badge: "border-amber-500/40 text-amber-300 bg-amber-900/40 font-bold" }},
                "baixa": {{ rotulo: "Tendência de Baixa", badge: "border-rose-500/30 text-rose-400 bg-rose-900/20" }},
                "indefinido": {{ rotulo: "Sem Dados", badge: "border-slate-700 text-slate-500 bg-slate-900" }}
            }};

            // 3. Mapa de Veredito IA com Acessibilidade (Cor + Ícone + Texto)
            const TEMA_IA = {{
                "compra": {{ icone: "●", label: "Favorável", classe: "border-emerald-500/40 text-emerald-400 bg-emerald-900/40 hover:bg-emerald-800/60" }},
                "alerta": {{ icone: "▲", label: "Cautela", classe: "border-amber-500/40 text-amber-400 bg-amber-900/40 hover:bg-amber-800/60" }},
                "venda": {{ icone: "■", label: "Desfavorável", classe: "border-rose-500/40 text-rose-400 bg-rose-900/40 hover:bg-rose-800/60" }},
                "neutro": {{ icone: "○", label: "Neutro", classe: "border-slate-600 text-slate-400 bg-slate-800 hover:bg-slate-700" }}
            }};

            // 4. Formatação de Score
            function formatarScore(num) {{
                if (num === null || num === undefined) return "N/D";
                const v = parseFloat(num);
                let label = "Fraco";
                if (v >= 80) label = "Excelente";
                else if (v >= 60) label = "Bom";
                else if (v >= 40) label = "Regular";
                return `${{Math.round(v)}} (${{label}})`;
            }}

            const tbody = document.getElementById('tabela-corpo');
            let ativosRenderizados = [...db.ativos];
            let ordenacaoAtual = {{ campo: null, ascendente: true }};

            // 5. Renderização Segura do DOM
            function renderizarTabela(lista) {{
                tbody.textContent = '';
                lista.forEach((ativo) => {{
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-slate-800/70 transition-colors';

                    // Ticker
                    const tdTicker = document.createElement('td');
                    tdTicker.className = 'px-6 py-4 font-bold text-white font-mono';
                    tdTicker.textContent = ativo.ticker;

                    // Preço
                    const tdPreco = document.createElement('td');
                    tdPreco.className = 'px-6 py-4 text-right font-medium text-slate-200';
                    tdPreco.textContent = ativo.preco_br;

                    // SMA 200
                    const tdSma = document.createElement('td');
                    tdSma.className = 'px-6 py-4 text-right text-slate-400';
                    tdSma.textContent = ativo.sma200_br;

                    // IFR(2)
                    const tdIfr = document.createElement('td');
                    tdIfr.className = 'px-6 py-4 text-right font-mono font-semibold';
                    tdIfr.textContent = ativo.rsi2.toFixed(1);
                    if (ativo.rsi2 <= 15) tdIfr.className += ' text-emerald-400';
                    else if (ativo.rsi2 >= 85) tdIfr.className += ' text-rose-400';
                    else tdIfr.className += ' text-slate-300';

                    // Fase Técnica
                    const tdFase = document.createElement('td');
                    tdFase.className = 'px-6 py-4 text-center';
                    const faseInfo = MAPA_FASES[ativo.fase_cod] || MAPA_FASES["indefinido"];
                    const spanFase = document.createElement('span');
                    spanFase.className = 'px-2.5 py-1 text-xs border rounded ' + faseInfo.badge;
                    spanFase.textContent = faseInfo.rotulo;
                    tdFase.appendChild(spanFase);

                    // Score
                    const tdScore = document.createElement('td');
                    tdScore.className = 'px-6 py-4 text-center text-slate-300 font-medium';
                    tdScore.textContent = formatarScore(ativo.score);

                    // Botão Veredito IA com Acessibilidade
                    const tdBtn = document.createElement('td');
                    tdBtn.className = 'px-6 py-4 text-center';
                    const iaInfo = TEMA_IA[ativo.sinal_ia] || TEMA_IA["neutro"];
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'btn-tese px-3 py-1 rounded-lg border text-xs font-bold uppercase tracking-wider inline-flex items-center space-x-1.5 transition-colors ' + iaInfo.classe;
                    btn.dataset.ticker = ativo.ticker;
                    btn.setAttribute('aria-label', `Abrir tese institucional de ${{ativo.ticker}} - Sinal: ${{iaInfo.label}}`);
                    
                    const spanIcone = document.createElement('span');
                    spanIcone.textContent = iaInfo.icone;
                    spanIcone.setAttribute('aria-hidden', 'true');
                    
                    const spanTxt = document.createElement('span');
                    spanTxt.textContent = iaInfo.label;

                    btn.append(spanIcone, spanTxt);
                    tdBtn.appendChild(btn);

                    tr.append(tdTicker, tdPreco, tdSma, tdIfr, tdFase, tdScore, tdBtn);
                    tbody.appendChild(tr);
                }});
            }}

            // 6. Ordenação Interativa por Coluna
            function ordenarPor(campo) {{
                if (ordenacaoAtual.campo === campo) {{
                    ordenacaoAtual.ascendente = !ordenacaoAtual.ascendente;
                }} else {{
                    ordenacaoAtual.campo = campo;
                    ordenacaoAtual.ascendente = true;
                }}

                ativosRenderizados.sort((a, b) => {{
                    let valA = a[campo];
                    let valB = b[campo];
                    if (valA === null || valA === undefined) return 1;
                    if (valB === null || valB === undefined) return -1;
                    
                    if (typeof valA === 'string') {{
                        return ordenacaoAtual.ascendente ? valA.localeCompare(valB) : valB.localeCompare(valA);
                    }}
                    return ordenacaoAtual.ascendente ? valA - valB : valB - valA;
                }});

                // Atualiza setas no cabeçalho
                document.querySelectorAll('th[data-campo]').forEach(th => {{
                    const c = th.dataset.campo;
                    const indicador = document.getElementById(`sort-${{c}}`);
                    if (c === campo) {{
                        indicador.textContent = ordenacaoAtual.ascendente ? '▲' : '▼';
                    }} else {{
                        indicador.textContent = '↕';
                    }}
                }});

                renderizarTabela(ativosRenderizados);
            }}

            document.querySelectorAll('th[data-campo]').forEach(th => {{
                th.addEventListener('click', () => ordenarPor(th.dataset.campo));
            }});

            // 7. Filtro em Tempo Real (usando evento 'input')
            document.getElementById('busca-ticker').addEventListener('input', (e) => {{
                const termo = e.target.value.trim().toUpperCase();
                ativosRenderizados = db.ativos.filter(a => a.ticker.includes(termo));
                renderizarTabela(ativosRenderizados);
            }});

            renderizarTabela(ativosRenderizados);

            // 8. Controle do <dialog> Nativo
            const dialog = document.getElementById('modal-dialog');
            tbody.addEventListener('click', (e) => {{
                const btn = e.target.closest('.btn-tese');
                if (!btn) return;
                const ticker = btn.dataset.ticker;
                const ativo = db.ativos.find(a => a.ticker === ticker);
                if (ativo) {{
                    document.getElementById('modal-ticker').textContent = ativo.ticker;
                    document.getElementById('modal-texto').textContent = ativo.tese_texto;
                    dialog.showModal();
                }}
            }});

            const fecharDialog = () => dialog.close();
            document.getElementById('btn-dialog-close').addEventListener('click', fecharDialog);
            document.getElementById('btn-dialog-close-x').addEventListener('click', fecharDialog);
            dialog.addEventListener('click', (e) => {{ if (e.target === dialog) fecharDialog(); }});

            // 9. Gráfico 1: Rosca Dinâmica (Fases calculadas a partir dos dados)
            const contagemFases = {{}};
            db.ativos.forEach(a => {{
                const rotulo = MAPA_FASES[a.fase_cod]?.rotulo || "Outros";
                contagemFases[rotulo] = (contagemFases[rotulo] || 0) + 1;
            }});

            new Chart(document.getElementById('graficoTendencias').getContext('2d'), {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(contagemFases),
                    datasets: [{{
                        data: Object.values(contagemFases),
                        backgroundColor: ['#a855f7', '#34d399', '#059669', '#64748b', '#fbbf24', '#f43f5e', '#475569'],
                        borderColor: '#1e293b',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'right', labels: {{ color: '#cbd5e1', font: {{ size: 11 }} }} }}
                    }}
                }}
            }});

            // 10. Gráfico 2: Top 8 Menores IFR com Escala Dinâmica
            const topPullbacks = [...db.ativos]
                .filter(a => !isNaN(a.rsi2))
                .sort((a, b) => a.rsi2 - b.rsi2)
                .slice(0, 8);

            const maxIfrTop8 = Math.max(...topPullbacks.map(a => a.rsi2), 0);
            const tetoSugerido = maxIfrTop8 < 20 ? Math.ceil(maxIfrTop8 + 5) : 100;

            new Chart(document.getElementById('graficoIfr').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: topPullbacks.map(a => a.ticker),
                    datasets: [{{
                        label: 'IFR(2)',
                        data: topPullbacks.map(a => a.rsi2),
                        backgroundColor: '#fbbf24',
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: tetoSugerido,
                            grid: {{ color: '#334155' }},
                            ticks: {{ color: '#94a3b8' }}
                        }},
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ color: '#cbd5e1', font: {{ weight: 'bold' }} }}
                        }}
                    }},
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        }});
    </script>
</body>
</html>"""

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Site moderno, reativo, com ordenacao por colunas e dialog nativo compilado com sucesso!")

if __name__ == "__main__":
    construir_painel()
