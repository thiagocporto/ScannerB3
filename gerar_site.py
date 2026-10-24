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
        return "border: 1px solid #475569; color: #94a3b8; background-color: rgba(30, 41, 59, 0.5);"
    
    parecer = str(teses[ticker].get("parecer", "")).lower()
    
    termos_vermelho = ["desfavorável", "desfavoravel", "venda", "alto risco", "deterioração", "desinvestir", "evitar", "pessimista"]
    termos_verde = ["favorável", "favoravel", "compra", "acumular", "acumulação", "positivo", "oportunidade", "atrativo", "alta convicção"]
    
    if any(p in parecer for p in termos_vermelho):
        # Vermelho translúcido
        return "border: 1px solid #f43f5e; color: #fda4af; background-color: rgba(225, 29, 72, 0.25); box-shadow: 0 0 8px rgba(244, 63, 94, 0.3);"
    elif any(p in parecer for p in termos_verde):
        # Verde esmeralda
        return "border: 1px solid #10b981; color: #6ee7b7; background-color: rgba(16, 185, 129, 0.25); box-shadow: 0 0 8px rgba(16, 185, 129, 0.3);"
    else:
        # Amarelo / Âmbar
        return "border: 1px solid #f59e0b; color: #fde68a; background-color: rgba(245, 158, 11, 0.25); box-shadow: 0 0 8px rgba(245, 158, 11, 0.3);"

def gerar_dashboard_html():
    if not os.path.exists(ARQUIVO_CSV):
        print(f"[ERRO] {ARQUIVO_CSV} não encontrado.")
        return

    df = pd.read_csv(ARQUIVO_CSV)
    teses = carregar_teses()
    agora_str = datetime.now().strftime("%Y-%m-%d às %H:%M")

    linhas_tabela = ""
    for _, row in df.iterrows():
        ticker = str(row.get("Ticker", "")).strip().upper()
        preco = float(row.get("Preço (R$)", 0.0))
        sma200 = float(row.get("SMA 200", 0.0))
        rsi2 = float(row.get("RSI(2)", 0.0))
        crsi = float(row.get("ConnorsRSI", rsi2))
        fase = str(row.get("Swing Trade", "Neutro"))
        score = str(row.get("Score Fundamentalista", "Regular"))

        # Selo da Fase Técnica idêntico ao seu layout
        badge_fase = f'<span class="px-3 py-1 text-xs rounded-full bg-slate-800/80 text-blue-300 border border-blue-500/30">{fase}</span>'
        
        # Selo do Score Fundamentalista
        if "Excelente" in score or "Bom" in score:
            badge_score = f'<span class="text-xs font-semibold text-emerald-400">{score}</span>'
        elif "Fraco" in score:
            badge_score = f'<span class="text-xs font-semibold text-rose-400">{score}</span>'
        else:
            badge_score = f'<span class="text-xs font-semibold text-amber-400">{score}</span>'

        cor_rsi = "text-emerald-400 font-bold" if rsi2 <= 15 else ("text-rose-400 font-bold" if rsi2 >= 85 else "text-slate-300")

        # Botão semafórico
        estilo_btn = classificar_estilo_botao(ticker, teses)
        btn_tese = f'''<button onclick="abrirModal('{ticker}')" style="{estilo_btn}" class="px-3 py-1 text-xs font-bold rounded cursor-pointer transition-all hover:scale-105">
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen p-4 sm:p-8 space-y-6">

    <!-- Container Principal do Painel -->
    <div class="max-w-7xl mx-auto space-y-4">
        
        <!-- Topo da Tabela idêntico ao seu print -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
            <div class="p-4 sm:p-5 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div>
                    <h2 class="text-base sm:text-lg font-bold text-white tracking-wide">Matriz de Ativos B3 (IBrX 100)</h2>
                    <p class="text-xs text-slate-400">Atualizado em: <span class="text-amber-400 font-semibold">{agora_str}</span></p>
                </div>
                <div class="text-xs text-slate-400 font-medium">
                    Total: {len(df)} ações monitoradas
                </div>
            </div>

            <!-- Tabela de Ativos -->
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs sm:text-sm">
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
    </div>

    <!-- Modal Flutuante Dark Navy -->
    <div id="modalBox" class="fixed inset-0 bg-slate-950/85 backdrop-blur-sm hidden items-center justify-center p-4 z-50">
        <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 id="modalTitulo" class="text-base font-bold text-white flex items-center gap-2">
                    📊 Tese Institucional
                </h3>
                <button onclick="fecharModal()" class="text-slate-400 hover:text-white text-xl font-bold transition-colors">&times;</button>
            </div>
            
            <div id="modalTexto" class="text-xs sm:text-sm text-slate-200 whitespace-pre-line leading-relaxed max-h-[60vh] overflow-y-auto pr-2">
            </div>

            <div class="border-t border-slate-800 pt-3 flex justify-between items-center text-xs text-slate-500">
                <span>WF Investimentos • Motor Analítico Gemini</span>
                <button onclick="fecharModal()" class="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg transition-colors">Fechar</button>
            </div>
        </div>
    </div>

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
    </script>
</body>
</html>
"""
    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ index.html gerado na raiz com sucesso às {agora_str}!")

if __name__ == "__main__":
    gerar_dashboard_html()
