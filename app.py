import os
import math
import time
import re
import shutil
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory
from core.matcher import DataMatcherEngine, detect_all_columns
from core.exporter import export_results_to_excel
from core.sample_generator import generate_samples

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'input')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Multi-tenant user session state (terisolasi per-klien / per-browser)
user_sessions = {}

def get_session_id():
    """Mengambil session ID unik dari Header HTTP, Query String, atau Cookie."""
    sid = request.headers.get('X-Session-Id') or request.args.get('session_id')
    if not sid:
        sid = request.cookies.get('nasdem_session_id')
    if not sid:
        sid = 'default'
    # Sanitize agar aman untuk penamaan folder filesystem
    clean_sid = re.sub(r'[^a-zA-Z0-9_\-]', '', str(sid))[:64]
    return clean_sid or 'default'

def get_session_data(sid=None):
    """Mengambil data sesi memori untuk klien tertentu."""
    if sid is None:
        sid = get_session_id()
    if sid not in user_sessions:
        user_sessions[sid] = {
            'master_df': None,
            'target_df': None,
            'master_path': None,
            'target_path': None,
            'master_meta': {},
            'target_meta': {},
            'matched_df': None,
            'unmatched_df': None,
            'summary': None,
            'engine': None,
            'last_active': time.time()
        }
    else:
        user_sessions[sid]['last_active'] = time.time()
    return user_sessions[sid]

def get_session_dirs(sid=None):
    """Menyiapkan direktori penyimpanan terisolasi untuk masing-masing pengguna."""
    if sid is None:
        sid = get_session_id()
    u_dir = os.path.join(app.config['UPLOAD_FOLDER'], sid)
    o_dir = os.path.join(app.config['OUTPUT_FOLDER'], sid)
    os.makedirs(u_dir, exist_ok=True)
    os.makedirs(o_dir, exist_ok=True)
    return u_dir, o_dir

def cleanup_old_sessions(max_age_seconds=86400):
    """Membersihkan sesi dan file sementara yang sudah tidak aktif lebih dari 24 jam."""
    now = time.time()
    expired = [sid for sid, s in user_sessions.items() if (now - s.get('last_active', now)) > max_age_seconds]
    for sid in expired:
        user_sessions.pop(sid, None)
        u_dir = os.path.join(app.config['UPLOAD_FOLDER'], sid)
        o_dir = os.path.join(app.config['OUTPUT_FOLDER'], sid)
        for d in [u_dir, o_dir]:
            if os.path.exists(d):
                try: shutil.rmtree(d, ignore_errors=True)
                except Exception: pass


