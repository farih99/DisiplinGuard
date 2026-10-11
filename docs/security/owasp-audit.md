# Laporan Audit Keamanan OWASP API DisiplinGuard

- **Tanggal audit:** 10 Oktober 2026
- **Basis audit:** source code scaffold DisiplinGuard FastAPI yang tersedia pada repositori kerja saat audit.
- **Cakupan:** OWASP API Security Top 10 (2023), dengan fokus API1 BOLA, API2 Broken Authentication, API4 Unrestricted Resource Consumption, dan validasi masukan/keluaran fitur AI.
- **Batas audit:** audit ini tidak mencakup penetration test jaringan, konfigurasi reverse proxy, konfigurasi produksi, atau pemeriksaan model AI terlatih karena model belum tersedia.

## 1. Ringkasan

Temuan paling penting pada kode awal adalah otorisasi data hanya memeriksa role staf, bukan apakah siswa berada dalam kelas/jurusan yang menjadi kewenangan pengguna. Signup juga sebelumnya menerima role `guru_bk` atau `wali_kelas` langsung dari request publik dan membuat akun aktif. Selain itu, riwayat pemantauan dikembalikan tanpa batas pagination, belum ada rate limiting aplikasi, dan beberapa masukan numerik AI belum memiliki batas atas atau pemeriksaan finite.

Patch audit memperkenalkan pemetaan kelas/jurusan eksplisit melalui `user_class_assignments`, default-deny bila tidak ada penugasan, pendaftaran akun `pending`/nonaktif tanpa field role publik, limiter per IP per proses, batas ukuran body request, pagination, validasi rentang masukan AI, dan sanitasi karakter kontrol untuk teks. Ini mengurangi risiko, tetapi belum berarti aplikasi sudah siap produksi.

## 2. Tabel Audit

