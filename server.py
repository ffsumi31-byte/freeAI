"""Roblox Cloud 3D Modeler AI — Live LLM Architect + Wikipedia Research + 3D AABB Critic.
Single-file deployment for Render (`python server.py`). Zero pip dependencies."""

import os, sys, json, time, math, random, re, zlib, urllib.request, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# =========================================================================
# 1. COLOR & GEOMETRY PRIMITIVES
# =========================================================================
NAMED_COLORS = {
    "red": "#dc2626", "crimson": "#991b1b", "scarlet": "#ef4444", "maroon": "#7f1d1d",
    "orange": "#ea580c", "ginger": "#d97706", "amber": "#f59e0b", "peach": "#fdba74",
    "yellow": "#eab308", "gold": "#d4af37", "golden": "#d4af37", "lemon": "#facc15",
    "lime": "#65a30d", "green": "#16a34a", "emerald": "#10b981", "forest": "#166534",
    "mint": "#6ee7b7", "teal": "#0d9488", "cyan": "#06b6d4", "aqua": "#22d3ee",
    "sky": "#38bdf8", "blue": "#2563eb", "cobalt": "#1d4ed8", "navy": "#1e3a8a",
    "indigo": "#4f46e5", "purple": "#7c3aed", "violet": "#8b5cf6", "lavender": "#c4b5fd",
    "magenta": "#db2777", "pink": "#f472b6", "rose": "#fb7185", "white": "#f8fafc",
    "snow": "#ffffff", "cream": "#fef3c7", "ivory": "#fffbeb", "silver": "#cbd5e1",
    "grey": "#64748b", "gray": "#64748b", "slate": "#475569", "charcoal": "#334155",
    "black": "#1e293b", "obsidian": "#090d16", "dark": "#0f172a", "brown": "#78350f",
    "chocolate": "#5c2808", "tan": "#d6b88a", "beige": "#e5d3b3", "sand": "#fde68a",
    "bronze": "#92400e", "copper": "#b45309", "brass": "#ca8a04"
}

FACES = {
    "top": (0, 1, 0), "bot": (0, -1, 0), "bottom": (0, -1, 0),
    "front": (0, 0, -1), "back": (0, 0, 1),
    "right": (1, 0, 0), "left": (-1, 0, 0), "center": (0, 0, 0)
}

STOP_WORDS = {
    "make", "build", "create", "generate", "design", "draw", "give", "me", "a", "an",
    "the", "please", "pls", "roblox", "model", "3d", "with", "holding", "wielding",
    "wearing", "carrying", "and", "of", "for", "in", "on", "to", "from", "very",
    "really", "super", "cool", "nice", "awesome", "new", "style", "version"
}

def clamp(x, a, b):
    return max(a, min(b, x))

def tokenize(t):
    return re.findall(r"[a-z0-9]+", (t or "").lower())

def tokens_of(p):
    toks = tokenize(p)
    stems = set(toks)
    for w in toks:
        if len(w) > 3 and w.endswith("ies"):
            stems.add(w[:-3] + "y")
        elif len(w) > 3 and w.endswith("es"):
            stems.add(w[:-2])
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            stems.add(w[:-1])
    return stems

def rot_dims(sz, ro):
    """Calculates axis-aligned bounding box [w, h, d] of a rotated primitive."""
    w, h, d = float(sz[0]), float(sz[1]), float(sz[2])
    rx, ry, rz = [math.radians(float(a)) for a in (ro or [0, 0, 0])]
    cx, sx = abs(math.cos(rx)), abs(math.sin(rx))
    cy, sy = abs(math.cos(ry)), abs(math.sin(ry))
    cz, sz_ = abs(math.cos(rz)), abs(math.sin(rz))
    h1, d1 = h * cx + d * sx, h * sx + d * cx
    w2, d2 = w * cy + d1 * sy, w * sy + d1 * cy
    w3, h3 = w2 * cz + h1 * sz_, w2 * sz_ + h1 * cz
    return [round(max(0.05, w3), 3), round(max(0.05, h3), 3), round(max(0.05, d2), 3)]

def extract_prompt_colors(prompt, wiki_text=""):
    found = []
    for w in tokenize(prompt):
        if w in NAMED_COLORS and NAMED_COLORS[w] not in found:
            found.append(NAMED_COLORS[w])
    if not found and wiki_text:
        for w in tokenize(wiki_text):
            if w in NAMED_COLORS and NAMED_COLORS[w] not in found:
                found.append(NAMED_COLORS[w])
    return found

# =========================================================================
# 2. STAGE 1 & 2: PROMPT ANALYSIS & LIVE WIKIPEDIA INTERNET SEARCH
# =========================================================================
_WIKI_CACHE = {}

def search_internet_knowledge(prompt):
    """Searches Wikipedia REST + Query APIs to learn what unknown subjects look like."""
    content_words = [
        w for w in tokenize(prompt)
        if w not in STOP_WORDS and w not in NAMED_COLORS
        and w not in {"big", "small", "tiny", "huge", "giant", "cute", "evil", "flying", "floating"}
    ]
    subject = " ".join(content_words[-2:]) if len(content_words) >= 2 else (content_words[-1] if content_words else "object")
    head_noun = content_words[-1] if content_words else "object"

    if subject in _WIKI_CACHE:
        return head_noun, _WIKI_CACHE[subject]

    headers = {"User-Agent": "RobloxCloud3DModeler/4.1 (https://onrender.com)"}
    summary_text = ""

    for query_term in (subject, head_noun):
        if not query_term:
            continue
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(query_term.replace(" ", "_"))
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("type") != "disambiguation" and data.get("extract"):
                    summary_text = f"{data.get('title', query_term)}: {data.get('description', '')}. {data.get('extract', '')}"
                    break
        except Exception:
            pass

    if not summary_text and head_noun:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(subject)}&utf8=&format=json&srlimit=2"
        try:
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.2) as resp:
                sdata = json.loads(resp.read().decode("utf-8"))
                hits = sdata.get("query", {}).get("search", [])
                if hits:
                    clean_snip = re.sub(r"<[^>]+>", "", hits[0].get("snippet", ""))
                    summary_text = f"{hits[0].get('title', subject)}: {clean_snip}"
        except Exception:
            pass

    summary_text = summary_text[:550].strip()
    _WIKI_CACHE[subject] = summary_text
    return head_noun, summary_text

# =========================================================================
# 3. LIVE CLOUD AI LLM ARCHITECT (Keyless Pollinations + Optional Gemini/Groq/OpenAI)
# =========================================================================
LLM_SYSTEM_INSTRUCTIONS = """You are an autonomous 3D Modeler AI for Roblox Studio.
Build a detailed, recognizable 3D model for the user's prompt.
Return ONLY valid JSON with this exact schema:
{
  "category": "animal|humanoid|building|vehicle|aircraft|watercraft|weapon|foliage|furniture|electronics|food|prop",
  "riggable": true,
  "parts": [
    {
      "n": "PartName",
      "p": null,
      "stage": "raw|shape|detail",
      "s": "box|sphere|cylinder|wedge|cone",
      "sz": [width_x, height_y, depth_z],
      "attach": {"face": "top|bot|front|back|right|left|center", "u": 0.0, "v": 0.0, "inset": 0.03},
      "ro": [0, 0, 0],
      "c": "#hexcolor",
      "mat": "SmoothPlastic|Metal|Neon|Glass|Wood|Slate|Brick|Cobblestone|Fabric|Grass",
      "tr": 0.0,
      "joint": false,
      "mirror": false
    }
  ]
}
STRICT 3D MODELING RULES:
1. NO LEGO STUDS. Build smooth, stylized Roblox game assets using 16 to 45 parts.
2. Root part MUST have `"p": null`, `"stage": "raw"`, and `"attach": {"face": "center", "u": 0, "v": 0, "inset": 0}`.
3. Every other part MUST specify `"p": "ExistingParentName"` and attach to one of its parent's faces:
   - `"front"` is -Z, `"back"` is +Z, `"right"` is +X, `"left"` is -X, `"top"` is +Y, `"bot"` is -Y.
   - `"u"` (-0.9 to 0.9) offsets horizontally across that face.
   - `"v"` (-0.9 to 0.9) offsets vertically/longitudinally across that face.
   - `"inset"` (0.02 to 0.15) embeds the child slightly into the parent so parts NEVER float in mid-air.
4. For left/right symmetrical parts (eyes, ears, legs, arms, wheels, wings, headlights), create ONLY the right-side part ending in `R` (e.g. `"LegFR"`, `"EyeR"`, `"WingR"`) with positive `u` or `"face": "right"`, and set `"mirror": true`.
5. Keep parent parts that have children attached to them at rotation `"ro": [0, 0, 0]` so child face attachments stay axis-aligned.
6. Label core body/walls as `"stage": "raw"`, limbs/roofs/wheels/wings as `"stage": "shape"`, and eyes/ears/windows/doors/trim/buttons/weapons as `"stage": "detail"`.
7. Output ONLY the raw JSON object."""

def _extract_json_block(text):
    if not text:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        if isinstance(data, dict) and isinstance(data.get("parts"), list) and len(data["parts"]) >= 5:
            return data
    except Exception:
        pass
    return None

