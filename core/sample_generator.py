import os
import random
import pandas as pd

def generate_samples(input_dir: str = "input") -> dict:
    """Membuat file simulasi data master dan target untuk testing langsung."""
    os.makedirs(input_dir, exist_ok=True)
    
    dpd_list = [
        ("Minahasa Selatan", [
            ("Amurang", ["Buyungon", "Uwuran Satu", "Uwuran Dua", "Ranoyapo"]),
            ("Tenga", ["Tenga", "Ranoiapo", "Pakuweru", "Sapa"]),
            ("Motoling", ["Motoling", "Motoling Dua", "Picuan", "Lalumpe"])
        ]),
        ("Kota Manado", [
            ("Wenang", ["Titiwungen Selatan", "Bumi Beringin", "Tikala Kumaraka", "Kompleks"]),
            ("Malalayang", ["Malalayang Satu", "Bahu", "Winangun", "Karegesan"]),
            ("Sario", ["Sario", "Sario Kotabaru", "Sario Tumpaan"])
        ]),
        ("Kota Kotamobagu", [
            ("Kotamobagu Barat", ["Mogolaing", "Molinow", "Mongkonai", "Gogagoman"]),
            ("Kotamobagu Timur", ["Kotobangon", "Matali", "Motoboi Besar", "Kobo Besar"])
        ]),
        ("Minahasa", [
            ("Tondano Barat", ["Rerewokan", "Roong", "Rinegetan", "Wawalintouan"]),
            ("Kakas", ["Sendangan", "Toulimembet", "Tumpaan"])
        ])
    ]

    first_names = [
        "Fajri", "Christian", "Novita", "Michael", "Meiske", "Steven", "Grace",
        "Hendy", "Vicky", "Priscilia", "Rendy", "Dewi", "Ferry", "Syalomitha",
        "Rian", "Megumi", "Rolando", "Astrid", "Billy", "Patricia", "Jordy",
        "Gabriella", "Aldo", "Yolanda", "Erick", "Stephanie", "Frangky", "Angel"
    ]
    last_names = [
        "Makalalag", "Runtuwene", "Lumentut", "Mokoginta", "Tendean", "Kandouw",
        "Wongkar", "Sumendap", "Paat", "Palar", "Lomban", "Kojongian", "Manoppo",
        "Senduk", "Pangemanan", "Dondokambey", "Polii", "Mamahit", "Mandagi"
    ]
    positions = [
        "Ketua", "Sekretaris", "Bendahara", "Wakil Ketua OKK", "Wakil Sekretaris",
        "Anggota", "Kader Pratama", "Koordinator Wilayah", "Bappilu"
    ]

    master_rows = []
    target_rows = []
    
    # 1. Bangun Data Master (60 orang dengan data lengkap)
    random.seed(42)
    nik_counter = 7105011001900001
    kta_counter = 991000123000
    
    idx = 0
    for dpd_name, dpc_sub in dpd_list:
        for dpc_name, dprt_sub in dpc_sub:
            for dprt_name in dprt_sub[:3]:
                idx += 1
                fn = random.choice(first_names)
                ln = random.choice(last_names)
                full_name = f"{fn} {ln}"
                
                nik = str(nik_counter)
                nik_counter += 17
                
                kta = f"NASDEM-{kta_counter}"
                kta_counter += 23
                
                hp = f"0812{random.randint(10000000, 99999999)}"
                email = f"{fn.lower()}.{ln.lower()}{random.randint(10,99)}@gmail.com"
                jabatan = random.choice(positions)
                
                master_rows.append({
                    'NAMA': full_name,
                    'DPD': f"Kabupaten {dpd_name}" if "Kota" not in dpd_name else dpd_name,
                    'DPC': f"Kecamatan {dpc_name}",
                    'DPRt': f"Kelurahan {dprt_name}",
                    'NIK': nik,
                    'eKTA': kta,
                    'No_Telepon': hp,
                    'Email': email,
                    'Jabatan': jabatan
                })

    master_df = pd.DataFrame(master_rows)

    # 2. Bangun Data Target (40 orang yang belum lengkap)
    # 30 orang diambil dari master (tetapi NIK/eKTA/Telp kosong, nama divariasikan spasi/huruf besar)
    for i in range(min(32, len(master_rows))):
        m = master_rows[i]
        
        # Variasi formatting untuk menguji cleaning engine
        raw_name = m['NAMA']
        if i % 3 == 0:
            raw_name = f"  {raw_name.upper()}  " # spasi berlebih dan huruf besar
        elif i % 4 == 0:
            raw_name = raw_name.lower()
            
        target_rows.append({
            'NAMA': raw_name,
            'DPD': m['DPD'].replace("Kabupaten ", "").replace("Kota ", "").strip(), # tanpa prefix
            'DPC': m['DPC'].replace("Kecamatan ", "").strip(),
            'DPRt': m['DPRt'].replace("Kelurahan ", "").strip(),
            'NIK': '', # Kosong, siap ditarik
            'eKTA': '', # Kosong, siap ditarik
            'No_Telepon': '', # Kosong, siap ditarik
            'Email': '', # Kosong, siap ditarik
            'Jabatan': m['Jabatan']
        })

    # Tambahkan 5 orang yang ada di Master tapi beda DPC/DPRt (untuk simulasi gagal match karena wilayah)
    if len(master_rows) > 35:
        m = master_rows[33]
        target_rows.append({
            'NAMA': m['NAMA'],
            'DPD': m['DPD'],
            'DPC': 'Kecamatan Tidak Terdaftar',
            'DPRt': 'Desa Fiktif',
            'NIK': '', 'eKTA': '', 'No_Telepon': '', 'Email': '', 'Jabatan': 'Pengurus'
        })

    # Tambahkan 3 orang yang sama sekali tidak ada di Master (untuk simulasi nama asing/baru)
    target_rows.append({
        'NAMA': 'Budi Santoso Antariksa',
        'DPD': 'Kota Manado',
        'DPC': 'Wenang',
        'DPRt': 'Tikala Kumaraka',
        'NIK': '', 'eKTA': '', 'No_Telepon': '', 'Email': '', 'Jabatan': 'Anggota Baru'
    })
    target_rows.append({
        'NAMA': 'Megawati Sukmawati',
        'DPD': 'Minahasa Selatan',
        'DPC': 'Amurang',
        'DPRt': 'Buyungon',
        'NIK': '', 'eKTA': '', 'No_Telepon': '', 'Email': '', 'Jabatan': 'Kader Baru'
    })

    target_df = pd.DataFrame(target_rows)

    path_master = os.path.join(input_dir, "data_master_sample.xlsx")
    path_target = os.path.join(input_dir, "data_target_sample.xlsx")

    master_df.to_excel(path_master, index=False, engine='openpyxl')
    target_df.to_excel(path_target, index=False, engine='openpyxl')

    return {
        'master_path': path_master,
        'target_path': path_target,
        'master_rows': len(master_df),
        'target_rows': len(target_df)
    }
