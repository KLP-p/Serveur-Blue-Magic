import requests
import hashlib
import random
import string
import time

API_URL = "https://serveur-blue-magic.onrender.com/api/admin/generate"
ADMIN_TOKEN = "183be6d4de5efe431efdec22c0483805a4e2b1250d9c28ded75f1bb257e6aeb8"

def generate_key():
    return "-".join(
        ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
        for _ in range(4)
    )

def hash_license(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def create_license(lic_type):
    key = generate_key()
    h = hash_license(key)

    resp = requests.post(
        API_URL,
        headers={"X-ADMIN-TOKEN": ADMIN_TOKEN},
        json={"license_hash": h, "type": lic_type}
    )

    if resp.status_code == 200 and resp.json().get("status") == "ok":
        print(f"[+] Licence {lic_type} créée : {key}")
    else:
        print("[x] Erreur serveur :", resp.text)

    time.sleep(0.05)

print("=== Génération des 500 licences weekly ===")
for _ in range(500):
    create_license("weekly")

print("=== Génération des 500 licences monthly ===")
for _ in range(500):
    create_license("monthly")

print("=== Génération des 500 licences lifetime ===")
for _ in range(500):
    create_license("lifetime")

print("=== FINI : 1500 licences générées ===")