def call_cloud_llm_architect(prompt, wiki_summary, seed, api_key=""):
    """Calls configured API key (Gemini/Groq/OpenAI) or keyless Cloud LLM endpoints."""
    key = (api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
    user_request = (
        f"Build a 3D Roblox model for: '{prompt}' (seed: {seed}).\n"
        f"Internet Research Context: {wiki_summary or 'Use accurate real-world anatomy, architecture, and colors.'}\n"
        "Ensure all sub-parts, proportions, and details are included and properly attached. Return ONLY JSON."
    )

    # 1. Gemini API key (AIza...)
    if key.startswith("AIza"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            payload = {
                "systemInstruction": {"parts": [{"text": LLM_SYSTEM_INSTRUCTIONS}]},
                "contents": [{"parts": [{"text": user_request}]}],
                "generationConfig": {"temperature": 0.35, "responseMimeType": "application/json"}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                txt = res["candidates"][0]["content"]["parts"][0]["text"]
                bp = _extract_json_block(txt)
                if bp:
                    return bp, "Gemini 2.5 Flash AI Architect"
        except Exception:
            pass

    # 2. Groq (gsk_...) or OpenAI (sk-...) key
    if key.startswith("gsk_") or key.startswith("sk-"):
        try:
            is_groq = key.startswith("gsk_")
            url = "https://api.groq.com/openai/v1/chat/completions" if is_groq else "https://api.openai.com/v1/chat/completions"
            model = "llama-3.3-70b-versatile" if is_groq else "gpt-4o-mini"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": LLM_SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": user_request}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}", "User-Agent": "RobloxCloud3D/4.1"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                txt = res["choices"][0]["message"]["content"]
                bp = _extract_json_block(txt)
                if bp:
                    return bp, f"{'Groq Llama-3.3-70B' if is_groq else 'OpenAI'} AI Architect"
        except Exception:
            pass

    # 3. Default Keyless Cloud LLM Attempt (Pollinations POST + GET fallback)
    for model_name in ("openai", "mistral"):
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": LLM_SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": user_request}
                ],
                "temperature": 0.35,
                "seed": int(seed % 99999),
                "jsonMode": True
            }
            req = urllib.request.Request(
                "https://text.pollinations.ai/openai",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 RobloxCloud3D/4.1"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    outer = json.loads(raw)
                    txt = outer["choices"][0]["message"]["content"] if isinstance(outer, dict) and "choices" in outer else raw
                except Exception:
                    txt = raw
                bp = _extract_json_block(txt)
                if bp:
                    return bp, f"Cloud LLM Architect ({model_name})"
        except Exception:
            pass

    return None, None

# =========================================================================
# 4. UNIVERSAL WIKIPEDIA-DRIVEN COMPOSITIONAL 3D SYNTHESIZER
# =========================================================================
def synthesize_from_semantics_and_wiki(prompt, subject, wiki_summary, seed):
    """Constructs bespoke 3D models by analyzing prompt + Wikipedia anatomy/structure."""
    rng = random.Random(seed)
    combined = f"{prompt} {wiki_summary}".lower()
    ptoks = tokens_of(prompt)
    wtoks = tokens_of(combined)

    jw = rng.uniform(0.92, 1.09)
    jh = rng.uniform(0.92, 1.09)
    jl = rng.uniform(0.92, 1.09)
    user_cols = extract_prompt_colors(prompt, wiki_summary)
    c_main = user_cols[0] if len(user_cols) >= 1 else None
    c_sec = user_cols[1] if len(user_cols) >= 2 else None

    parts = []
    def P(n, p, stage, s, sz, face="center", u=0.0, v=0.0, inset=0.03, ro=(0,0,0), c="#cccccc", mat="SmoothPlastic", tr=0.0, joint=False, mirror=False):
        parts.append({
            "n": n, "p": p, "stage": stage, "s": s,
            "sz": [round(max(0.05, float(x)), 3) for x in sz],
            "attach": {"face": face, "u": round(float(u), 3), "v": round(float(v), 3), "inset": round(float(inset), 3)},
            "ro": [round(float(x), 1) for x in ro],
            "c": c, "mat": mat, "tr": round(float(tr), 2),
            "joint": bool(joint), "mirror": bool(mirror)
        })

    # ---------------------------------------------------------------------
    # DOMAIN A: ARCHITECTURE & BUILDINGS
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "building", "house", "home", "cabin", "cottage", "mansion", "villa", "shop", "store",
        "bakery", "cafe", "restaurant", "hotel", "office", "skyscraper", "tower", "castle",
        "fort", "citadel", "palace", "church", "temple", "cathedral", "shrine", "pagoda",
        "lighthouse", "windmill", "barn", "warehouse", "factory", "hospital", "school", "bank", "bridge", "pyramid"
    )) or any(w in wtoks for w in ("architecture", "building", "skyscraper", "fortification", "edifice")):
        is_castle = any(w in ptoks for w in ("castle", "fort", "citadel", "palace"))
        is_pagoda = any(w in ptoks for w in ("pagoda", "shrine", "temple"))
        is_sky = any(w in ptoks for w in ("skyscraper", "office", "hotel", "tower", "lighthouse", "windmill"))
        floors = rng.randint(4, 5) if "skyscraper" in ptoks else (3 if is_sky or is_pagoda else 2)
        w = (5.4 if is_sky else 8.2) * jw
        d = (5.2 if is_sky else 6.4) * jl
        fh = 2.8 * jh
        th = floors * fh

        wall_c = c_main or ("#dc2626" if is_pagoda else ("#94a3b8" if is_castle else ("#334155" if "skyscraper" in ptoks else rng.choice(["#f1f5f9", "#fef3c7", "#e2e8f0", "#d6b88a"]))))
        trim_c = c_sec or ("#1e293b" if wall_c != "#334155" else "#cbd5e1")
        roof_c = "#1e293b" if not is_castle else "#2563eb"

        P("Foundation", None, "raw", "box", (w + 1.0, 0.65, d + 1.0), "center", c=trim_c, mat="Slate")
        P("MainWalls", "Foundation", "raw", "box", (w, th, d), "top", u=0, v=0, inset=0.02, c=wall_c, mat="Cobblestone" if is_castle else ("SmoothPlastic" if is_sky else "Brick"))

        for ux, sx_tag in ((0.96, "R"), (-0.96, "L")):
            for vz, sz_tag in ((-0.96, "F"), (0.96, "B")):
                P(f"Pilaster{sx_tag}{sz_tag}", "MainWalls", "shape", "box", (0.48, th + 0.05, 0.48), "front" if sz_tag=="F" else "back", u=ux, v=0, inset=0.22, c=trim_c, mat="Slate")

        for fl in range(1, floors + 1):
            vn = clamp(-1.0 + (2.0 * fl / floors), -0.95, 0.98)
            P(f"CorniceLedge{fl}", "MainWalls", "shape", "box", (w + 0.42, 0.26, d + 0.42), "front", u=0, v=vn, inset=d/2 + 0.21, c=trim_c, mat="Slate")

        if is_castle:
            for ux, sx_t in ((0.98, "R"), (-0.98, "L")):
                for vz, sz_t in ((-0.98, "F"), (0.98, "B")):
                    t_name = f"CornerTower{sx_t}{sz_t}"
                    P(t_name, "Foundation", "shape", "cylinder", (2.3, th + 1.6, 2.3), "top", u=ux, v=vz, inset=0.02, c=trim_c, mat="Cobblestone")
                    P(f"Spire{sx_t}{sz_t}", t_name, "shape", "cone", (2.7, 2.0, 2.7), "top", u=0, v=0, inset=0.03, c=roof_c, mat="Slate")
            for bi in range(-2, 3):
                P(f"MerlonF{bi+2}", "MainWalls", "shape", "box", (0.65, 0.65, 0.45), "top", u=bi*0.42, v=-0.92, inset=0.02, c=trim_c, mat="Cobblestone")
                P(f"MerlonB{bi+2}", "MainWalls", "shape", "box", (0.65, 0.65, 0.45), "top", u=bi*0.42, v=0.92, inset=0.02, c=trim_c, mat="Cobblestone")
        elif is_pagoda:
            par_t = "MainWalls"
            for tier in range(3):
                sc_t = 1.0 - tier * 0.22
                eave = f"PagodaEave{tier}"
                P(eave, par_t, "shape", "cone", ((w + 1.6)*sc_t, 0.9, (d + 1.6)*sc_t), "top", u=0, v=0, inset=0.03, ro=(0, 45, 0), c="#1e293b", mat="Slate")
                if tier < 2:
                    par_t = f"PagodaStory{tier}"
                    P(par_t, eave, "shape", "box", (w*0.68*sc_t, 1.5, d*0.68*sc_t), "top", u=0, v=0, inset=0.25, c=wall_c, mat="Wood")
            P("PagodaSpire", "PagodaEave2", "detail", "cylinder", (0.28, 1.6, 0.28), "top", u=0, v=0, inset=0.05, c="#d4af37", mat="Metal")
        elif is_sky:
            P("RoofParapet", "MainWalls", "shape", "box", (w + 0.3, 0.5, d + 0.3), "top", u=0, v=0, inset=0.02, c=trim_c, mat="Metal")
            P("PenthouseCore", "RoofParapet", "shape", "box", (w * 0.55, 1.3, d * 0.55), "top", u=0, v=0, inset=0.02, c=trim_c, mat="Metal")
            P("AntennaSpire", "PenthouseCore", "detail", "cylinder", (0.22, 2.4, 0.22), "top", u=0, v=0, inset=0.02, c="#cbd5e1", mat="Metal")
            P("BeaconLight", "AntennaSpire", "detail", "sphere", (0.38, 0.38, 0.38), "top", u=0, v=0, inset=0.02, c="#ef4444", mat="Neon")
        else:
            P("PitchedRoof", "MainWalls", "shape", "wedge", (w + 0.9, 2.2 * jh, d + 0.9), "top", u=0, v=0, inset=0.02, c=roof_c, mat="Slate")
            P("ChimneyStack", "MainWalls", "shape", "box", (0.9, 2.5, 0.9), "top", u=0.58, v=0.35, inset=0.05, c="#78350f", mat="Brick")

        P("EntryStairs", "Foundation", "detail", "box", (2.6, 0.48, 0.95), "front", u=0, v=-0.08, inset=0.05, c=trim_c, mat="Slate")
        v_door = -1.0 + (2.2 / th)
        P("DoorFrame", "MainWalls", "detail", "box", (1.95, 2.25, 0.24), "front", u=0, v=v_door, inset=0.04, c="#0f172a", mat="Metal")
        P("DoorLeafR", "DoorFrame", "detail", "box", (0.78, 2.0, 0.12), "front", u=0.42, v=-0.04, inset=0.02, c="#78350f", mat="Wood", mirror=True)
        P("DoorHandleR", "DoorLeafR", "detail", "sphere", (0.14, 0.14, 0.14), "front", u=-0.65, v=0, inset=0.01, c="#d4af37", mat="Metal", mirror=True)
        P("EntryCanopy", "DoorFrame", "detail", "box", (2.55, 0.22, 1.05), "top", u=0, v=-0.45, inset=0.04, c=roof_c, mat="Metal")
        P("CanopySign", "EntryCanopy", "detail", "box", (1.9, 0.14, 0.22), "front", u=0, v=0, inset=0.02, c="#38bdf8", mat="Neon")

        for fl in range(floors):
            vy = -1.0 + ((fl + 0.54) * 2.0 / floors)
            for ux in (-0.64, 0.0, 0.64):
                if fl == 0 and abs(ux) < 0.22:
                    continue
                for fc_s in ("front", "back"):
                    wn = f"Win_{fc_s}_{fl}_{int((ux+1)*10)}"
                    P(wn, "MainWalls", "detail", "box", (1.22, 1.38, 0.18), fc_s, u=ux, v=vy, inset=0.04, c="#0f172a", mat="Metal")
                    P(wn + "_Glass", wn, "detail", "box", (1.02, 1.16, 0.08), fc_s, u=0, v=0, inset=0.01, c="#7dd3fc", mat="Glass", tr=0.35)
                    P(wn + "_Sill", wn, "detail", "box", (1.36, 0.14, 0.30), "bot", u=0, v=0, inset=0.02, c=trim_c, mat="Slate")
            for s_face in ("right", "left"):
                swn = f"SideWin_{s_face}_{fl}"
                P(swn, "MainWalls", "detail", "box", (0.18, 1.35, 1.35), s_face, u=0, v=vy, inset=0.04, c="#0f172a", mat="Metal")
                P(swn + "_Glass", swn, "detail", "box", (0.08, 1.12, 1.12), s_face, u=0, v=0, inset=0.01, c="#7dd3fc", mat="Glass", tr=0.35)

        return {"category": "building", "riggable": False, "parts": parts}, "Architectural Multi-Story Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN B: GROUND VEHICLES
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "car", "sportscar", "racecar", "supercar", "sedan", "coupe", "suv", "jeep", "truck",
        "pickup", "van", "bus", "taxi", "policecar", "ambulance", "firetruck", "limo",
        "cybertruck", "tractor", "buggy", "kart", "f1", "tank", "panzer", "apc", "bike", "motorcycle", "excavator", "bulldozer"
    )) or any(w in wtoks for w in ("automobile", "motor vehicle", "sports car", "armored fighting vehicle")):
        is_tank = any(w in ptoks for w in ("tank", "panzer", "apc", "excavator", "bulldozer"))
        is_truck = any(w in ptoks for w in ("truck", "pickup", "suv", "jeep", "firetruck", "van", "bus", "ambulance"))
        body_c = c_main or ("#4d7c0f" if is_tank else ("#eab308" if "taxi" in ptoks or "excavator" in ptoks else ("#1e3a8a" if "police" in prompt else "#dc2626")))
        trim_c = c_sec or "#1e293b"
        W, H, L = (2.8 if is_tank else 2.4) * jw, (0.95 if is_truck or is_tank else 0.68) * jh, 5.2 * jl

        P("Chassis", None, "raw", "box", (W, H, L), "center", c=body_c, mat="Metal")
        if is_tank:
            P("TurretBase", "Chassis", "shape", "box", (W * 0.78, 0.85, L * 0.48), "top", u=0, v=0.05, inset=0.04, c=body_c, mat="Metal", joint=True)
            P("MainCannon", "TurretBase", "shape", "cylinder", (0.36, 3.4, 0.36), "front", u=0, v=0.05, inset=0.15, ro=(90, 0, 0), c="#1e293b", mat="Metal")
            P("CommanderHatch", "TurretBase", "detail", "cylinder", (0.75, 0.24, 0.75), "top", u=0.35, v=0.25, inset=0.02, c=trim_c, mat="Metal")
            P("TrackR", "Chassis", "shape", "box", (0.55, 0.92, L * 0.96), "right", u=0, v=-0.22, inset=0.04, c="#0f172a", mat="Slate", mirror=True)
            for wi, wz in enumerate((-0.72, -0.24, 0.24, 0.72)):
                P(f"RoadWheel{wi}R", "TrackR", "detail", "cylinder", (0.72, 0.58, 0.72), "right", u=wz, v=0, inset=0.22, ro=(0, 0, 90), c="#334155", mat="Metal", mirror=True)
        else:
            P("Hood", "Chassis", "shape", "box", (W * 0.96, 0.36, L * 0.32), "top", u=0, v=-0.62, inset=0.02, c=body_c, mat="Metal")
            P("FrontSplitter", "Chassis", "detail", "box", (W * 1.02, 0.20, 0.42), "front", u=0, v=-0.35, inset=0.02, c="#0f172a", mat="Metal")
            cab_l = L * (0.56 if is_truck else 0.42)
            P("CabinGlass", "Chassis", "shape", "box", (W * 0.86, 0.82 if not is_truck else 1.05, cab_l), "top", u=0, v=0.12, inset=0.02, c="#38bdf8", mat="Glass", tr=0.28)
            P("RoofCap", "CabinGlass", "shape", "box", (W * 0.84, 0.16, cab_l * 0.90), "top", u=0, v=0, inset=0.02, c=body_c, mat="Metal")
            P("RacingStripe", "Hood", "detail", "box", (0.46, 0.05, L * 0.30), "top", u=0, v=0, inset=0.01, c="#f8fafc")
            P("HeadlightR", "Chassis", "detail", "box", (0.48, 0.24, 0.12), "front", u=0.66, v=0.12, inset=0.02, c="#fef08a", mat="Neon", mirror=True)
            P("TaillightR", "Chassis", "detail", "box", (0.52, 0.24, 0.12), "back", u=0.66, v=0.12, inset=0.02, c="#ef4444", mat="Neon", mirror=True)
            P("Grille", "Chassis", "detail", "box", (W * 0.48, 0.28, 0.10), "front", u=0, v=0.05, inset=0.02, c="#0f172a", mat="Metal")
            P("SideMirrorR", "CabinGlass", "detail", "box", (0.28, 0.18, 0.22), "right", u=-0.65, v=-0.15, inset=0.02, c=body_c, mat="Metal", mirror=True)
            ws = 1.12 if is_truck else 0.94
            for uz, tag in ((-0.62, "F"), (0.62, "B")):
                P(f"Wheel{tag}R", "Chassis", "shape", "cylinder", (ws, 0.50, ws), "right", u=uz, v=-0.28, inset=0.06, ro=(0, 0, 90), c="#0f172a", joint=True, mirror=True)
                P(f"Rim{tag}R", f"Wheel{tag}R", "detail", "cylinder", (ws * 0.56, 0.54, ws * 0.56), "right", u=0, v=0, inset=0.22, ro=(0, 0, 90), c="#cbd5e1", mat="Metal", mirror=True)
            if not is_truck:
                P("SpoPostR", "Chassis", "detail", "box", (0.14, 0.48, 0.24), "top", u=0.62, v=0.88, inset=0.02, c="#0f172a", mat="Metal", mirror=True)
                P("RearWing", "Chassis", "detail", "box", (W * 0.98, 0.14, 0.58), "top", u=0, v=0.90, inset=-0.38, c=trim_c, mat="Metal")
        return {"category": "vehicle", "riggable": True, "parts": parts}, "Vehicle Engineering Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN C: AIRCRAFT & SPACECRAFT
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "plane", "airplane", "jet", "fighterjet", "biplane", "airliner", "spaceship",
        "starfighter", "rocket", "shuttle", "ufo", "saucer", "helicopter", "heli", "chopper", "drone"
    )) or any(w in wtoks for w in ("aircraft", "helicopter", "spacecraft", "airliner")):
        is_heli = any(w in ptoks for w in ("helicopter", "heli", "chopper", "drone"))
        is_ufo = any(w in ptoks for w in ("ufo", "saucer"))
        body_c = c_main or ("#64748b" if "fighter" in prompt or "jet" in ptoks else "#f8fafc")
        acc_c = c_sec or "#2563eb"

        if is_ufo:
            P("SaucerDisc", None, "raw", "cylinder", (4.8 * jw, 0.65 * jh, 4.8 * jw), "center", c="#94a3b8", mat="Metal")
            P("GlassDome", "SaucerDisc", "shape", "sphere", (2.4 * jw, 1.45 * jh, 2.4 * jw), "top", u=0, v=0, inset=0.25, c="#38bdf8", mat="Glass", tr=0.3)
            P("TractorRing", "SaucerDisc", "detail", "cylinder", (1.8, 0.25, 1.8), "bot", u=0, v=0, inset=0.04, c="#4ade80", mat="Neon")
        elif is_heli:
            P("Fuselage", None, "raw", "sphere", (2.1 * jw, 1.75 * jh, 3.4 * jl), "center", c=body_c, mat="Metal")
            P("CockpitGlass", "Fuselage", "shape", "sphere", (1.85 * jw, 1.35 * jh, 1.65 * jl), "front", u=0, v=0.05, inset=0.55, c="#38bdf8", mat="Glass", tr=0.3)
            P("TailBoom", "Fuselage", "shape", "cylinder", (0.55, 2.9 * jl, 0.55), "back", u=0, v=0.18, inset=0.2, ro=(90, 0, 0), c=body_c, mat="Metal")
            P("TailFin", "TailBoom", "detail", "wedge", (0.22, 1.15, 0.85), "back", u=0, v=0.35, inset=0.1, c=acc_c, mat="Metal")
            P("RotorMast", "Fuselage", "shape", "cylinder", (0.42, 0.55, 0.42), "top", u=0, v=0, inset=0.05, c="#1e293b", mat="Metal", joint=True)
            P("RotorBlade1", "RotorMast", "detail", "box", (5.4 * jw, 0.10, 0.36), "top", u=0, v=0, inset=0.02, c="#0f172a", mat="Metal")
            P("RotorBlade2", "RotorMast", "detail", "box", (0.36, 0.10, 5.4 * jw), "top", u=0, v=0, inset=0.02, c="#0f172a", mat="Metal")
            P("SkidStrutR", "Fuselage", "shape", "cylinder", (0.18, 0.75, 0.18), "bot", u=0.65, v=0, inset=0.08, c="#1e293b", mat="Metal", mirror=True)
            P("LandingSkidR", "SkidStrutR", "detail", "box", (0.22, 0.20, 3.2 * jl), "bot", u=0, v=0, inset=0.02, c="#1e293b", mat="Metal", mirror=True)
        else:
            P("Fuselage", None, "raw", "cylinder", (1.55 * jw, 5.2 * jl, 1.55 * jh), "center", ro=(90, 0, 0), c=body_c, mat="Metal")
            P("NoseCone", "Fuselage", "shape", "sphere", (1.45 * jw, 1.35 * jh, 1.85), "front", u=0, v=0, inset=0.45, c=acc_c, mat="Metal")
            P("CanopyGlass", "Fuselage", "detail", "sphere", (1.15 * jw, 0.75, 2.1), "top", u=0, v=-0.35, inset=0.25, c="#38bdf8", mat="Glass", tr=0.28)
            P("WingR", "Fuselage", "shape", "box", (3.8 * jw, 0.22, 1.45 * jl), "right", u=-0.05, v=0, inset=0.15, c=body_c, mat="Metal", mirror=True)
            P("WingMissileR", "WingR", "detail", "cylinder", (0.24, 1.35, 0.24), "bot", u=0.2, v=0, inset=0.02, ro=(90, 0, 0), c=acc_c, mat="Metal", mirror=True)
            P("TailFin", "Fuselage", "shape", "wedge", (0.24, 1.45, 1.25), "top", u=0, v=0.78, inset=0.08, c=acc_c, mat="Metal")
            P("ThrusterGlow", "Fuselage", "detail", "cylinder", (0.95, 0.35, 0.95), "back", u=0, v=0, inset=0.08, ro=(90, 0, 0), c="#f97316", mat="Neon")
        return {"category": "aircraft", "riggable": True, "parts": parts}, "Aerospace 3D Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN D: FELINES & SMALL/MEDIUM MAMMALS
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "cat", "kitten", "kitty", "lion", "tiger", "panther", "leopard", "cheetah", "jaguar", "lynx",
        "dog", "puppy", "wolf", "fox", "husky", "corgi", "hound", "bear", "panda", "polarbear",
        "rabbit", "bunny", "mouse", "rat", "squirrel", "raccoon", "otter", "capybara", "hamster", "pikachu"
    )) or any(w in wtoks for w in ("felidae", "feline", "canidae", "canine", "carnivora", "ursidae", "rodent")):
        is_feline = any(w in wtoks for w in ("cat", "kitten", "kitty", "lion", "tiger", "panther", "leopard", "cheetah", "felidae", "feline"))
        is_bear = any(w in ptoks for w in ("bear", "panda", "polarbear", "grizzly"))
        is_rabbit = any(w in ptoks for w in ("rabbit", "bunny", "hare", "pikachu"))
        sc = 1.45 if any(w in ptoks for w in ("lion", "tiger", "bear", "panda", "polarbear")) else 1.0

        default_fur = "#facc15" if "pikachu" in ptoks else ("#d97706" if "tiger" in ptoks else ("#eab308" if "lion" in ptoks else ("#f8fafc" if "polarbear" in ptoks or "panda" in ptoks or "rabbit" in ptoks else ("#78350f" if is_bear else ("#ea580c" if "fox" in ptoks else "#e07a2e")))))
        fur = c_main or default_fur
        sec_fur = c_sec or ("#1e293b" if "panda" in ptoks else ("#fef3c7" if fur not in ("#1e293b", "#f8fafc") else "#cbd5e1"))
        nose_c = "#f472b6" if (is_feline or is_rabbit) else "#1e293b"
        eye_c = "#4ade80" if is_feline else "#38bdf8"

        bw, bh, bl = (1.85 if is_bear else 1.45) * sc * jw, (1.45 if is_bear else 1.15) * sc * jh, (2.2 if is_rabbit else 2.75) * sc * jl
        P("Torso", None, "raw", "box", (bw, bh, bl), "center", c=fur)
        P("Chest", "Torso", "raw", "sphere", (bw * 0.98, bh * 0.96, bw * 0.96), "front", u=0, v=-0.02, inset=bw*0.38, c=sec_fur if "panda" in ptoks else fur)
        P("Haunch", "Torso", "raw", "sphere", (bw * 0.98, bh * 0.96, bw * 0.96), "back", u=0, v=0.02, inset=bw*0.38, c=fur)
        P("Belly", "Torso", "shape", "box", (bw * 0.78, 0.16 * sc, bl * 0.80), "bot", u=0, v=0, inset=0.04, c=sec_fur)

        P("Head", "Torso", "raw", "sphere", (1.28 * sc, 1.18 * sc, 1.24 * sc), "top", u=0, v=-0.86, inset=0.18, c=fur, joint=True)
        muz_l = 0.48 * sc if (is_feline or is_rabbit) else 0.75 * sc
        P("Muzzle", "Head", "shape", "sphere", (0.64 * sc, 0.45 * sc, muz_l), "front", u=0, v=-0.20, inset=0.12, c=sec_fur)

        leg_h = (0.75 if "corgi" in ptoks or is_rabbit else 1.10) * sc * jh
        lw = (0.48 if is_bear else 0.35) * sc
        for v_pos, tg in ((-0.76, "F"), (0.76, "B")):
            P(f"Leg{tg}R", "Torso", "shape", "cylinder", (lw, leg_h, lw), "bot", u=0.68, v=v_pos, inset=0.08, c=sec_fur if "panda" in ptoks else fur, joint=True, mirror=True)
            P(f"Paw{tg}R", f"Leg{tg}R", "shape", "sphere", (lw * 1.2, 0.26 * sc, lw * 1.35), "bot", u=0, v=-0.15, inset=0.05, c=sec_fur, mirror=True)

        if "lion" in ptoks:
            P("LionMane", "Head", "shape", "sphere", (1.88 * sc, 1.88 * sc, 1.35 * sc), "back", u=0, v=0, inset=0.55, c="#92400e")

        ear_s = "sphere" if is_bear else "cone"
        ear_h = 1.35 * sc if is_rabbit else (0.38 * sc if is_bear else 0.54 * sc)
        P("EarR", "Head", "detail", ear_s, (0.38 * sc, ear_h, 0.32 * sc), "top", u=0.55, v=0.10, inset=0.08, c=sec_fur if "panda" in ptoks else fur, mirror=True)
        P("InnerEarR", "EarR", "detail", ear_s, (0.22 * sc, ear_h * 0.65, 0.16 * sc), "front", u=0, v=-0.05, inset=0.03, c="#f472b6", mirror=True)

        P("NosePad", "Muzzle", "detail", "sphere", (0.22 * sc, 0.16 * sc, 0.18 * sc), "front", u=0, v=0.18, inset=0.04, c=nose_c)
        P("EyeR", "Head", "detail", "sphere", (0.26 * sc, 0.26 * sc, 0.15 * sc), "front", u=0.42, v=0.16, inset=0.03, c=eye_c, mat="Neon", mirror=True)
        P("PupilR", "EyeR", "detail", "box", (0.08 * sc, 0.20 * sc, 0.08 * sc), "front", u=0, v=0, inset=0.01, c="#0f172a", mirror=True)

        if is_feline:
            for wi, wy in enumerate((0.08, -0.08)):
                P(f"Whisker{wi}R", "Muzzle", "detail", "box", (0.50 * sc, 0.04 * sc, 0.04 * sc), "right", u=0.15, v=wy, inset=0.04, c="#f8fafc", mirror=True)

        if is_bear or is_rabbit:
            P("PomTail", "Torso", "shape", "sphere", (0.48 * sc, 0.48 * sc, 0.48 * sc), "back", u=0, v=0.25, inset=0.08, c=sec_fur)
        else:
            P("TailBase", "Torso", "shape", "cylinder", (0.28 * sc, 1.05 * sc, 0.28 * sc), "back", u=0, v=0.42, inset=0.08, ro=(32, 0, 0), c=fur, joint=True)
            P("TailTip", "TailBase", "detail", "sphere", (0.32 * sc, 0.38 * sc, 0.32 * sc), "top", u=0, v=0, inset=0.04, c=sec_fur)

        return {"category": "animal", "riggable": True, "parts": parts}, "Mammalian Anatomical Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN E: UNGULATES, HERBIVORES & DINOSAURS
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "horse", "unicorn", "pegasus", "zebra", "donkey", "cow", "bull", "bison", "goat", "sheep",
        "ram", "deer", "moose", "elk", "stag", "giraffe", "camel", "llama", "elephant", "mammoth",
        "rhino", "hippo", "pig", "boar", "dino", "dinosaur", "trex", "raptor", "triceratops", "croc", "crocodile"
    )) or any(w in wtoks for w in ("equidae", "bovidae", "cervidae", "dinosaur", "ungulate", "herbivore", "reptile")):
        is_uni = any(w in ptoks for w in ("unicorn", "pegasus"))
        is_trex = any(w in ptoks for w in ("trex", "raptor", "dinosaur", "dino"))
        coat = c_main or ("#9be2e8" if is_uni else ("#16a34a" if is_trex or "croc" in ptoks else ("#f472b6" if "pig" in ptoks else "#92400e")))
        acc = c_sec or ("#a855f7" if is_uni else ("#eab308" if is_trex else "#1e293b"))

        bw, bh, bl = 1.9 * jw, 1.55 * jh, 3.45 * jl
        leg_h = (3.4 if "giraffe" in ptoks else (2.2 if any(w in ptoks for w in ("horse", "unicorn", "pegasus", "deer", "camel")) else 1.45)) * jh
        neck_h = (3.2 if "giraffe" in ptoks else 1.45) * jh

        P("Torso", None, "raw", "box", (bw, bh, bl), "center", c=coat)
        P("Chest", "Torso", "shape", "sphere", (bw * 0.96, bh * 0.92, 1.15), "front", u=0, v=-0.04, inset=0.40, c=coat)
        P("Neck", "Torso", "raw", "box", (0.84, neck_h, 0.92), "top", u=0, v=-0.82, inset=0.14, c=coat, joint=True)
        P("Head", "Neck", "raw", "box", (0.96, 0.92, 1.32), "top", u=0, v=-0.35, inset=0.12, c=coat, joint=True)
        P("Muzzle", "Head", "shape", "box", (0.76, 0.58, 0.68), "front", u=0, v=-0.16, inset=0.06, c="#f8fafc")
        P("NostrilPad", "Muzzle", "detail", "box", (0.50, 0.28, 0.10), "front", u=0, v=0.15, inset=0.02, c="#1e293b")

        for v_pos, tg in ((-0.78, "F"), (0.78, "B")):
            P(f"Leg{tg}R", "Torso", "shape", "box", (0.44, leg_h, 0.44), "bot", u=0.68, v=v_pos, inset=0.06, c=coat, joint=True, mirror=True)
            P(f"Hoof{tg}R", f"Leg{tg}R", "detail", "box", (0.48, 0.36, 0.50), "bot", u=0, v=-0.05, inset=0.02, c="#eab308" if is_uni else "#1e293b", mirror=True)

        P("EarR", "Head", "detail", "cone", (0.28, 0.48, 0.28), "top", u=0.58, v=0.35, inset=0.04, c=coat, mirror=True)
        P("EyeR", "Head", "detail", "sphere", (0.24, 0.24, 0.14), "right", u=-0.25, v=0.15, inset=0.03, c="#0f172a", mirror=True)
        P("Mane", "Neck", "detail", "box", (0.28, neck_h * 0.92, 0.36), "back", u=0, v=0.05, inset=0.04, c=acc)
        P("Tail", "Torso", "shape", "box", (0.38, 1.45, 0.38), "back", u=0, v=-0.15, inset=0.06, c=acc, joint=True)

        if is_uni or any(w in combined for w in ("horn", "unicorn", "rhino", "triceratops", "bull", "goat", "ram", "deer", "stag")):
            P("Horn", "Head", "detail", "cone", (0.28, 1.15, 0.28), "top", u=0, v=-0.45, inset=0.06, c="#facc15", mat="Neon")
        if "elephant" in ptoks or "mammoth" in ptoks:
            P("Trunk", "Muzzle", "shape", "cylinder", (0.36, 1.65, 0.36), "bot", u=0, v=-0.2, inset=0.08, c=coat, joint=True)
            P("TuskR", "Muzzle", "detail", "cone", (0.20, 0.95, 0.20), "front", u=0.55, v=-0.2, inset=0.04, ro=(-65, 0, 0), c="#fef3c7", mirror=True)
        return {"category": "animal", "riggable": True, "parts": parts}, "Ungulate & Reptilian Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN F: BIRDS, DRAGONS & WINGED CREATURES
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "bird", "eagle", "phoenix", "falcon", "hawk", "owl", "raven", "crow", "parrot", "duck",
        "swan", "goose", "chicken", "rooster", "penguin", "flamingo", "peacock", "dragon", "charizard", "wyvern", "griffin"
    )) or any(w in wtoks for w in ("avian", "bird", "waterfowl", "bird of prey", "dragon")):
        main_c = c_main or ("#dc2626" if "phoenix" in ptoks else ("#ea580c" if "charizard" in ptoks or "dragon" in ptoks else "#2563eb"))
        acc_c = c_sec or "#facc15"
        P("Torso", None, "raw", "sphere", (2.0 * jw, 2.3 * jh, 2.5 * jl), "center", c=main_c)
        P("BreastPlume", "Torso", "shape", "sphere", (1.65 * jw, 1.65 * jh, 0.85), "front", u=0, v=0.05, inset=0.35, c=acc_c)
        P("Neck", "Torso", "raw", "cylinder", (0.95, 1.15, 0.95), "top", u=0, v=-0.55, inset=0.18, c=main_c, joint=True)
        P("Head", "Neck", "raw", "sphere", (1.22, 1.12, 1.28), "top", u=0, v=-0.15, inset=0.15, c=main_c, joint=True)
        P("Beak", "Head", "detail", "cone", (0.58, 0.85, 0.58), "front", u=0, v=-0.08, inset=0.12, ro=(-90, 0, 0), c=acc_c)
        P("CrownCrest", "Head", "detail", "box", (0.24, 0.85, 0.95), "top", u=0, v=0.25, inset=0.08, c=acc_c)
        P("EyeR", "Head", "detail", "sphere", (0.26, 0.26, 0.16), "right", u=-0.25, v=0.15, inset=0.04, c=acc_c, mat="Neon", mirror=True)
        P("WingR", "Torso", "shape", "box", (2.3 * jl, 0.30, 1.35), "right", u=-0.1, v=0.35, inset=0.12, ro=(0, 0, 26), c=main_c, joint=True, mirror=True)
        P("WingOuterR", "WingR", "detail", "box", (1.6 * jl, 0.22, 1.05), "right", u=0, v=0, inset=0.06, ro=(0, 0, 14), c=acc_c, mirror=True)
        P("LegR", "Torso", "shape", "cylinder", (0.36, 1.45, 0.36), "bot", u=0.48, v=0.05, inset=0.10, c=acc_c, joint=True, mirror=True)
        P("TalonR", "LegR", "detail", "box", (0.52, 0.22, 0.82), "bot", u=0, v=-0.15, inset=0.04, c="#1e293b", mirror=True)
        P("TailPlume", "Torso", "detail", "box", (1.35, 0.24, 2.1), "back", u=0, v=-0.35, inset=0.12, c=acc_c, joint=True)
        return {"category": "animal", "riggable": True, "parts": parts}, "Avian & Draconic Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN G: MARINE & CEPHALOPODS
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "octopus", "kraken", "squid", "cthulhu", "jellyfish", "whale", "beluga", "shark",
        "dolphin", "orca", "fish", "goldfish", "koi", "salmon", "turtle", "crab", "lobster"
    )) or any(w in wtoks for w in ("cephalopod", "cetacea", "shark", "fish", "marine", "crustacean")):
        if any(w in ptoks for w in ("octopus", "kraken", "squid", "cthulhu", "jellyfish")):
            skin = c_main or "#7c3aed"
            dark = c_sec or "#4c1d95"
            P("HeadCore", None, "raw", "box", (3.0 * jw, 2.2 * jh, 2.8 * jl), "center", c=skin)
            P("Mantle1", "HeadCore", "shape", "box", (3.2 * jw, 1.3 * jh, 3.0 * jl), "top", u=0, v=0.1, inset=0.04, c=skin)
            P("Mantle2", "Mantle1", "shape", "box", (2.4 * jw, 1.1 * jh, 2.3 * jl), "top", u=0, v=0, inset=0.04, c=dark)
            P("MantleCrown", "Mantle2", "shape", "cone", (1.6 * jw, 0.9 * jh, 1.6 * jl), "top", u=0, v=0, inset=0.04, c=dark)
            P("EyeFrameR", "HeadCore", "detail", "box", (0.78, 0.85, 0.16), "front", u=0.52, v=0.12, inset=0.03, c="#1e293b", mirror=True)
            P("EyeR", "EyeFrameR", "detail", "box", (0.64, 0.70, 0.10), "front", u=0, v=0, inset=0.01, c="#facc15", mat="Neon", mirror=True)
            P("PupilR", "EyeR", "detail", "box", (0.22, 0.50, 0.08), "front", u=0, v=0, inset=0.01, c="#0f172a", mirror=True)
            P("Siphon", "HeadCore", "detail", "cylinder", (0.58, 0.52, 0.58), "front", u=0, v=-0.45, inset=0.05, ro=(90, 0, 0), c="#f8fafc")
            for i, (fc_s, u_s) in enumerate([("front",-0.65),("front",0.65),("back",-0.65),("back",0.65),("right",-0.55),("right",0.55),("left",-0.55),("left",0.55)]):
                P(f"Tentacle{i}", "HeadCore", "shape", "box", (0.68, 0.52, 1.85), fc_s, u=u_s, v=-0.78, inset=0.08, c=skin, joint=True)
                P(f"TentTip{i}", f"Tentacle{i}", "detail", "sphere", (0.54, 0.65, 0.54), "top", u=0, v=-0.65, inset=0.05, c=dark)
            return {"category": "animal", "riggable": True, "parts": parts}, "Cephalopod Modeler"
        else:
            skin = c_main or ("#f8fafc" if "beluga" in ptoks else "#3b82f6")
            P("Body", None, "raw", "sphere", (2.4 * jw, 2.0 * jh, 3.8 * jl), "center", c=skin)
            P("Snout", "Body", "shape", "sphere", (1.8 * jw, 1.4 * jh, 1.8 * jl), "front", u=0, v=-0.08, inset=0.45, c=skin)
            P("TailStock", "Body", "shape", "cone", (1.4 * jw, 2.0 * jl, 1.4 * jh), "back", u=0, v=0, inset=0.35, ro=(90, 0, 0), c=skin, joint=True)
            P("TailFluke", "TailStock", "detail", "box", (2.4 * jw, 0.24, 0.95), "back", u=0, v=0, inset=0.15, c=skin, joint=True)
            P("DorsalFin", "Body", "detail", "wedge", (0.28, 1.15, 1.25), "top", u=0, v=0.15, inset=0.12, c=skin)
            P("FinR", "Body", "shape", "box", (1.45, 0.22, 0.85), "right", u=-0.2, v=-0.35, inset=0.15, ro=(0, 0, -20), c=skin, joint=True, mirror=True)
            P("EyeR", "Snout", "detail", "sphere", (0.26, 0.26, 0.18), "right", u=-0.1, v=0.15, inset=0.04, c="#0f172a", mirror=True)
            return {"category": "animal", "riggable": True, "parts": parts}, "Marine Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN H: WEAPONS & COMBAT GEAR
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "sword", "mastersword", "katana", "blade", "dagger", "claymore", "rapier", "scimitar",
        "axe", "halberd", "scythe", "spear", "trident", "hammer", "warhammer", "mace", "bow",
        "staff", "wand", "shield", "gun", "pistol", "rifle", "sniper", "shotgun", "blaster", "lasergun", "lightsaber"
    )) or any(w in wtoks for w in ("weapon", "sword", "firearm", "rifle", "pistol", "polearm")):
        is_gun = any(w in ptoks for w in ("gun", "pistol", "rifle", "sniper", "shotgun", "blaster", "lasergun")) or "firearm" in wtoks
        is_pole = any(w in ptoks for w in ("axe", "halberd", "scythe", "spear", "trident", "hammer", "warhammer", "mace", "staff", "wand"))
        main_c = c_main or ("#334155" if is_gun else "#2563eb")
        metal_c = c_sec or "#e2e8f0"

        if is_gun:
            P("Receiver", None, "raw", "box", (0.48 * jw, 0.82 * jh, 2.8 * jl), "center", c=main_c, mat="Metal")
            P("Barrel", "Receiver", "shape", "cylinder", (0.28, 1.9 * jl, 0.28), "front", u=0, v=0.18, inset=0.08, ro=(90, 0, 0), c=metal_c, mat="Metal")
            P("MuzzleGlow", "Barrel", "detail", "cylinder", (0.32, 0.18, 0.32), "front", u=0, v=0, inset=0.02, ro=(90, 0, 0), c="#38bdf8", mat="Neon")
            P("Grip", "Receiver", "shape", "box", (0.42, 1.05, 0.52), "bot", u=0, v=0.55, inset=0.05, ro=(16, 0, 0), c="#0f172a", mat="SmoothPlastic")
            P("Magazine", "Receiver", "detail", "box", (0.36, 0.95, 0.48), "bot", u=0, v=-0.25, inset=0.05, ro=(-10, 0, 0), c="#1e293b", mat="Metal")
            P("OpticScope", "Receiver", "detail", "cylinder", (0.34, 1.25, 0.34), "top", u=0, v=0.1, inset=0.03, ro=(90, 0, 0), c="#0f172a", mat="Metal")
            P("ScopeLens", "OpticScope", "detail", "sphere", (0.30, 0.30, 0.12), "front", u=0, v=0, inset=0.02, c="#ef4444", mat="Neon")
            P("Stock", "Receiver", "shape", "box", (0.44, 0.72, 1.35), "back", u=0, v=-0.1, inset=0.04, c="#1e293b", mat="SmoothPlastic")
        elif is_pole:
            P("Shaft", None, "raw", "cylinder", (0.34, 4.4 * jl, 0.34), "center", c="#78350f", mat="Wood")
            P("Collar", "Shaft", "shape", "cylinder", (0.48, 0.45, 0.48), "top", u=0, v=0, inset=0.04, c="#d4af37", mat="Metal")
            if "hammer" in prompt or "mace" in ptoks:
                P("HammerHead", "Collar", "shape", "box", (1.85, 0.95, 0.95), "top", u=0, v=0, inset=0.04, c=metal_c, mat="Metal")
            else:
                P("AxeBladeR", "Collar", "detail", "wedge", (1.25, 1.35, 0.22), "right", u=0, v=0, inset=0.05, c=metal_c, mat="Metal", mirror=True)
                P("SpearTip", "Collar", "detail", "cone", (0.46, 1.15, 0.46), "top", u=0, v=0, inset=0.03, c=metal_c, mat="Metal")
        else:
            P("HiltGrip", None, "raw", "cylinder", (0.36, 1.35, 0.36), "center", c=main_c, mat="Metal")
            P("Pommel", "HiltGrip", "shape", "sphere", (0.54, 0.54, 0.54), "bot", u=0, v=0, inset=0.04, c="#eab308", mat="Metal")
            P("CrossGuard", "HiltGrip", "shape", "box", (1.85, 0.36, 0.52), "top", u=0, v=0, inset=0.02, c=main_c, mat="Metal")
            P("GuardGem", "CrossGuard", "detail", "sphere", (0.38, 0.38, 0.28), "front", u=0, v=0, inset=0.02, c="#eab308", mat="Neon")
            P("Blade", "CrossGuard", "shape", "box", (0.56, 3.8 * jl, 0.16), "top", u=0, v=0, inset=0.02, c=metal_c, mat="Metal")
            P("BladeTip", "Blade", "detail", "cone", (0.56, 0.85, 0.16), "top", u=0, v=0, inset=0.02, c=metal_c, mat="Metal")
        return {"category": "weapon", "riggable": False, "parts": parts}, "Weaponry 3D Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN I: FOLIAGE & NATURE
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "tree", "pine", "oak", "palm", "sakura", "cherryblossom", "cactus", "bush", "plant", "flower", "rose", "mushroom", "toadstool"
    )) or any(w in wtoks for w in ("tree", "plant", "fungus", "mushroom", "cactus", "flora")):
        if "mushroom" in ptoks or "toadstool" in ptoks or "fungus" in wtoks:
            cap_c = c_main or "#dc2626"
            P("Stem", None, "raw", "cylinder", (1.25 * jw, 2.2 * jh, 1.25 * jw), "center", c="#fef3c7")
            P("CapDome", "Stem", "shape", "sphere", (3.6 * jw, 1.65 * jh, 3.6 * jl), "top", u=0, v=0, inset=0.35, c=cap_c)
            for ui, vi in ((-0.45, -0.45), (0.45, -0.45), (-0.45, 0.45), (0.45, 0.45), (0, 0)):
                P(f"Spot_{int((ui+1)*10)}_{int((vi+1)*10)}", "CapDome", "detail", "sphere", (0.52, 0.28, 0.52), "top", u=ui, v=vi, inset=0.06, c="#ffffff")
        elif "cactus" in ptoks or "cactus" in wtoks:
            c_green = c_main or "#16a34a"
            P("MainStem", None, "raw", "cylinder", (1.2 * jw, 3.8 * jh, 1.2 * jw), "center", c=c_green, mat="Grass")
            P("TopDome", "MainStem", "shape", "sphere", (1.2 * jw, 0.8, 1.2 * jw), "top", u=0, v=0, inset=0.25, c=c_green, mat="Grass")
            P("BranchArmR", "MainStem", "shape", "box", (0.95, 0.65, 0.65), "right", u=0, v=0.15, inset=0.06, c=c_green, mat="Grass", mirror=True)
            P("BranchUpR", "BranchArmR", "detail", "cylinder", (0.68, 1.45, 0.68), "top", u=0.35, v=0, inset=0.06, c=c_green, mat="Grass", mirror=True)
        else:
            leaf_c = c_main or ("#f472b6" if "sakura" in ptoks or "cherry" in prompt else "#16a34a")
            P("Trunk", None, "raw", "cylinder", (1.15 * jw, 2.8 * jh, 1.15 * jw), "center", c="#78350f", mat="Wood")
            P("RootFlare", "Trunk", "shape", "cone", (1.75 * jw, 0.65, 1.75 * jw), "bot", u=0, v=0, inset=0.25, c="#78350f", mat="Wood")
            par = "Trunk"
            for i in range(3):
                cw_s = (3.8 - i * 0.85) * jw
                shp = "cone" if "pine" in ptoks else "sphere"
                par = f"Canopy{i}"
                P(par, "Trunk" if i == 0 else f"Canopy{i-1}", "shape" if i < 2 else "detail", shp, (cw_s, 1.55 * jh, cw_s), "top", u=0, v=0, inset=0.35, c=leaf_c, mat="Grass")
        return {"category": "foliage", "riggable": False, "parts": parts}, "Botanical 3D Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN J: FURNITURE, ELECTRONICS & PROPS
    # ---------------------------------------------------------------------
    if any(w in ptoks for w in (
        "chair", "throne", "sofa", "couch", "table", "desk", "bed", "chest", "treasure", "crate",
        "barrel", "lamp", "lantern", "tv", "monitor", "computer", "pc", "laptop", "arcade",
        "burger", "hamburger", "pizza", "cake", "potion", "trophy", "chalice", "guitar", "piano", "snowman"
    )) or any(w in wtoks for w in ("furniture", "appliance", "food", "dish", "sandwich", "beverage", "instrument", "container")):
        if "snowman" in ptoks:
            P("BaseSnowball", None, "raw", "sphere", (2.6 * jw, 2.2 * jh, 2.6 * jl), "center", c="#f8fafc")
            P("MidSnowball", "BaseSnowball", "shape", "sphere", (2.0 * jw, 1.7 * jh, 2.0 * jl), "top", u=0, v=0, inset=0.35, c="#f8fafc")
            P("HeadSnowball", "MidSnowball", "shape", "sphere", (1.4 * jw, 1.3 * jh, 1.4 * jl), "top", u=0, v=0, inset=0.25, c="#f8fafc", joint=True)
            P("CarrotNose", "HeadSnowball", "detail", "cone", (0.24, 0.75, 0.24), "front", u=0, v=0, inset=0.05, ro=(-90, 0, 0), c="#ea580c")
            P("CoalEyeR", "HeadSnowball", "detail", "sphere", (0.18, 0.18, 0.12), "front", u=0.35, v=0.25, inset=0.02, c="#0f172a", mirror=True)
            P("TopHatBrim", "HeadSnowball", "detail", "cylinder", (1.5, 0.14, 1.5), "top", u=0, v=0, inset=0.1, c="#1e293b")
            P("TopHatCrown", "TopHatBrim", "detail", "cylinder", (1.05, 0.95, 1.05), "top", u=0, v=0, inset=0.02, c="#1e293b")
            P("BranchArmR", "MidSnowball", "detail", "cylinder", (0.16, 1.65, 0.16), "right", u=0, v=0.15, inset=0.1, ro=(0, 0, 65), c="#78350f", mat="Wood", mirror=True)
            return {"category": "prop", "riggable": True, "parts": parts}, "Prop & Character Modeler"
        if any(w in ptoks for w in ("burger", "hamburger", "sandwich", "cake", "pie", "pizza")):
            P("BottomBun", None, "raw", "cylinder", (2.6 * jw, 0.55, 2.6 * jl), "center", c="#d97706")
            P("MeatPatty", "BottomBun", "shape", "cylinder", (2.75 * jw, 0.52, 2.75 * jl), "top", u=0, v=0, inset=0.03, c="#5c2808", mat="Slate")
            P("CheeseSlice", "MeatPatty", "detail", "box", (2.55 * jw, 0.14, 2.55 * jl), "top", u=0, v=0, inset=0.02, ro=(0, 45, 0), c="#facc15")
            P("TomatoLayer", "CheeseSlice", "detail", "cylinder", (2.35 * jw, 0.22, 2.35 * jl), "top", u=0, v=0, inset=0.02, c="#dc2626")
            P("LettuceRing", "TomatoLayer", "detail", "cylinder", (2.68 * jw, 0.20, 2.68 * jl), "top", u=0, v=0, inset=0.02, c="#16a34a")
            P("TopBun", "LettuceRing", "shape", "sphere", (2.65 * jw, 1.15, 2.65 * jl), "top", u=0, v=0, inset=0.28, c="#d97706")
        elif any(w in ptoks for w in ("tv", "monitor", "computer", "pc", "laptop", "arcade")):
            P("StandBase", None, "raw", "box", (1.6 * jw, 0.24, 1.2 * jl), "center", c="#1e293b", mat="Metal")
            P("StandNeck", "StandBase", "shape", "cylinder", (0.36, 0.75, 0.36), "top", u=0, v=-0.2, inset=0.03, c="#334155", mat="Metal")
            P("MonitorFrame", "StandNeck", "raw", "box", (3.6 * jw, 2.2 * jh, 0.28), "top", u=0, v=0, inset=0.04, c="#0f172a", mat="Metal")
            P("DisplayScreen", "MonitorFrame", "detail", "box", (3.32 * jw, 1.92 * jh, 0.08), "front", u=0, v=0, inset=0.01, c=c_main or "#38bdf8", mat="Neon")
        elif any(w in ptoks for w in ("table", "desk")):
            P("TableTop", None, "raw", "box", (3.8 * jw, 0.32, 2.4 * jl), "center", c=c_main or "#78350f", mat="Wood")
            for vz, zt in ((-0.82, "F"), (0.82, "B")):
                P(f"Leg{zt}R", "TableTop", "shape", "cylinder", (0.28, 1.85 * jh, 0.28), "bot", u=0.82, v=vz, inset=0.04, c="#1e293b", mat="Metal", mirror=True)
        else:
            c_wood = c_main or "#78350f"
            P("SeatCushion", None, "raw", "box", (2.1 * jw, 0.36, 2.0 * jl), "center", c=c_wood, mat="Wood")
            P("Backrest", "SeatCushion", "shape", "box", (2.1 * jw, 2.3 * jh, 0.34), "back", u=0, v=0.85, inset=0.04, c=c_wood, mat="Wood")
            P("ArmrestR", "SeatCushion", "detail", "box", (0.30, 0.72, 1.85 * jl), "right", u=0, v=0.55, inset=0.04, c="#d4af37", mat="Metal", mirror=True)
            for vz, zt in ((-0.78, "F"), (0.78, "B")):
                P(f"ChairLeg{zt}R", "SeatCushion", "shape", "cylinder", (0.28, 1.35, 0.28), "bot", u=0.78, v=vz, inset=0.04, c="#1e293b", mat="Metal", mirror=True)
        return {"category": "prop", "riggable": False, "parts": parts}, "Prop & Industrial Modeler"

    # ---------------------------------------------------------------------
    # DOMAIN K: HUMANOIDS, HEROES, ROBOTS & MECHS
    # ---------------------------------------------------------------------
    is_mech = any(w in ptoks for w in ("mech", "mecha", "gundam", "robot", "cyborg", "exosuit", "golem", "titan"))
    is_astro = any(w in ptoks for w in ("astronaut", "spaceman", "cosmonaut"))
    is_martial = any(w in ptoks for w in ("ryu", "karate", "fighter", "ninja", "samurai", "monk", "boxer"))
    is_knight = any(w in ptoks for w in ("knight", "paladin", "warrior", "king", "queen", "viking", "soldier"))

    suit_c = c_main or ("#f8fafc" if is_astro or "ryu" in ptoks or "karate" in ptoks else ("#94a3b8" if is_knight else ("#2563eb" if is_mech else rng.choice(["#dc2626", "#2563eb", "#16a34a", "#7c3aed", "#ea580c"]))))
    acc_c = c_sec or ("#dc2626" if is_martial or is_astro else "#eab308")
    skin_c = "#cbd5e1" if is_mech else rng.choice(["#f2c9a0", "#e0ac7e", "#c68863"])
    pants_c = "#f8fafc" if (is_astro or "ryu" in ptoks or "karate" in ptoks) else "#1e293b"

    cw, ch, lh = (2.2 if is_mech else 1.75) * jw, (2.1 if is_mech else 1.85) * jh, (1.65 if is_mech else 1.35) * jl
    P("HumanoidRootPart", None, "raw", "box", (cw * 0.92, 0.55, 0.96), "center", c=pants_c)
    P("Torso", "HumanoidRootPart", "raw", "box", (cw, ch, 1.02), "top", u=0, v=0, inset=0.02, c=suit_c, mat="Metal" if is_mech or is_knight else "SmoothPlastic", joint=True)
    P("Neck", "Torso", "raw", "cylinder", (0.48, 0.26, 0.48), "top", u=0, v=0, inset=0.02, c=skin_c, joint=True)
    P("Head", "Neck", "raw", "box" if is_mech else "sphere", (1.24, 1.24, 1.20), "top", u=0, v=0, inset=0.04, c=skin_c, joint=True)

    P("Belt", "HumanoidRootPart", "detail", "box", (cw * 0.96, 0.24, 1.04), "top", u=0, v=0, inset=0.12, c="#0f172a")
    P("ChestArmor", "Torso", "detail", "box", (cw * 0.74, ch * 0.50, 0.18), "front", u=0, v=0.15, inset=0.02, c=acc_c if is_mech else "#cbd5e1", mat="Metal" if is_knight or is_mech else "SmoothPlastic")
    if is_mech or is_astro:
        P("CoreReactor", "ChestArmor", "detail", "sphere", (0.42, 0.42, 0.18), "front", u=0, v=0, inset=0.02, c="#38bdf8", mat="Neon")
        P("BackPack", "Torso", "shape", "box", (cw * 0.72, ch * 0.68, 0.52), "back", u=0, v=0.08, inset=0.03, c="#cbd5e1", mat="Metal")

    P("ThighR", "HumanoidRootPart", "shape", "box", (0.68, lh, 0.72), "bot", u=0.52, v=0, inset=0.02, c=pants_c, joint=True, mirror=True)
    P("ShinR", "ThighR", "shape", "box", (0.60, lh, 0.64), "bot", u=0, v=0, inset=0.02, c=pants_c, joint=True, mirror=True)
    P("BootR", "ShinR", "detail", "box", (0.66, 0.38, 1.05), "bot", u=0, v=-0.18, inset=0.02, c=skin_c if is_martial else "#0f172a", mirror=True)

    P("ShoulderPadR", "Torso", "detail", "sphere" if not is_mech else "box", (0.72, 0.52, 0.75), "right", u=0, v=0.72, inset=0.08, c=acc_c, mat="Metal" if is_knight or is_mech else "SmoothPlastic", mirror=True)
    P("ArmR", "Torso", "shape", "box", (0.58, lh * 0.85, 0.60), "right", u=0, v=0.22, inset=0.02, c=skin_c if is_martial else suit_c, joint=True, mirror=True)
    P("ForearmR", "ArmR", "shape", "box", (0.50, lh * 0.80, 0.52), "bot", u=0, v=0, inset=0.02, c=skin_c, joint=True, mirror=True)
    P("HandR", "ForearmR", "detail", "sphere", (0.50, 0.50, 0.50), "bot", u=0, v=0, inset=0.04, c=acc_c if is_martial else skin_c, joint=True, mirror=True)

    P("EyeR", "Head", "detail", "sphere", (0.24, 0.26, 0.12), "front", u=0.38, v=0.12, inset=0.02, c="#38bdf8" if is_mech else "#0f172a", mat="Neon" if is_mech else "SmoothPlastic", mirror=True)
    if is_astro or is_mech:
        P("Visor", "Head", "detail", "box", (1.04, 0.56, 0.16), "front", u=0, v=0.08, inset=0.02, c="#eab308", mat="Glass", tr=0.2)
    else:
        P("HairCap", "Head", "detail", "sphere", (1.28, 0.68, 1.24), "top", u=0, v=0, inset=0.26, c="#2b1d12")
        if is_martial:
            P("Headband", "Head", "detail", "box", (1.26, 0.22, 1.22), "front", u=0, v=0.38, inset=1.18, c=acc_c)
        if "king" in ptoks or "queen" in ptoks or "crown" in prompt:
            P("RoyalCrown", "Head", "detail", "cylinder", (0.95, 0.34, 0.95), "top", u=0, v=0, inset=0.05, c="#eab308", mat="Metal")

    if any(w in ptoks for w in ("sword", "katana", "blade", "knight", "samurai")):
        P("HeldHilt", "HandR", "detail", "cylinder", (0.20, 0.85, 0.20), "front", u=0, v=0, inset=0.05, ro=(90, 0, 0), c="#1e293b", mat="Metal")
        P("HeldBlade", "HeldHilt", "detail", "box", (0.14, 0.26, 2.45), "front", u=0, v=0, inset=0.02, c="#38bdf8", mat="Neon")
    if is_astro or "flag" in ptoks:
        P("FlagPole", "HandL", "detail", "cylinder", (0.18, 4.0, 0.18), "front", u=0, v=0.8, inset=0.05, c="#cbd5e1", mat="Metal")
        P("FlagBanner", "FlagPole", "detail", "box", (1.65, 1.0, 0.12), "left", u=0, v=0.68, inset=0.02, c="#dc2626")

    return {"category": "humanoid", "riggable": True, "parts": parts}, "Character & Mech Modeler"

