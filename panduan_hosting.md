# Panduan Hosting & Akses Multi-User (Tanpa Login)

Sistem ini telah dilengkapi dengan **Arsitektur Multi-Tenant Client-Side (Session Isolation)**:
- Setiap pengguna yang membuka URL web akan otomatis diberikan **ID Sesi Unik** yang disimpan di `localStorage` browser mereka masing-masing.
- Jika 5 orang (atau lebih) mengakses web secara bersamaan:
  - File yang diunggah oleh User A tidak akan terlihat oleh User B.
  - Hasil pencocokan dan tombol reset/hapus hanya berlaku pada workspace pengguna tersebut.
  - **Tidak memerlukan sistem login atau password**, sehingga sangat cepat dan mudah digunakan oleh staf lapangan/operator.

---

## Pilihan 1: Cloud Hosting Gratis (Render.com) — Rekomendasi Terbaik (Online 24 Jam)

Dengan cara ini, web akan menyala 24 jam di cloud tanpa memerlukan laptop Anda tetap hidup.

### Langkah-langkah:
1. **Upload / Push Project ke GitHub:**
   - Buat repository baru di GitHub (bisa *Public* atau *Private*).
   - Upload seluruh folder project ini ke GitHub.
2. **Daftar di Render:**
   - Kunjungi [https://render.com](https://render.com) lalu Login dengan akun GitHub Anda.
3. **Buat Web Service Baru:**
   - Klik tombol **"New +"** di pojok kanan atas > Pilih **"Web Service"**.
   - Pilih repository GitHub project NasDem Anda.
4. **Pengaturan Deploy:**
   - **Name**: `nasdem-data-enrichment` (atau nama lain sesuai keinginan)
   - **Region**: Singapore (paling cepat untuk Indonesia)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 4 --timeout 120` *(File Procfile sudah disediakan di project)*
   - **Instance Type**: `Free`
5. **Klik "Deploy Web Service":**
   - Tunggu sekitar 2-3 menit hingga proses build selesai.
   - Anda akan mendapatkan URL HTTPS gratis, contoh:  
     👉 **`https://nasdem-data-enrichment.onrender.com`**
   - Bagikan link ini ke 5 rekan kerja Anda, dan mereka bisa langsung menggunakannya secara mandiri!

---

## Pilihan 2: Instan dari Laptop Sendiri (Localtunnel / Cloudflare Tunnel) — Aktif dalam 2 Menit!

Jika Anda ingin langsung membagikan link ke rekan kerja sekarang juga tanpa perlu deploy ke cloud:

### Cara Menggunakan Localtunnel:
1. Pastikan server lokal Anda sedang berjalan:
   ```bash
   python run.py
   ```
2. Buka terminal baru (Command Prompt / PowerShell), lalu ketik:
   ```bash
   npx -y localtunnel --port 5000
   ```
3. Anda akan langsung mendapatkan URL publik, contoh:
   ```text
   your url is: https://nasdem-sulut.loca.lt
   ```
4. Kirim link tersebut ke 5 rekan kerja Anda. Mereka bisa langsung membukanya di browser HP atau laptop masing-masing!

*(Catatan: Saat rekan kerja membuka link pertama kali, localtunnel akan meminta password IP. Cukup buka [loca.lt/mytunnelpassword](https://loca.lt/mytunnelpassword) di laptop Anda untuk melihat IP tersebut).*

---

## Pilihan 3: Server VPS Resmi Partai (Ubuntu / Debian)

Untuk operasional jangka panjang DPW/DPD dengan domain sendiri (misal: `https://data.nasdemsulut.id`):

1. **Clone repository di server VPS:**
   ```bash
   git clone <repo_url>
   cd pendataan-python
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Buat Systemd Service (`/etc/systemd/system/nasdem.service`):**
   ```ini
   [Unit]
   Description=Nasdem Auto-Enrichment Web Dashboard
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/var/www/pendataan-python
   ExecStart=/var/www/pendataan-python/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. **Jalankan Service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start nasdem
   sudo systemctl enable nasdem
   ```
4. **Konfigurasi Reverse Proxy Nginx & SSL (Certbot):**
   ```nginx
   server {
       server_name data.nasdemsulut.id;
       client_max_body_size 100M;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```
   Lalu pasang SSL gratis dengan: `sudo certbot --nginx -d data.nasdemsulut.id`.

---

## 🔒 Keamanan & Isolasi Data Multi-Pengguna
- Setiap pengguna memiliki folder penyimpanan terisolasi di server:  
  `input/<session_id>/` dan `output/<session_id>/`.
- Sesi yang tidak aktif lebih dari 24 jam akan otomatis dibersihkan oleh sistem agar penyimpanan server tidak penuh.
