import sqlite3
import hashlib
import random
import string
from datetime import datetime

DB = "licenses.db"

def generate_key():
    return "-".join(
        ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
        for _ in range(4)
    )

def hash_license(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def regenerate_license(lic_type):
    key = generate_key()
    h = hash_license(key)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO licenses (license_hash, type, activated_at, expire_at, status) VALUES (?, ?, ?, ?, ?)",
        (h, lic_type, None, None, "unused")
    )
    conn.commit()
    conn.close()

    print(f"[+] Nouvelle licence générée ({lic_type}) : {key}")

def cleanup():
    now = datetime.utcnow()

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, type, expire_at FROM licenses WHERE expire_at IS NOT NULL")
    rows = c.fetchall()

    for lic_id, lic_type, expire_at in rows:
        exp = datetime.fromisoformat(expire_at)
        if now > exp:
            print(f"[x] Licence expirée supprimée : id={lic_id} ({lic_type})")
            c.execute("DELETE FROM licenses WHERE id = ?", (lic_id,))
            conn.commit()
            regenerate_license(lic_type)

    conn.close()

if __name__ == "__main__":
    cleanup()