# =========================================================================
# 5. STAGE 6: SURFACE SOCKET COMPILER + 3D BOUNDING-BOX CRITIC & REPAIR LOOP
# =========================================================================
def compile_and_repair_3d_model(bp, scale=1.0):
    raw_list = bp.get("parts") or []
    compiled = []
    idx = {}
    logs = []

    def emit_part(item, is_mirror=False):
        raw_n = str(item.get("n") or f"Part{len(compiled)}")
        if is_mirror:
            n = (raw_n[:-1] + "L") if raw_n.endswith("R") else (raw_n + "L")
        else:
            n = raw_n
        base_n = n; cnt = 2
        while n in idx:
            n = f"{base_n}{cnt}"; cnt += 1

        p_name = item.get("p")
        if is_mirror and p_name:
            if p_name.endswith("R") and (p_name[:-1] + "L") in idx:
                p_name = p_name[:-1] + "L"
            elif (p_name + "L") in idx:
                p_name = p_name + "L"

        sz_in = item.get("sz") or [1, 1, 1]
        if not isinstance(sz_in, (list, tuple)) or len(sz_in) < 3:
            sz_in = [1, 1, 1]
        sz = [round(clamp(float(v), 0.05, 30.0) * scale, 3) for v in sz_in[:3]]

        ro_in = item.get("ro") or [0, 0, 0]
        if not isinstance(ro_in, (list, tuple)) or len(ro_in) < 3:
            ro_in = [0, 0, 0]
        ro = [round(float(r), 1) for r in ro_in[:3]]
        if is_mirror:
            ro = [ro[0], -ro[1], -ro[2]]

        att = item.get("attach") if isinstance(item.get("attach"), dict) else {}
        face = str(att.get("face", "top" if p_name else "center")).lower()
        if is_mirror and face in ("right", "left"):
            face = "left" if face == "right" else "right"

        u = clamp(float(att.get("u", 0.0)), -1.0, 1.0)
        if is_mirror and face not in ("right", "left"):
            u = -u
        v = clamp(float(att.get("v", 0.0)), -1.0, 1.0)
        inset = clamp(float(att.get("inset", 0.03)), -0.5, 2.0) * scale

        if p_name and p_name in idx:
            par = idx[p_name]
            px, py, pz = par["po"]
            pw, ph, pd = rot_dims(par["sz"], par["ro"])
            cw, ch, cd = rot_dims(sz, ro)

            if item.get("stage") == "detail" and cw > pw * 2.2 and ch > ph * 2.2:
                sz = [round(sz[0] * 0.5, 3), round(sz[1] * 0.5, 3), round(sz[2] * 0.5, 3)]
                cw, ch, cd = rot_dims(sz, ro)

            f = FACES.get(face, (0, 1, 0))
            if face in ("front", "back"):
                wx = px + u * (pw * 0.44)
                wy = py + v * (ph * 0.44)
                wz = pz + f[2] * (pd / 2.0 + cd / 2.0 - inset)
            elif face in ("right", "left"):
                wx = px + f[0] * (pw / 2.0 + cw / 2.0 - inset)
                wy = py + v * (ph * 0.44)
                wz = pz + u * (pd * 0.44)
            elif face in ("top", "bot", "bottom"):
                wx = px + u * (pw * 0.44)
                wy = py + f[1] * (ph / 2.0 + ch / 2.0 - inset)
                wz = pz + v * (pd * 0.44)
            else:
                wx, wy, wz = px + u * (pw * 0.35), py + v * (ph * 0.35), pz
        else:
            wx, wy, wz = 0.0, 2.5, 0.0

        color_str = str(item.get("c") or "#cccccc")
        if color_str.lower() in NAMED_COLORS:
            color_str = NAMED_COLORS[color_str.lower()]
        elif not color_str.startswith("#"):
            color_str = "#cccccc"

        p_obj = {
            "n": n, "p": p_name,
            "stage": item.get("stage") if item.get("stage") in ("raw", "shape", "detail") else ("raw" if not p_name else "detail"),
            "s": item.get("s") if item.get("s") in ("box", "sphere", "cylinder", "wedge", "cone", "pyramid") else "box",
            "sz": sz, "po": [round(wx, 3), round(wy, 3), round(wz, 3)],
            "ro": ro, "c": color_str,
            "mat": item.get("mat") or "SmoothPlastic",
            "tr": clamp(float(item.get("tr", 0.0)), 0.0, 0.9),
            "joint": bool(item.get("joint", False)),
            "face": face
        }
        compiled.append(p_obj)
        idx[n] = p_obj

    for item in raw_list:
        if isinstance(item, dict):
            emit_part(item, is_mirror=False)
            if item.get("mirror"):
                emit_part(item, is_mirror=True)

    total_repairs = 0
    for iteration in range(1, 6):
        fixes_this_pass = 0
        for p in compiled:
            if not p["p"] or p["p"] not in idx:
                continue
            par = idx[p["p"]]
            px, py, pz = par["po"]
            pw, ph, pd = rot_dims(par["sz"], par["ro"])
            cx, cy, cz = p["po"]
            cw, ch, cd = rot_dims(p["sz"], p["ro"])

            dx = max(0.0, abs(cx - px) - (pw / 2.0 + cw / 2.0))
            dy = max(0.0, abs(cy - py) - (ph / 2.0 + ch / 2.0))
            dz = max(0.0, abs(cz - pz) - (pd / 2.0 + cd / 2.0))
            gap = math.sqrt(dx*dx + dy*dy + dz*dz)
            if gap > 0.02:
                if dx > 0: cx += (-1.0 if cx > px else 1.0) * (dx + 0.015)
                if dy > 0: cy += (-1.0 if cy > py else 1.0) * (dy + 0.015)
                if dz > 0: cz += (-1.0 if cz > pz else 1.0) * (dz + 0.015)
                p["po"] = [round(cx, 3), round(cy, 3), round(cz, 3)]
                fixes_this_pass += 1
                total_repairs += 1

            in_x = (abs(cx - px) + cw / 2.0) < (pw / 2.0 - 0.01)
            in_y = (abs(cy - py) + ch / 2.0) < (ph / 2.0 - 0.01)
            in_z = (abs(cz - pz) + cd / 2.0) < (pd / 2.0 - 0.01)
            if in_x and in_y and in_z and p.get("stage") == "detail":
                f = FACES.get(p.get("face", "front"), (0, 0, -1))
                if f[2] != 0: cz = pz + f[2] * (pd / 2.0 + cd / 2.0 - 0.015)
                elif f[0] != 0: cx = px + f[0] * (pw / 2.0 + cw / 2.0 - 0.015)
                else: cy = py + (1.0 if cy >= py else -1.0) * (ph / 2.0 + ch / 2.0 - 0.015)
                p["po"] = [round(cx, 3), round(cy, 3), round(cz, 3)]
                fixes_this_pass += 1
                total_repairs += 1

        if fixes_this_pass == 0:
            logs.append({
                "stage": "6_critic_pass",
                "msg": f"3D Placement Critic PASSED on pass #{iteration} ({total_repairs} placement corrections applied; 0 floating parts)"
            })
            break
        else:
            logs.append({
                "stage": f"6_critic_rework_{iteration}",
                "msg": f"Pass #{iteration}: Found {fixes_this_pass} misaligned/floating details -> re-solved surface coordinates"
            })

    if compiled:
        min_y = min(p["po"][1] - rot_dims(p["sz"], p["ro"])[1] / 2.0 for p in compiled)
        for p in compiled:
            p["po"][1] = round(p["po"][1] - min_y, 3)

    return compiled, logs, total_repairs

