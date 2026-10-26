import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from typing import Dict, Any, Optional

def export_enriched_original_template(original_target_path: str, matched_df: pd.DataFrame, output_dir: str) -> str:
    """
    Menyimpan hasil langsung ke salinan template file target asli pengguna,
    sehingga format, font, merge cell, dan layout asli tidak berubah sama sekali.
    """
    os.makedirs(output_dir, exist_ok=True)
    orig_filename = os.path.basename(original_target_path)
    base_name, ext = os.path.splitext(orig_filename)
    
    # Gunakan nama file yang sama dengan file target asli pengguna
    output_filename = f"{orig_filename}"
    output_path = os.path.join(output_dir, output_filename)
    
    wb = openpyxl.load_workbook(original_target_path)
    ws = wb.active
    
    # 1. Cari baris header
    header_row_num = 1
    for r in range(1, 10):
        vals = [str(ws.cell(r, c).value or '').lower() for c in range(1, ws.max_column + 1)]
        if any('nama' in v for v in vals):
            header_row_num = r
            break
            
    # 2. Pemetaan kolom header ke indeks kolom Excel (1-based)
    col_map = {}
    for c in range(1, ws.max_column + 1):
        val = str(ws.cell(header_row_num, c).value or '').strip().lower()
        if val:
            col_map[val] = c
            
    # 3. Masukkan data yang diperkaya langsung ke sel template asli
    if matched_df is not None and not matched_df.empty:
        for idx, m_row in matched_df.iterrows():
            excel_row = header_row_num + 1 + idx
            
            # Isi NIK
            for k in ['no. nik', 'nomor ktp', 'nik', 'no nik']:
                if k in col_map and m_row.get('No. NIK'):
                    c_idx = col_map[k]
                    cell = ws.cell(excel_row, c_idx)
                    cell.value = str(m_row['No. NIK'])
                    cell.number_format = '@'
                    break
                    
            # Isi E-KTA
            for k in ['e-kta nasdem', 'nomor e-kta', 'ekta', 'kta', 'nomor ekta']:
                if k in col_map and m_row.get('E-KTA NasDem'):
                    c_idx = col_map[k]
                    cell = ws.cell(excel_row, c_idx)
                    cell.value = str(m_row['E-KTA NasDem'])
                    cell.number_format = '@'
                    break
                    
            # Isi Email
            for k in ['email', 'surel']:
                if k in col_map and m_row.get('Email'):
                    c_idx = col_map[k]
                    cell = ws.cell(excel_row, c_idx)
                    cell.value = str(m_row['Email'])
                    break
                    
            # Isi No Telepon
            for k in ['no telepon', 'no hp', 'telepon', 'no telp', 'phone']:
                if k in col_map and m_row.get('No Telepon'):
                    c_idx = col_map[k]
                    cell = ws.cell(excel_row, c_idx)
                    cell.value = str(m_row['No Telepon'])
                    cell.number_format = '@'
                    break

    wb.save(output_path)
    return output_path

def style_excel_sheet(ws, is_success: bool = True):
    """Menerapkan styling profesional pada worksheet openpyxl."""
    header_color = "1E3A8A" if is_success else "881337"
    header_fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )
    
    for col_num in range(1, ws.max_column + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 28

    for row in range(2, ws.max_row + 1):
        ws.row_dimensions[row].height = 20
        bg_color = "F8FAFC" if row % 2 == 0 else "FFFFFF"
        row_fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
        
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=row, column=col)
            cell.border = thin_border
            cell.fill = row_fill
            cell.font = Font(name="Arial", size=9)
            
            header_name = str(ws.cell(row=1, column=col).value or "").lower()
            if any(k in header_name for k in ['nik', 'ktp', 'hp', 'telp', 'phone', 'telepon', 'kta', 'ekta']):
                cell.number_format = '@'
                if cell.value is not None:
                    cell.value = str(cell.value)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(vertical="center")

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 40)

def export_results_to_excel(matched_df: pd.DataFrame, unmatched_df: pd.DataFrame,
                           output_dir: str, original_target_path: Optional[str] = None) -> Dict[str, str]:
    """
    Mengekspor data hasil matching:
    1. Template Asli Target yang telah diisi langsung (mempertahankan font, warna, judul, dll 100%)
    2. Data_Lengkap_Sukses.xlsx
    3. Data_Gagal_Match.xlsx
    """
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    # 1. Ekspor ke Template Asli Target jika ada
    if original_target_path and os.path.exists(original_target_path):
        template_file = export_enriched_original_template(original_target_path, matched_df, output_dir)
        results['template_file'] = template_file
        results['template_filename'] = os.path.basename(template_file)

    # 2. Ekspor standar Data_Lengkap_Sukses.xlsx
    df_sukses = matched_df.copy() if matched_df is not None and not matched_df.empty else pd.DataFrame()
    if not df_sukses.empty:
        if '_kolom_diperkaya' in df_sukses.columns:
            df_sukses.rename(columns={'_kolom_diperkaya': 'Kolom_Ditambahkan'}, inplace=True)
        if '_metode_match' in df_sukses.columns:
            df_sukses.rename(columns={'_metode_match': 'Metode_Pencocokan'}, inplace=True)
        if '_status' in df_sukses.columns:
            df_sukses.drop(columns=['_status'], inplace=True)
            
    df_gagal = unmatched_df.copy() if unmatched_df is not None and not unmatched_df.empty else pd.DataFrame()
    if not df_gagal.empty:
        if '_status' in df_gagal.columns:
            df_gagal.drop(columns=['_status'], inplace=True)
        if 'Keterangan_Gagal' in df_gagal.columns:
            cols = [c for c in df_gagal.columns if c != 'Keterangan_Gagal']
            df_gagal = df_gagal[['Keterangan_Gagal'] + cols]

    path_sukses = os.path.join(output_dir, "Data_Lengkap_Sukses.xlsx")
    path_gagal = os.path.join(output_dir, "Data_Gagal_Match.xlsx")

    if not df_sukses.empty:
        df_sukses.to_excel(path_sukses, index=False, engine='openpyxl')
        wb_sukses = openpyxl.load_workbook(path_sukses)
        style_excel_sheet(wb_sukses.active, is_success=True)
        wb_sukses.save(path_sukses)
    else:
        wb = openpyxl.Workbook()
        wb.active.title = "Data Kosong"
        wb.save(path_sukses)

    if not df_gagal.empty:
        df_gagal.to_excel(path_gagal, index=False, engine='openpyxl')
        wb_gagal = openpyxl.load_workbook(path_gagal)
        style_excel_sheet(wb_gagal.active, is_success=False)
        wb_gagal.save(path_gagal)
    else:
        wb = openpyxl.Workbook()
        wb.active.title = "Data Kosong"
        wb.save(path_gagal)

    results['sukses_file'] = path_sukses
    results['gagal_file'] = path_gagal

    return results
