#!/usr/bin/env python3
"""ws entry point. `ws --help` and `ws help` are the guide."""
import os
import sys

if sys.version_info < (3, 8):   # wslib uses 3.8 syntax; say so plainly instead of failing with a SyntaxError inside it
    sys.exit("ws needs Python 3.8 or newer; this is %s (%s)" % (sys.version.split()[0], sys.executable))

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from wslib.cli import main  # noqa: E402

sys.exit(main())