| Endpoint / Area | Kerentanan OWASP | Tingkat Risiko Sebelum Patch | Temuan Berbasis Kode | Patch / Rekomendasi | Status |
|---|---|---:|---|---|---|
| `GET /api/students` | API1:2023 BOLA | Tinggi | Daftar dibatasi berdasarkan role, tetapi query awal mengambil semua siswa. Dua wali kelas dengan role sama memperoleh daftar yang sama. | `user_class_assignments` menjadi scope eksplisit; repository hanya mengambil kelas/jurusan yang ditugaskan. Pengguna tanpa assignment ditolak. | **DIPATCH**; assignment harus diprovisikan secara tepercaya. |
| `GET /api/students/{student_id}` | API1:2023 BOLA | Tinggi | `ensure_student_data_access()` semula tidak memeriksa kewenangan atas objek. `student_id` hanya dicek positif. | Ambil objek, lalu pastikan pasangan `class_name` dan `major` milik penugasan pengguna sebelum mengembalikan data. | **DIPATCH**; provisioning penugasan masih manual. |
| `GET /api/students/{student_id}/attendance` dan `/academic` | API1:2023 BOLA | Tinggi | Endpoint mengikuti otorisasi role yang sama seperti detail siswa, sehingga data anak kelas lain berpotensi diakses. | Pemeriksaan scope objek melalui `StudentService.get_student()` dilakukan sebelum repository absensi/nilai dipanggil. | **DIPATCH** |
| `POST /api/predictions` | API1:2023 BOLA, API4:2023 | Tinggi | Role staf saja sebelumnya cukup untuk meminta inference bagi `student_id` mana pun. Tidak ada limiter AI. | Validasi role, cek bahwa siswa ada, cek assignment objek sebelum inference; limiter AI 10 request/menit/IP dan validasi fitur numerik. | **DIPATCH**; rate limiter lokal bukan kontrol terdistribusi. |
| `GET /api/predictions/{prediction_id}` | API1:2023 BOLA | Tinggi | Pemeriksaan role dilakukan, tetapi belum membatasi siswa yang terkait dengan prediction. | Ambil prediction, cari student terkait, kemudian verifikasi assignment terhadap student tersebut. | **DIPATCH** |
| `GET /api/priority-students` | API1:2023 BOLA, API4:2023 | Tinggi | Daftar risiko semula lintas kelas dan `limit` dapat mencapai 500. | Query disaring dengan assignment kelas/jurusan; batas endpoint diturunkan menjadi maksimum 100. | **DIPATCH** |
| `GET /api/dashboard/summary` | API1:2023 BOLA | Sedang–tinggi | Agregat total siswa dan kategori prediksi dihitung untuk seluruh sekolah tanpa scope pengguna. | Perhitungan total dan kategori prediksi sekarang hanya mencakup kelas/jurusan yang ditugaskan. | **DIPATCH** |
| `POST /api/monitoring-history` | API1:2023 BOLA | Tinggi | Pengguna staf bisa membuat catatan untuk siswa mana pun jika mengetahui ID. `user_id` sudah berasal dari token, hal ini dipertahankan. | Validasi assignment siswa sebelum membuat catatan; `user_id` selalu berasal dari `current_user`, bukan request. | **DIPATCH** |
| `GET /api/monitoring-history/{student_id}` | API1:2023 BOLA, API4:2023 | Tinggi | Akses tidak dibatasi oleh assignment dan semua riwayat siswa dikembalikan tanpa batas. | Cek assignment objek dan pagination `offset`/`limit` dengan `limit <= 100`. | **DIPATCH** |
| `POST /api/auth/signup` | API2:2023 Broken Authentication / privilege escalation | Tinggi | `UserCreate` menerima `role` yang bisa berupa `guru_bk` atau `wali_kelas`, sedangkan repository membuat akun aktif. Pengunjung publik dapat meminta role staf. | Field `role` dihapus dari schema dan extra field ditolak. Signup menciptakan role `pending` dan `is_active=False`; provisioning staf harus dilakukan melalui kanal tepercaya. | **DIPATCH**; proses provisioning admin belum tersedia di API. |
| `POST /api/auth/login`, `/signup`, `/refresh` | API2:2023, API4:2023 | Sedang–tinggi | Kode awal tidak menerapkan limiter aplikasi per endpoint untuk login/signup/refresh. | Limiter auth 5 request/menit/IP/endpoint serta generic API limiter. Respons `429` mencantumkan `Retry-After`. | **DIPATCH parsial**; limiter in-memory tidak berbagi state antar worker/instance. |
| Semua request dengan body | API4:2023 | Sedang | Tidak ada batas body global yang terlihat dalam scaffold awal. | Middleware membatasi body aktual, termasuk body chunked, ke `MAX_REQUEST_BODY_BYTES` (default 1 MiB). | **DIPATCH parsial**; tambahkan limit pada proxy/load balancer untuk menahan slowloris/traffic volumetrik. |
| `GET /api/monitoring-history/{student_id}` dan daftar prioritas | API4:2023 | Sedang | Riwayat tidak terbatas dan daftar prioritas berpotensi memproduksi banyak record. | Pagination riwayat dan batas 100 untuk daftar prioritas. | **DIPATCH** |
| Schema input AI `PredictionCreateRequest` | API4:2023 / input validation | Sedang | Kehadiran sudah 0–100, tetapi count dan nilai akademik awalnya hanya memiliki batas bawah. `NaN`/infinity dan field tak dikenal perlu ditolak eksplisit. | Tolak bool/string untuk angka, cek finite; kehadiran 0–100; count 0–`MAX_AI_COUNT`; nilai 0–`MAX_AVERAGE_SCORE`; `extra='forbid'`. | **DIPATCH dengan asumsi**: `[ASUMSI-15]` count maksimum 366; `[ASUMSI-16]` nilai akademik maksimum 100. Konfirmasi terhadap periode dan skala sekolah. |
| Keluaran model AI | Validasi data / integritas | Sedang | Kode awal tidak memvalidasi bahwa `risk_score` finite dan dalam rentang; rekomendasi tidak dibatasi panjang atau karakter kontrol. | Service menolak skor selain 0–1 dan membersihkan rekomendasi hingga 5.000 karakter; constraint DB ditambahkan. | **DIPATCH dengan [ASUMSI-17]** bahwa `risk_score` memakai skala 0–1. Sinkronkan migrasi DB produksi. |
| Teks `follow_up` dan `notes` | Input validation / penyalahgunaan downstream | Rendah–sedang | Panjang sudah dibatasi, tetapi karakter kontrol dapat tersimpan dan menimbulkan log injection atau tampilan tidak diinginkan. | Sanitasi Unicode control/format characters dan whitespace sebelum penyimpanan. HTML tetap wajib di-escape saat dirender oleh client. | **DIPATCH**; data lama perlu pemeriksaan/migrasi terpisah. |
| Fitur AI dan “prompt injection” | Input validation | Tidak berlaku langsung pada model saat ini | `AIInferenceService` masih `503 AI_UNAVAILABLE` dan kontrak input hanya berisi angka, bukan prompt teks untuk LLM. Karena itu, prompt injection klasik belum menjadi jalur yang terbukti dari kode ini. | Validasi numerik dan validasi keluaran dilakukan. Jika kelak model LLM menerima teks bebas, buat threat model prompt injection terpisah. | **Tercatat; belum ada LLM yang diaudit.** |
| Konfigurasi JWT | API2:2023 | Sedang | `ALGORITHM` dibaca dari environment lalu dipakai sebagai allowed algorithm saat decode tanpa allow-list eksplisit. | Konfigurasi kini menolak algoritma selain `HS256`, sesuai kontrak proyek. `SECRET_KEY` tetap wajib dari environment dan minimal 32 karakter. | **DIPATCH** |

