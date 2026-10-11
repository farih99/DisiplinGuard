# DisiplinGuard FastAPI Scaffold

Scaffold backend DisiplinGuard menggunakan FastAPI, Pydantic v2, SQLAlchemy 2, dan PostgreSQL (production) atau SQLite (prototype). Struktur mengikuti pola **Router → Service → Repository**.

## Status implementasi

- Autentikasi JWT: signup, login, refresh dengan rotasi refresh token, serta `/auth/me` telah diimplementasikan. Password disimpan sebagai bcrypt hash; rahasia dan masa berlaku token dibaca dari environment.

- `GET /api/students` dan endpoint detail/indikator siswa memiliki contoh implementasi dasar.
- Endpoint `POST /api/predictions` telah memiliki kontrak input, orchestration service, dan fallback HTTP `503`; inferensi model masih berupa placeholder dan **tidak menghasilkan prediksi palsu**.
- Endpoint resource lain dan autentikasi tersedia sebagai kerangka yang merespons `501 Not Implemented` sampai logika PTM-06 diselesaikan.
- Tabel dapat dibuat untuk prototipe lokal melalui script `scripts/init_db.py`. Untuk production, gunakan migration tool seperti Alembic setelah diputuskan tim.

## Menjalankan secara lokal

1. Buat virtual environment.
2. Instal dependency: `pip install -r requirements.txt`.
3. Salin `.env.example` menjadi `.env` lalu ubah `SECRET_KEY` dengan nilai acak yang aman. Jangan commit `.env`.
4. Inisialisasi tabel prototipe: `python -m scripts.init_db`.
5. Jalankan aplikasi: `uvicorn app.main:app --reload`.
6. Buka `http://localhost:8000/docs` untuk Swagger UI atau `http://localhost:8000/redoc` untuk ReDoc.

Di Windows PowerShell, langkah penyalinan environment dapat dilakukan dengan `Copy-Item .env.example .env`.

## PostgreSQL

Ganti `DATABASE_URL` di `.env`, misalnya:

`postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE_NAME`

Gunakan kredensial database dari environment/deployment secret manager. Jangan menaruh kredensial asli di repository.

## Placeholder yang harus diselesaikan (`TODO: [PTM-06]`)

- Integrasi model terlatih pada `app/services/ai_inference_service.py`.
- Definisi mapping output model ke kategori dan skor risiko.
- Aturan rekomendasi intervensi, karena tabel aturan belum diberikan pada SRS/HLD.
- Otorisasi role yang lebih terperinci dan kebijakan administrasi akun.
- Query dashboard, daftar prioritas, serta riwayat pemantauan.
- Migration production, logging, dan pengujian keamanan.

## Catatan kontrak

- Kategori kedisiplinan: `tinggi`, `sedang`, `rendah`.
- Input AI: `student_id`, `attendance_percentage`, `alpha_count`, `late_count`, `average_score`.
- Target latensi prediksi `<= 3 detik` masih berstatus `[ASUMSI-07]`.
- Batas atas nilai akademik dan skala `risk_score` perlu diputuskan tim.
- Gunakan data siswa hanya untuk tujuan DisiplinGuard dan batasi akses ke pengguna berwenang.

## Endpoint autentikasi

- `POST /api/auth/signup`: buat akun dengan role `guru_bk` atau `wali_kelas`; mengembalikan data publik pengguna tanpa hash password.
- `POST /api/auth/login`: menerima JSON `{ "email": "guru@example.com", "password": "..." }` dan form OAuth2 (`username` berisi email, serta `password`).
- `POST /api/auth/refresh`: validasi refresh token, mencabut JTI lama, lalu menerbitkan pasangan token baru. Token refresh yang sudah dipakai tidak dapat digunakan kembali.
- `GET /api/auth/me`: memerlukan header `Authorization: Bearer <access_token>` dan menolak akun tidak aktif dengan HTTP 403.

`refresh_token_sessions` menyimpan JTI dan status pencabutan, bukan token mentah. Untuk production, gunakan Alembic migration, HTTPS, manajemen secret yang sesuai deployment, pembatasan percobaan login, serta tinjau kebijakan siapa yang boleh membuat akun.
