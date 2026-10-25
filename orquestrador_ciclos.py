import time
import subprocess
import os
from datetime import datetime

# Grade oficial calibrada de 5 ciclos
CICLOS_DIARIOS = [
    (9, 47),   # Ciclo 1: Pré-Abertura / Sentimento de Leilão B3
    (10, 15),  # Ciclo 2: Abertura e Primeiras Cotações Contínuas
    (13, 0),   # Ciclo 3: Meio de Pregão e Digestão NY
    (15, 0),   # Ciclo 4: Reta Final / Janela Institucional
    (17, 45)   # Ciclo 5: Fechamento Oficial Consolidado
]

def executar_comando(cmd):
    print(f"\n[ROBÔ WF] Executando: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr and "warning" not in res.stderr.lower():
        print(res.stderr.strip())

def rodar_ciclo_completo(nome_ciclo):
    agora_str = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
    print("\n" + "=" * 65)
    print(f"INICIANDO {nome_ciclo.upper()} - {agora_str}")
    print("=" * 65)

    py = r".\venv\Scripts\python.exe"

    # 1. Análise Técnica e Cotações Quantitativas (Ações, FIIs, ETFs e BDRs)
    executar_comando(f"{py} engine_analise.py")

    # 2. Pareceres Qualitativos da IA
    executar_comando(f"{py} analisador_qualitativo.py")

    # 3. Compilação do Site Seguro
    executar_comando(f"{py} gerar_site.py")

    # 4. Deploy no GitHub Pages
    msg = f"deploy: {nome_ciclo} - {datetime.now().strftime('%H:%M')}"
    executar_comando('git add scanner_fechamento.csv teses_qualitativas.json index.html universo_b3.json')
    executar_comando(f'git commit -m "{msg}"')
    executar_comando('git push origin main')

    print("\n" + "=" * 65)
    print(f"{nome_ciclo.upper()} CONCLUÍDO E PUBLICADO COM SUCESSO!")
    print("=" * 65 + "\n")

def loop_agendador():
    print("=" * 65)
    print("ORQUESTRADOR DE PREGÃO B3 WF INVESTIMENTOS INICIADO")
    print("Grade Diária: 09:47 | 10:15 | 13:00 | 15:00 | 17:45")
    print("=" * 65)

    ciclos_executados_hoje = set()
    data_atual = datetime.now().date()

    while True:
        agora = datetime.now()

        # Reseta os disparos na virada da meia-noite
        if agora.date() != data_atual:
            data_atual = agora.date()
            ciclos_executados_hoje.clear()

        # Dias úteis (Segunda a Sexta)
        if agora.weekday() < 5:
            hora_min = (agora.hour, agora.minute)

            for h_alvo, m_alvo in CICLOS_DIARIOS:
                chave_ciclo = f"{h_alvo:02d}:{m_alvo:02d}"

                if hora_min >= (h_alvo, m_alvo) and chave_ciclo not in ciclos_executados_hoje:
                    ciclos_executados_hoje.add(chave_ciclo)
                    
                    rotulo = "Pré-Market / Leilão" if chave_ciclo == "09:47" else f"Ciclo das {chave_ciclo}"
                    rodar_ciclo_completo(rotulo)
                    break

        time.sleep(20)

if __name__ == "__main__":
    loop_agendador()
