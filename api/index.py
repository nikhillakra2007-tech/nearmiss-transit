import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path so 'backend' and 'scripts' packages are resolvable on Vercel
API_DIR = Path(__file__).resolve().parent
ROOT_DIR = API_DIR.parent

for p in (str(ROOT_DIR), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Setup writable database in /tmp for Vercel serverless environment
if os.environ.get("VERCEL"):
    os.environ["DEMO_MODE"] = "true"
    src_db = API_DIR / "nearmiss.db"
    if not src_db.exists():
        src_db = ROOT_DIR / "nearmiss.db"
    
    tmp_db = Path("/tmp/nearmiss.db")
    if src_db.exists():
        try:
            if not tmp_db.exists() or tmp_db.stat().st_size == 0:
                shutil.copy(str(src_db), str(tmp_db))
        except Exception as e:
            print("DB copy error:", e)

    os.environ["DATABASE_URL"] = "sqlite:////tmp/nearmiss.db"

from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.db.models.pattern import Pattern

# Auto-prep demo data if database is empty on cold start
try:
    with SessionLocal() as db:
        if db.query(Pattern).count() == 0:
            from scripts.prep_demo import main as prep_demo_main
            prep_demo_main()
except Exception as err:
    print(f"Auto-prep demo check: {err}")
