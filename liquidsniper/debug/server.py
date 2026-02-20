from __future__ import annotations

import os
from wsgiref.simple_server import make_server

from .service import build_app


def main() -> None:
    host = os.getenv("LIQUIDSNIPER_DEBUG_HOST", "127.0.0.1")
    port = int(os.getenv("LIQUIDSNIPER_DEBUG_PORT", "8787"))
    app = build_app()
    with make_server(host, port, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
