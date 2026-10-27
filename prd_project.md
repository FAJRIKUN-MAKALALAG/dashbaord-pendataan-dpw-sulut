PRODUCT REQUIREMENTS DOCUMENT (PRD)
Nama Produk: Sistem Otomatisasi Kelengkapan Data Anggota & Pengurus (Auto-Enrichment Data System)
Dokumen Versi: 1.0
Target Pengguna: Admin Data / Operator Utama

1. Ringkasan & Latar Belakang (Executive Summary)
Saat ini, proses melengkapi data pengurus dan anggota dari tingkat DPW, DPD, DPC, hingga DPRt dilakukan secara manual dengan mencari satu per satu di web pusat. Dengan jumlah data mencapai lebih dari 20.000 baris, proses manual ini sangat tidak efisien, memakan waktu berminggu-minggu, dan rentan terhadap human error (salah input).
Produk ini adalah script otomatisasi berbasis Python yang dirancang untuk mencocokkan data yang belum lengkap (Data Target) dengan database lengkap dari pusat (Data Master), lalu mengisi kolom yang kosong secara otomatis berdasarkan kunci pencocokan ganda (composite key).

2. Tujuan (Objectives)
Efisiensi Waktu: Mengurangi waktu pengerjaan dari berminggu-minggu menjadi kurang dari 5 menit untuk 20.000+ data.

Akurasi Data: Menghilangkan human error akibat copy-paste manual.

Otomatisasi Laporan: Memisahkan data yang berhasil dicocokkan dan data yang gagal (anomali) agar pengecekan manual hanya dilakukan pada data yang bermasalah.

3. Kebutuhan Fitur (Feature Requirements)
Fitur Utama:

Data Ingestion (Pembacaan Data): Sistem mampu membaca file Excel/CSV dari Data Master (Pusat) dan Data Target (Lokal).

Data Cleansing (Pembersihan Data Otomatis):

Menghapus spasi berlebih di awal/akhir teks.

Mengubah semua huruf menjadi huruf kecil (lowercase) sementara selama proses pencocokan untuk menghindari gagal match karena Case Sensitive (contoh: "Amurang" vs "AMURANG").

Composite Key Matching (Pencocokan Kunci Ganda): Melakukan metode Left Join atau VLOOKUP menggunakan 4 parameter utama: Nama, DPD, DPC, dan DPRt.

Data Extraction & Merge: Mengambil kolom NIK, eKTA, Email, dan No. Telepon dari Data Master dan memasukkannya ke baris yang sesuai di Data Target.

Output Generation (Pembuatan Laporan):

Menghasilkan file Excel "Data_Lengkap_Sukses.xlsx".

Menghasilkan file Excel "Data_Gagal_Match.xlsx" (berisi data yang namanya typo atau wilayahnya tidak sinkron sehingga gagal ditarik datanya).

4. Alur Pengguna (User Flow)
Persiapan: Pengguna mengunduh Data Master dari web pusat format Excel, dan menyiapkan Data Target di folder yang sama.

Eksekusi: Pengguna menjalankan script Python.

Proses Latar Belakang:

Python memuat kedua file.

Melakukan pembersihan spasi dan huruf kapital di kolom Nama, DPD, DPC, DPRt.

Memasukkan data NIK, eKTA, dll ke Data Target.

Selesai: Python menampilkan notifikasi "Proses Selesai: X data berhasil, Y data gagal".

Tindak Lanjut: Pengguna mengambil file hasil yang sudah lengkap, lalu mengecek file gagal untuk diperbaiki manual (misal karena singkatan Minsel vs Minahasa Selatan).

5. Spesifikasi Teknis (Technical Specs)
Bahasa Pemrograman: Python 3.x

Library Utama: pandas (untuk manipulasi Dataframe Excel) dan openpyxl (untuk membaca dan menulis format .xlsx).

Format Input/Output: .xlsx atau .csv

Kebutuhan Hardware: Komputer standar perkantoran (RAM minimal 4GB/8GB cukup untuk memproses 20.000 - 50.000 baris menggunakan pandas).

6. Asumsi dan Batasan (Assumptions & Constraints)
Asumsi Penamaan Kolom: Header baris pertama pada kedua file Excel harus konsisten sebelum script dijalankan (misal: penulisan header harus sama-sama "NAMA", "DPD", bukan yang satu "Nama Pengurus" yang satu "NAMA").

Asumsi Hierarki Wilayah: Data target sudah harus memisahkan lokasi ke dalam kolom DPD, DPC, dan DPRt yang terpisah, tidak digabung dalam satu kalimat/kolom "Alamat".

Batasan Typo: Sistem tidak menggunakan Fuzzy String Matching (kecerdasan buatan untuk menebak typo parah). Jika data pusat tertulis "Fajrikun" dan data target "Fajrikoen", sistem akan menganggapnya gagal match dan melemparnya ke file "Data_Gagal_Match.xlsx".

7. Kriteria Sukses (Success Metrics)
Script berhasil dijalankan tanpa error (crash).

Waktu pemrosesan 20.000 data di bawah 3 menit.

Minimal 85% - 90% data berhasil terisi otomatis, menyisakan maksimal 10% - 15% untuk ditinjau manual akibat typo ejaan nama atau wilayah.