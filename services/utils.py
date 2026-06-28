
import re
from pathlib import Path
from datetime import datetime
import base64

UPLOADS = Path("uploads")
UPLOADS.mkdir(exist_ok=True)

def money(v):
    try:
        return float(str(v).replace(".", "").replace(",", "."))
    except Exception:
        return 0.0

def safe_name(s):
    return re.sub(r"[^A-Za-z0-9_ -]", "_", s or "Senza_Azienda").strip().replace(" ", "_")

def save_upload(file, subfolder):
    if not file:
        return ""
    folder = UPLOADS / safe_name(subfolder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / file.name
    path.write_bytes(file.getvalue())
    return str(path)

def b64(path):
    p = Path(path)
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""

def now_iso():
    return datetime.now().isoformat()
