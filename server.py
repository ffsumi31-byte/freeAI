"""BrickForge AI — Cloud-Ready HTTP Server (Render / Railway / Local)."""
import os, json, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import brain

MEM_FILE = "memory.json"

def load_mem():
    if os.path.exists(MEM_FILE):
        try:
            with open(MEM_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"entries": []}

def save_mem(mem):
    try:
        with open(MEM_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f)
    except Exception:
        pass

class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, data, status=200):
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self._send_json({"ok": True})

    def do_GET(self):
        if self.path.startswith("/health"):
            return self._send_json({"ok": True, "scheme": "v12"})
        if self.path.startswith("/memory"):
            return self._send_json(load_mem())
        if self.path.startswith("/test"):
            results = {}
            for p in ("human", "astronaut", "ryu karate", "purple octopus", "phoenix", "sports car", "unicorn"):
                spec, I = brain.build_one(p)
                checks = brain.structural_checks(spec, I)
                results[p] = {"ok": all(v for _, v in checks), "parts": len(spec["parts"]), "checks": dict(checks)}
            return self._send_json({"ok": all(r["ok"] for r in results.values()), "results": results})
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}") if length > 0 else {}
        mem = load_mem()

        if self.path.startswith("/generate") or self.path.startswith("/api/generate"):
            spec = brain.generate(body, mem)
            return self._send_json(spec)

        if self.path.startswith("/feedback") or self.path.startswith("/like"):
            spec = body.get("spec") or {}
            if spec.get("parts"):
                mem.setdefault("entries", []).append({
                    "prompt": body.get("prompt", ""),
                    "archetype": spec.get("archetype", "prop"),
                    "palette": spec.get("palette"),
                    "style": brain.style_vector(spec),
                    "ts": time.time()
                })
                mem["entries"] = mem["entries"][-200:]
                save_mem(mem)
            return self._send_json({"ok": True, "count": len(mem.get("entries", []))})

        return self._send_json({"error": "unknown endpoint"}, 404)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"BrickForge AI running on http://0.0.0.0:{port}")
    srv.serve_forever()