def smart_load_file(file_path: str):
    """
    Membaca file Excel atau CSV secara cerdas:
    1. Otomatis mendeteksi baris header jika baris awal berisi judul (misal baris 1 atau 2).
    2. Menangkap metadata wilayah (seperti KECAMATAN TARERAN).
    3. Memaksa pembacaan string murni untuk mencegah korupsi NIK dan nomor telepon.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(max_row=8, values_only=True))
        header_idx = 0
        metadata = {}
        
        keywords = ['nama', 'ktp', 'nik', 'jabatan', 'kecamatan', 'kab/kota', 'e-kta', 'ekta', 'kta', 'telepon', 'hp', 'email', 'no']
        
        for idx, r in enumerate(rows):
            vals = [str(c or '').lower().strip() for c in r]
            matched_kw = sum(1 for v in vals if any(k in v for k in keywords))
            if matched_kw >= 2:
                header_idx = idx
                break
            
            # Cek apakah baris memuat info wilayah
            full_text = ' '.join(vals).upper()
            if 'KECAMATAN' in full_text:
                m = re.search(r'KECAMATAN\s+([A-Z\s]+)', full_text)
                if m: metadata['kecamatan'] = m.group(1).strip()
            if 'KABUPATEN' in full_text or 'KAB.' in full_text:
                m = re.search(r'KAB(?:UPATEN|\.)\s+([A-Z\s]+)', full_text)
                if m: metadata['dpd'] = m.group(1).strip()

        df = pd.read_excel(file_path, skiprows=header_idx, dtype=str)
        df = df.dropna(how='all')
        return df, metadata
    elif ext == '.csv':
        df = pd.read_csv(file_path, dtype=str).dropna(how='all')
        return df, {}
    else:
        raise ValueError("Format file harus .xlsx, .xls, atau .csv")

def check_and_autoload_input_dir(sid=None):
    """Mengecek file sesi lokal pengguna atau default."""
    if sid is None:
        sid = get_session_id()
    session = get_session_data(sid)
    u_dir, _ = get_session_dirs(sid)
    
    files = [f for f in os.listdir(u_dir) if f.endswith(('.xlsx', '.xls', '.csv')) and not f.startswith('~$')]
    scan_dir = u_dir

    # Fallback ke root input/ jika folder sesi kosong (untuk pengujian offline/lokal)
    if not files and sid == 'default':
        root_dir = app.config['UPLOAD_FOLDER']
        files = [f for f in os.listdir(root_dir) if os.path.isfile(os.path.join(root_dir, f)) and f.endswith(('.xlsx', '.xls', '.csv')) and not f.startswith('~$')]
        scan_dir = root_dir
    
    if session['master_df'] is None:
        master_candidates = [f for f in files if any(k in f.lower() for k in ['master', 'pusat', 'digital'])]
        if master_candidates:
            m_path = os.path.join(scan_dir, master_candidates[0])
            try:
                df, meta = smart_load_file(m_path)
                session['master_df'] = df
                session['master_meta'] = meta
                session['master_path'] = m_path
            except Exception: pass

    if session['target_df'] is None:
        target_candidates = [f for f in files if any(k in f.lower() for k in ['target', 'dpc', 'dpd', 'dprt', 'pengurus', 'lokal', 'tareran'])]
        if target_candidates:
            t_path = os.path.join(scan_dir, target_candidates[0])
            try:
                df, meta = smart_load_file(t_path)
                session['target_df'] = df
                session['target_meta'] = meta
                session['target_path'] = t_path
            except Exception: pass


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    sid = get_session_id()
    cleanup_old_sessions()
    check_and_autoload_input_dir(sid)
    session = get_session_data(sid)
    
    has_master = session['master_df'] is not None
    has_target = session['target_df'] is not None
    has_processed = session['matched_df'] is not None
    
    return jsonify({
        'session_id': sid,
        'has_master': has_master,
        'has_target': has_target,
        'has_processed': has_processed,
        'master_filename': os.path.basename(session['master_path']) if session.get('master_path') else '',
        'target_filename': os.path.basename(session['target_path']) if session.get('target_path') else '',
        'master_rows': len(session['master_df']) if has_master else 0,
        'target_rows': len(session['target_df']) if has_target else 0,
        'summary': session['summary']
    })

@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    """Menghapus salah satu file (master atau target) dari sesi pengguna saat ini."""
    try:
        sid = get_session_id()
        session = get_session_data(sid)
        data = request.get_json() or {}
        file_type = data.get('type') # 'master' atau 'target'
        
        if file_type == 'master':
            path = session.get('master_path')
            if path and os.path.exists(path):
                try: os.remove(path)
                except Exception: pass
            session['master_df'] = None
            session['master_meta'] = {}
            session['master_path'] = None
            session['matched_df'] = None
            session['unmatched_df'] = None
            session['summary'] = None
            msg = "File Data Master berhasil dihapus dari sesi Anda."
        elif file_type == 'target':
            path = session.get('target_path')
            if path and os.path.exists(path):
                try: os.remove(path)
                except Exception: pass
            session['target_df'] = None
            session['target_meta'] = {}
            session['target_path'] = None
            session['matched_df'] = None
            session['unmatched_df'] = None
            session['summary'] = None
            msg = "File Data Target berhasil dihapus dari sesi Anda."
        else:
            return jsonify({'success': False, 'error': 'Tipe file tidak valid.'}), 400

        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_data():
    """Mereset data dan membersihkan file terisolasi milik sesi pengguna saat ini."""
    sid = get_session_id()
    session = get_session_data(sid)
    session['master_df'] = None
    session['target_df'] = None
    session['master_path'] = None
    session['target_path'] = None
    session['master_meta'] = {}
    session['target_meta'] = {}
    session['matched_df'] = None
    session['unmatched_df'] = None
    session['summary'] = None
    session['engine'] = None

    # Bersihkan file hanya di folder sesi pengguna ini
    u_dir, o_dir = get_session_dirs(sid)
    for folder in [u_dir, o_dir]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                file_p = os.path.join(folder, f)
                if os.path.isfile(file_p):
                    try: os.remove(file_p)
                    except Exception: pass

    return jsonify({
        'success': True,
        'message': 'Semua data dan file pada sesi Anda berhasil dibersihkan.'
    })


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Menerima file upload Master dan Target ke dalam folder sesi terisolasi."""
    try:
        sid = get_session_id()
        session = get_session_data(sid)
        u_dir, _ = get_session_dirs(sid)

        master_file = request.files.get('master_file')
        target_file = request.files.get('target_file')
        
        if not master_file and not target_file:
            return jsonify({'success': False, 'error': 'Tidak ada file yang diunggah.'}), 400

        if master_file and master_file.filename != '':
            m_path = os.path.join(u_dir, master_file.filename)
            master_file.save(m_path)
            df, meta = smart_load_file(m_path)
            session['master_df'] = df
            session['master_meta'] = meta
            session['master_path'] = m_path

        if target_file and target_file.filename != '':
            t_path = os.path.join(u_dir, target_file.filename)
            target_file.save(t_path)
            df, meta = smart_load_file(t_path)
            session['target_df'] = df
            session['target_meta'] = meta
            session['target_path'] = t_path

        session['matched_df'] = None
        session['unmatched_df'] = None
        session['summary'] = None

        return jsonify({
            'success': True,
            'message': 'File berhasil diunggah ke workspace Anda.',
            'master_rows': len(session['master_df']) if session['master_df'] is not None else 0,
            'target_rows': len(session['target_df']) if session['target_df'] is not None else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_data():
    """Menjalankan mesin pencocokan data multi-tier pada data sesi pengguna."""
    try:
        sid = get_session_id()
        session = get_session_data(sid)

        if session['master_df'] is None or session['target_df'] is None:
            return jsonify({'success': False, 'error': 'Mohon unggah Data Master dan Data Target terlebih dahulu.'}), 400

        engine = DataMatcherEngine(
            session['master_df'],
            session['target_df'],
            target_metadata=session['target_meta']
        )
        summary = engine.process()
        
        session['engine'] = engine
        session['matched_df'] = engine.matched_df
        session['unmatched_df'] = engine.unmatched_df
        session['summary'] = summary

        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/preview', methods=['GET'])
def get_preview():
    """Mengambil preview data sesi pengguna dengan pagination, pencarian cepat, dan filter."""
    sid = get_session_id()
    session = get_session_data(sid)

    dataset_type = request.args.get('dataset', 'matched')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 15))
    search = request.args.get('search', '').strip().lower()
    dpd_filter = request.args.get('dpd', '').strip()

    df = None
    if dataset_type == 'matched':
        df = session['matched_df']
    elif dataset_type == 'unmatched':
        df = session['unmatched_df']
    elif dataset_type == 'target':
        df = session['target_df']
    elif dataset_type == 'master':
        df = session['master_df']

    if df is None or df.empty:
        return jsonify({
            'columns': [],
            'rows': [],
            'total_rows': 0,
            'page': 1,
            'total_pages': 0,
            'dpd_list': []
        })

    # Buat salinan untuk filtering
    filtered_df = df.copy()

    # Cari kolom DPD untuk dropdown filter
    dpd_col = None
    for col in filtered_df.columns:
        if any(k in col.lower() for k in ['dpd', 'kabupaten', 'kota']):
            dpd_col = col
            break

    dpd_list = []
    if dpd_col and dpd_col in filtered_df.columns:
        dpd_list = sorted([str(x) for x in filtered_df[dpd_col].dropna().unique() if str(x).strip()])

    # Terapkan filter DPD
    if dpd_filter and dpd_col and dpd_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[dpd_col].astype(str) == dpd_filter]

    # Terapkan Search jika ada
    if search:
        mask = filtered_df.astype(str).apply(lambda row: row.str.lower().str.contains(search).any(), axis=1)
        filtered_df = filtered_df[mask]

    total_rows = len(filtered_df)
    total_pages = math.ceil(total_rows / limit) if total_rows > 0 else 1
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_df = filtered_df.iloc[start_idx:end_idx].fillna("")

    # Konversi ke dict
    rows = page_df.to_dict(orient='records')
    columns = list(page_df.columns)

    return jsonify({
        'columns': columns,
        'rows': rows,
        'total_rows': total_rows,
        'page': page,
        'total_pages': total_pages,
        'dpd_list': dpd_list
    })

