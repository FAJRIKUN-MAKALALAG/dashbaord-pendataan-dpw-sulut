import re
import pandas as pd
from typing import Any

def clean_text(val: Any) -> str:
    """
    Membersihkan teks dari whitespace berlebih, karakter non-breaking (\xa0),
    dan mengonversi nilai kosong (NaN/None) menjadi string kosong "".
    """
    if pd.isna(val) or val is None:
        return ""
    
    text = str(val).strip()
    # Ganti non-breaking space dan variasi whitespace unicode lainnya
    text = text.replace('\xa0', ' ').replace('\u200b', '').replace('\t', ' ')
    # Hapus spasi berlebih menjadi 1 spasi
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_nik(val: Any) -> str:
    """
    Membersihkan dan memformat NIK menjadi string numerik murni.
    Mencegah bug notasi ilmiah Excel (misal 7.102E+15) atau float .0.
    """
    if pd.isna(val) or val is None:
        return ""
    
    text = str(val).strip()
    # Jika float berakhir dengan .0, hapus
    if text.endswith('.0'):
        text = text[:-2]
    
    # Ambil hanya karakter angka
    digits = re.sub(r'\D', '', text)
    return digits

def clean_phone(val: Any) -> str:
    """
    Membersihkan nomor telepon, menjaga angka 0 di depan,
    dan menghapus karakter non-digit kecuali tanda plus (+ jika ada di awal).
    """
    if pd.isna(val) or val is None:
        return ""
    
    text = str(val).strip()
    if text.endswith('.0'):
        text = text[:-2]
    
    # Hapus spasi dan strip
    text = re.sub(r'[\s\-\(\)]', '', text)
    # Jika diawali 62 atau +62, standarkan
    if text.startswith('+62'):
        text = '0' + text[3:]
    elif text.startswith('62'):
        text = '0' + text[2:]
    
    return text

def normalize_region_name(text: str) -> str:
    """
    Menormalkan nama wilayah untuk pencocokan kunci (composite key):
    - Huruf kecil
    - Hapus prefix umum seperti KAB., KABUPATEN, KOTA, KEC., KECAMATAN, KEL., KELURAHAN, DESA
    - Hapus tanda baca
    """
    cleaned = clean_text(text).lower()
    if not cleaned:
        return ""
    
    # Hapus prefix umum daerah agar match lebih toleran
    prefixes = [
        r'^kabupaten\s+', r'^kab\.\s*', r'^kab\s+',
        r'^kota\s+',
        r'^kecamatan\s+', r'^kec\.\s*', r'^kec\s+',
        r'^kelurahan\s+', r'^kel\.\s*', r'^kel\s+',
        r'^desa\s+'
    ]
    for p in prefixes:
        cleaned = re.sub(p, '', cleaned)
    
    # Hapus tanda baca
    cleaned = re.sub(r'[^a-z0-9\s]', '', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()

def normalize_person_name(name: str) -> str:
    """
    Menormalkan nama orang untuk pencocokan kunci:
    - Lowercase
    - Hapus tanda baca (titik, koma, kutip)
    - Hapus spasi ganda
    """
    cleaned = clean_text(name).lower()
    if not cleaned:
        return ""
    # Hapus tanda baca umum di nama seperti Drs., S.H., M.Si dsb
    cleaned = re.sub(r'[\.,\'"\-]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def build_composite_key(row: pd.Series, name_col: str, dpd_col: str, dpc_col: str, dprt_col: str) -> str:
    """
    Membangun Composite Key dari 4 parameter:
    nama_norm | dpd_norm | dpc_norm | dprt_norm
    """
    n = normalize_person_name(row.get(name_col, ''))
    dpd = normalize_region_name(row.get(dpd_col, ''))
    dpc = normalize_region_name(row.get(dpc_col, ''))
    dprt = normalize_region_name(row.get(dprt_col, ''))
    
    return f"{n}___{dpd}___{dpc}___{dprt}"
