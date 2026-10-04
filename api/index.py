import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path so 'backend' package is resolvable on Vercel serverless
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# On Vercel serverless environment, setup writable database in /tmp
if os.environ.get("VERCEL"):
    os.environ["DEMO_MODE"] = "true"
    src_db = ROOT_DIR / "nearmiss.db"
    tmp_db = Path("/tmp/nearmiss.db")
    if src_db.exists():
        try:
            if not tmp_db.exists() or tmp_db.stat().st_size == 0:
                shutil.copy(str(src_db), str(tmp_db))
        except Exception:
            pass
    os.environ["DATABASE_URL"] = "sqlite:////tmp/nearmiss.db"

from backend.app.main import app