@app.route('/api/export', methods=['POST'])
def export_files():
    """Mengekspor data ke template file asli target dan menyimpannya di folder output sesi."""
    try:
        sid = get_session_id()
        session = get_session_data(sid)
        _, o_dir = get_session_dirs(sid)

        if session['matched_df'] is None or session['unmatched_df'] is None:
            return jsonify({'success': False, 'error': 'Belum ada data hasil pencocokan untuk diekspor.'}), 400

        res = export_results_to_excel(
            session['matched_df'],
            session['unmatched_df'],
            o_dir,
            original_target_path=session.get('target_path')
        )

        template_fn = res.get('template_filename')

        return jsonify({
            'success': True,
            'message': 'File Excel berhasil diupdate sesuai template asli Anda!',
            'template_filename': template_fn,
            'files': {
                'template': template_fn,
                'sukses': 'Data_Lengkap_Sukses.xlsx',
                'gagal': 'Data_Gagal_Match.xlsx'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Mengunduh file Excel yang telah dihasilkan dalam sesi pengguna."""
    sid = get_session_id()
    _, o_dir = get_session_dirs(sid)
    
    # Cek di folder sesi user
    if os.path.exists(os.path.join(o_dir, filename)):
        return send_from_directory(o_dir, filename, as_attachment=True)
        
    # Fallback ke folder root output jika ada
    root_out = app.config['OUTPUT_FOLDER']
    if os.path.exists(os.path.join(root_out, filename)):
        return send_from_directory(root_out, filename, as_attachment=True)
        
    return jsonify({'error': 'File tidak ditemukan atau telah kedaluwarsa.'}), 404

if __name__ == '__main__':
    import sys
    try:
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("=================================================================")
    print("[SERVER RUNNING] Auto-Enrichment Data System (NasDem Sulut)")
    print("Dashboard URL: http://127.0.0.1:5000")
    print("Multi-tenant Session Isolation: ACTIVE")
    print("=================================================================")
    app.run(host='0.0.0.0', port=5000, debug=False)
