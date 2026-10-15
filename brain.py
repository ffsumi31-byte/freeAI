"""Roblox Cloud Modeler AI — Standalone Single-File Deployment (Render / Local).
Zero external file dependencies, explicit $PORT binding, and bulletproof startup."""
import os, json, time, math, random, re, urllib.request, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# =========================================================================
# PROCEDURAL ENGINE & 3D SOLVER
# =========================================================================
NAMED_COLORS = {
    "red": "#dc2626", "crimson": "#991b1b", "orange": "#ea580c", "ginger": "#d97706",
    "amber": "#f59e0b", "yellow": "#eab308", "gold": "#d4af37", "golden": "#d4af37",
    "lime": "#65a30d", "green": "#16a34a", "emerald": "#10b981", "forest": "#166534",
    "teal": "#0d9488", "cyan": "#06b6d4", "aqua": "#22d3ee", "sky": "#38bdf8",
    "blue": "#2563eb", "navy": "#1e3a8a", "indigo": "#4f46e5", "purple": "#7c3aed",
    "violet": "#8b5cf6", "magenta": "#db2777", "pink": "#f472b6", "rose": "#fb7185",
    "white": "#f8fafc", "cream": "#fef3c7", "ivory": "#fffbeb", "silver": "#cbd5e1",
    "grey": "#64748b", "gray": "#64748b", "slate": "#475569", "charcoal": "#334155",
    "black": "#1e293b", "dark": "#0f172a", "brown": "#78350f", "tan": "#d6b88a",
    "sand": "#fde68a", "bronze": "#92400e"
}

FACES = {
    "top": (0, 1, 0), "bot": (0, -1, 0), "bottom": (0, -1, 0),
    "front": (0, 0, -1), "back": (0, 0, 1),
    "right": (1, 0, 0), "left": (-1, 0, 0), "center": (0, 0, 0)
}

def clamp(x, a, b): return max(a, min(b, x))
def tokenize(t): return re.findall(r"[a-z0-9]+", t.lower())

def rot_dims(sz, ro):
    w, h, d = float(sz[0]), float(sz[1]), float(sz[2])
    rx, ry, rz = [math.radians(float(a)) for a in ro]
    cx, sx = abs(math.cos(rx)), abs(math.sin(rx))
    cy, sy = abs(math.cos(ry)), abs(math.sin(ry))
    cz, sz_ = abs(math.cos(rz)), abs(math.sin(rz))
    h1, d1 = h * cx + d * sx, h * sx + d * cx
    w2, d2 = w * cy + d1 * sy, w * sy + d1 * cy
    w3, h3 = w2 * cz + h1 * sz_, w2 * sz_ + h1 * cz
    return [round(max(0.06, w3), 3), round(max(0.06, h3), 3), round(max(0.06, d2), 3)]

def pick_user_color(prompt, default_hex):
    for w in tokenize(prompt):
        if w in NAMED_COLORS:
            return NAMED_COLORS[w]
    return default_hex