## 3. Patch Konkret dan Perubahan Kode

### 3.1 Anti-BOLA dengan scope kelas/jurusan

**File:** `app/models/user_class_assignment.py`, `app/repositories/user_class_assignment_repository.py`, `app/services/access_control.py`.

Kode awal hanya mengenali role. Patch menambahkan tabel assignment dengan pasangan `user_id`, `class_name`, dan `major` yang unik. Semua query daftar, dashboard, prioritas, detail, prediksi, dan riwayat kini menggunakan scope tersebut. Jika staf tidak memiliki assignment, sistem menolak akses (*default deny*).

Contoh data provisioning melalui proses administrasi tepercaya:

```sql
INSERT INTO user_class_assignments (user_id, class_name, major)
VALUES (12, 'X TKJ 1', 'TKJ');
```

Jangan membuat endpoint publik untuk mengubah assignment. Role `guru_bk` yang memang boleh melihat seluruh sekolah harus diberi assignment seluruh kelas/jurusan secara eksplisit oleh proses provisioning tepercaya.

**[ASUMSI-01]** Kebijakan akses dipilih pada tingkat pasangan kelas/jurusan. Jika kebijakan sekolah berbeda, sesuaikan model assignment dan query sebelum production.

### 3.2 Pencegahan privilege escalation saat signup

**File:** `app/schemas/auth.py`, `app/services/auth_service.py`, `app/repositories/user_repository.py`.

- `UserCreate` hanya menerima email dan password.
- `extra='forbid'` membuat payload yang membawa `role` menghasilkan `422`.
- Signup tetap membuat akun, tetapi akun baru berstatus `role='pending'` dan `is_active=False`.
- Login menolak akun nonaktif. Aktivasi dan pemberian role staf harus berasal dari proses administrasi tepercaya.
- Password tetap disimpan sebagai hash bcrypt.

### 3.3 Rate limit dan ukuran request

**File:** `app/core/rate_limit.py`, `app/middleware/request_size_limit.py`, `app/core/config.py`, `.env.example`, dan router.

Nilai awal yang configurable dari environment:

- `API_RATE_LIMIT_REQUESTS=120` per 60 detik
- `AUTH_RATE_LIMIT_REQUESTS=5` per 60 detik per endpoint auth
- `AI_RATE_LIMIT_REQUESTS=10` per 60 detik pada endpoint prediksi
- `MAX_REQUEST_BODY_BYTES=1048576`

Limiter mengembalikan `429 RATE_LIMIT_EXCEEDED` dan `Retry-After`. Implementasi ini **in-memory per proses**, sehingga hanya lapisan proteksi awal. Production multi-worker perlu backend rate-limit bersama, misalnya Redis, dan aturan trusted proxy yang tepat agar sumber IP tidak salah dibaca.

