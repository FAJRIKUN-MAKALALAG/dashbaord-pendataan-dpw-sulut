# Sistem Otomatisasi Kelengkapan Data Anggota & Pengurus (Auto-Enrichment)

Aplikasi otomatisasi berbasis Python dan Web Dashboard modern untuk melengkapi data anggota & pengurus (DPW, DPD, DPC, DPRt) secara instan.

Mencocokkan **Data Target (mentahan lokal yang belum lengkap)** dengan **Data Master (database rujukan pusat)** menggunakan metode *Composite Key Matching* (`Nama + DPD + DPC + DPRt`) dan secara otomatis menarik `NIK`, `eKTA`, `No Telepon`, `Email`, dan `Jabatan`.

---

## 🌟 Fitur Utama

1. **Pratinjau Tabel Visualisasi Sebelum Ekspor**:
   - Operator dapat melihat data hasil tarikan (*enriched*), data target mentah, dan data rujukan sebelum file Excel final diunduh.
   - Kolom yang baru terisi ditandai secara visual dengan highlight hijau.
   - Filter wilayah (DPD) dan fitur pencarian cepat (*instant search*).
2. **Pembersihan Data Cerdas (*Data Cleansing Engine*)**:
   - Menghapus spasi ganda, spasi di awal/akhir, dan karakter tersembunyi (`\xa0`).
   - Normalisasi huruf kecil (*case folding*) agar tidak sensitif huruf besar/kecil.
   - Menghapus variasi prefix wilayah seperti `Kabupaten / Kab.`, `Kecamatan / Kec.`, `Kelurahan / Desa`.
3. **Proteksi Format NIK & No. Telepon**:
   - Mencegah *bug* notasi ilmiah Excel (misal `7.102E+15`) dan angka 0 hilang di nomor HP.
   - Sel NIK dan Telepon disimpan dengan format teks murni (`@`) pada Excel.
4. **Analisis Alasan Gagal Otomatis**:
   - Pada file `Data_Gagal_Match.xlsx`, sistem memberikan keterangan spesifik:
     - *"Nama terdaftar di DPD yang sama, tetapi DPC atau DPRt berbeda"*
     - *"Nama terdaftar di DPD lain di pusat"*
     - *"Nama sama sekali tidak ditemukan pada database pusat"*
5. **Dua Mode Pengoperasian**:
   - **Mode Web Dashboard**: Antarmuka modern interaktif di browser.
   - **Mode Terminal / CLI**: Eksekusi cepat langsung dari terminal/command prompt.

---

## 🚀 Cara Menjalankan

### 1. Cara Paling Cepat & Praktis (1 File / 1 Klik)

Cukup jalankan satu perintah berikut di terminal:
```bash
python run.py
```
*Atau klik ganda file **`run.bat`** langsung dari Windows Explorer tanpa perlu membuka terminal.*

**Apa yang otomatis dilakukan?**
- Memeriksa dependensi library.
- Menjalankan server aplikasi di latar belakang.
- **Otomatis membuka browser Anda** langsung ke alamat:
  👉 **`http://127.0.0.1:5000`**

Di web dashboard Anda dapat:
- Menekan tombol **"⚡ Muat Data Sampel Demo"** untuk mencoba langsung simulasi data Sulut.
- Atau mengunggah file Excel Master dan Target Anda sendiri (drag-and-drop).
- Meninjau data pada tabel visualisasi.
- Menekan tombol **"💾 Konfirmasi & Export Excel"** untuk mengunduh `Data_Lengkap_Sukses.xlsx` dan `Data_Gagal_Match.xlsx`.

---

### 2. Menjalankan Mode Terminal / CLI

Jika Anda lebih memilih menjalankan via Command Prompt:
```bash
python run_cli.py
```
Script akan membaca file dari folder `input/`, menampilkan tabel ringkasan dan cuplikan data teratas, lalu meminta konfirmasi `[Y/n]` sebelum mengekspor file Excel ke folder `output/`.

---

## 📁 Struktur Direktori

```text
pendataan-python/
├── app.py                     # Server Web Dashboard (Flask)
├── run_cli.py                 # Runner Command Prompt (CLI)
├── requirements.txt           # Library pendukung
├── prd_project.md             # Dokumen PRD
├── core/
│   ├── cleaner.py             # Normalisasi teks, pembersihan NIK & Telepon
│   ├── matcher.py             # Mesin pencocokan composite key & diagnosa gagal
│   ├── exporter.py            # Generator Excel dengan styling openpyxl
│   └── sample_generator.py    # Pembuat data sampel simulasi
├── templates/
│   └── index.html             # Tampilan Web Dashboard
├── static/
│   ├── css/style.css          # Desain antarmuka modern
│   └── js/app.js              # Logika interaktif tabel, filter, & unduhan
├── input/                     # Tempat menyimpan file master & target
└── output/                    # Tempat menyimpan file hasil ekspor Excel
```
