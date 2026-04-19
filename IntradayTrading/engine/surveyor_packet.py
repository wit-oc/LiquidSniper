from __future__ import annotations

import sys
from pathlib import Path


_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(_WORKSPACE_ROOT))


from intraday_revisit.engine.surveyor_packet import *  # noqa: F401,F403

