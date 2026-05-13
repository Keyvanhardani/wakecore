"""Enable `python -m wakecore ...` as an alias for the wakecore CLI."""
from .cli import main
import sys

sys.exit(main())
