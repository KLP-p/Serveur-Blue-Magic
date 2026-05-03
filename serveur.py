import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

DB = "licenses.db"
ADMIN_TOKEN = "CHANGE_THIS_ADMIN_TOKEN"

app = Flask(__name__)

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

@app.route("/api/admin/generate", methods=["POST"])
def admin_generate():
    if request.headers.get("X-ADMIN-TOKEN") != ADMIN_TOKEN:
        return jsonify({"status": "forbidden"}), 403

    data = request.json
    license_hash = data.get("license_hash")
    lic_type = data.get("type")

    if lic_type not in ["weekly", "monthly", "lifetime"]:
        return jsonify({"status": "error", "msg": "invalid type"}), 400

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO licenses (license_hash, type, activated_at, expire_at, status) VALUES (?, ?, ?, ?, ?)",
        (license_hash, lic_type, None, None, "unused")
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/check_license", methods=["POST"])
def check_license():
    data = request.json
    license_hash = data.get("license_hash")

    if not license_hash:
        return jsonify({"status": "invalid"}), 400

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, type, activated_at, expire_at, status FROM licenses WHERE license_hash = ?", (license_hash,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "invalid"})

    lic_id, lic_type, activated_at, expire_at, status = row

    if status == "banned":
        return jsonify({"status": "banned"})

    now = datetime.utcnow()

    # Première activation → le compte à rebours commence ici
    if activated_at is None:
        if lic_type == "weekly":
            exp = now + timedelta(days=7)
        elif lic_type == "monthly":
            exp = now + timedelta(days=30)
        else:  # lifetime
            exp = None

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute(
            "UPDATE licenses SET activated_at=?, expire_at=?, status='active' WHERE id=?",
            (now.isoformat(), exp.isoformat() if exp else None, lic_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "status": "ok",
            "type": lic_type,
            "activated_at": now.isoformat(),
            "expire_at": exp.isoformat() if exp else "never"
        })

    # Déjà activée → vérifier expiration
    if expire_at:
        exp = datetime.fromisoformat(expire_at)
        if now > exp:
            return jsonify({"status": "expired"})

    return jsonify({
        "status": "ok",
        "type": lic_type,
        "activated_at": activated_at,
        "expire_at": expire_at if expire_at else "never"
    })

@app.route("/", methods=["GET"])
def root():
    return "BlueMagic License Server", 200

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