### 3.4 Validasi dan sanitasi input AI

**File:** `app/core/input_sanitization.py`, `app/schemas/prediction.py`, dan `app/services/prediction_service.py`.

| Field | Validasi patch |
|---|---|
| `student_id` | Integer positif dan strict |
| `attendance_percentage` | Angka finite, 0–100 |
| `alpha_count` | Integer, 0–`MAX_AI_COUNT` |
| `late_count` | Integer, 0–`MAX_AI_COUNT` |
| `average_score` | Angka finite, 0–`MAX_AVERAGE_SCORE` |
| `discipline_category` | Salah satu `tinggi`, `sedang`, `rendah` |
| `risk_score` | Finite dan 0–1 dengan `[ASUMSI-17]` |
| `recommendation` | String bersih, tidak kosong, maksimum 5.000 karakter |

**[ASUMSI-15]** Batas count default 366 adalah pagar resource/validasi sementara, bukan fakta periode absensi sekolah. Ubah setelah periode agregasi dikonfirmasi.

**[ASUMSI-16]** Skala nilai akademik dianggap 0–100 sampai sekolah mengonfirmasi skala yang sebenarnya.

**[ASUMSI-17]** `risk_score` dianggap skala 0–1. Jika hasil model nantinya menggunakan 0–100, ubah validasi service, constraint database, dokumentasi API, dan test secara serentak.

Input fitur model saat ini berupa numerik, bukan prompt teks. Sanitasi string tidak dapat menggantikan validasi fitur numerik. Prompt injection klasik baru relevan jika arsitektur menambahkan LLM atau mengirim teks bebas ke instruksi model.

### 3.5 Pembatasan output besar

- `GET /api/monitoring-history/{student_id}` kini menerima `offset` dan `limit` dengan `limit <= 100`.
- `GET /api/priority-students` membatasi `limit <= 100`.
- `GET /api/students` memiliki `limit <= 100` dan batas `page` untuk menahan offset yang ekstrem.

### 3.6 Konfigurasi JWT

**File:** `app/core/config.py`.

Konfigurasi startup sekarang gagal jika `ALGORITHM` bukan `HS256`. Hal ini menghindari accidental misconfiguration terhadap algoritma JWT. Access token tetap tidak memiliki revocation store; akibatnya, token access yang diterbitkan masih berlaku sampai kedaluwarsa walaupun refresh token sudah dirotasi/dicabut.

## 4. Potongan Patch Minimal

Potongan berikut menunjukkan inti perubahan. Implementasi lengkap berada pada file proyek yang disebutkan di atas.

### Anti-BOLA

```python
# app/services/access_control.py
scopes = assignment_repository.list_scopes(user.id)
if not scopes:
    raise AccessDeniedError("Pengguna belum memiliki penugasan kelas yang dapat diakses.")
if (student.class_name, student.major) not in set(scopes):
    raise AccessDeniedError("Pengguna tidak berwenang mengakses siswa tersebut.")
```

### Pencegahan role injection saat signup

```python
# app/schemas/auth.py
class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    # Tidak ada field role dalam schema publik.
```

```python
# app/services/auth_service.py
user = self.user_repository.create(
    email=email,
    password_hash=hash_password(payload.password),
    role="pending",
    is_active=False,
)
```

### Validasi fitur AI

```python
# app/schemas/prediction.py
attendance_percentage: float = Field(ge=0, le=100, allow_inf_nan=False)
alpha_count: int = Field(ge=0, le=settings.max_ai_count, strict=True)
late_count: int = Field(ge=0, le=settings.max_ai_count, strict=True)
average_score: float = Field(ge=0, le=settings.max_average_score, allow_inf_nan=False)
```

### Pengendalian resource

```python
# app/api/routers/monitoring_history.py
limit: int = Query(default=50, ge=1, le=100)
offset: int = Query(default=0, ge=0, le=1_000_000)
```

```python
# app/api/routers/predictions.py
@router.post("", dependencies=[Depends(ai_rate_limit)], ...)
```

### Sanitasi teks

