"""
Script migrasi untuk menambah kolom-kolom baru yang belum ada di database.
Jalankan SEKALI dengan: python migrate.py
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from app.database import engine
from sqlalchemy import text

MIGRATIONS = [
    # Users table
    ("users.is_active",
     "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"),

    # Pemberitahuan table
    ("CREATE pemberitahuan", """
        CREATE TABLE IF NOT EXISTS pemberitahuan (
            id SERIAL PRIMARY KEY,
            judul VARCHAR(255) NOT NULL,
            isi TEXT NOT NULL,
            foto VARCHAR(500),
            target_rt VARCHAR(10),
            target_rw VARCHAR(10),
            is_publik BOOLEAN DEFAULT TRUE,
            created_by VARCHAR(36) REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            expired_at TIMESTAMP
        )
    """),

    # Pemberitahuan: kolom yang mungkin belum ada jika tabel sudah dibuat sebelumnya
    ("pemberitahuan.foto",
     "ALTER TABLE pemberitahuan ADD COLUMN IF NOT EXISTS foto VARCHAR(500)"),
    ("pemberitahuan.is_publik",
     "ALTER TABLE pemberitahuan ADD COLUMN IF NOT EXISTS is_publik BOOLEAN DEFAULT TRUE"),
    ("pemberitahuan.expired_at",
     "ALTER TABLE pemberitahuan ADD COLUMN IF NOT EXISTS expired_at TIMESTAMP"),
    ("pemberitahuan.target_rt",
     "ALTER TABLE pemberitahuan ADD COLUMN IF NOT EXISTS target_rt VARCHAR(10)"),
    ("pemberitahuan.target_rw",
     "ALTER TABLE pemberitahuan ADD COLUMN IF NOT EXISTS target_rw VARCHAR(10)"),
    ("pemberitahuan.created_by",
     "ALTER TABLE pemberitahuan ADD COLUMN IF NOT EXISTS created_by VARCHAR(36) REFERENCES users(id)"),

    # Aset: foto, deskripsi
    ("aset.foto",
     "ALTER TABLE aset ADD COLUMN IF NOT EXISTS foto VARCHAR(500)"),
    ("aset.deskripsi",
     "ALTER TABLE aset ADD COLUMN IF NOT EXISTS deskripsi TEXT"),

    # Aduan: lokasi, foto bukti/selesai, balasan, rt_id
    ("aduan.latitude",
     "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS latitude FLOAT"),
    ("aduan.longitude",
     "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS longitude FLOAT"),
    ("aduan.foto_bukti",
     "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS foto_bukti VARCHAR(500)"),
    ("aduan.foto_selesai",
     "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS foto_selesai VARCHAR(500)"),
    ("aduan.balasan",
     "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS balasan TEXT"),
    ("aduan.rt_id",
     "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS rt_id VARCHAR(36) REFERENCES users(id)"),

    # IuranSetting table
    ("CREATE iuran_setting", """
        CREATE TABLE IF NOT EXISTS iuran_setting (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            rt VARCHAR(10) NOT NULL,
            rw VARCHAR(10) NOT NULL,
            nominal FLOAT NOT NULL DEFAULT 50000,
            tanggal_mulai VARCHAR(20),
            keterangan TEXT,
            set_by VARCHAR(36) REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """),

    # PeminjamanAset table — dengan ON DELETE CASCADE agar aset bisa dihapus
    ("CREATE peminjaman_aset", """
        CREATE TABLE IF NOT EXISTS peminjaman_aset (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            aset_id VARCHAR(36) NOT NULL REFERENCES aset(id) ON DELETE CASCADE,
            peminjam_id VARCHAR(36) NOT NULL REFERENCES users(id),
            disetujui_oleh VARCHAR(36) REFERENCES users(id),
            status VARCHAR(50) DEFAULT 'menunggu',
            keperluan TEXT,
            tanggal_pinjam TIMESTAMP,
            tanggal_kembali_rencana TIMESTAMP,
            tanggal_kembali_aktual TIMESTAMP,
            catatan TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """),

    # Fix FK peminjaman_aset jika tabel sudah ada tanpa CASCADE
    ("peminjaman_aset.fk_cascade", """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'peminjaman_aset'
                AND constraint_name = 'peminjaman_aset_aset_id_fkey'
            ) THEN
                ALTER TABLE peminjaman_aset DROP CONSTRAINT peminjaman_aset_aset_id_fkey;
                ALTER TABLE peminjaman_aset ADD CONSTRAINT peminjaman_aset_aset_id_fkey
                    FOREIGN KEY (aset_id) REFERENCES aset(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """),

    # SuratPengantar: kolom yang mungkin belum ada
    ("surat_pengantar.file_ttd_digital",
     "ALTER TABLE surat_pengantar ADD COLUMN IF NOT EXISTS file_ttd_digital TEXT"),
    ("surat_pengantar.catatan",
     "ALTER TABLE surat_pengantar ADD COLUMN IF NOT EXISTS catatan TEXT"),
]


def run_migrations():
    with engine.connect() as conn:
        for label, sql in MIGRATIONS:
            try:
                conn.execute(text(sql.strip()))
                conn.commit()
                print(f"  [OK]   {label}")
            except Exception as e:
                conn.rollback()
                short = str(e).split('\n')[0][:120]
                print(f"  [SKIP] {label}: {short}")


if __name__ == "__main__":
    print("[*] Menjalankan migrasi database KICAU...")
    run_migrations()
    print("[DONE] Selesai!")