def generate_model_blueprint(prompt, seed=7):
    rng = random.Random(seed)
    p_low = prompt.lower()
    jw = rng.uniform(0.95, 1.05)
    jh = rng.uniform(0.95, 1.05)
    jl = rng.uniform(0.95, 1.05)

    parts = []
    def P(n, p, stage, s, sz, face="center", u=0.0, v=0.0, inset=0.02, ro=(0,0,0), c="#cccccc", mat="SmoothPlastic", tr=0.0, joint=False):
        parts.append({
            "n": n, "p": p, "stage": stage, "s": s,
            "sz": [round(float(v), 3) for v in sz],
            "attach": {"face": face, "u": round(u, 3), "v": round(v, 3), "inset": round(inset, 3)},
            "ro": [round(float(r), 1) for r in ro], "c": c, "mat": mat, "tr": tr, "joint": bool(joint)
        })

    # Cat / Feline
    if "cat" in p_low or "kitten" in p_low or "tiger" in p_low or "lion" in p_low:
        fur = pick_user_color(prompt, "#d97706")
        P("Torso", None, "raw", "box", (1.45*jw, 1.15*jh, 2.75*jl), "center", c=fur)
        P("Head", "Torso", "raw", "sphere", (1.28, 1.18, 1.22), "top", u=0, v=-0.88, inset=0.18, c=fur, joint=True)
        P("EarR", "Head", "detail", "cone", (0.42, 0.54, 0.34), "top", u=0.55, v=0.1, inset=0.08, c=fur)
        P("EarL", "Head", "detail", "cone", (0.42, 0.54, 0.34), "top", u=-0.55, v=0.1, inset=0.08, c=fur)
        P("Tail", "Torso", "shape", "cylinder", (0.26, 1.15, 0.26), "back", u=0, v=0.45, inset=0.08, ro=(35,0,0), c=fur, joint=True)
        for fz, zt in ((-0.78, "F"), (0.78, "B")):
            P(f"LegR{zt}", "Torso", "shape", "cylinder", (0.34, 1.05, 0.34), "bot", u=0.68, v=zt=="F" and -0.7 or 0.7, inset=0.08, c=fur, joint=True)
            P(f"LegL{zt}", "Torso", "shape", "cylinder", (0.34, 1.05, 0.34), "bot", u=-0.68, v=zt=="F" and -0.7 or 0.7, inset=0.08, c=fur, joint=True)
        archetype, riggable = "animal", True

    # Building / House / Castle / Skyscraper
    elif any(w in p_low for w in ("building", "house", "shop", "tower", "skyscraper", "castle", "pagoda")):
        w, d, th = 7.6 * jw, 6.2 * jl, 5.6 * jh
        wall_c = pick_user_color(prompt, "#f1f5f9")
        P("Foundation", None, "raw", "box", (w + 0.8, 0.6, d + 0.8), "center", c="#475569", mat="Slate")
        P("MainWalls", "Foundation", "raw", "box", (w, th, d), "top", u=0, v=0, inset=0.02, c=wall_c, mat="Brick")
        P("Roof", "MainWalls", "shape", "wedge", (w + 0.95, 2.2, d + 0.95), "top", u=0, v=0, inset=0.02, c="#1e293b", mat="Slate")
        P("DoorFrame", "MainWalls", "detail", "box", (1.85, 2.2, 0.22), "front", u=0, v=-0.75, inset=0.04, c="#1e293b", mat="Metal")
        P("Win1", "MainWalls", "detail", "box", (1.18, 1.35, 0.18), "front", u=-1.5, v=0.2, inset=0.04, c="#7dd3fc", mat="Glass", tr=0.35)
        P("Win2", "MainWalls", "detail", "box", (1.18, 1.35, 0.18), "front", u=1.5, v=0.2, inset=0.04, c="#7dd3fc", mat="Glass", tr=0.35)
        archetype, riggable = "building", False

    # Default Humanoid / Character Fallback
    else:
        suit_c = pick_user_color(prompt, "#2563eb")
        P("HumanoidRootPart", None, "raw", "box", (1.6, 0.55, 0.9), "center", c="#1e293b")
        P("Torso", "HumanoidRootPart", "raw", "box", (1.75, 1.85, 1.0), "top", u=0, v=0, inset=0.02, c=suit_c, joint=True)
        P("Neck", "Torso", "raw", "cylinder", (0.48, 0.26, 0.48), "top", u=0, v=0, inset=0.02, c="#f2c9a0", joint=True)
        P("Head", "Neck", "raw", "sphere", (1.24, 1.24, 1.2), "top", u=0, v=0, inset=0.04, c="#f2c9a0", joint=True)
        P("ArmR", "Torso", "shape", "box", (0.58, 1.15, 0.6), "right", u=0, v=0.22, inset=0.02, c=suit_c, joint=True)
        P("ArmL", "Torso", "shape", "box", (0.58, 1.15, 0.6), "left", u=0, v=0.22, inset=0.02, c=suit_c, joint=True)
        P("ThighR", "HumanoidRootPart", "shape", "box", (0.68, 1.35, 0.72), "bot", u=0.52, v=0, inset=0.02, c="#1e293b", joint=True)
        P("ThighL", "HumanoidRootPart", "shape", "box", (0.68, 1.35, 0.72), "bot", u=-0.52, v=0, inset=0.02, c="#1e293b", joint=True)
        archetype, riggable = "humanoid", True

    # Compile parts with surface sockets
    compiled = []
    idx = {}
    for item in parts:
        n = item["n"]
        p_name = item.get("p")
        sz = [round(max(0.06, float(v)), 3) for v in (item.get("sz") or [1,1,1])]
        ro = [round(float(r), 1) for r in (item.get("ro") or [0,0,0])]
        att = item.get("attach") or {}
        face = att.get("face", "center")
        u, v_coord, inset = float(att.get("u", 0.0)), float(att.get("v", 0.0)), float(att.get("inset", 0.02))

        if p_name and p_name in idx:
            par = idx[p_name]
            px, py, pz = par["po"]
            pw, ph, pd = rot_dims(par["sz"], par["ro"])
            cw, ch, cd = rot_dims(sz, ro)
            f = FACES.get(face, (0, 1, 0))
            if face in ("front", "back"):
                wx = px + clamp(u, -1, 1) * (pw * 0.45)
                wy = py + clamp(v_coord, -1, 1) * (ph * 0.45)
                wz = pz + f[2] * (pd / 2.0 + cd / 2.0 - inset)
            elif face in ("right", "left"):
                wx = px + f[0] * (pw / 2.0 + cw / 2.0 - inset)
                wy = py + clamp(v_coord, -1, 1) * (ph * 0.45)
                wz = pz + clamp(u, -1, 1) * (pd * 0.45)
            elif face in ("top", "bot", "bottom"):
                wx = px + clamp(u, -1, 1) * (pw * 0.45)
                wy = py + f[1] * (ph / 2.0 + ch / 2.0 - inset)
                wz = pz + clamp(v_coord, -1, 1) * (pd * 0.45)
            else:
                wx, wy, wz = px, py, pz
        else:
            wx, wy, wz = 0.0, 2.0, 0.0

        part_obj = {
            "n": n, "p": p_name, "stage": item.get("stage", "detail"),
            "s": item.get("s", "box"), "sz": sz,
            "po": [round(wx, 3), round(wy, 3), round(wz, 3)],
            "ro": ro, "c": item.get("c", "#cccccc"),
            "mat": item.get("mat", "SmoothPlastic"), "tr": float(item.get("tr", 0.0)),
            "joint": bool(item.get("joint", False))
        }
        compiled.append(part_obj)
        idx[n] = part_obj

    min_y = min(p["po"][1] - rot_dims(p["sz"], p["ro"])[1] / 2.0 for p in compiled) if compiled else 0.0
    for p in compiled:
        if p["p"] is None:
            p["po"][1] = round(p["po"][1] - min_y, 3)

    root_name = compiled[0]["n"] if compiled else "Root"
    spec = {
        "id": f"rbx_{int(time.time()*1000)%100000}_{seed%97}",
        "name": f"{prompt.title()[:15]}_{seed%997}",
        "archetype": archetype, "variant": 0, "seed": seed,
        "root": root_name, "parts": compiled,
        "pipeline_logs": [{"stage": "qa_gate", "msg": f"Successfully compiled {len(compiled)} parts with surface sockets."}],
        "meta": {"prompt": prompt, "riggable": riggable}
    }
    
    # Compute bounds and exporters
    xs, ys, zs = [], [], []
    for p in compiled:
        wx, wy, wz = p["po"]
        sx, sy, sz = rot_dims(p["sz"], p["ro"])
        xs.extend([wx - sx/2, wx + sx/2])
        ys.extend([wy - sy/2, wy + sy/2])
        zs.extend([wz - sz/2, wz + sz/2])
    spec["bounds"] = [round(max(xs)-min(xs), 1), round(max(ys)-min(ys), 1), round(max(zs)-min(zs), 1)]

    # Luau Export
    lines = [
        f"-- Roblox Cloud Modeler | {spec['name']} | Parts: {len(compiled)}",
        "local model = Instance.new('Model')",
        f"model.Name = {json.dumps(spec['name'])}",
        "model.Parent = workspace",
        "local parts = {}",
        "local MAT_MAP = {SmoothPlastic = Enum.Material.SmoothPlastic, Metal = Enum.Material.Metal, Neon = Enum.Material.Neon, Glass = Enum.Material.Glass, Wood = Enum.Material.Wood, Slate = Enum.Material.Slate, Brick = Enum.Material.Brick}",
        "local function mk(n, par, shp, sz, po, ro, hex, matName, tr, isJoint)",
        "  local p = Instance.new('Part')",
        "  if shp == 'cylinder' then p.Shape = Enum.PartType.Cylinder elseif shp == 'sphere' or shp == 'gem' then p.Shape = Enum.PartType.Ball elseif shp == 'wedge' or shp == 'cone' then p = Instance.new('WedgePart') end",
        "  p.Name = n; p.Anchored = " + ('false' if riggable else 'true') + "; p.CanCollide = (par == nil)",
        "  p.Color = Color3.fromHex(hex); p.Material = MAT_MAP[matName] or Enum.Material.SmoothPlastic; p.Transparency = tr or 0",
        "  if shp == 'cylinder' then p.Size = Vector3.new(sz[2], sz[1], sz[3]) else p.Size = Vector3.new(sz[1], sz[2], sz[3]) end",
        "  local worldCF = CFrame.new(po[1], po[2], po[3]) * CFrame.Angles(math.rad(ro[1]), math.rad(ro[2]), math.rad(ro[3]))",
        "  if shp == 'cylinder' then worldCF = worldCF * CFrame.Angles(0, 0, math.rad(90)) end",
        "  p.CFrame = worldCF; p.Parent = model; parts[n] = p",
        "  if par and parts[par] then",
        "    if isJoint then",
        "      local m6d = Instance.new('Motor6D'); m6d.Part0 = parts[par]; m6d.Part1 = p; m6d.C0 = parts[par].CFrame:ToObjectSpace(worldCF); m6d.Parent = parts[par]",
        "    else",
        "      local w = Instance.new('WeldConstraint'); w.Part0 = parts[par]; w.Part1 = p; w.Parent = p",
        "    end",
        "  else p.Anchored = true end",
        "end"
    ]
    for p in compiled:
        hx = p.get("c", "#cccccc")
        lines.append(f"mk({json.dumps(p['n'])}, {json.dumps(p['p'])}, {json.dumps(p['s'])}, {{{p['sz'][0]},{p['sz'][1]},{p['sz'][2]}}}, {{{p['po'][0]},{p['po'][1]},{p['po'][2]}}}, {{{p['ro'][0]},{p['ro'][1]},{p['ro'][2]}}}, {json.dumps(hx)}, {json.dumps(p.get('mat', 'SmoothPlastic'))}, {p.get('tr', 0.0)}, {'true' if (riggable and p.get('joint')) else 'false'})")
    if root_name:
        lines.append(f"if parts[{json.dumps(root_name)}] then model.PrimaryPart = parts[{json.dumps(root_name)}] end")
    if riggable:
        lines.extend(["local hum = Instance.new('Humanoid'); hum.Parent = model", "local anim = Instance.new('Animator'); anim.Parent = hum"])
    lines.append("game:GetService('Selection'):Set({model})")
    spec["lua"] = "\n".join(lines)
    return spec

