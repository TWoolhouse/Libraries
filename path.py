import sys
from pathlib import Path

Path = Path(sys.argv[0]).parent.absolute()
PATH = Path.as_posix()
