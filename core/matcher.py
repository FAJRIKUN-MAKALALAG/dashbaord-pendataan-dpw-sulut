import time
import re
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from .cleaner import (
    clean_text, clean_nik, clean_phone,
    normalize_person_name, normalize_region_name
)

COLUMN_SYNONYMS = {
    'nama': [
        'nama lengkap (sesuai ktp)', 'nama lengkap (sesuai ktp)', 'nama lengkap',
        'nama', 'nama pengurus', 'name', 'full name', 'nama anggota'
    ],
    'dpd': [
        'kab/kota', 'kabupaten/kota', 'kabupaten', 'kota', 'dpd',
        'wilayah dpd', 'tingkat dpd'
    ],
    'dpc': [
        'kecamatan', 'dpc', 'wilayah dpc', 'tingkat dpc'
    ],
    'dprt': [
        'kelurahan', 'desa', 'kelurahan/desa', 'desa/kelurahan', 'dprt',
        'ranting', 'tingkat dprt', 'wilayah dprt'
    ],
    'nik': [
        'nomor ktp', 'no. nik', 'no nik', 'nik', 'no ktp', 'nomor nik',
        'ktp', 'no_ktp', 'no_nik'
    ],
    'ekta': [
        'nomor e-kta', 'e-kta nasdem', 'nomor ekta', 'ekta', 'kta', 'no kta',
        'no. kta', 'nomor kta', 'id anggota', 'no_kta', 'e_kta', 'e-kta'
    ],
    'telepon': [
        'no hp', 'no telepon', 'no telp', 'no. hp', 'telepon', 'phone',
        'no. telepon', 'hp', 'no_hp', 'kontak', 'handphone'
    ],
    'email': [
        'email', 'surel', 'e-mail'
    ],
    'jabatan': [
        'jabatan pengurus', 'jabatan', 'posisi', 'struktural'
    ]
}

def detect_column(df_columns: List[str], target_key: str) -> Optional[str]:
    """Mendeteksi nama kolom yang paling cocok dari daftar sinonim."""
    cols_clean = {c: clean_text(c).lower() for c in df_columns}
    synonyms = COLUMN_SYNONYMS.get(target_key, [target_key])
    
    # 1. Exact match dengan key
    for orig, cleaned in cols_clean.items():
        if cleaned == target_key:
            return orig
            
    # 2. Exact match dengan salah satu sinonim
    for s in synonyms:
        for orig, cleaned in cols_clean.items():
            if cleaned == s:
                return orig
                
    # 3. Substring match
    for s in synonyms:
        for orig, cleaned in cols_clean.items():
            if s in cleaned or cleaned in s:
                return orig
                
    return None

