# Provisioning penugasan kelas DisiplinGuard

Semua pengguna dengan role `guru_bk` atau `wali_kelas` memerlukan baris pada `user_class_assignments`. Tanpa assignment, semua endpoint data siswa menggunakan kebijakan default-deny dan mengembalikan 403.

Lakukan provisioning melalui proses database/admin tepercaya, bukan endpoint publik. Contoh PostgreSQL:

```sql
-- Contoh: beri user 12 akses ke kelas X TKJ 1 pada jurusan TKJ.
INSERT INTO user_class_assignments (user_id, class_name, major)
VALUES (12, 'X TKJ 1', 'TKJ')
ON CONFLICT (user_id, class_name, major) DO NOTHING;
```

Untuk `guru_bk` yang memiliki kewenangan seluruh sekolah, masukkan setiap pasangan kelas/jurusan yang disetujui sekolah. Jangan memberi seluruh scope secara default hanya berdasarkan role jika kebijakan sekolah belum mengesahkannya.

Pada deployment yang sudah memiliki database, buat dan jalankan migration terkelola untuk tabel baru dan constraint. `Base.metadata.create_all()` tidak mengubah tabel yang telah ada.
