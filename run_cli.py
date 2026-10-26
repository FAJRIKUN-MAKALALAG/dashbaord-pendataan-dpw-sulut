import os
import sys
import pandas as pd
from tabulate import tabulate
from core.matcher import DataMatcherEngine
from core.exporter import export_results_to_excel
from core.sample_generator import generate_samples

def main():
    try:
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("\n" + "=" * 70)
    print(" [AUTO-ENRICHMENT DATA SYSTEM - CLI RUNNER]")
    print("  NasDem Pendataan Otomatis Anggota & Pengurus")
    print("=" * 70 + "\n")


    input_dir = os.path.join(os.path.dirname(__file__), 'input')
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Cek file yang tersedia
    files = [f for f in os.listdir(input_dir) if f.endswith(('.xlsx', '.xls', '.csv'))]
    
    if not files or len(files) < 2:
        print("💡 File data real belum lengkap di folder 'input/'.")
        print("👉 Silakan letakkan file Data Master dan Data Target (format .xlsx atau .csv) ke dalam folder:")
        print(f"   {os.path.abspath(input_dir)}")
        print("\nLalu jalankan kembali: python run_cli.py")
        sys.exit(0)


    # Identifikasi master dan target
    master_candidates = [f for f in files if any(k in f.lower() for k in ['master', 'pusat', 'digital'])]
    target_candidates = [f for f in files if any(k in f.lower() for k in ['target', 'dpc', 'dpd', 'dprt', 'lokal', 'mentah', 'tareran'])]

    master_file = master_candidates[0] if master_candidates else files[0]
    target_file = target_candidates[0] if target_candidates else (files[1] if len(files) > 1 else files[0])

    print(f"📂 File Master : {master_file}")
    print(f"📂 File Target : {target_file}")
    print("-" * 70)

    m_path = os.path.join(input_dir, master_file)
    t_path = os.path.join(input_dir, target_file)

    print("⏳ Membaca dan mendeteksi header secara cerdas...")
    from app import smart_load_file
    master_df, master_meta = smart_load_file(m_path)
    target_df, target_meta = smart_load_file(t_path)

    print(f"📊 Total Master: {len(master_df)} baris | Total Target: {len(target_df)} baris")
    if target_meta.get('kecamatan'):
        print(f"📍 Terdeteksi Wilayah Target: Kecamatan {target_meta['kecamatan']}")

    # Jalankan Matching Multi-Tier
    print("⚡ Menjalankan pencocokan multi-tier (NIK, E-KTA, Nama, & Wilayah)...")
    engine = DataMatcherEngine(master_df, target_df, target_metadata=target_meta)
    summary = engine.process()


    print("\n" + "=" * 70)
    print(" 📈 RINGKASAN HASIL PENCOCOKAN")
    print("=" * 70)
    print(f" • Total Data Target       : {summary['total_target']} baris")
    print(f" • Berhasil Diperkaya      : {summary['matched_count']} baris ({summary['match_rate_pct']}%)")
    print(f" • Gagal / Belum Lengkap   : {summary['unmatched_count']} baris")
    print(f" • Waktu Eksekusi          : {summary['elapsed_seconds']} detik")
    print("=" * 70 + "\n")

    # Tampilkan preview tabel di CLI sebelum ekspor
    print("🔍 PREVIEW TABEL DATA BERHASIL DIPERKAYA (Top 5 baris):")
    if engine.matched_df is not None and not engine.matched_df.empty:
        preview_cols = [c for c in engine.matched_df.columns if not c.startswith('_')][:7]
        print(tabulate(engine.matched_df[preview_cols].head(5), headers='keys', tablefmt='fancy_grid', showindex=False))
    else:
        print(" (Tidak ada data match)")

    print("\n🔍 PREVIEW TABEL DATA GAGAL MATCH (Top 5 baris):")
    if engine.unmatched_df is not None and not engine.unmatched_df.empty:
        preview_cols = [c for c in engine.unmatched_df.columns if not c.startswith('_')][:6]
        if 'Keterangan_Gagal' in engine.unmatched_df.columns and 'Keterangan_Gagal' not in preview_cols:
            preview_cols.append('Keterangan_Gagal')
        print(tabulate(engine.unmatched_df[preview_cols].head(5), headers='keys', tablefmt='fancy_grid', showindex=False))
    else:
        print(" (Semua data berhasil cocok 100%!)")

    print("\n" + "-" * 70)
    konfirm = input("💾 Konfirmasi: Apakah Anda ingin mengekspor hasil ke Excel sekarang? [Y/n]: ").strip().lower()
    if konfirm in ['', 'y', 'ya', 'yes']:
        res = export_results_to_excel(engine.matched_df, engine.unmatched_df, output_dir, original_target_path=t_path)
        print("\n✅ File Excel berhasil diperbarui:")
        if res.get('template_file'):
            print(f" 🌟 File Template Asli Lengkap : {res['template_file']}")
        print(f" 📄 File Laporan Sukses        : {res['sukses_file']}")
        if len(engine.unmatched_df) > 0:
            print(f" 📄 File Laporan Gagal         : {res['gagal_file']}")
        print("\n🎉 Proses Selesai dengan sukses! Format file asli 100% dipertahankan.")
    else:
        print("❌ Ekspor dibatalkan.")


if __name__ == '__main__':
    main()
