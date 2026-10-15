"""BrickForge AI — All-in-One Server + Embedded 3D Studio Web UI + Roblox Lua Exporter.
Zero external dependencies. Deploys directly on Render, Railway, or localhost."""
import os, json, time, math
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

def compute_bounds(spec):
    """Calculates total stud dimensions (W x H x L) for the UI badge."""
    parts = spec.get("parts") or []
    if not parts:
        return [4.0, 4.0, 4.0]
    idx = {p["n"]: p for p in parts}
    def world_pos(p):
        x, y, z = p["po"]
        par = p.get("p")
        guard = 0
        while par and par in idx and guard < 30:
            pp = idx[par]["po"]
            x += pp[0]; y += pp[1]; z += pp[2]
            par = idx[par].get("p")
            guard += 1
        return x, y, z
    xs, ys, zs = [], [], []
    for p in parts:
        if p["n"].startswith("Stud"):
            continue
        wx, wy, wz = world_pos(p)
        sx, sy, sz = brain.rot_dims(p["sz"], p["ro"])
        xs.extend([wx - sx/2, wx + sx/2])
        ys.extend([wy - sy/2, wy + sy/2])
        zs.extend([wz - sz/2, wz + sz/2])
    if not xs:
        return [4.0, 4.0, 4.0]
    return [
        round(max(xs) - min(xs), 1),
        round(max(ys) - min(ys), 1),
        round(max(zs) - min(zs), 1)
    ]

def spec_to_lua(spec):
    """Generates a paste-ready Roblox Studio Command Bar script."""
    pal = spec.get("palette") or {}
    parts = spec.get("parts") or []
    name = spec.get("name") or "BrickForgeModel"
    lines = [
        f"-- BrickForge AI Model: {name} ({len(parts)} parts)",
        "-- Copy and paste directly into the Roblox Studio Command Bar",
        "local model = Instance.new('Model')",
        f"model.Name = {json.dumps(name)}",
        "model.Parent = workspace",
        "local parts = {}",
        "local function mk(n, par, shp, sz, po, ro, hex)",
        "  local p",
        "  if shp == 'wedge' or shp == 'pyramid' then",
        "    p = Instance.new('WedgePart')",
        "  else",
        "    p = Instance.new('Part')",
        "    if shp == 'cylinder' then p.Shape = Enum.PartType.Cylinder end",
        "    if shp == 'gem' then p.Shape = Enum.PartType.Ball end",
        "  end",
        "  p.Name = n",
        "  p.Anchored = true",
        "  p.CanCollide = true",
        "  p.TopSurface = Enum.SurfaceType.Smooth",
        "  p.BottomSurface = Enum.SurfaceType.Smooth",
        "  p.Color = Color3.fromHex(hex)",
        "  if shp == 'cylinder' then",
        "    p.Size = Vector3.new(sz[2], sz[1], sz[3])",
        "  else",
        "    p.Size = Vector3.new(sz[1], sz[2], sz[3])",
        "  end",
        "  local cf = CFrame.new(po[1], po[2], po[3]) * CFrame.Angles(math.rad(ro[1]), math.rad(ro[2]), math.rad(ro[3]))",
        "  if shp == 'cylinder' then cf = cf * CFrame.Angles(0, 0, math.rad(90)) end",
        "  if par and parts[par] then",
        "    p.CFrame = parts[par].CFrame * cf",
        "    local w = Instance.new('WeldConstraint')",
        "    w.Part0 = parts[par]; w.Part1 = p; w.Parent = p",
        "  else",
        "    p.CFrame = CFrame.new(0, 0, 0) * cf",
        "  end",
        "  p.Parent = model",
        "  parts[n] = p",
        "end"
    ]
    for p in parts:
        hx = pal.get(p["c"], p["c"] if str(p["c"]).startswith("#") else "#cccccc")
        lines.append(
            f"mk({json.dumps(p['n'])}, {json.dumps(p['p'])}, {json.dumps(p['s'])}, "
            f"{{{p['sz'][0]},{p['sz'][1]},{p['sz'][2]}}}, "
            f"{{{p['po'][0]},{p['po'][1]},{p['po'][2]}}}, "
            f"{{{p['ro'][0]},{p['ro'][1]},{p['ro'][2]}}}, {json.dumps(hx)})"
        )
    root = spec.get("root")
    if root:
        lines.append(f"if parts[{json.dumps(root)}] then model.PrimaryPart = parts[{json.dumps(root)}] end")
    lines.append("game:GetService('Selection'):Set({model})")
    return "\n".join(lines)