def detect_all_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Mendeteksi pemetaan kolom standar untuk sebuah DataFrame."""
    mapping = {}
    for key in ['nama', 'dpd', 'dpc', 'dprt', 'nik', 'ekta', 'telepon', 'email', 'jabatan']:
        mapping[key] = detect_column(df.columns.tolist(), key)
    return mapping

class DataMatcherEngine:
    def __init__(self, master_df: pd.DataFrame, target_df: pd.DataFrame,
                 target_metadata: Optional[Dict[str, Any]] = None,
                 custom_cols_master: Optional[Dict[str, str]] = None,
                 custom_cols_target: Optional[Dict[str, str]] = None):
        self.master_df = master_df.copy()
        self.target_df = target_df.copy()
        self.target_metadata = target_metadata or {}
        
        # Deteksi kolom
        self.master_cols = custom_cols_master or detect_all_columns(self.master_df)
        self.target_cols = custom_cols_target or detect_all_columns(self.target_df)
        
        self.matched_df: Optional[pd.DataFrame] = None
        self.unmatched_df: Optional[pd.DataFrame] = None
        self.summary: Dict[str, Any] = {}

    def validate_columns(self) -> Tuple[bool, str]:
        """Memastikan minimal kolom Nama terdeteksi pada kedua file."""
        if not self.master_cols.get('nama'):
            return False, "Kolom 'NAMA' tidak terdeteksi pada Data Master."
        if not self.target_cols.get('nama'):
            return False, "Kolom 'NAMA' (atau Nama Lengkap) tidak terdeteksi pada Data Target."
        return True, ""

    def process(self) -> Dict[str, Any]:
        """
        Menjalankan Multi-Tier Matching Engine:
        Tier 1: NIK (Nomor KTP)
        Tier 2: E-KTA
        Tier 3: Nama + Kecamatan/Wilayah
        Tier 4: Nama Token + Kecamatan
        Tier 5: Nama Lengkap
        """
        start_time = time.time()
        
        valid, msg = self.validate_columns()
        if not valid:
            raise ValueError(msg)

        m_nama_col = self.master_cols['nama']
        m_nik_col = self.master_cols.get('nik')
        m_kta_col = self.master_cols.get('ekta')
        m_dpc_col = self.master_cols.get('dpc')
        m_dpd_col = self.master_cols.get('dpd')
        m_telp_col = self.master_cols.get('telepon')
        m_email_col = self.master_cols.get('email')

        t_nama_col = self.target_cols['nama']
        t_nik_col = self.target_cols.get('nik')
        t_kta_col = self.target_cols.get('ekta')
        t_dpc_col = self.target_cols.get('dpc')
        t_telp_col = self.target_cols.get('telepon')
        t_email_col = self.target_cols.get('email')

        # 1. Persiapkan Master Data Lookup
        master_clean = self.master_df.copy()
        master_clean['_clean_nama'] = master_clean[m_nama_col].apply(normalize_person_name)
        
        if m_nik_col:
            master_clean['_clean_nik'] = master_clean[m_nik_col].apply(clean_nik)
            # Filter baris yang punya NIK valid (biasanya 16 digit)
            valid_nik_master = master_clean[master_clean['_clean_nik'] != ''].drop_duplicates(subset=['_clean_nik'], keep='first')
            nik_lookup = valid_nik_master.set_index('_clean_nik')
        else:
            nik_lookup = pd.DataFrame()

        if m_kta_col:
            master_clean['_clean_kta'] = master_clean[m_kta_col].apply(clean_nik)
            valid_kta_master = master_clean[master_clean['_clean_kta'] != ''].drop_duplicates(subset=['_clean_kta'], keep='first')
            kta_lookup = valid_kta_master.set_index('_clean_kta')
        else:
            kta_lookup = pd.DataFrame()

        if m_dpc_col:
            master_clean['_clean_dpc'] = master_clean[m_dpc_col].astype(str).apply(normalize_region_name)
        else:
            master_clean['_clean_dpc'] = ""

        # Default kecamatan dari metadata target jika ada (misal judul header: KECAMATAN TARERAN)
        default_kecamatan = normalize_region_name(self.target_metadata.get('kecamatan', ''))

        matched_records = []
        unmatched_records = []

        # 2. Iterasi Data Target
        for idx, row in self.target_df.iterrows():
            row_dict = row.to_dict()
            raw_nama = clean_text(row.get(t_nama_col, ''))
            norm_nama = normalize_person_name(raw_nama)
            
            raw_nik = clean_nik(row.get(t_nik_col, '')) if t_nik_col else ''
            raw_kta = clean_nik(row.get(t_kta_col, '')) if t_kta_col else ''
            
            # Deteksi kecamatan baris target
            if t_dpc_col and clean_text(row.get(t_dpc_col, '')):
                row_kec = normalize_region_name(row.get(t_dpc_col, ''))
            else:
                row_kec = default_kecamatan

            matched_master_row = None
            match_source = None

            # TIER 1: Match by NIK
            if raw_nik and not nik_lookup.empty and raw_nik in nik_lookup.index:
                matched_master_row = nik_lookup.loc[raw_nik]
                match_source = "NIK (Nomor KTP)"

            # TIER 2: Match by E-KTA
            if matched_master_row is None and raw_kta and not kta_lookup.empty and raw_kta in kta_lookup.index:
                matched_master_row = kta_lookup.loc[raw_kta]
                match_source = "Nomor E-KTA"

            # TIER 3: Match by Nama + Kecamatan
            if matched_master_row is None and norm_nama:
                if row_kec:
                    # Cari di kecamatan yang sama
                    kec_candidates = master_clean[master_clean['_clean_dpc'] == row_kec]
                    # Exact nama match di kecamatan ini
                    exact_cand = kec_candidates[kec_candidates['_clean_nama'] == norm_nama]
                    if not exact_cand.empty:
                        matched_master_row = exact_cand.iloc[0]
                        match_source = "Nama Lengkap & Kecamatan"
                    else:
                        # Token containment match (mengatasi nama tengah disingkat, misal Denny W Kondoj vs Denny Kondoj)
                        target_tokens = norm_nama.split()
                        if len(target_tokens) >= 2:
                            for _, c_row in kec_candidates.iterrows():
                                c_tokens = c_row['_clean_nama'].split()
                                if target_tokens[0] in c_tokens and target_tokens[-1] in c_tokens:
                                    matched_master_row = c_row
                                    match_source = "Nama Mirip & Kecamatan"
                                    break

            # TIER 4: Match by Nama Global di Master
            if matched_master_row is None and norm_nama:
                global_exact = master_clean[master_clean['_clean_nama'] == norm_nama]
                if not global_exact.empty:
                    matched_master_row = global_exact.iloc[0]
                    match_source = "Nama Lengkap (Database Pusat)"

            # Jika series/dataframe
            if isinstance(matched_master_row, pd.DataFrame):
                matched_master_row = matched_master_row.iloc[0]

            # 3. Penarikan Data (Enrichment)
            if matched_master_row is not None:
                enriched_fields = []

                # NIK
                if m_nik_col:
                    val_nik = clean_nik(matched_master_row.get(m_nik_col, ''))
                    if val_nik:
                        col_target_nik = t_nik_col or 'No. NIK'
                        current_nik = clean_nik(row_dict.get(col_target_nik, ''))
                        if current_nik != val_nik:
                            row_dict[col_target_nik] = val_nik
                            enriched_fields.append("NIK")

                # E-KTA
                if m_kta_col:
                    val_kta = clean_nik(matched_master_row.get(m_kta_col, ''))
                    if val_kta:
                        col_target_kta = t_kta_col or 'E-KTA NasDem'
                        current_kta = clean_nik(row_dict.get(col_target_kta, ''))
                        if current_kta != val_kta:
                            row_dict[col_target_kta] = val_kta
                            enriched_fields.append("E-KTA")

                # Telepon / HP
                if m_telp_col:
                    val_telp = clean_phone(matched_master_row.get(m_telp_col, ''))
                    if val_telp:
                        col_target_telp = t_telp_col or 'No Telepon'
                        current_telp = clean_phone(row_dict.get(col_target_telp, ''))
                        if not current_telp or current_telp != val_telp:
                            row_dict[col_target_telp] = val_telp
                            enriched_fields.append("No Telepon")

                # Email
                if m_email_col:
                    val_email = clean_text(matched_master_row.get(m_email_col, ''))
                    if val_email:
                        col_target_email = t_email_col or 'Email'
                        current_email = clean_text(row_dict.get(col_target_email, ''))
                        if not current_email:
                            row_dict[col_target_email] = val_email
                            enriched_fields.append("Email")

                row_dict['_status'] = 'BERHASIL'
                row_dict['_metode_match'] = match_source
                row_dict['_kolom_diperkaya'] = ", ".join(enriched_fields) if enriched_fields else "Sudah Lengkap"
                matched_records.append(row_dict)
            else:
                # Gagal Match
                alasan = "Nama dan NIK/E-KTA tidak ditemukan pada database pusat."
                if norm_nama:
                    # Cek apakah nama ada di kecamatan lain
                    other_cand = master_clean[master_clean['_clean_nama'].str.contains(norm_nama.split()[0], na=False)]
                    if not other_cand.empty:
                        kec_found = other_cand.iloc[0].get(m_dpc_col, 'wilayah lain')
                        alasan = f"Nama depan ditemukan di {kec_found}, tetapi wilayah/nama lengkap tidak cocok."

                row_dict['_status'] = 'GAGAL'
                row_dict['Keterangan_Gagal'] = alasan
                unmatched_records.append(row_dict)

        self.matched_df = pd.DataFrame(matched_records)
        self.unmatched_df = pd.DataFrame(unmatched_records)

        elapsed = round(time.time() - start_time, 2)
        total_target = len(self.target_df)
        total_matched = len(self.matched_df)
        total_unmatched = len(self.unmatched_df)
        rate = round((total_matched / total_target * 100), 2) if total_target > 0 else 0

        self.summary = {
            'total_target': total_target,
            'total_master': len(self.master_df),
            'matched_count': total_matched,
            'unmatched_count': total_unmatched,
            'match_rate_pct': rate,
            'elapsed_seconds': elapsed,
            'master_columns': self.master_cols,
            'target_columns': self.target_cols,
            'target_metadata': self.target_metadata
        }

        return self.summary