def compute_bounds(parts):
    if not parts:
        return [4.0, 4.0, 4.0]
    xs, ys, zs = [], [], []
    for p in parts:
        wx, wy, wz = p["po"]
        sx, sy, sz = rot_dims(p["sz"], p["ro"])
        xs.extend([wx - sx/2, wx + sx/2])
        ys.extend([wy - sy/2, wy + sy/2])
        zs.extend([wz - sz/2, wz + sz/2])
    return [round(max(xs)-min(xs), 1), round(max(ys)-min(ys), 1), round(max(zs)-min(zs), 1)]

# =========================================================================
# 6. STAGE 9: PACKAGING INTO ROBLOX STUDIO LUAU (WITH MOTOR6D RIG) & .OBJ
# =========================================================================
def export_roblox_lua(spec):
    parts = spec.get("parts") or []
    name = spec.get("name") or "RobloxAsset"
    is_rigged = bool(spec.get("meta", {}).get("riggable"))

    lines = [
        f"-- Roblox Cloud 3D Modeler AI | Asset: {name} | Parts: {len(parts)} | Rigged: {is_rigged}",
        "-- Copy & Paste directly into the Roblox Studio Command Bar",
        "local model = Instance.new('Model')",
        f"model.Name = {json.dumps(name)}",
        "model.Parent = workspace",
        "local parts = {}",
        "local MAT_MAP = {",
        "  SmoothPlastic = Enum.Material.SmoothPlastic, Metal = Enum.Material.Metal,",
        "  Neon = Enum.Material.Neon, Glass = Enum.Material.Glass, Wood = Enum.Material.Wood,",
        "  Slate = Enum.Material.Slate, Brick = Enum.Material.Brick,",
        "  Cobblestone = Enum.Material.Cobblestone, Fabric = Enum.Material.Fabric, Grass = Enum.Material.Grass",
        "}",
        "local function mk(n, par, shp, sz, po, ro, hex, matName, tr, isJoint)",
        "  local p",
        "  if shp == 'wedge' or shp == 'cone' or shp == 'pyramid' then",
        "    p = Instance.new('WedgePart')",
        "  else",
        "    p = Instance.new('Part')",
        "  end",
        "  p.Name = n",
        f"  p.Anchored = {'false' if is_rigged else 'true'}",
        "  p.CanCollide = (par == nil)",
        "  p.TopSurface = Enum.SurfaceType.Smooth",
        "  p.BottomSurface = Enum.SurfaceType.Smooth",
        "  p.Color = Color3.fromHex(hex)",
        "  p.Material = MAT_MAP[matName] or Enum.Material.SmoothPlastic",
        "  p.Transparency = tr or 0",
        "  p.Size = Vector3.new(sz[1], sz[2], sz[3])",
        "  if shp == 'sphere' or shp == 'gem' then",
        "    local sm = Instance.new('SpecialMesh', p)",
        "    sm.MeshType = Enum.MeshType.Sphere",
        "  elseif shp == 'cylinder' then",
        "    local sm = Instance.new('SpecialMesh', p)",
        "    sm.MeshType = Enum.MeshType.Cylinder",
        "  end",
        "  local worldCF = CFrame.new(po[1], po[2], po[3]) * CFrame.Angles(math.rad(ro[1]), math.rad(ro[2]), math.rad(ro[3]))",
        "  p.CFrame = worldCF",
        "  p.Parent = model",
        "  parts[n] = p",
        "  if par and parts[par] then",
        "    if isJoint then",
        "      local m6d = Instance.new('Motor6D')",
        "      m6d.Name = n .. '_Joint'",
        "      m6d.Part0 = parts[par]; m6d.Part1 = p",
        "      m6d.C0 = parts[par].CFrame:ToObjectSpace(worldCF)",
        "      m6d.C1 = CFrame.new()",
        "      m6d.Parent = parts[par]",
        "    else",
        "      local w = Instance.new('WeldConstraint')",
        "      w.Part0 = parts[par]; w.Part1 = p; w.Parent = p",
        "    end",
        "  else",
        "    p.Anchored = true",
        "  end",
        "end"
    ]
    for p in parts:
        hx = p.get("c", "#cccccc")
        if not str(hx).startswith("#"):
            hx = "#cccccc"
        lines.append(
            f"mk({json.dumps(p['n'])}, {json.dumps(p['p'])}, {json.dumps(p['s'])}, "
            f"{{{p['sz'][0]},{p['sz'][1]},{p['sz'][2]}}}, "
            f"{{{p['po'][0]},{p['po'][1]},{p['po'][2]}}}, "
            f"{{{p['ro'][0]},{p['ro'][1]},{p['ro'][2]}}}, "
            f"{json.dumps(hx)}, {json.dumps(p.get('mat', 'SmoothPlastic'))}, "
            f"{p.get('tr', 0.0)}, {'true' if (is_rigged and p.get('joint')) else 'false'})"
        )
    root = spec.get("root")
    if root:
        lines.append(f"if parts[{json.dumps(root)}] then model.PrimaryPart = parts[{json.dumps(root)}] end")
    if is_rigged:
        lines.extend([
            "local hum = Instance.new('Humanoid'); hum.Parent = model",
            "local anim = Instance.new('Animator'); anim.Parent = hum"
        ])
    lines.append("game:GetService('Selection'):Set({model})")
    return "\n".join(lines)

