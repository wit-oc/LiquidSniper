from __future__ import annotations

import os
import time


def main() -> None:
    mode = os.getenv("LIQUIDSNIPER_MODE", "paper").strip().lower()
    if mode != "paper":
        raise RuntimeError("paper_daemon only supports LIQUIDSNIPER_MODE=paper")

    loop_seconds = int(os.getenv("LIQUIDSNIPER_LOOP_SECONDS", "60"))
    # MVP daemon loop placeholder: orchestration wiring can invoke full cycle function here.
    while True:
        time.sleep(max(1, loop_seconds))


if __name__ == "__main__":
    main()
