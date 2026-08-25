#!/usr/bin/env python
"""Small static file server for local preview.

`python -m http.server` speaks HTTP/1.0 and closes the socket after every
response, which some browsers handle poorly for larger payloads.  This one
sets HTTP/1.1 so keep-alive and Content-Length are honoured.

    python scripts/serve.py               # serve the repository, open /site/
    python scripts/serve.py _site 8766    # serve an assembled build at /
"""

from __future__ import annotations

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        # Local preview should never serve a stale scan.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    handler = partial(Handler, directory=directory)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"serving {directory} at http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
