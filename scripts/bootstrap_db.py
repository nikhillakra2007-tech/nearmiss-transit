"""Create tables (dev bootstrap). Usage: python scripts/bootstrap_db.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.db.base import Base
from backend.app.db import models  # noqa
from backend.app.db.session import engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("bootstrap complete")
