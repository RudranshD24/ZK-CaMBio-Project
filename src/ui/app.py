"""src/ui/app.py

ZK-CaMBio UI service placeholder (fleshed out in Phase 8).
Serves a basic HTTP status page on port 8501.
"""

from __future__ import annotations

import http.server
import socketserver

PORT = 8501


class StatusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ZK-CaMBio UI Service (Phase 8 Placeholder)")


if __name__ == "__main__":
    print(f"ZK-CaMBio UI placeholder running on port {PORT}")
    with socketserver.TCPServer(("", PORT), StatusHandler) as httpd:
        httpd.serve_forever()
