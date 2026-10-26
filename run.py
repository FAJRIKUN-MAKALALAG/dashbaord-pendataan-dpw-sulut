"""
Launcher Utama - Sistem Otomatisasi Kelengkapan Data Anggota & Pengurus NasDem
Cukup jalankan file ini di terminal:
    python run.py
Atau klik ganda file run.bat di Windows.
"""
import sys
import os
import time
import webbrowser
import threading

# Pastikan UTF-8 encoding di Windows console
try:
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def open_browser():
    """Membuka halaman web dashboard di browser default otomatis setelah server siap."""
    time.sleep(1.2)
    url = "http://127.0.0.1:5000"
    print(f"[INFO] Membuka browser otomatis ke {url}...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[WARN] Tidak dapat membuka browser otomatis: {e}")

def main():
    print("=" * 65)
    print("   SISTEM OTOMATISASI KELENGKAPAN DATA NASDEM (AUTO-ENRICHMENT)")
    print("=" * 65)
    print(" [1/3] Memeriksa dependensi sistem...")

    # Cek dependencies utama
    try:
        import pandas
        import openpyxl
        import flask
    except ImportError as e:
        print(f"\n[!] Dependensi belum lengkap: {e}")
        print("Silakan pasang library terlebih dahulu dengan mengetik:")
        print("    pip install -r requirements.txt\n")
        input("Tekan Enter untuk keluar...")
        sys.exit(1)

    print(" [2/3] Membuka antarmuka visual dashboard...")
    threading.Thread(target=open_browser, daemon=True).start()

    print(" [3/3] Server aktif di: http://127.0.0.1:5000")
    print(" -------------------------------------------------------------")
    print(" Tips:")
    print("  - Dashboard visual akan terbuka otomatis di browser Anda.")
    print("  - Anda bisa Drag & Drop file Excel Master & Target langsung di web.")
    print("  - Preview tabel visual & tombol Download Template Asli sudah siap.")
    print("  - Untuk menghentikan server, tekan Ctrl + C di terminal ini.")
    print("=" * 65 + "\n")

    try:
        from app import app
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n[INFO] Server dimatikan. Sampai jumpa!")
    except Exception as e:
        print(f"\n[ERROR] Server mengalami kendala: {e}")
        input("\nTekan Enter untuk menutup...")

if __name__ == '__main__':
    main()