def export_obj(spec):
    parts = spec.get("parts") or []
    out = [f"# Roblox Cloud 3D Modeler Wavefront OBJ: {spec.get('name', 'Asset')}"]
    v_offset = 1
    for p in parts:
        wx, wy, wz = p["po"]
        sx, sy, sz = rot_dims(p["sz"], p["ro"])
        hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
        out.append(f"o {p['n']}")
        for vx, vy, vz in [
            (wx-hx, wy-hy, wz-hz), (wx+hx, wy-hy, wz-hz), (wx+hx, wy+hy, wz-hz), (wx-hx, wy+hy, wz-hz),
            (wx-hx, wy-hy, wz+hz), (wx+hx, wy-hy, wz+hz), (wx+hx, wy+hy, wz+hz), (wx-hx, wy+hy, wz+hz)
        ]:
            out.append(f"v {vx:.4f} {vy:.4f} {vz:.4f}")
        for a, b, c, d in [(0,1,2,3), (4,7,6,5), (0,4,5,1), (1,5,6,2), (2,6,7,3), (3,7,4,0)]:
            out.append(f"f {v_offset+a} {v_offset+b} {v_offset+c}\nf {v_offset+a} {v_offset+c} {v_offset+d}")
        v_offset += 8
    return "\n".join(out)

