# PTM-06 Prompt Log — DisiplinGuard

## Ringkasan Penggunaan AI

| No | Target Prompt | Alat AI & Versi | Ringkasan Prompt | Kualitas (1-5) | Revisi Manual |
|----|---------------|-----------------|------------------|----------------|---------------|
| 1 | D.1 Scaffold Modular | Grok / GPT-4o | Generate struktur Router-Service-Repo + model SQLAlchemy + .env.example | 4 | Ya – penyesuaian endpoint DisiplinGuard |
| 2 | D.2 Autentikasi JWT | Grok / GPT-4o | Implementasi signup/login/refresh/me + bcrypt + token pair + rotasi | 5 | Ya – rotasi refresh + JTI store + akun pending |
| 3 | D.3 Audit OWASP & BOLA | Grok / GPT-4o | Audit BOLA, privilege escalation, rate limit, sanitasi input AI | 5 | Ya – user_class_assignments + rate limit + validasi |
| 4 | Iterasi lanjutan | Grok / GPT-4o | Postman collection + perbaikan schema signup + laporan audit | 5 | Minor – penyesuaian test script & dokumentasi |

## Detail Iterasi

### D.1 Scaffold Modular
**Masalah output pertama:** Struktur masih generik; endpoint AI dan auth belum terpisah jelas.  
**Revisi:** Spesifikkan resource DisiplinGuard; buat kerangka Router-Service-Repo lengkap + `.env.example`.

### D.2 Autentikasi JWT
**Masalah output pertama:** Refresh token belum dirotasi; signup masih menerima role dari client.  
**Revisi:** Tambah rotasi refresh token + penyimpanan JTI; hapus field `role` dari signup; akun baru berstatus `pending` dan nonaktif.

### D.3 Audit OWASP & BOLA
**Masalah output pertama:** Akses hanya berbasis role; belum ada scope kelas/jurusan; belum ada rate limit.  
**Revisi:** Tambah tabel `user_class_assignments`, kebijakan default-deny, rate limiting, validasi numerik AI, sanitasi teks.

## Daftar Asumsi Teknis

| Kode | Isi Asumsi | Verifikasi Tim |
|------|-----------|----------------|
| ASUMSI-01 | Akses data dibatasi pasangan class_name + major via user_class_assignments | Diterapkan |
| ASUMSI-15 | Batas count indikator AI maksimum 366 (pagar resource sementara) | Diterapkan |
| ASUMSI-16 | Skala nilai akademik 0–100 sampai dikonfirmasi sekolah | Diterapkan |
| ASUMSI-17 | risk_score memakai skala 0–1 | Diterapkan |

## Deklarasi Penggunaan AI
Tim menggunakan AI (Grok / GPT-4o) sebagai co-pilot untuk menyusun scaffold, autentikasi JWT, audit keamanan OWASP, dan Postman collection. Seluruh keputusan desain, constraint keamanan, dan penyesuaian final dilakukan serta diverifikasi oleh tim. AI tidak menggantikan pemahaman terhadap requirement dan standar keamanan.