```python
# app/core/input_sanitization.py
cleaned = "".join(
    " " if unicodedata.category(char) in {"Cc", "Cf"} else char
    for char in unicodedata.normalize("NFKC", value)
)
cleaned = " ".join(cleaned.split())
```

Sanitasi di atas digunakan untuk teks riwayat dan rekomendasi hasil AI. Data numerik fitur AI divalidasi dengan rentang dan finite-value check, bukan disaring sebagai teks.

## 5. Pengujian yang Ditambahkan

- `tests/test_bola_scoping.py`: membuktikan daftar, prioritas, dan dashboard hanya menghitung scope kelas/jurusan yang diberikan.
- `tests/test_business_access.py`: role tidak diizinkan, pengguna tanpa assignment, dan akses kelas berbeda ditolak.
- `tests/test_input_security.py`: rentang numerik, `NaN`/infinity, field ekstra, sanitasi teks, serta keluaran risk score invalid.
- `tests/test_rate_limit.py`: menguji respons 429 dan header `Retry-After`.
- `tests/test_request_size_limit.py`: menguji body yang melampaui batas, termasuk simulasi chunked body.
- `tests/test_signup_schema.py`: memastikan role tidak dapat disuplai pada signup.

Pada lingkungan audit, **32 test pada suite keamanan non-JWT lulus**. Suite autentikasi integrasi penuh tidak dapat dijalankan di lingkungan ini karena dependensi `python-jose` dan `passlib` tidak terpasang dan jaringan instalasi paket tidak tersedia. Karena itu, status patch autentikasi perlu diverifikasi ulang dengan seluruh dependency proyek terpasang.

## 6. Risiko Residual dan Tindak Lanjut

1. **[ASUMSI-01] Provisioning assignment:** model penugasan sudah tersedia, tetapi belum ada alur administrasi untuk memasukkan kelas/jurusan. Data assignment wajib diprovisikan sebelum endpoint bisnis digunakan. Default kosong adalah deny.
2. **[ASUMSI-15/16/17] Rentang numerik:** konfirmasi periode absensi, skala nilai, dan definisi risk score sebelum dataset produksi diproses.
3. **Rate limit terdistribusi:** ganti limiter in-memory dengan penyimpanan bersama untuk multi-worker/instance dan pasang batas pada reverse proxy.
4. **Migrasi database:** tabel `user_class_assignments` akan dibuat pada database baru dengan `create_all`, tetapi perubahan constraint pada tabel yang sudah ada memerlukan migrasi database yang terkelola. Jangan mengandalkan `create_all` untuk mengubah tabel production.
5. **Provisioning signup:** akun publik tetap pending/nonaktif. Tetapkan mekanisme aktivasi/penetapan role staf yang diaudit.
6. **Access token revocation:** access token tetap berlaku sampai TTL berakhir. Jika kebutuhan pencabutan segera muncul, tambahkan mekanisme token-version/denylist yang dibagikan antar-instance.
7. **Output encoding:** sanitasi karakter kontrol bukan perlindungan XSS lengkap. Client harus menggunakan output encoding kontekstual dan tidak menyisipkan teks pengguna/AI secara mentah ke HTML.
8. **Logging dan pemantauan produksi:** kode yang diaudit belum menunjukkan integrasi alerting, audit log terpusat, WAF, atau deteksi brute force tingkat infrastruktur. Verifikasi konfigurasi deployment terpisah.
9. **AI belum tersedia:** `AIInferenceService` tetap mengembalikan `503 AI_UNAVAILABLE` sampai model benar-benar diintegrasikan. Tidak ada prediksi tiruan pada fallback.

## 7. Cara Menjalankan Test

Dari root proyek dengan dependency terpasang:

```bash
python -m compileall -q app tests scripts
python -m pytest -q tests/test_input_security.py tests/test_rate_limit.py tests/test_business_access.py tests/test_bola_scoping.py tests/test_request_size_limit.py tests/test_signup_schema.py
python -m pytest -q
```

Suite terakhir perlu dijalankan pada lingkungan yang sudah memasang `python-jose`, `passlib`, `bcrypt`, dan semua dependency dari `requirements.txt`.
