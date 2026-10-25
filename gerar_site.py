# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

def gerar_dashboard_html():
    csv_file = "scanner_fechamento.csv"
    if not os.path.exists(csv_file):
        print("Erro: scanner_fechamento.csv nao encontrado.")
        return

    df = pd.read_csv(csv_file)

    # Identificacao tolerante das colunas de IFR e Preco
    col_ifr = "IFR(2)" if "IFR(2)" in df.columns else ("RSI(2)" if "RSI(2)" in df.columns else None)
    col_preco = "Pre?o (R$)" if "Pre?o (R$)" in df.columns else "Preco (R$)"

    # Carregamento de teses
    teses = {}
    if os.path.exists("teses_qualitativas.json"):
        try:
            with open("teses_qualitativas.json", "r", encoding="utf-8") as f:
                teses = json.load(f)
        except Exception:
            teses = {}

    # Data e hora oficiais com fuso de Brasilia (GMT-3)
    fuso_br = ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.now(fuso_br).strftime("%d/%m/%Y ?s %H:%M")

    # Contadores para o grafico Donut
    fases_count = {
        "Tend?ncia de Alta": 0,
        "Sobrecomprado": 0,
        "Consolida??o / Neutro": 0,
        "Tend?ncia de Baixa": 0,
        "Pullback em Alta": 0,
        "Tend?ncia de Baixa (Sobrevendido)": 0
    }

    ativos_validos = []
    for _, row in df.iterrows():
        t = str(row.get("Ticker", "")).strip().upper()
        if not t or t == "NAN": 
            continue

        preco = float(row.get(col_preco, 0.0) or 0.0)
        sma200 = float(row.get("SMA 200", 0.0) or 0.0)
        
        ifr_val = 50.0
        if col_ifr and pd.notna(row.get(col_ifr)):
            try:
                ifr_val = float(row.get(col_ifr))
            except Exception:
                ifr_val = 50.0

        fase = str(row.get("Swing Trade", "Lateraliza??o / Neutro"))
        if "Alta Forte" in fase: fases_count["Tend?ncia de Alta"] += 1
        elif "Sobrecomprado" in fase: fases_count["Sobrecomprado"] += 1
        elif "Sobrevendido (Oportunidade)" in fase: fases_count["Pullback em Alta"] += 1
        elif "Sobrevendido em Tend?ncia Baixa" in fase: fases_count["Tend?ncia de Baixa (Sobrevendido)"] += 1
        elif "Baixa" in fase: fases_count["Tend?ncia de Baixa"] += 1
        else: fases_count["Consolida??o / Neutro"] += 1

        score = str(row.get("Score Fundamentalista", "50 (Regular)"))
        tipo = str(row.get("Tipo", "ACAO"))
        nome = str(row.get("Nome", t))

        tese_info = teses.get(t, {"veredito_sinal": "neutro", "parecer": "An?lise pendente de processamento."})

        ativos_validos.append({
            "ticker": t,
            "tipo": tipo,
            "nome": nome,
            "preco": preco,
            "sma200": sma200,
            "ifr2": ifr_val,
            "fase": fase,
            "score": score,
            "veredito": tese_info.get("veredito_sinal", "neutro"),
            "parecer": tese_info.get("parecer", "")
        })

    # Top 8 menores IFR(2)
    candidatos_pullback = [a for a in ativos_validos if a["ifr2"] > 0]
    candidatos_pullback.sort(key=lambda x: x["ifr2"])
    top8 = candidatos_pullback[:8]

    top8_tickers = [a["ticker"] for a in top8]
    top8_valores = [round(a["ifr2"], 1) for a in top8]

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WF Investimentos | Scanner B3 Institucional</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background-color: #0b1120; color: #f8fafc; padding: 24px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eab308; padding-bottom: 16px; margin-bottom: 24px; }}
        .logo-box {{ display: flex; align-items: center; gap: 14px; }}
        .logo-circle {{ width: 44px; height: 44px; border-radius: 50%; border: 2px solid #eab308; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #eab308; font-size: 18px; }}
        .title h1 {{ font-size: 22px; font-weight: 800; letter-spacing: 1px; color: #ffffff; }}
        .title p {{ font-size: 11px; color: #eab308; font-weight: 600; letter-spacing: 0.5px; }}
        .meta {{ text-align: right; font-size: 13px; color: #94a3b8; }}
        .meta strong {{ color: #ffffff; }}
        .search-card {{ background: #111c35; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 24px; }}
        .search-title {{ font-size: 15px; font-weight: 700; color: #ffffff; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }}
        .search-bar {{ display: flex; gap: 10px; margin-top: 12px; }}
        .search-bar input {{ flex: 1; max-width: 450px; background: #070d1e; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; color: #fff; font-size: 14px; text-transform: uppercase; }}
        .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 30px; }}
        .chart-box {{ background: #111c35; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; }}
        .chart-box h2 {{ font-size: 14px; font-weight: 700; color: #e2e8f0; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .table-box {{ background: #111c35; border: 1px solid #1e293b; border-radius: 12px; overflow: hidden; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }}
        th {{ background: #0a1122; color: #94a3b8; padding: 14px 16px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; border-bottom: 1px solid #1e293b; }}
        td {{ padding: 14px 16px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }}
        tr:hover {{ background-color: #17233f; }}
        .ticker {{ font-weight: 700; color: #ffffff; }}
        .badge {{ padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; }}
        .badge-alta {{ background: #3b0764; color: #d8b4fe; border: 1px solid #a855f7; }}
        .badge-pullback {{ background: #451a03; color: #fde047; border: 1px solid #eab308; }}
        .badge-sobrecomprado {{ background: #064e3b; color: #6ee7b7; border: 1px solid #10b981; }}
        .badge-baixa {{ background: #3f1d24; color: #fca5a5; border: 1px solid #ef4444; }}
        .badge-neutro {{ background: #1e293b; color: #94a3b8; border: 1px solid #475569; }}
        .btn-ia {{ padding: 5px 12px; border-radius: 6px; font-weight: 700; font-size: 11px; cursor: pointer; border: 1px solid transparent; }}
        .btn-compra {{ background: #042f2e; color: #5eead4; border-color: #14b8a6; }}
        .btn-alerta {{ background: #422006; color: #fde047; border-color: #eab308; }}
        .btn-venda {{ background: #450a0a; color: #fca5a5; border-color: #ef4444; }}
        .btn-neutro {{ background: #1e293b; color: #cbd5e1; border-color: #475569; }}
        .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 999; justify-content: center; align-items: center; }}
        .modal-box {{ background: #0f172a; border: 1px solid #eab308; border-radius: 12px; max-width: 650px; width: 90%; padding: 24px; position: relative; max-height: 85vh; overflow-y: auto; }}
        .modal-close {{ position: absolute; top: 16px; right: 18px; color: #94a3b8; font-size: 20px; font-weight: bold; cursor: pointer; }}
        .modal-close:hover {{ color: #fff; }}
        .modal-body {{ font-size: 13px; line-height: 1.6; color: #e2e8f0; white-space: pre-wrap; margin-top: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-box">
            <div class="logo-circle">WF</div>
            <div class="title">
                <h1>WF INVESTIMENTOS</h1>
                <p>AVALIA??O INSTITUCIONAL & SCANNER B3</p>
            </div>
        </div>
        <div class="meta">
            <div>Atualizado em: <strong>{agora_br}</strong></div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">(Hor?rio de Bras?lia)</div>
            <div style="margin-top: 4px;">Universo Monitorado: <strong>{len(ativos_validos)} Ativos</strong></div>
        </div>
    </div>

    <div class="search-card">
        <div class="search-title">?? CONSULTA DIRETA DE ATIVO B3</div>
        <div style="font-size: 12px; color: #94a3b8;">Consulte diagn?sticos e teses de A??es, FIIs, BDRs ou ETFs negociados na bolsa.</div>
        <div class="search-bar">
            <input type="text" id="filtro" placeholder="DIGITE O TICKER (EX: PETR4, HGLG11, IVVB11)..." onkeyup="filtrarTabela()">
        </div>
    </div>

    <div class="charts-grid">
        <div class="chart-box">
            <h2>?? DISTRIBUI??O DE FASES T?CNICAS</h2>
            <div style="height: 250px;"><canvas id="chartDonut"></canvas></div>
        </div>
        <div class="chart-box">
            <h2>? TOP 8 PULLBACKS - MENORES IFR(2)</h2>
            <div style="height: 250px;"><canvas id="chartBar"></canvas></div>
        </div>
    </div>

    <div class="table-box">
        <table id="tabelaAtivos">
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Tipo</th>
                    <th>Pre?o (R$)</th>
                    <th>SMA 200</th>
                    <th>IFR(2)</th>
                    <th>Fase T?cnica</th>
                    <th>Score Fundamentalista</th>
                    <th>Parecer IA</th>
                </tr>
            </thead>
            <tbody>
"""

    for a in ativos_validos:
        fase_nome = a["fase"]
        if "Alta Forte" in fase_nome: b_class = "badge-alta"
        elif "Sobrecomprado" in fase_nome: b_class = "badge-sobrecomprado"
        elif "Sobrevendido (Oportunidade)" in fase_nome: b_class = "badge-pullback"
        elif "Baixa" in fase_nome: b_class = "badge-baixa"
        else: b_class = "badge-neutro"

        v = a["veredito"].lower()
        if v == "compra": btn_class = "btn-compra"
        elif v == "alerta": btn_class = "btn-alerta"
        elif v == "venda": btn_class = "btn-venda"
        else: btn_class = "btn-neutro"

        html_content += f"""
                <tr>
                    <td class="ticker">{a['ticker']}</td>
                    <td>{a['tipo']}</td>
                    <td>R$ {a['preco']:.2f}</td>
                    <td>R$ {a['sma200']:.2f}</td>
                    <td style="font-weight: 700; color: {'#4ade80' if a['ifr2'] <= 15 else ('#f87171' if a['ifr2'] >= 85 else '#cbd5e1')};">{a['ifr2']:.1f}</td>
                    <td><span class="badge {b_class}">{fase_nome}</span></td>
                    <td>{a['score']}</td>
                    <td>
                        <button class="btn-ia {btn_class}" onclick="abrirModal('{a['ticker']}', `{a['parecer']}`)">
                            Tese IA ({v.upper()})
                        </button>
                    </td>
                </tr>
"""

    html_content += f"""
            </tbody>
        </table>
    </div>

    <div id="modalTese" class="modal" onclick="fecharModalFora(event)">
        <div class="modal-box">
            <span class="modal-close" onclick="fecharModal()">&times;</span>
            <h3 id="modalTitulo" style="color: #eab308; font-size: 16px; margin-bottom: 8px;"></h3>
            <div id="modalCorpo" class="modal-body"></div>
        </div>
    </div>

    <script>
        new Chart(document.getElementById('chartDonut'), {{
            type: 'doughnut',
            data: {{
                labels: {list(fases_count.keys())},
                datasets: [{{
                    data: {list(fases_count.values())},
                    backgroundColor: ['#a855f7', '#10b981', '#475569', '#64748b', '#eab308', '#ef4444'],
                    borderWidth: 0
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }} }} }}
        }});

        new Chart(document.getElementById('chartBar'), {{
            type: 'bar',
            data: {{
                labels: {top8_tickers},
                datasets: [{{
                    label: 'IFR(2)',
                    data: {top8_valores},
                    backgroundColor: '#38bdf8',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, max: 50, grid: {{ color: '#1e293b' }}, ticks: {{ color: '#94a3b8' }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ color: '#cbd5e1' }} }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});

        function filtrarTabela() {{
            const val = document.getElementById('filtro').value.toUpperCase();
            const trs = document.querySelectorAll('#tabelaAtivos tbody tr');
            trs.forEach(tr => {{
                const ticker = tr.querySelector('.ticker').innerText.toUpperCase();
                tr.style.display = ticker.includes(val) ? '' : 'none';
            }});
        }}

        function abrirModal(ticker, parecer) {{
            document.getElementById('modalTitulo').innerText = "Tese Qualitativa IA - #" + ticker;
            document.getElementById('modalCorpo').innerText = parecer ? parecer : "Parecer em analise.";
            document.getElementById('modalTese').style.display = 'flex';
        }}

        function fecharModal() {{
            document.getElementById('modalTese').style.display = 'none';
        }}

        function fecharModalFora(e) {{
            if (e.target.id === 'modalTese') fecharModal();
        }}
    </script>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Sucesso: index.html compilado com fuso de Brasilia e IFR corrigido.")

if __name__ == "__main__":
    gerar_dashboard_html()
