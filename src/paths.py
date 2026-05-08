from pathlib import Path

FILE: Path = Path(__file__).resolve()
ROOT_DIR: Path = FILE.parents[1]

_DATA_DIR: Path = ROOT_DIR / ".data"
LOGS_DIR: Path = _DATA_DIR / "logs"
