# Catatan Keamanan DisiplinGuard

## Perubahan patch audit OWASP

- Semua endpoint bisnis menggunakan `get_current_active_user` dan rate limiter API.
- Otorisasi objek memakai penugasan eksplisit pada pasangan `class_name` + `major` melalui tabel `user_class_assignments`. Jika tidak ada penugasan, akses ditolak. Provisioning assignment harus dilakukan lewat proses tepercaya.
- Signup publik tidak menerima field `role`; akun baru berstatus `pending` dan nonaktif.
- Input AI menolak angka non-finite dan batas yang invalid. Asumsi sementara: jumlah indikator maksimum 366, nilai akademik maksimum 100, dan `risk_score` 0-1. Lihat `docs/security/owasp-audit.md`.
- Rate limit default: 120 request/menit per IP untuk API, 5 request/menit per endpoint auth, dan 10 request/menit untuk prediksi AI. Limiter saat ini in-memory, jadi belum cukup sebagai kontrol tunggal pada deployment multi-instance.
- Body request dibatasi default 1 MiB.
- Riwayat pemantauan dipaginasi; list prioritas dibatasi 100 item.
- Model AI masih placeholder. Prediksi belum tersedia akan mengembalikan `503 AI_UNAVAILABLE`, tanpa hasil palsu.

## Penting sebelum digunakan

1. Isi `user_class_assignments` melalui proses administrasi tepercaya. Role staf tanpa assignment akan menerima `403`.
2. Konfirmasi asumsi batas numerik serta skala `risk_score` dengan tim/standar sekolah.
3. Tambahkan migrasi database yang terkelola untuk database production, khususnya constraint baru pada `predictions`.
4. Ganti rate limiter in-memory dengan backend shared seperti Redis saat menggunakan lebih dari satu worker/instance.
5. Jalankan seluruh pengujian setelah dependency dari `requirements.txt` dipasang.

Laporan rinci: `docs/security/owasp-audit.md`.
