import os
import json
import pandas as pd
from datetime import datetime

ARQUIVO_CSV = r"D:\ScannerB3\scanner_fechamento.csv"
ARQUIVO_HTML = r"D:\ScannerB3\index.html"
ARQUIVO_OPORTUNIDADES = r"D:\ScannerB3\oportunidades_hoje.json"
ARQUIVO_MACRO = r"D:\ScannerB3\macro_contexto.json"

def carregar_dados_macro():
    if not os.path.exists(ARQUIVO_MACRO):
        return None
    try:
        with open(ARQUIVO_MACRO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def carregar_oportunidades_intraday():
    if not os.path.exists(ARQUIVO_OPORTUNIDADES):
        return []
    try:
        with open(ARQUIVO_OPORTUNIDADES, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def gerar_dashboard_html():
    print("A compilar o dashboard com suporte a Fatores Externos (Macro)...")
    
    # 1. Carrega dados do CSV
    if not os.path.exists(ARQUIVO_CSV):
        print(f"[AVISO] '{ARQUIVO_CSV}' não encontrado.")
        return

    df = pd.read_csv(ARQUIVO_CSV)
    oportunidades = carregar_oportunidades_intraday()
    macro = carregar_dados_macro()
    hora_agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # 2. Monta o bloco HTML de Macroeconomia / Choques Externos
    html_macro = ""
    if macro:
        clima = macro.get("clima", "Neutro")
        risco = macro.get("risco_fiscal", "Moderado")
        setores = macro.get("setores", "Mercado amplo")
        resumo = macro.get("resumo", "Acompanhamento de fatores externos e regulação ativo.")
        janela = macro.get("janela", "CONJUNTURA").replace("_", " ")
        atualizado = macro.get("atualizado_em", hora_agora)

        cor_clima = "bg-amber-500/20 text-amber-300 border-amber-500/40" if clima in ["Cautela", "Pânico"] else "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
        cor_risco = "bg-rose-500/20 text-rose-300 border-rose-500/40" if risco == "Alto" else ("bg-amber-500/20 text-amber-300 border-amber-500/40" if risco == "Moderado" else "bg-emerald-500/20 text-emerald-300 border-emerald-500/40")

        html_macro = f"""
        <div class="mb-8 rounded-xl bg-slate-800/80 border border-slate-700/80 p-5 shadow-lg backdrop-blur-md">
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-700 pb-3 mb-3">
                <div class="flex items-center gap-2">
                    <span class="text-xl">🌐</span>
                    <h2 class="text-lg font-bold text-white tracking-wide">Conjuntura Externa, Risco Político & Fatores Macro</h2>
                    <span class="text-xs px-2 py-0.5 rounded uppercase font-semibold bg-slate-700 text-slate-300">{janela}</span>
                </div>
                <div class="text-xs text-slate-400">Atualizado: <span class="text-slate-200 font-medium">{atualizado}</span></div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-700/50">
                    <div class="text-xs font-semibold text-slate-400 mb-1">CLIMA DO MERCADO</div>
                    <span class="inline-block px-2.5 py-1 text-xs font-bold rounded-md border {cor_clima}">{clima}</span>
                </div>
                <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-700/50">
                    <div class="text-xs font-semibold text-slate-400 mb-1">RISCO POLÍTICO / FISCAL</div>
                    <span class="inline-block px-2.5 py-1 text-xs font-bold rounded-md border {cor_risco}">{risco}</span>
                </div>
                <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-700/50">
                    <div class="text-xs font-semibold text-slate-400 mb-1">VULNERABILIDADE SETORIAL</div>
                    <div class="text-xs font-medium text-slate-200 truncate" title="{setores}">{setores}</div>
                </div>
            </div>
            <div class="text-xs text-slate-300 bg-slate-900/40 p-2.5 rounded border border-slate-700/40 leading-relaxed">
                <span class="font-semibold text-amber-400">Diagnóstico Qualitativo:</span> {resumo}
            </div>
        </div>
        """

    # 3. Monta o bloco de oportunidades do dia (se houver)
    html_oportunidades = ""
    if oportunidades:
        cards_html = ""
        for op in oportunidades:
            t = op.get("ticker", "ATIVO")
            p = op.get("preco", 0.0)
            a = op.get("alvo", 0.0)
            u = op.get("upside", 0.0)
            crsi = op.get("connors_rsi", 0.0)
            cards_html += f"""
            <div class="p-4 rounded-lg bg-emerald-950/40 border border-emerald-500/40 flex flex-col justify-between">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-white text-base">#{t}</span>
                    <span class="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">Gatilho Ativo</span>
                </div>
                <div class="text-xs text-slate-300 space-y-1">
                    <div>Entrada: <span class="text-white font-medium">R$ {p:.2f}</span></div>
                    <div>Alvo SMA 5: <span class="text-emerald-400 font-medium">R$ {a:.2f} (+{u:.1f}%)</span></div>
                    <div>ConnorsRSI: <span class="text-white font-medium">{crsi:.1f}</span></div>
                </div>
            </div>
            """
        html_oportunidades = f"""
        <div class="mb-8 rounded-xl bg-slate-800/80 border border-emerald-500/30 p-5 shadow-lg">
            <h2 class="text-lg font-bold text-emerald-400 mb-3 flex items-center gap-2">
                <span>🔥</span> Oportunidades Janela de Ouro Detectadas Hoje
            </h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                {cards_html}
            </div>
        </div>
        """

    # 4. Linhas da tabela
    linhas_tabela = ""
    for _, row in df.iterrows():
        t = row.get("Ticker", "-")
        p = row.get("Preço (R$)", 0.0)
        s200 = row.get("SMA 200", 0.0)
        ifr = row.get("RSI(2)", 0.0)
        crsi = row.get("ConnorsRSI", ifr)
        st = str(row.get("Swing Trade", "-"))
        sc = str(row.get("Score Fundamentalista", "-"))

        cor_swing = "bg-slate-800 text-slate-300"
        if "COMPRA" in st:
            cor_swing = "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold"
        elif "Alta" in st:
            cor_swing = "bg-blue-500/20 text-blue-300 border border-blue-500/30"
        elif "Baixa" in st:
            cor_swing = "bg-rose-500/20 text-rose-300 border border-rose-500/30"

        cor_score = "text-slate-400"
        if "Excelente" in sc or "Bom" in sc:
            cor_score = "text-emerald-400 font-bold"
        elif "Regular" in sc:
            cor_score = "text-amber-400 font-medium"
        elif "Fraco" in sc:
            cor_score = "text-rose-400"

        linhas_tabela += f"""
        <tr class="border-b border-slate-700/60 hover:bg-slate-700/30 transition-colors">
            <td class="px-4 py-3 font-bold text-white">{t}</td>
            <td class="px-4 py-3 text-right text-slate-200">R$ {p:.2f}</td>
            <td class="px-4 py-3 text-right text-slate-400">R$ {s200:.2f}</td>
            <td class="px-4 py-3 text-right font-medium text-slate-300">{ifr:.1f}</td>
            <td class="px-4 py-3 text-right font-semibold text-amber-300">{crsi:.1f}</td>
            <td class="px-4 py-3 text-center"><span class="px-2.5 py-1 text-xs rounded-full {cor_swing}">{st}</span></td>
            <td class="px-4 py-3 text-center text-xs {cor_score}">{sc}</td>
        </tr>
        """

    # 5. Template HTML completo
    html_final = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WF Investimentos | Radar B3 & Análise Macro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen antialiased">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Cabeçalho -->
        <header class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-6 mb-6">
            <div class="flex items-center gap-3">
                <img src="logo.png" alt="WF Investimentos" class="h-10 w-auto rounded" onerror="this.style.display='none'">
                <div>
                    <h1 class="text-2xl font-black tracking-wider text-white">WF INVESTIMENTOS</h1>
                    <p class="text-xs text-amber-400 font-medium">SISTEMA QUANTITATIVO B3 & MATRIZ DE RISCO EXTERNO</p>
                </div>
            </div>
            <div class="text-right text-xs text-slate-400">
                <div>Consolidado em: <span class="text-slate-200 font-semibold">{hora_agora}</span></div>
                <div class="text-emerald-400 font-medium mt-0.5">● Sistema 100% Operacional</div>
            </div>
        </header>

        <!-- Bloco 1: Banner Macro e Fatores Externos -->
        {html_macro}

        <!-- Bloco 2: Oportunidades do Dia (se houver) -->
        {html_oportunidades}

        <!-- Bloco 3: Tabela Geral de Ativos IBrX 100 -->
        <div class="rounded-xl bg-slate-800/80 border border-slate-700/80 shadow-lg overflow-hidden">
            <div class="p-4 border-b border-slate-700 flex justify-between items-center">
                <h3 class="font-bold text-white text-base">Matriz de Ativos B3 (IBrX 100)</h3>
                <span class="text-xs text-slate-400">Total: {len(df)} ações monitoradas</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead class="bg-slate-950/60 text-xs text-slate-400 uppercase border-b border-slate-700">
                        <tr>
                            <th class="px-4 py-3">Ticker</th>
                            <th class="px-4 py-3 text-right">Preço</th>
                            <th class="px-4 py-3 text-right">SMA 200</th>
                            <th class="px-4 py-3 text-right">IFR(2)</th>
                            <th class="px-4 py-3 text-right">ConnorsRSI</th>
                            <th class="px-4 py-3 text-center">Fase Técnica</th>
                            <th class="px-4 py-3 text-center">Score Fund.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_tabela}
                    </tbody>
                </table>
            </div>
        </div>

        <footer class="mt-8 pt-4 border-t border-slate-800 text-center text-xs text-slate-500">
            WF Investimentos © {datetime.now().year} — Ferramenta analítica quantitativa e qualitativa para tomada de decisão.
        </footer>
    </div>
</body>
</html>
"""
    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html_final)
    print("✅ Dashboard atualizado com sucesso em 'index.html'!")

if __name__ == "__main__":
    gerar_dashboard_html()
