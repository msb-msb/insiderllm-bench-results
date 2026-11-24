import http.client, http.server, json, sys, time, socketserver
UP = ("127.0.0.1", 8081); LOG = open(sys.argv[1], "a")
class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    def _go(self):
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n) if n else None
        rec = {"t": time.time(), "method": self.command, "path": self.path}
        if body:
            try:
                j = json.loads(body)
                rec["stream"] = j.get("stream"); rec["n_tools"] = len(j.get("tools") or [])
                rec["tool_names"] = [t.get("function", {}).get("name") for t in (j.get("tools") or [])]
                rec["messages"] = [{"role": m.get("role"), "content": (m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content")))[:600]} for m in j.get("messages", [])]
                rec["keys"] = sorted(j)
            except Exception as e:
                rec["raw"] = body[:300].decode(errors="replace")
        if self.path not in ("/health", "/slots") and not self.path.startswith("/v1/models") and not self.path.startswith("/models"):
            LOG.write(json.dumps(rec, ensure_ascii=False) + "\n"); LOG.flush()
        c = http.client.HTTPConnection(*UP, timeout=600)
        hd = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "connection", "content-length")}
        c.request(self.command, self.path, body=body, headers=hd); r = c.getresponse()
        self.send_response(r.status)
        for k, v in r.getheaders():
            if k.lower() not in ("transfer-encoding", "connection", "content-length"): self.send_header(k, v)
        self.end_headers()
        while True:
            b = r.read1(65536)
            if not b: break
            self.wfile.write(b); self.wfile.flush()
    do_GET = do_POST = _go
    def log_message(self, *a): pass
class S(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads = True
S(("0.0.0.0", 8080), H).serve_forever()
