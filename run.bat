@echo off
title Auto-Enrichment Data NasDem
echo ===================================================
echo  Menjalankan Sistem Otomatisasi Data NasDem...
echo ===================================================
python run.py
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal menjalankan python run.py. Pastikan Python sudah terinstal di komputer Anda.
    pause
)
