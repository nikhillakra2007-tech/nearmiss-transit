import os
import shutil
from pathlib import Path

# On Vercel serverless environment, setup writable database in /tmp
if os.environ.get("VERCEL"):
    os.environ["DEMO_MODE"] = "true"
    src_db = Path(__file__).resolve().parent.parent / "nearmiss.db"
    tmp_db = Path("/tmp/nearmiss.db")
    if src_db.exists() and not tmp_db.exists():
        try:
            shutil.copy(str(src_db), str(tmp_db))
        except Exception:
            pass
    if tmp_db.exists():
        os.environ["DATABASE_URL"] = "sqlite:////tmp/nearmiss.db"

from backend.app.main import app
