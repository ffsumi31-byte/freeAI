"""Roblox Cloud 3D Modeler Server — Live 9-Stage Pipeline UI + Luau Rig & Wavefront .OBJ Exporter."""
import os, json, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
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

HTML_UI = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Roblox Cloud 3D Modeler AI</title>
<style>
  :root {
    --bg: #0f1117;
    --panel: #171a23;
    --border: #262b38;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --accent: #3b82f6;
    --success: #10b981;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: var(--bg); color: var(--text); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

  .topbar { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: var(--panel); border-bottom: 1px solid var(--border); overflow-x: auto; white-space: nowrap; }
  .brand { font-weight: 800; font-size: 13px; letter-spacing: 0.8px; color: #60a5fa; margin-right: 8px; }
  .pill { padding: 6px 12px; border-radius: 999px; border: 1px solid var(--border); background: #1e2330; font-size: 12px; font-weight: 600; color: var(--text); cursor: pointer; transition: 0.15s; }
  .pill:hover { background: var(--accent); border-color: var(--accent); color: #fff; }

  .subheader { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: #13161f; border-bottom: 1px solid var(--border); }
  .title-group { display: flex; align-items: center; gap: 10px; }
  .model-title { font-weight: 800; font-size: 13px; text-transform: uppercase; letter-spacing: 0.6px; }
  .badge { background: rgba(16,185,129,0.15); color: var(--success); border: 1px solid rgba(16,185,129,0.3); font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; }
  .actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .btn-sm { padding: 6px 12px; border-radius: 8px; border: 1px solid var(--border); background: #1e2330; color: var(--text); font-size: 11px; font-weight: 700; cursor: pointer; }
  .btn-sm:hover { background: #2a3142; }
  .btn-sm.primary { background: var(--accent); border-color: var(--accent); color: #fff; }

  .workspace { position: relative; flex: 1; display: flex; overflow: hidden; }
  #viewport { flex: 1; height: 100%; display: block; background: radial-gradient(circle at 50% 45%, #1e2433 0%, #0d0f14 100%); }

  /* Right Pipeline Inspector Drawer */
  .pipeline-sidebar { width: 320px; background: var(--panel); border-left: 1px solid var(--border); padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
  .pipe-title { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); margin-bottom: 4px; }
  .step-card { background: #12151e; border: 1px solid var(--border); border-left: 3px solid var(--success); border-radius: 6px; padding: 8px 10px; font-size: 11px; }
  .step-stage { font-weight: 800; color: #60a5fa; text-transform: uppercase; font-size: 10px; margin-bottom: 2px; }
  .step-msg { color: #cbd5e1; line-height: 1.35; }

  .stats-pill { position: absolute; bottom: 14px; left: 16px; background: rgba(15,17,23,0.88); border: 1px solid var(--border); padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: 600; color: var(--muted); font-family: monospace; pointer-events: none; }

  #scriptPanel { position: absolute; inset: 16px; background: rgba(15,17,23,0.97); border: 1px solid var(--border); border-radius: 12px; padding: 16px; display: none; flex-direction: column; gap: 10px; z-index: 20; }
  #scriptPanel.open { display: flex; }
  #codeBox { flex: 1; width: 100%; background: #090b0e; color: #86efac; border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 12px; resize: none; }

  .bottom-panel { background: var(--panel); border-top: 1px solid var(--border); padding: 10px 16px 14px; display: flex; flex-direction: column; gap: 8px; }
  .prompt-row { display: flex; gap: 8px; }
  #promptInput { flex: 1; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border); font-size: 14px; outline: none; background: #11141c; color: #fff; }
  #promptInput:focus { border-color: var(--accent); }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>

<div class="topbar">
  <span class="brand">ROBLOX CLOUD 3D</span>
  <button class="pill" onclick="runPrompt('modern two story shop building')">Modern Building</button>
  <button class="pill" onclick="runPrompt('japanese red pagoda tower')">Pagoda Tower</button>
  <button class="pill" onclick="runPrompt('medieval stone castle fort')">Stone Castle</button>
  <button class="pill" onclick="runPrompt('cyberpunk skyscraper building')">Skyscraper</button>
  <button class="pill" onclick="runPrompt('astronaut holding flag')">Rigged Astronaut</button>
  <button class="pill" onclick="runPrompt('ryu karate fighter')">Rigged Fighter</button>
  <button class="pill" onclick="runPrompt('gundam mech exosuit')">Rigged Mech</button>
  <button class="pill" onclick="runPrompt('purple kraken octopus')">Rigged Kraken</button>
  <button class="pill" onclick="runPrompt('phoenix bird')">Rigged Phoenix</button>
  <button class="pill" onclick="runPrompt('magical horse unicorn')">Rigged Unicorn</button>
  <button class="pill" onclick="runPrompt('red sports car')">Sports Car</button>
  <button class="pill" onclick="runPrompt('mastersword blade')">Master Sword</button>
</div>

<div class="subheader">
  <div class="title-group">
    <span class="model-title" id="modelTitle">INITIALIZING PIPELINE...</span>
    <span class="badge" id="rigBadge">QA PASSED</span>
  </div>
  <div class="actions">
    <button class="btn-sm" onclick="downloadFile('obj')">DOWNLOAD .OBJ</button>
    <button class="btn-sm" onclick="downloadFile('lua')">DOWNLOAD .LUA</button>
    <button class="btn-sm" onclick="toggleScript()">VIEW LUAU / OBJ</button>
    <button class="btn-sm primary" onclick="copyLua()" id="copyBtn">COPY RIGGED STUDIO SCRIPT</button>
  </div>
</div>

<div class="workspace">
  <canvas id="viewport"></canvas>
  <div class="stats-pill" id="statsPill">0 parts • 0.0 × 0.0 × 0.0 studs</div>

  <div class="pipeline-sidebar">
    <div class="pipe-title">Autonomous 9-Stage Pipeline</div>
    <div id="pipelineSteps"></div>
  </div>

  <div id="scriptPanel">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <strong>Packaged Output (Roblox Luau with Motor6D Rigging)</strong>
      <div style="display:flex;gap:8px;">
        <button class="btn-sm primary" onclick="copyLua()">Copy Luau</button>
        <button class="btn-sm" onclick="toggleScript()">Close</button>
      </div>
    </div>
    <textarea id="codeBox" readonly></textarea>
  </div>
</div>

<div class="bottom-panel">
  <div class="prompt-row">
    <input type="text" id="promptInput" placeholder='Enter any building, character, creature, vehicle, or prop...' onkeydown="if(event.key==='Enter') generateNew()" />
    <button class="btn-sm" onclick="reviseModel()">Re-Roll Seed</button>
    <button class="btn-sm primary" style="padding:10px 18px;font-size:13px;" onclick="generateNew()">Build 3D Asset</button>
  </div>
</div>

<script>
let scene, camera, renderer, controls, modelGroup;
let currentSpec = null;
let currentPrompt = "modern two story shop building";
let currentIter = 0;

function init3D() {
  const canvas = document.getElementById("viewport");
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(42, canvas.clientWidth / canvas.clientHeight, 0.1, 500);
  camera.position.set(11, 8.5, -14);

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;

  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 2.8, 0);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 0.9));
  const dir = new THREE.DirectionalLight(0xffffff, 0.85);
  dir.position.set(15, 25, -18);
  dir.castShadow = true;
  scene.add(dir);

  const grid = new THREE.GridHelper(40, 40, 0x334155, 0x1e293b);
  scene.add(grid);

  modelGroup = new THREE.Group();
  scene.add(modelGroup);

  window.addEventListener("resize", () => {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();
}

function makeGeometry(shape, sz) {
  const [w, h, d] = sz;
  if (shape === "cylinder") return new THREE.CylinderGeometry(w/2, w/2, h, 24);
  if (shape === "sphere" || shape === "gem") return new THREE.SphereGeometry(Math.max(w,h,d)/2, 20, 16);
  if (shape === "pyramid") {
    const g = new THREE.ConeGeometry(Math.max(w, d) * 0.68, h, 4);
    g.rotateY(Math.PI / 4);
    return g;
  }
  if (shape === "wedge") {
    const hw = w/2, hh = h/2, hd = d/2;
    const geom = new THREE.BufferGeometry();
    const vertices = new Float32Array([
      -hw,-hh,-hd,  hw,-hh,-hd,  hw,-hh, hd, -hw,-hh, hd,
      -hw, hh, hd,  hw, hh, hd
    ]);
    geom.setIndex([0,1,2, 0,2,3, 3,2,5, 3,5,4, 0,4,5, 0,5,1, 0,3,4, 1,5,2]);
    geom.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
    geom.computeVertexNormals();
    return geom;
  }
  return new THREE.BoxGeometry(w, h, d);
}

function makeRobloxMaterial(hex, matName, tr) {
  const color = new THREE.Color(hex);
  const opts = { color, roughness: 0.35, metalness: 0.1 };
  if (matName === "Metal") { opts.roughness = 0.22; opts.metalness = 0.75; }
  if (matName === "Neon") { opts.emissive = color; opts.emissiveIntensity = 0.65; opts.roughness = 0.1; }
  if (matName === "Glass" || tr > 0) { opts.transparent = true; opts.opacity = 1.0 - (tr || 0.35); opts.roughness = 0.08; }
  if (matName === "Slate" || matName === "Cobblestone" || matName === "Brick") { opts.roughness = 0.78; }
  return new THREE.MeshStandardMaterial(opts);
}

function renderSpec(spec) {
  currentSpec = spec;
  while (modelGroup.children.length > 0) modelGroup.remove(modelGroup.children[0]);
  const pal = spec.palette || {};
  const nodes = {};

  (spec.parts || []).forEach(p => {
    const pivot = new THREE.Group();
    pivot.position.set(p.po[0], p.po[1], p.po[2]);
    pivot.rotation.set(
      THREE.MathUtils.degToRad(p.ro[0] || 0),
      THREE.MathUtils.degToRad(p.ro[1] || 0),
      THREE.MathUtils.degToRad(p.ro[2] || 0)
    );
    const hex = pal[p.c] || (String(p.c).startsWith("#") ? p.c : "#cccccc");
    const mat = makeRobloxMaterial(hex, p.mat || "SmoothPlastic", p.tr || 0);
    const mesh = new THREE.Mesh(makeGeometry(p.s, p.sz), mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    pivot.add(mesh);
    nodes[p.n] = pivot;
  });

  (spec.parts || []).forEach(p => {
    if (p.p && nodes[p.p]) nodes[p.p].add(nodes[p.n]);
    else modelGroup.add(nodes[p.n]);
  });

  const b = spec.bounds || [6, 6, 6];
  const isRig = spec.meta && spec.meta.riggable;
  document.getElementById("modelTitle").textContent = `${(spec.meta && spec.meta.prompt) ? spec.meta.prompt : spec.name} (${spec.archetype})`;
  document.getElementById("rigBadge").textContent = isRig ? "MOTOR6D RIG + QA PASS" : "WELDED ASSET + QA PASS";
  document.getElementById("statsPill").textContent = `${spec.parts.length} Roblox parts • ${b[0]} × ${b[1]} × ${b[2]} studs`;
  document.getElementById("codeBox").value = spec.lua || "";

  const logBox = document.getElementById("pipelineSteps");
  logBox.innerHTML = (spec.pipeline_logs || []).map(item => `
    <div class="step-card">
      <div class="step-stage">${item.stage.replace(/_/g, ' ')}</div>
      <div class="step-msg">${item.msg}</div>
    </div>
  `).join("");

  controls.target.set(0, Math.max(1.8, b[1] * 0.45), 0);
  controls.update();
}

async function fetchModel(prompt, iteration) {
  document.getElementById("modelTitle").textContent = "RUNNING 9-STAGE PIPELINE...";
  const res = await fetch("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, iteration, nonce: String(Date.now()) })
  });
  const data = await res.json();
  renderSpec(data);
}

function runPrompt(p) {
  currentPrompt = p; currentIter = 0;
  document.getElementById("promptInput").value = p;
  fetchModel(p, 0);
}

function generateNew() {
  currentPrompt = document.getElementById("promptInput").value.trim() || currentPrompt;
  currentIter = 0;
  fetchModel(currentPrompt, 0);
}

function reviseModel() {
  currentIter += 1;
  fetchModel(currentPrompt, currentIter);
}

function toggleScript() {
  document.getElementById("scriptPanel").classList.toggle("open");
}

function copyLua() {
  if (!currentSpec || !currentSpec.lua) return;
  navigator.clipboard.writeText(currentSpec.lua);
  const btn = document.getElementById("copyBtn");
  btn.textContent = "COPIED TO CLIPBOARD!";
  setTimeout(() => { btn.textContent = "COPY RIGGED STUDIO SCRIPT"; }, 1800);
}

function downloadFile(ext) {
  if (!currentSpec) return;
  const content = ext === "obj" ? currentSpec.obj : currentSpec.lua;
  const blob = new Blob([content], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${currentSpec.name || "roblox_asset"}.${ext}`;
  a.click();
}

window.addEventListener("DOMContentLoaded", () => {
  init3D();
  runPrompt("modern two story shop building");
});
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, raw_bytes, content_type="application/json; charset=utf-8", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw_bytes)))
        self.end_headers()
        self.wfile.write(raw_bytes)

    def _send_json(self, data, status=200):
        self._send(json.dumps(data).encode("utf-8"), "application/json; charset=utf-8", status)

    def do_OPTIONS(self):
        self._send_json({"ok": True})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            return self._send(HTML_UI.encode("utf-8"), "text/html; charset=utf-8", 200)
        if path.startswith("/health"):
            return self._send_json({"ok": True, "scheme": "roblox_cloud_v1"})
        if path.startswith("/memory"):
            return self._send_json(load_mem())
        if path.startswith("/generate") or path.startswith("/api/generate"):
            qs = parse_qs(parsed.query)
            prompt = (qs.get("prompt") or ["modern two story shop building"])[0]
            return self._send_json(brain.generate({"prompt": prompt, "iteration": 0}, load_mem()))
        if path.startswith("/test"):
            results = {}
            for p in ("modern house building", "pagoda tower", "astronaut", "purple kraken", "sports car", "unicorn"):
                spec, I = brain.build_one(p)
                checks = brain.structural_checks(spec, I)
                results[p] = {"ok": all(v for _, v in checks), "parts": len(spec["parts"])}
            return self._send_json({"ok": all(r["ok"] for r in results.values()), "results": results})
        return self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw or "{}")
        except Exception:
            body = {}
        mem = load_mem()
        if self.path.startswith("/generate") or self.path.startswith("/api/generate") or self.path.startswith("/revise"):
            return self._send_json(brain.generate(body, mem))
        if self.path.startswith("/feedback") or self.path.startswith("/like"):
            return self._send_json({"ok": True})
        return self._send_json({"error": "unknown endpoint"}, 404)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Roblox Cloud 3D Modeler live at http://0.0.0.0:{port}")
    srv.serve_forever()