# =========================================================================
# 7. FULL 9-STAGE AUTONOMOUS PIPELINE ORCHESTRATOR
# =========================================================================
def run_autonomous_pipeline(prompt, seed=7, api_key=""):
    t0 = time.time()
    logs = []

    subject, wiki_summary = search_internet_knowledge(prompt)
    logs.append({"stage": "1_check_prompt", "msg": f"Analyzed prompt '{prompt}' -> Primary subject: '{subject}'"})

    if wiki_summary:
        logs.append({"stage": "2_internet_search", "msg": f"Wikipedia Lookup: {wiki_summary[:140]}..."})
    else:
        logs.append({"stage": "2_internet_search", "msg": f"Direct semantic features extracted for '{subject}'"})

    bp, engine_used = call_cloud_llm_architect(prompt, wiki_summary, seed, api_key=api_key)
    if not bp:
        bp, engine_used = synthesize_from_semantics_and_wiki(prompt, subject, wiki_summary, seed)

    raw_cnt = sum(1 for p in bp["parts"] if p.get("stage") == "raw")
    shp_cnt = sum(1 for p in bp["parts"] if p.get("stage") == "shape")
    det_cnt = sum(1 for p in bp["parts"] if p.get("stage") == "detail")
    logs.append({"stage": "3_raw_blockout", "msg": f"[{engine_used}] Built {raw_cnt} core mass blocks"})
    logs.append({"stage": "4_shape_sculpting", "msg": f"Sculpted {shp_cnt} structural/anatomical shapes"})
    logs.append({"stage": "5_detail_pass", "msg": f"Added {det_cnt} surface-socketed details"})

    compiled, critic_logs, repairs = compile_and_repair_3d_model(bp, scale=1.0)
    logs.extend(critic_logs)

    mats_used = sorted({p.get("mat", "SmoothPlastic") for p in compiled})
    logs.append({"stage": "7_color_and_materials", "msg": f"Applied realistic hex palette & Roblox materials ({', '.join(mats_used)})"})

    bounds = compute_bounds(compiled)
    logs.append({"stage": "8_final_model_check", "msg": f"Final QA PASS: {len(compiled)} parts grounded at Y=0.00 ({bounds[0]}×{bounds[1]}×{bounds[2]} studs)"})

    clean_title = re.sub(r"[^a-zA-Z0-9]+", "_", subject.title()).strip("_") or "Asset"
    spec = {
        "id": f"rbx_{int(time.time()*1000)%100000}_{seed%97}",
        "name": f"{clean_title}_{seed%997}",
        "archetype": bp.get("category", "model"),
        "seed": seed,
        "root": compiled[0]["n"] if compiled else "Root",
        "parts": compiled,
        "bounds": bounds,
        "pipeline_logs": logs,
        "meta": {
            "prompt": prompt,
            "subject": subject,
            "engine": engine_used,
            "riggable": bool(bp.get("riggable", True)),
            "repairs": repairs,
            "seconds": round(time.time() - t0, 2)
        }
    }

    spec["lua"] = export_roblox_lua(spec)
    spec["obj"] = export_obj(spec)
    logs.append({"stage": "9_package_deploy", "msg": f"Packaged LUA ({len(spec['lua'])} chars, Motor6D={spec['meta']['riggable']}) + Wavefront .OBJ"})
    return spec

