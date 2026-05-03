from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import hashlib

app = Flask(__name__)
DB = "licenses.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_hash TEXT UNIQUE,
            type TEXT,
            activated_at TEXT,
            expire_at TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/api/create_license", methods=["POST"])
def create_license():
    data = request.json
    license_hash = data.get("license_hash")
    lic_type = data.get("type")

    if lic_type not in ["weekly", "monthly", "lifetime"]:
        return jsonify({"status": "error", "msg": "invalid type"}), 400

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO licenses (license_hash, type, activated_at, expire_at, status) VALUES (?, ?, ?, ?, ?)",
              (license_hash, lic_type, None, None, "unused"))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/check_license", methods=["POST"])
def check_license():
    data = request.json
    license_hash = data.get("license_hash")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT type, activated_at, expire_at, status FROM licenses WHERE license_hash = ?", (license_hash,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "invalid"})

    lic_type, activated_at, expire_at, status = row

    if status != "active" and status != "unused":
        return jsonify({"status": "banned"})

    # Première activation
    if activated_at is None:
        now = datetime.utcnow()
        if lic_type == "weekly":
            exp = now + timedelta(days=7)
        elif lic_type == "monthly":
            exp = now + timedelta(days=30)
        else:
            exp = None

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("UPDATE licenses SET activated_at=?, expire_at=?, status='active' WHERE license_hash=?",
                  (now.isoformat(), exp.isoformat() if exp else None, license_hash))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "ok",
            "type": lic_type,
            "activated_at": now.isoformat(),
            "expire_at": exp.isoformat() if exp else "never"
        })

    # Déjà activée
    if expire_at and datetime.utcnow() > datetime.fromisoformat(expire_at):
        return jsonify({"status": "expired"})

    return jsonify({
        "status": "ok",
        "type": lic_type,
        "activated_at": activated_at,
        "expire_at": expire_at if expire_at else "never"
    })

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)