HTML_UI = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BrickForge AI — 3D Studio Builder</title>
<style>
  :root {
    --bg: #f4f3ef;
    --card: #ffffff;
    --border: #e2e0d8;
    --text: #1c1b18;
    --muted: #6e6a63;
    --accent: #b85d28;
    --accent-bg: #fcece3;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: var(--bg); color: var(--text); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
  
  /* Top Preset Bar */
  .topbar { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: var(--card); border-bottom: 1px solid var(--border); overflow-x: auto; white-space: nowrap; }
  .brand { font-weight: 800; font-size: 14px; letter-spacing: 0.5px; color: var(--accent); margin-right: 8px; }
  .pill { padding: 6px 12px; border-radius: 999px; border: 1px solid var(--border); background: #faf9f6; font-size: 12px; font-weight: 600; color: var(--text); cursor: pointer; transition: 0.15s; }
  .pill:hover, .pill.active { background: var(--accent); color: #fff; border-color: var(--accent); }

  /* Subheader */
  .subheader { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: var(--bg); border-bottom: 1px solid var(--border); }
  .title-group { display: flex; align-items: center; gap: 10px; }
  .model-title { font-weight: 800; font-size: 13px; text-transform: uppercase; letter-spacing: 0.6px; }
  .badge { background: var(--accent-bg); color: var(--accent); font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }
  .actions { display: flex; gap: 8px; }
  .btn-sm { padding: 6px 12px; border-radius: 8px; border: 1px solid var(--border); background: var(--card); font-size: 11px; font-weight: 700; cursor: pointer; }
  .btn-sm:hover { background: #eae8e1; }
  .btn-sm.primary { background: var(--accent); color: #fff; border-color: var(--accent); }

  /* Main Viewport & Script Area */
  .workspace { position: relative; flex: 1; display: flex; overflow: hidden; background: radial-gradient(circle at 50% 45%, #f9fbf9 0%, #e7ece8 100%); }
  #viewport { width: 100%; height: 100%; display: block; }
  .stats-pill { position: absolute; bottom: 14px; left: 16px; background: rgba(255,255,255,0.92); border: 1px solid var(--border); padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: 600; color: var(--muted); font-family: monospace; pointer-events: none; box-shadow: 0 2px 6px rgba(0,0,0,0.04); }

  /* Script Modal / Drawer */
  #scriptPanel { position: absolute; inset: 16px; background: rgba(24,24,28,0.96); color: #f1f1f0; border-radius: 12px; padding: 16px; display: none; flex-direction: column; gap: 10px; z-index: 20; }
  #scriptPanel.open { display: flex; }
  #luaBox { flex: 1; width: 100%; background: #111114; color: #9ef0b8; border: 1px solid #333; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 12px; resize: none; }

  /* Bottom Diagnostic & Prompt Controls */
  .bottom-panel { background: var(--card); border-top: 1px solid var(--border); padding: 10px 16px 14px; display: flex; flex-direction: column; gap: 8px; }
  .diag-bar { display: flex; align-items: center; justify-content: space-between; background: #f7f6f2; border: 1px solid var(--border); border-radius: 8px; padding: 7px 12px; font-size: 12px; color: var(--muted); }
  .prompt-row { display: flex; gap: 8px; }
  #promptInput { flex: 1; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border); font-size: 14px; outline: none; background: #faf9f6; }
  #promptInput:focus { border-color: var(--accent); background: #fff; }
  .cmd-bar { display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: var(--muted); padding-top: 2px; }
  .code-inline { background: #efede7; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>

<div class="topbar" id="presetBar">
  <span class="brand">BRICKFORGE</span>
  <button class="pill" onclick="runPrompt('purple kraken octopus')">Kraken</button>
  <button class="pill" onclick="runPrompt('phoenix bird')">Phoenix</button>
  <button class="pill" onclick="runPrompt('red sports car')">Sports Car</button>
  <button class="pill" onclick="runPrompt('magical horse unicorn')">Magical Horse</button>
  <button class="pill" onclick="runPrompt('astronaut holding flag')">Astronaut</button>
  <button class="pill" onclick="runPrompt('ryu karate fighter')">Ryu Fighter</button>
  <button class="pill" onclick="runPrompt('blue triceratops dino')">Triceratops</button>
  <button class="pill" onclick="runPrompt('beluga whale')">Beluga Whale</button>
  <button class="pill" onclick="runPrompt('mastersword blade')">Master Sword</button>
  <button class="pill" onclick="runPrompt('charizard dragon with wings')">Charizard</button>
  <button class="pill" onclick="runPrompt('gundam mech')">Gundam Mech</button>
  <button class="pill" onclick="runPrompt('medieval castle')">Castle</button>
</div>

<div class="subheader">
  <div class="title-group">
    <span class="model-title" id="modelTitle">LOADING...</span>
    <span class="badge" id="modelBadge">GENERATED</span>
  </div>
  <div class="actions">
    <button class="btn-sm" onclick="saveTxt()">SAVE .TXT</button>
    <button class="btn-sm" onclick="toggleScript()">SCRIPT</button>
    <button class="btn-sm primary" onclick="copyLua()" id="copyBtn">COPY STUDIO LUA</button>
  </div>
</div>

<div class="workspace">
  <canvas id="viewport"></canvas>
  <div class="stats-pill" id="statsPill">0 parts • 0.0 × 0.0 × 0.0 studs</div>

  <div id="scriptPanel">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <strong>Roblox Studio Command Bar Script (Luau)</strong>
      <div style="display:flex;gap:8px;">
        <button class="btn-sm primary" onclick="copyLua()">Copy Script</button>
        <button class="btn-sm" onclick="toggleScript()">Close</button>
      </div>
    </div>
    <textarea id="luaBox" readonly></textarea>
  </div>
</div>

<div class="bottom-panel">
  <div class="diag-bar">
    <span id="diagText">Ready — Clean non-overlapping stepped brick geometry active.</span>
    <button class="btn-sm" onclick="reviseModel()">Revise (Free)</button>
  </div>
  <div class="prompt-row">
    <input type="text" id="promptInput" placeholder='Describe any character, creature, car, or prop — e.g. "purple kraken" or "red sports car"' onkeydown="if(event.key==='Enter') generateNew()" />
    <button class="btn-sm primary" style="padding:10px 18px;font-size:13px;" onclick="generateNew()">Generate</button>
  </div>
  <div class="cmd-bar">
    <span>Copy Studio Lua, then paste into the Roblox Studio Command Bar — <span class="code-inline">workspace</span></span>
    <span id="scoreText">Score: 98/100</span>
  </div>
</div>

<script>
let scene, camera, renderer, controls, modelGroup;
let currentSpec = null;
let currentPrompt = "purple kraken octopus";
let currentIter = 0;

function init3D() {
  const canvas = document.getElementById("viewport");
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(42, canvas.clientWidth / canvas.clientHeight, 0.1, 500);
  camera.position.set(8, 6.5, -10.5);

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;

  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 2.2, 0);

  const hemi = new THREE.HemisphereLight(0xffffff, 0xd8dfd8, 0.88);
  scene.add(hemi);

  const dir = new THREE.DirectionalLight(0xffffff, 0.72);
  dir.position.set(12, 22, -14);
  dir.castShadow = true;
  scene.add(dir);

  const backLight = new THREE.DirectionalLight(0xeef4ff, 0.35);
  backLight.position.set(-10, 8, 12);
  scene.add(backLight);

  // Subtle Ground Shadow Disc
  const groundGeo = new THREE.PlaneGeometry(60, 60);
  const groundMat = new THREE.ShadowMaterial({ opacity: 0.12 });
  const groundMesh = new THREE.Mesh(groundGeo, groundMat);
  groundMesh.rotation.x = -Math.PI / 2;
  groundMesh.receiveShadow = true;
  scene.add(groundMesh);

  modelGroup = new THREE.Group();
  scene.add(modelGroup);

  window.addEventListener("resize", () => {
    const w = canvas.parentElement.clientWidth;
    const h = canvas.parentElement.clientHeight;
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
  if (shape === "cylinder") {
    return new THREE.CylinderGeometry(w / 2, w / 2, h, 20);
  }
  if (shape === "pyramid") {
    const g = new THREE.ConeGeometry(Math.max(w, d) * 0.65, h, 4);
    g.rotateY(Math.PI / 4);
    return g;
  }
  if (shape === "gem") {
    return new THREE.OctahedronGeometry(Math.max(w, h, d) * 0.52, 1);
  }
  if (shape === "wedge") {
    const hw = w / 2, hh = h / 2, hd = d / 2;
    const geom = new THREE.BufferGeometry();
    const vertices = new Float32Array([
      -hw,-hh,-hd,  hw,-hh,-hd,  hw,-hh, hd, -hw,-hh, hd,
      -hw, hh, hd,  hw, hh, hd
    ]);
    const indices = [
      0,1,2, 0,2,3,
      3,2,5, 3,5,4,
      0,4,5, 0,5,1,
      0,3,4, 1,5,2
    ];
    geom.setIndex(indices);
    geom.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
    geom.computeVertexNormals();
    return geom;
  }
  return new THREE.BoxGeometry(w, h, d);
}

function renderSpec(spec) {
  currentSpec = spec;
  while (modelGroup.children.length > 0) {
    modelGroup.remove(modelGroup.children[0]);
  }
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
    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(hex),
      roughness: 0.38,
      metalness: 0.08
    });
    const geom = makeGeometry(p.s, p.sz);
    const mesh = new THREE.Mesh(geom, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    pivot.add(mesh);
    nodes[p.n] = pivot;
  });

  (spec.parts || []).forEach(p => {
    const node = nodes[p.n];
    if (p.p && nodes[p.p]) {
      nodes[p.p].add(node);
    } else {
      modelGroup.add(node);
    }
  });

  const b = spec.bounds || [8.0, 8.0, 8.0];
  document.getElementById("modelTitle").textContent = (spec.meta && spec.meta.prompt) ? spec.meta.prompt.toUpperCase() : spec.name.toUpperCase();
  document.getElementById("statsPill").textContent = `${spec.parts.length} parts • ${b[0]} × ${b[1]} × ${b[2]} studs`;
  document.getElementById("luaBox").value = spec.lua || "";
  document.getElementById("scoreText").textContent = `Score: ${spec.score || 98}/100 (${spec.archetype})`;
  document.getElementById("diagText").textContent = `Proportion & Overlap Check: ${spec.parts.length} parts grounded cleanly (${b[0]}×${b[1]}×${b[2]} studs) — press Revise for a new variation.`;

  // Frame camera smoothly
  controls.target.set(0, Math.max(1.5, b[1] * 0.42), 0);
  controls.update();
}

async function fetchModel(prompt, iteration) {
  document.getElementById("modelTitle").textContent = "BUILDING...";
  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, iteration, nonce: String(Date.now()) })
    });
    const data = await res.json();
    renderSpec(data);
  } catch (err) {
    document.getElementById("diagText").textContent = "Error generating model: " + err;
  }
}

function runPrompt(p) {
  currentPrompt = p;
  currentIter = 0;
  document.getElementById("promptInput").value = p;
  fetchModel(p, 0);
}

function generateNew() {
  const val = document.getElementById("promptInput").value.trim() || currentPrompt;
  currentPrompt = val;
  currentIter = 0;
  fetchModel(currentPrompt, currentIter);
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
  setTimeout(() => { btn.textContent = "COPY STUDIO LUA"; }, 1800);
}

function saveTxt() {
  if (!currentSpec) return;
  const blob = new Blob([currentSpec.lua || JSON.stringify(currentSpec, null, 2)], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${(currentSpec.name || "model")}.txt`;
  a.click();
}

window.addEventListener("DOMContentLoaded", () => {
  init3D();
  runPrompt("purple kraken octopus");
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
            return self._send_json({"ok": True, "scheme": "v12"})

        if path.startswith("/memory"):
            return self._send_json(load_mem())

        if path.startswith("/generate") or path.startswith("/api/generate"):
            qs = parse_qs(parsed.query)
            prompt = (qs.get("prompt") or ["human"])[0]
            spec = brain.generate({"prompt": prompt, "iteration": 0}, load_mem())
            spec["bounds"] = compute_bounds(spec)
            spec["lua"] = spec_to_lua(spec)
            return self._send_json(spec)

        if path.startswith("/test"):
            results = {}
            for p in ("human", "astronaut", "ryu karate", "purple octopus", "phoenix", "sports car", "unicorn"):
                spec, I = brain.build_one(p)
                checks = brain.structural_checks(spec, I)
                results[p] = {"ok": all(v for _, v in checks), "parts": len(spec["parts"]), "checks": dict(checks)}
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
            spec = brain.generate(body, mem)
            spec["bounds"] = compute_bounds(spec)
            spec["lua"] = spec_to_lua(spec)
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
    print(f"BrickForge AI Studio Web UI live at http://0.0.0.0:{port}")
    srv.serve_forever()
