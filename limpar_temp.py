import json
import os

ARQUIVO = r"D:\ScannerB3\teses_qualitativas.json"
PRIMEIROS = ["ALOS3", "ALPA4", "ABEV3", "ANIM3", "ASAI3", "AURE3", "AXIA3", "AZZA3", "B3SA3", "BBSE3", "BBDC3"]

if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        dados = json.load(f)
    for t in PRIMEIROS:
        dados.pop(t, None)
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print("Banco preparado para regerar os 11 ativos incompletos.")
