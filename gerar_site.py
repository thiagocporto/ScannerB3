# -*- coding: utf-8 -*-
import json
import os
import base64
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

def obter_logo_em_base64():
    """Converte a imagem da logo para Base64 para garantir carregamento infalível."""
    extensoes = ["logo.jpg", "logo.png", "logo.jpeg", "Logo.jpg", "LOGO.JPG"]
    for nome in extensoes:
        caminho = BASE_DIR / nome
        if caminho.exists():
            try:
                with open(caminho, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    mime = "image/png" if nome.lower().endswith(".png") else "image/jpeg"
                    return f"data:{mime};base64,{b64}"
            except Exception:
                pass
    return ""

def gerar_dashboard_html():
    csv_file = BASE_DIR / "scanner_fechamento.csv"
    if not csv_file.exists():
        print("Erro: scanner_fechamento.csv nao encontrado.")
        return

    df = pd.read_csv(csv_file)

    col_ticker = next((c for c in df.columns if "ticker" in c.lower()), df.columns[0])
    col_tipo = next((c for c in df.columns if "tipo" in c.lower() or "classe" in c.lower()), None)
    col_preco = next((c for c in df.columns if "pre" in c.lower() or "close" in c.lower() or "cota" in c.lower()), None)
    col_sma200 = next((c for c in df.columns if "200" in c or "mm200" in c.lower()), None)
    col_ifr = next((c for c in df.columns if "ifr" in c.lower() or "rsi" in c.lower()), None)
    col_fase = next((c for c in df.columns if "fase" in c.lower() or "swing" in c.lower()), None)
    col_score = next((c for c in df.columns if "score" in c.lower()), None)

    teses = {}
    arquivo_teses = BASE_DIR / "teses_qualitativas.json"
    if arquivo_teses.exists():
        try:
            with open(arquivo_teses, "r", encoding="utf-8") as f:
                teses = json.load(f)
        except Exception:
            teses = {}

    fuso_br = ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.now(fuso_br).strftime("%d/%m/%Y às %H:%M")

    fases_count = {
        "Tendência de Alta": 0,
        "Sobrecomprado": 0,
        "Consolidação / Neutro": 0,
        "Tendência de Baixa": 0,
        "Pullback em Alta": 0,
        "Tendência de Baixa (Sobrevendido)": 0
    }

    ativos_validos = []
    mapa_teses_js = {}

    for _, row in df.iterrows():
        t = str(row.get(col_ticker, "")).strip().upper()
        if not t or t == "NAN":
            continue

        preco = float(row.get(col_preco, 0.0) or 0.0) if col_preco else 0.0
        sma200 = float(row.get(col_sma200, 0.0) or 0.0) if col_sma200 else 0.0
        
        ifr_val = 50.0
        if col_ifr and pd.notna(row.get(col_ifr)):
            try:
                ifr_val = float(row.get(col_ifr))
            except Exception:
                ifr_val = 50.0

        raw_fase = str(row.get(col_fase, "")).upper() if col_fase else ""
        if "SOBRECOMPRADO" in raw_fase:
            fase_padrao = "Sobrecomprado"
            fases_count["Sobrecomprado"] += 1
        elif ("SOBREVENDIDO" in raw_fase and "BAIXA" in raw_fase) or "BAIXA (SOBREVENDIDO)" in raw_fase:
            fase_padrao = "Tendência de Baixa (Sobrevendido)"
            fases_count["Tendência de Baixa (Sobrevendido)"] += 1
        elif "SOBREVENDIDO" in raw_fase or "PULLBACK" in raw_fase or "OPORTUNIDADE" in raw_fase:
            fase_padrao = "Pullback em Alta"
            fases_count["Pullback em Alta"] += 1
        elif "ALTA" in raw_fase:
            fase_padrao = "Tendência de Alta"
            fases_count["Tendência de Alta"] += 1
        elif "BAIXA" in raw_fase:
            fase_padrao = "Tendência de Baixa"
            fases_count["Tendência de Baixa"] += 1
        else:
            fase_padrao = "Consolidação / Neutro"
            fases_count["Consolidação / Neutro"] += 1

        tipo = str(row.get(col_tipo, "ACAO")) if col_tipo else "ACAO"
        score = str(row.get(col_score, "50 (Regular)")) if col_score else "50 (Regular)"
        tese_info = teses.get(t, {"veredito_sinal": "neutro", "parecer": "Análise pendente de processamento."})

        parecer_texto = tese_info.get("parecer", "")
        mapa_teses_js[t] = parecer_texto

        ativos_validos.append({
            "ticker": t,
            "tipo": tipo,
            "preco": preco,
            "sma200": sma200,
            "ifr2": ifr_val,
            "fase": fase_padrao,
            "score": score,
            "veredito": tese_info.get("veredito_sinal", "neutro"),
            "parecer": parecer_texto
        })

    candidatos_pullback = [a for a in ativos_validos if a["ifr2"] > 0]
    candidatos_pullback.sort(key=lambda x: x["ifr2"])
    top8 = candidatos_pullback[:8]
    top8_tickers = [a["ticker"] for a in top8]
    top8_valores = [round(a["ifr2"], 1) for a in top8]

    logo_b64 = obter_logo_em_base64()
    if logo_b64:
        logo_html = f'<img src="{logo_b64}" alt="WF Investimentos" class="logo-img">'
    else:
        logo_html = '<div class="logo-circle">WF</div>'

    cdn_chart = "https://" + "cdn" + chr(46) + "jsdelivr" + chr(46) + "net/npm/chart" + chr(46) + "js"
    json_teses_seguro = json.dumps(mapa_teses_js, ensure_ascii=False).replace("</", "<\\/")

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WF Investimentos | Scanner B3 Institucional</title>
    <script src="{cdn_chart}"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background-color: #0b1120; color: #f8fafc; padding: 24px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eab308; padding-bottom: 16px; margin-bottom: 24px; }}
        .logo-box {{ display: flex; align-items: center; gap: 14px; }}
        .logo-img {{ width: 52px; height: 52px; border-radius: 50%; border: 2px solid #eab308; object-fit: cover; box-shadow: 0 0 12px rgba(234, 179, 8, 0.4); }}
        .logo-circle {{ width: 52px; height: 52px; border-radius: 50%; border: 2px solid #eab308; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #eab308; font-size: 18px; }}
        .title h1 {{ font-size: 22px; font-weight: 800; letter-spacing: 1px; color: #ffffff; }}
        .title p {{ font-size: 11px; color: #eab308; font-weight: 600; letter-spacing: 0.5px; }}
        .meta {{ text-align: right; font-size: 13px; color: #94a3b8; }}
        .meta strong {{ color: #ffffff; }}
        .search-card {{ background: #111c35; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 24px; }}
        .search-title {{ font-size: 15px; font-weight: 700; color: #ffffff; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }}
        .search-bar {{ display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }}
        .search-bar input {{ flex: 1; min-width: 280px; max-width: 450px; background: #070d1e; border: 1px solid #334155; border-radius: 8px; padding: 11px 16px; color: #fff; font-size: 14px; text-transform: uppercase; outline: none; }}
        .search-bar input:focus {{ border-color: #eab308; box-shadow: 0 0 8px rgba(234, 179, 8, 0.3); }}
        .btn-consultar {{ background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%); color: #000; font-weight: 800; font-size: 13px; border: none; border-radius: 8px; padding: 11px 22px; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; display: inline-flex; align-items: center; gap: 6px; }}
        .btn-consultar:hover {{ transform: translateY(-1px); box-shadow: 0 4px 14px rgba(234, 179, 8, 0.4); }}
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
        .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 999; justify-content: center; align-items: center; }}
        .modal-box {{ background: #0f172a; border: 1px solid #eab308; border-radius: 12px; max-width: 650px; width: 90%; padding: 24px; position: relative; max-height: 85vh; overflow-y: auto; }}
        .modal-close {{ position: absolute; top: 16px; right: 18px; color: #94a3b8; font-size: 22px; font-weight: bold; cursor: pointer; }}
        .modal-close:hover {{ color: #fff; }}
        .modal-body {{ font-size: 13px; line-height: 1.6; color: #e2e8f0; white-space: pre-wrap; margin-top: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-box">
            {logo_html}
            <div class="title">
                <h1>WF INVESTIMENTOS</h1>
                <p>AVALIAÇÃO INSTITUCIONAL &amp; SCANNER B3</p>
            </div>
        </div>
        <div class="meta">
            <div>Atualizado em: <strong>{agora_br}</strong></div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">(Horário de Brasília)</div>
            <div style="margin-top: 4px;">Universo Monitorado: <strong>{len(ativos_validos)} Ativos</strong></div>
        </div>
    </div>

    <div class="search-card">
        <div class="search-title">&#x1F50D; CONSULTA DIRETA DE ATIVO B3</div>
        <div style="font-size: 12px; color: #94a3b8;">Digite o ticker para filtrar a tabela ou clique em <strong>CONSULTAR TESE</strong> para abrir o diagnóstico da IA instantaneamente.</div>
        <div class="search-bar">
            <input type="text" id="filtro" placeholder="DIGITE O TICKER (EX: PETR4, HGLG11, IVVB11)..." onkeyup="filtrarTabela()" onkeydown="checarEnter(event)">
            <button class="btn-consultar" onclick="consultarAtivoDireto()">
                &#x1F50E; CONSULTAR TESE
            </button>
        </div>
    </div>

    <div class="charts-grid">
        <div class="chart-box">
            <h2>&#x1F4CA; DISTRIBUIÇÃO DE FASES TÉCNICAS</h2>
            <div style="height: 250px;"><canvas id="chartDonut"></canvas></div>
        </div>
        <div class="chart-box">
            <h2>&#x2611; TOP 8 PULLBACKS - MENORES IFR(2)</h2>
            <div style="height: 250px;"><canvas id="chartBar"></canvas></div>
        </div>
    </div>

    <div class="table-box">
        <table id="tabelaAtivos">
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Tipo</th>
                    <th>Preço (R$)</th>
                    <th>SMA 200</th>
                    <th>IFR(2)</th>
                    <th>Fase Técnica</th>
                    <th>Score Fundamentalista</th>
                    <th>Parecer IA</th>
                </tr>
            </thead>
            <tbody>
"""

    for a in ativos_validos:
        f = a["fase"]
        if "Sobrecomprado" in f: b_class = "badge-sobrecomprado"
        elif "Pullback" in f: b_class = "badge-pullback"
        elif "Baixa" in f: b_class = "badge-baixa"
        elif "Alta" in f: b_class = "badge-alta"
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
                    <td><span class="badge {b_class}">{f}</span></td>
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
        const BANCO_TESES = {json_teses_seguro};

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
            const val = document.getElementById('filtro').value.toUpperCase().trim();
            const trs = document.querySelectorAll('#tabelaAtivos tbody tr');
            trs.forEach(tr => {{
                const ticker = tr.querySelector('.ticker').innerText.toUpperCase();
                tr.style.display = ticker.includes(val) ? '' : 'none';
            }});
        }}

        function checarEnter(event) {{
            if (event.key === 'Enter') {{
                consultarAtivoDireto();
            }}
        }}

        function consultarAtivoDireto() {{
            const inputVal = document.getElementById('filtro').value.toUpperCase().trim();
            if (!inputVal) {{
                alert('Digite um ticker (ex: PETR4, VALE3, HGLG11) para consultar.');
                return;
            }}

            // 1. Procura correspondência exata
            if (BANCO_TESES[inputVal]) {{
                abrirModal(inputVal, BANCO_TESES[inputVal]);
                return;
            }}

            // 2. Procura primeiro ticker que contenha o termo digitado
            const achado = Object.keys(BANCO_TESES).find(t => t.includes(inputVal));
            if (achado) {{
                abrirModal(achado, BANCO_TESES[achado]);
                return;
            }}

            alert(`Ativo '${inputVal}' não localizado no catálogo atual.`);
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

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') fecharModal();
        }});
    </script>
</body>
</html>
"""

    caminho_saida = BASE_DIR / "index.html"
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Sucesso: index.html compilado com o Botão de Consulta e Logo Base64 em '{caminho_saida}'!")

if __name__ == "__main__":
    gerar_dashboard_html()