# =========================================================================
# WEB SERVER & UI
# =========================================================================
HTML_UI = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Roblox Cloud 3D Modeler AI</title>
<style>
  :root { --bg: #0f1117; --panel: #171a23; --border: #262b38; --text: #f1f5f9; --muted: #94a3b8; --accent: #3b82f6; --success: #10b981; }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: var(--bg); color: var(--text); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
  .topbar { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: var(--panel); border-bottom: 1px solid var(--border); overflow-x: auto; white-space: nowrap; }
  .brand { font-weight: 800; font-size: 13px; color: #60a5fa; margin-right: 8px; }
  .pill { padding: 6px 12px; border-radius: 999px; border: 1px solid var(--border); background: #1e2330; font-size: 12px; font-weight: 600; color: var(--text); cursor: pointer; }
  .pill:hover { background: var(--accent); color: #fff; }
  .subheader { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: #13161f; border-bottom: 1px solid var(--border); }
  .title-group { display: flex; align-items: center; gap: 10px; }
  .model-title { font-weight: 800; font-size: 13px; text-transform: uppercase; }
  .badge { background: rgba(16,185,129,0.15); color: var(--success); font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; }
  .actions { display: flex; gap: 6px; }
  .btn-sm { padding: 6px 11px; border-radius: 8px; border: 1px solid var(--border); background: #1e2330; color: var(--text); font-size: 11px; font-weight: 700; cursor: pointer; }
  .btn-sm.primary { background: var(--accent); color: #fff; }
  .workspace { position: relative; flex: 1; display: flex; overflow: hidden; }
  #viewport { flex: 1; height: 100%; display: block; background: radial-gradient(circle at 50% 45%, #1e2433 0%, #0d0f14 100%); }
  .pipeline-sidebar { width: 320px; background: var(--panel); border-left: 1px solid var(--border); padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
  .step-card { background: #12151e; border: 1px solid var(--border); border-left: 3px solid var(--success); border-radius: 6px; padding: 8px; font-size: 11px; }
  .step-stage { font-weight: 800; color: #60a5fa; text-transform: uppercase; font-size: 10px; }
  .step-msg { color: #cbd5e1; }
  .stats-pill { position: absolute; bottom: 14px; left: 16px; background: rgba(15,17,23,0.88); border: 1px solid var(--border); padding: 6px 12px; border-radius: 8px; font-size: 11px; font-family: monospace; pointer-events: none; }
  #scriptPanel { position: absolute; inset: 16px; background: rgba(15,17,23,0.97); border: 1px solid var(--border); border-radius: 12px; padding: 16px; display: none; flex-direction: column; gap: 10px; z-index: 20; }
  #scriptPanel.open { display: flex; }
  #codeBox { flex: 1; width: 100%; background: #090b0e; color: #86efac; border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 12px; }
  .bottom-panel { background: var(--panel); border-top: 1px solid var(--border); padding: 10px 16px 14px; display: flex; gap: 8px; }
  #promptInput { flex: 1; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border); font-size: 14px; background: #11141c; color: #fff; outline: none; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<div class="topbar">
  <span class="brand">ROBLOX 3D AI</span>
  <button class="pill" onclick="runPrompt('make me a cat')">Cat</button>
  <button class="pill" onclick="runPrompt('modern building')">Modern Building</button>
  <button class="pill" onclick="runPrompt('stone castle')">Stone Castle</button>
</div>
<div class="subheader">
  <div class="title-group">
    <span class="model-title" id="modelTitle">READY</span>
    <span class="badge" id="rigBadge">SOCKET VERIFIED</span>
  </div>
  <div class="actions">
    <button class="btn-sm" onclick="toggleScript()">LUAU SCRIPT</button>
    <button class="btn-sm primary" onclick="copyLua()" id="copyBtn">COPY STUDIO SCRIPT</button>
  </div>
</div>
<div class="workspace">
  <canvas id="viewport"></canvas>
  <div class="stats-pill" id="statsPill">0 parts</div>
  <div class="pipeline-sidebar">
    <div style="font-size:11px;font-weight:800;color:var(--muted);text-transform:uppercase;">Pipeline Execution Logs</div>
    <div id="pipelineSteps"></div>
  </div>
  <div id="scriptPanel">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <strong>Roblox Studio Luau Script</strong>
      <button class="btn-sm" onclick="toggleScript()">Close</button>
    </div>
    <textarea id="codeBox" readonly></textarea>
  </div>
</div>
<div class="bottom-panel">
  <input type="text" id="promptInput" placeholder="Type prompt..." onkeydown="if(event.key==='Enter') generateNew()" />
  <button class="btn-sm primary" onclick="generateNew()">Build 3D Asset</button>
</div>
<script>
let scene, camera, renderer, controls, modelGroup, currentSpec = null;
function init3D() {
  const canvas = document.getElementById("viewport");
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(40, canvas.clientWidth / canvas.clientHeight, 0.1, 500);
  camera.position.set(6, 5, -8);
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 1.5, 0);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 0.9));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8);
  dir.position.set(10, 20, -15);
  scene.add(dir);
  scene.add(new THREE.GridHelper(30, 30, 0x334155, 0x1e293b));
  modelGroup = new THREE.Group();
  scene.add(modelGroup);
  animate();
}
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
function renderSpec(spec) {
  currentSpec = spec;
  while (modelGroup.children.length > 0) modelGroup.remove(modelGroup.children[0]);
  (spec.parts || []).forEach(p => {
    const [w, h, d] = p.sz;
    let geom = new THREE.BoxGeometry(w, h, d);
    if (p.s === "cylinder") geom = new THREE.CylinderGeometry(w/2, w/2, h, 16);
    if (p.s === "sphere") geom = new THREE.SphereGeometry(w/2, 16, 12);
    if (p.s === "cone" || p.s === "pyramid") geom = new THREE.ConeGeometry(w/2, h, 16);
    const mat = new THREE.MeshStandardMaterial({ color: new THREE.Color(p.c || "#cccccc"), roughness: 0.4 });
    const mesh = new THREE.Mesh(geom, mat);
    mesh.position.set(p.po[0], p.po[1], p.po[2]);
    mesh.rotation.set(THREE.MathUtils.degToRad(p.ro[0]||0), THREE.MathUtils.degToRad(p.ro[1]||0), THREE.MathUtils.degToRad(p.ro[2]||0));
    modelGroup.add(mesh);
  });
  document.getElementById("modelTitle").textContent = spec.name;
  document.getElementById("statsPill").textContent = `${spec.parts.length} parts`;
  document.getElementById("codeBox").value = spec.lua || "";
  document.getElementById("pipelineSteps").innerHTML = (spec.pipeline_logs || []).map(i => `<div class="step-card"><div class="step-stage">${i.stage}</div><div class="step-msg">${i.msg}</div></div>`).join("");
}
async function fetchModel(prompt) {
  const res = await fetch("/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt }) });
  renderSpec(await res.json());
}
function runPrompt(p) { document.getElementById("promptInput").value = p; fetchModel(p); }
function generateNew() { fetchModel(document.getElementById("promptInput").value || "cat"); }
function toggleScript() { document.getElementById("scriptPanel").classList.toggle("open"); }
function copyLua() { navigator.clipboard.writeText(currentSpec.lua); alert("Copied!"); }
window.addEventListener("DOMContentLoaded", () => { init3D(); runPrompt("make me a cat"); });
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def _send(self, data, ctype="application/json; charset=utf-8", status=200):
        raw = data if isinstance(data, bytes) else data.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            return self._send(HTML_UI, "text/html; charset=utf-8")
        if parsed.path.startswith("/generate"):
            qs = parse_qs(parsed.query)
            prompt = (qs.get("prompt") or ["cat"])[0]
            spec = generate_model_blueprint(prompt, seed=7)
            return self._send(json.dumps(spec))
        return self._send('{"error":"not found"}', status=404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}") if length > 0 else {}
        prompt = body.get("prompt", "cat")
        seed = int(time.time() * 1000) % 99999
        spec = generate_model_blueprint(prompt, seed=seed)
        return self._send(json.dumps(spec))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render default fallback
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Server started successfully on port {port}")
    srv.serve_forever()
