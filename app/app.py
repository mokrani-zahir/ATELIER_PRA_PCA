import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request
import glob
import time

DB_PATH = os.getenv("DB_PATH", "/data/app.db")

app = Flask(__name__)

# ---------- DB helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- Routes ----------

@app.get("/")
def hello():
    init_db()
    return jsonify(status="Bonjour tout le monde !")


@app.get("/health")
def health():
    init_db()
    return jsonify(status="ok")

@app.get("/add")
def add():
    init_db()

    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"

    conn = get_conn()
    conn.execute(
        "INSERT INTO events (ts, message) VALUES (?, ?)",
        (ts, msg)
    )
    conn.commit()
    conn.close()

    return jsonify(
        status="added",
        timestamp=ts,
        message=msg
    )

@app.get("/consultation")
def consultation():
    init_db()

    conn = get_conn()
    cur = conn.execute(
        "SELECT id, ts, message FROM events ORDER BY id DESC LIMIT 50"
    )

    rows = [
        {"id": r[0], "timestamp": r[1], "message": r[2]}
        for r in cur.fetchall()
    ]

    conn.close()

    return jsonify(rows)

@app.get("/count")
def count():
    init_db()

    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()

    return jsonify(count=n)

@app.get("/status")
def status():
    init_db()

    # Nombre d'événements
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    count = cur.fetchone()[0]
    conn.close()

    backup_dir = "/backup"

    # Recherche des fichiers de sauvegarde
    backup_files = glob.glob(os.path.join(backup_dir, "*"))

    if backup_files:
        # Dernier fichier modifié
        last_backup = max(backup_files, key=os.path.getmtime)

        last_backup_file = os.path.basename(last_backup)
        backup_age_seconds = int(time.time() - os.path.getmtime(last_backup))
    else:
        last_backup_file = None
        backup_age_seconds = None

    return jsonify({
        "count": count,
        "last_backup_file": last_backup_file,
        "backup_age_seconds": backup_age_seconds
    })
# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
