from __future__ import annotations

import atexit
import os
from pathlib import Path
from tempfile import mkstemp

descriptor, database_path = mkstemp(prefix="aipedia-hub-test-", suffix=".db")
os.close(descriptor)
Path(database_path).unlink()
os.environ["AIPEDIA_DATABASE_URL"] = f"sqlite:///{database_path}"


@atexit.register
def remove_test_database() -> None:
    for suffix in ("", "-wal", "-shm"):
        Path(f"{database_path}{suffix}").unlink(missing_ok=True)
