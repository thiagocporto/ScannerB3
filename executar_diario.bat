@echo off
cd /d D:\ScannerB3
call .\venv\Scripts\activate.bat
python main.py >> automacao.log 2>&1
