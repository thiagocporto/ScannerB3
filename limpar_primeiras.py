import json
import os

ARQUIVO_TESES = r"D:\ScannerB3\teses_qualitativas.json"
PRIMEIRAS_11 = ["ALOS3", "ALPA4", "ABEV3", "ANIM3", "ASAI3", "AURE3", "AXIA3", "AZZA3", "B3SA3", "BBSE3", "BBDC3"]

if os.path.exists(ARQUIVO_TESES):
    with open(ARQUIVO_TESES, "r", encoding="utf-8") as f:
        teses = json.load(f)
    removidos = [t for t in PRIMEIRAS_11 if t in teses]
    for t in removidos:
        del teses[t]
    with open(ARQUIVO_TESES, "w", encoding="utf-8") as f:
        json.dump(teses, f, indent=4, ensure_ascii=False)
    print(f"Limpas {len(removidos)} teses para regerar com profundidade máxima.")