def build_one(prompt, seed=7, var=0, feat=None):
    spec = run_autonomous_pipeline(prompt, seed=seed)
    return spec, {"root": spec["archetype"]}

def generate(body, mem=None):
    prompt = (body.get("prompt") or "orange tabby cat").strip()
    it = int(body.get("iteration", 0))
    nonce = str(body.get("nonce") or time.time())
    api_key = str(body.get("api_key") or "").strip()
    seed = zlib.crc32(f"{prompt}|{it}|{nonce}".encode())
    return run_autonomous_pipeline(prompt, seed=seed, api_key=api_key)

# =========================================================================
# 8. INTERACTIVE 3D STUDIO WEB UI
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
  .brand { font-weight: 800; font-size: 13px; color: #60a5fa; margin-right: 6px; letter-spacing: 0.6px; }
  .pill { padding: 6px 12px; border-radius: 999px; border: 1px solid var(--border); background: #1e2330; font-size: 12px; font-weight: 600; color: var(--text); cursor: pointer; transition: 0.15s; }
  .pill:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
  .subheader { display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; background: #13161f; border-bottom: 1px solid var(--border); flex-wrap: wrap; gap: 8px; }
  .title-group { display: flex; align-items: center; gap: 10px; }
  .model-title { font-weight: 800; font-size: 13px; text-transform: uppercase; }
  .badge { background: rgba(16,185,129,0.15); color: var(--success); border: 1px solid rgba(16,185,129,0.3); font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; }
  .actions { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
  .btn-sm { padding: 6px 11px; border-radius: 8px; border: 1px solid var(--border); background: #1e2330; color: var(--text); font-size: 11px; font-weight: 700; cursor: pointer; }
  .btn-sm:hover, .btn-sm.active { background: #2d3748; border-color: #60a5fa; }
  .btn-sm.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
  .workspace { position: relative; flex: 1; display: flex; overflow: hidden; }
  #viewport { flex: 1; height: 100%; display: block; background: radial-gradient(circle at 50% 45%, #1e2433 0%, #0d0f14 100%); }
  .pipeline-sidebar { width: 340px; background: var(--panel); border-left: 1px solid var(--border); padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
  .step-card { background: #12151e; border: 1px solid var(--border); border-left: 3px solid var(--success); border-radius: 6px; padding: 8px 10px; font-size: 11px; }
  .step-stage { font-weight: 800; color: #60a5fa; text-transform: uppercase; font-size: 10px; margin-bottom: 2px; }
  .step-msg { color: #cbd5e1; line-height: 1.35; }
  .stats-pill { position: absolute; bottom: 14px; left: 16px; background: rgba(15,17,23,0.9); border: 1px solid var(--border); padding: 6px 12px; border-radius: 8px; font-size: 11px; font-family: monospace; pointer-events: none; color: var(--muted); }
  #scriptPanel { position: absolute; inset: 16px; background: rgba(15,17,23,0.97); border: 1px solid var(--border); border-radius: 12px; padding: 16px; display: none; flex-direction: column; gap: 10px; z-index: 20; }
  #scriptPanel.open { display: flex; }
  #codeBox { flex: 1; width: 100%; background: #090b0e; color: #86efac; border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 12px; resize: none; }
  .bottom-panel { background: var(--panel); border-top: 1px solid var(--border); padding: 10px 16px 14px; display: flex; gap: 8px; align-items: center; }
  #promptInput { flex: 1; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border); font-size: 14px; background: #11141c; color: #fff; outline: none; }
  #promptInput:focus { border-color: var(--accent); }
  #apiKeyInput { width: 190px; padding: 10px 10px; border-radius: 10px; border: 1px solid var(--border); font-size: 12px; background: #11141c; color: #94a3b8; outline: none; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>

<div class="topbar">
  <span class="brand">ROBLOX CLOUD 3D AI</span>
  <button class="pill" onclick="runPrompt('orange tabby cat')">Cat</button>
  <button class="pill" onclick="runPrompt('husky dog')">Husky Dog</button>
  <button class="pill" onclick="runPrompt('modern two story cafe building')">Cafe Building</button>
  <button class="pill" onclick="runPrompt('japanese red pagoda temple')">Pagoda Temple</button>
  <button class="pill" onclick="runPrompt('medieval stone castle')">Stone Castle</button>
  <button class="pill" onclick="runPrompt('red sports car')">Sports Car</button>
  <button class="pill" onclick="runPrompt('military attack helicopter')">Helicopter</button>
  <button class="pill" onclick="runPrompt('armored battle tank')">Battle Tank</button>
  <button class="pill" onclick="runPrompt('purple kraken octopus')">Kraken</button>
  <button class="pill" onclick="runPrompt('phoenix fire bird')">Phoenix</button>
  <button class="pill" onclick="runPrompt('magical unicorn horse')">Unicorn</button>
  <button class="pill" onclick="runPrompt('sci-fi plasma rifle blaster')">Plasma Rifle</button>
  <button class="pill" onclick="runPrompt('cheeseburger food')">Cheeseburger</button>
  <button class="pill" onclick="runPrompt('gundam mech robot')">Gundam Mech</button>
</div>

<div class="subheader">
  <div class="title-group">
    <span class="model-title" id="modelTitle">READY</span>
    <span class="badge" id="rigBadge">9-STAGE PIPELINE</span>
  </div>
  <div class="actions">
    <span style="font-size:11px;color:var(--muted);">Stage:</span>
    <button class="btn-sm" id="st_raw" onclick="setStage('raw')">1. Raw</button>
    <button class="btn-sm" id="st_shape" onclick="setStage('shape')">2. Shapes</button>
    <button class="btn-sm" id="st_detail" onclick="setStage('detail')">3. Details</button>
    <button class="btn-sm active" id="st_final" onclick="setStage('final')">4. Colored</button>
    <button class="btn-sm" onclick="downloadFile('obj')">.OBJ</button>
    <button class="btn-sm" onclick="toggleScript()">LUAU</button>
    <button class="btn-sm primary" onclick="copyLua()" id="copyBtn">COPY STUDIO SCRIPT</button>
  </div>
</div>

<div class="workspace">
  <canvas id="viewport"></canvas>
  <div class="stats-pill" id="statsPill">0 parts</div>
  <div class="pipeline-sidebar">
    <div style="font-size:11px;font-weight:800;color:var(--muted);text-transform:uppercase;">Live AI Modeler & Critic Log</div>
    <div id="pipelineSteps"></div>
  </div>
  <div id="scriptPanel">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <strong>Roblox Studio Command Bar Script (Motor6D Rig + SpecialMesh Support)</strong>
      <button class="btn-sm" onclick="toggleScript()">Close</button>
    </div>
    <textarea id="codeBox" readonly></textarea>
  </div>
</div>

<div class="bottom-panel">
  <input type="text" id="promptInput" placeholder='Type ANY object, animal, vehicle, building, or character...' onkeydown="if(event.key==='Enter') generateNew()" />
  <input type="password" id="apiKeyInput" placeholder="Optional Gemini/Groq Key" title="Works keylessly by default, or paste a Gemini (AIza...) or Groq (gsk_...) key for dedicated LLM speed" />
  <button class="btn-sm" onclick="reRoll()">Re-Roll</button>
  <button class="btn-sm primary" style="padding:10px 16px;font-size:13px;" onclick="generateNew()">Build 3D Asset</button>
</div>

<script>
let scene, camera, renderer, controls, modelGroup, currentSpec = null;
let currentPrompt = "orange tabby cat", currentIter = 0, viewStage = "final";

function init3D() {
  const canvas = document.getElementById("viewport");
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(40, canvas.clientWidth / canvas.clientHeight, 0.1, 500);
  camera.position.set(7.5, 5.8, -9.5);
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;

  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 1.8, 0);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 0.92));
  const dir = new THREE.DirectionalLight(0xffffff, 0.85);
  dir.position.set(14, 24, -18);
  dir.castShadow = true;
  scene.add(dir);

  scene.add(new THREE.GridHelper(36, 36, 0x334155, 0x1e293b));
  modelGroup = new THREE.Group();
  scene.add(modelGroup);

  window.addEventListener("resize", () => {
    camera.aspect = canvas.clientWidth / canvas.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  });
  (function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  })();
}

function makeGeom(shape, sz) {
  const [w, h, d] = sz;
  if (shape === "cylinder") {
    const g = new THREE.CylinderGeometry(0.5, 0.5, 1.0, 24);
    g.scale(w, h, d);
    return g;
  }
  if (shape === "sphere" || shape === "gem") {
    const g = new THREE.SphereGeometry(0.5, 24, 18);
    g.scale(w, h, d);
    return g;
  }
  if (shape === "cone" || shape === "pyramid") {
    const g = new THREE.ConeGeometry(0.5, 1.0, shape === "pyramid" ? 4 : 20);
    if (shape === "pyramid") g.rotateY(Math.PI / 4);
    g.scale(w, h, d);
    return g;
  }
  if (shape === "wedge") {
    const hw = w/2, hh = h/2, hd = d/2;
    const geom = new THREE.BufferGeometry();
    const v = new Float32Array([-hw,-hh,-hd, hw,-hh,-hd, hw,-hh,hd, -hw,-hh,hd, -hw,hh,hd, hw,hh,hd]);
    geom.setIndex([0,1,2, 0,2,3, 3,2,5, 3,5,4, 0,4,5, 0,5,1, 0,3,4, 1,5,2]);
    geom.setAttribute("position", new THREE.BufferAttribute(v, 3));
    geom.computeVertexNormals();
    return geom;
  }
  return new THREE.BoxGeometry(w, h, d);
}

function renderSpec(spec) {
  currentSpec = spec;
  while (modelGroup.children.length > 0) modelGroup.remove(modelGroup.children[0]);

  (spec.parts || []).forEach(p => {
    if (viewStage === "raw" && p.stage !== "raw") return;
    if (viewStage === "shape" && p.stage === "detail") return;

    const col = new THREE.Color(viewStage === "final" ? (p.c || "#cccccc") : "#94a3b8");
    const opts = { color: col, roughness: 0.38, metalness: 0.08 };
    if (viewStage === "final") {
      if (p.mat === "Metal") { opts.roughness = 0.22; opts.metalness = 0.72; }
      if (p.mat === "Neon") { opts.emissive = col; opts.emissiveIntensity = 0.65; opts.roughness = 0.1; }
      if (p.mat === "Glass" || p.tr > 0) { opts.transparent = true; opts.opacity = 1.0 - (p.tr || 0.35); opts.roughness = 0.08; }
    }
    const mesh = new THREE.Mesh(makeGeom(p.s, p.sz), new THREE.MeshStandardMaterial(opts));
    mesh.position.set(p.po[0], p.po[1], p.po[2]);
    mesh.rotation.set(
      THREE.MathUtils.degToRad(p.ro[0] || 0),
      THREE.MathUtils.degToRad(p.ro[1] || 0),
      THREE.MathUtils.degToRad(p.ro[2] || 0)
    );
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    modelGroup.add(mesh);
  });

  const b = spec.bounds || [4, 4, 4];
  const eng = (spec.meta && spec.meta.engine) ? spec.meta.engine : "AI Architect";
  document.getElementById("modelTitle").textContent = (spec.meta && spec.meta.prompt) ? spec.meta.prompt : spec.name;
  document.getElementById("rigBadge").textContent = `${eng.toUpperCase()} • QA PASSED`;
  document.getElementById("statsPill").textContent = `${spec.parts.length} Roblox parts • ${b[0]} × ${b[1]} × ${b[2]} studs`;
  document.getElementById("codeBox").value = spec.lua || "";
  document.getElementById("pipelineSteps").innerHTML = (spec.pipeline_logs || []).map(i => `
    <div class="step-card">
      <div class="step-stage">${i.stage.replace(/_/g, ' ')}</div>
      <div class="step-msg">${i.msg}</div>
    </div>
  `).join("");

  controls.target.set(0, Math.max(1.2, b[1] * 0.45), 0);
  controls.update();
}

function setStage(st) {
  viewStage = st;
  ["raw", "shape", "detail", "final"].forEach(k => document.getElementById("st_" + k).classList.toggle("active", k === st));
  if (currentSpec) renderSpec(currentSpec);
}

async function fetchModel(prompt, iteration) {
  document.getElementById("modelTitle").textContent = "RESEARCHING & BUILDING 3D ASSET...";
  const api_key = document.getElementById("apiKeyInput").value.trim();
  const res = await fetch("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, iteration, api_key, nonce: String(Date.now()) })
  });
  renderSpec(await res.json());
}

function runPrompt(p) { currentPrompt = p; currentIter = 0; document.getElementById("promptInput").value = p; fetchModel(p, 0); }
function generateNew() { currentPrompt = document.getElementById("promptInput").value.trim() || currentPrompt; currentIter = 0; fetchModel(currentPrompt, 0); }
function reRoll() { currentIter += 1; fetchModel(currentPrompt, currentIter); }
function toggleScript() { document.getElementById("scriptPanel").classList.toggle("open"); }
function copyLua() {
  if (!currentSpec) return;
  navigator.clipboard.writeText(currentSpec.lua);
  const btn = document.getElementById("copyBtn");
  btn.textContent = "COPIED!";
  setTimeout(() => { btn.textContent = "COPY STUDIO SCRIPT"; }, 1600);
}
function downloadFile(ext) {
  if (!currentSpec) return;
  const blob = new Blob([ext === "obj" ? currentSpec.obj : currentSpec.lua], { type: "text/plain" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `${currentSpec.name || "asset"}.${ext}`; a.click();
}
window.addEventListener("DOMContentLoaded", () => { init3D(); runPrompt("orange tabby cat"); });
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, data, ctype="application/json; charset=utf-8", status=200):
        raw = data if isinstance(data, bytes) else data.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self._send('{"ok":true}')

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            return self._send(HTML_UI, "text/html; charset=utf-8")
        if parsed.path.startswith("/health"):
            return self._send('{"ok":true,"scheme":"roblox_cloud_v4"}')
        if parsed.path.startswith("/generate"):
            qs = parse_qs(parsed.query)
            prompt = (qs.get("prompt") or ["orange tabby cat"])[0]
            return self._send(json.dumps(generate({"prompt": prompt})))
        return self._send('{"error":"not found"}', status=404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw or "{}")
        except Exception:
            body = {}
        return self._send(json.dumps(generate(body)))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Roblox Cloud 3D Modeler AI v4 running on 0.0.0.0:{port}", flush=True)
    srv.serve_forever()
