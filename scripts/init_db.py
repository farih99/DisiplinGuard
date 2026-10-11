from app.core.database import init_db_for_prototype


if __name__ == "__main__":
    init_db_for_prototype()
    print("Tabel prototipe berhasil dibuat. Untuk production, gunakan migration.")
