"""BrickForge AI v2 — cognitive core. Bugfixed + expanded.
New: connector-joint rotation splitting (no crashes), time-budgeted beam search,
hill-climb refinement, pattern painter, pose system, evolution from memory,
detail LOD, richer critique, hardened generate()."""
import math, random, re, colorsys, zlib, time
from collections import Counter
BUDGET = 7.0  # seconds max per generate call (Render-safe)

# ============================ 1. LEXICON / ONTOLOGY ============================
ARCH_SYN = {
 "octopus": ["octopus","squid","kraken","cephalopod","ink"],
 "serpent": ["snake","serpent","dragon","wyrm","eel","viper","wyvern"],
 "fish":    ["fish","shark","koi","bass","piranha","manta","goldfish"],
 "bird":    ["bird","eagle","phoenix","falcon","owl","raven","parrot","hawk"],
 "crab":    ["crab","lobster","scorpion","shrimp","prawn"],
 "spider":  ["spider","arachnid","tarantula","weaver"],
 "golem":   ["golem","titan","colossus","elemental"],
 "humanoid":["robot","humanoid","knight","warrior","mech","android","samurai","guard"],
 "turtle":  ["turtle","tortoise","snail"],
 "jelly":   ["jelly","jellyfish","medusa","blob"]}
ARCHES = list(ARCH_SYN)
INHERENT = {"octopus":{"tentacles"},"serpent":{"tail"},"fish":{"fins","tail"},"bird":{"wings"},
 "crab":{"claws"},"spider":set(),"golem":{"armor"},"humanoid":{"armor"},"turtle":{"shell","tail"},
 "jelly":{"tentacles","frill"}}
TRAIT_SYN = {
 "wings":["wing","wings","winged","flying"],"horns":["horn","horns","horned","antler"],
 "crest":["crest","mohawk","crown","crested"],"spikes":["spike","spikes","spiky","sharp","edgy","thorn"],
 "tail":["tail","tailed"],"claws":["claw","claws","pincer"],"armor":["armor","armored","plate","plated","shield"],
 "glow":["glow","glowing","crystal","gem","shine"],"antennae":["antenna","antennae","feelers","sensor"],
 "teeth":["teeth","tooth","fang","fanged"],"beak":["beak","bill"],
 "mane":["mane","frill","ruff","collar"],"shell":["shell","carapace","spiral"],
 "blades":["blade","scythe","saber"],"fins":["fin","fins","finned"],
 "frill":["frill","frilled","skirt","lace"],"tentacles":["tentacle","tentacles"]}
MATERIAL = {"metal":{"s":0.25,"v":1.15},"metallic":{"s":0.25,"v":1.15},"steel":{"s":0.2,"v":1.1},
 "ice":{"h":195,"s":0.35,"v":0.95},"frozen":{"h":195,"s":0.35,"v":0.95},"lava":{"h":15,"s":0.95,"v":0.9},
 "magma":{"h":15,"s":0.95,"v":0.9},"gold":{"h":45,"s":0.85,"v":0.95},"golden":{"h":45,"s":0.85,"v":0.95},
 "obsidian":{"h":270,"s":0.25,"v":0.18},"crystal":{"s":0.5,"v":1.1},"bone":{"h":40,"s":0.15,"v":0.92},
 "wood":{"h":28,"s":0.5,"v":0.5},"neon":{"s":1.0,"v":1.0}}
MOOD = {"cute":{"spike":-0.6,"scale":0.85,"sat":0.8},"chibi":{"spike":-0.6,"scale":0.8,"sat":0.85},
 "fierce":{"spike":0.7,"sat":1.1,"pose":-8},"majestic":{"spike":0.3,"scale":1.15,"sat":0.9,"pose":6},
 "royal":{"spike":0.2,"sat":0.9,"pose":4},"creepy":{"spike":0.5,"sat":0.7,"val":0.8,"pose":-5},
 "evil":{"spike":0.6,"sat":0.9,"val":0.85,"pose":-6},"gentle":{"spike":-0.4,"sat":0.85,"pose":2}}
INTEN = {"slight":0.5,"small":0.7,"tiny":0.55,"little":0.7,"some":0.8,"few":0.7,"very":1.4,"extra":1.5,
 "super":1.6,"mega":1.8,"huge":1.7,"massive":1.8,"giant":1.8,"big":1.35,"large":1.3,"long":1.4,
 "tall":1.3,"heavy":1.4,"light":0.8,"subtle":0.7,"extreme":1.9,"ultra":1.8}
COUNTS = {"one":1,"two":2,"twin":2,"double":2,"pair":2,"three":3,"triple":3,"four":4,"quad":4,
 "five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,"many":8,"multi":6,"multiple":6}
SIZEW = {"tiny":0.7,"small":0.85,"big":1.3,"huge":1.55,"giant":1.6,"massive":1.65,"colossal":1.7,"mini":0.75,"large":1.3}
STYLE = {"blocky":1.0,"chunky":1.15,"sleek":0.9,"slim":0.85,"ornate":1.25,"detailed":1.25,
 "minimal":0.7,"simple":0.8}
PATTERN = {"striped":"stripes","stripe":"stripes","spots":"spots","spotted":"spots",
 "speckled":"spots","gradient":"gradient","fade":"gradient","faded":"gradient","counter":"counter"}
NEG = {"no","without","lack","lacks","not","never","minus"}
COLOR_WORDS = {"red":(0,0.85,0.62),"crimson":(348,0.9,0.55),"scarlet":(8,0.9,0.6),"orange":(24,0.9,0.62),
 "amber":(38,0.95,0.7),"yellow":(52,0.9,0.65),"gold":(45,0.85,0.72),"lime":(80,0.8,0.6),
 "green":(140,0.7,0.5),"emerald":(152,0.8,0.45),"teal":(172,0.75,0.5),"cyan":(185,0.85,0.65),
 "azure":(205,0.85,0.62),"blue":(215,0.8,0.55),"navy":(225,0.8,0.3),"indigo":(250,0.7,0.5),
 "purple":(275,0.7,0.55),"violet":(285,0.75,0.6),"magenta":(310,0.8,0.6),"pink":(330,0.7,0.75),
 "rose":(340,0.7,0.65),"white":(0,0.0,0.96),"snow":(210,0.05,0.96),"black":(260,0.2,0.14),
 "dark":(260,0.2,0.2),"grey":(220,0.05,0.55),"gray":(220,0.05,0.55),"brown":(25,0.6,0.42),
 "tan":(35,0.45,0.72),"beige":(40,0.3,0.85),"maroon":(355,0.8,0.35),"olive":(70,0.6,0.4),
 "mint":(160,0.45,0.8),"coral":(12,0.8,0.72),"lavender":(265,0.45,0.8),"turquoise":(175,0.7,0.6),
 "silver":(210,0.08,0.82),"bronze":(22,0.65,0.5)}

# ============================ 2. INTENT PARSER ============================
def tokenize(t): return re.findall(r"[a-z]+", t.lower())
def parse_intent(prompt):
    toks = tokenize(prompt); raw = prompt.lower()
    I = {"arch": Counter(), "traits": {}, "neg": set(), "colors": [], "size": 1.0, "sharp": 1.0,
         "sat": 1.0, "val": 1.0, "style": 1.0, "mood": None, "material": None, "pattern": None,
         "pose": 0, "tokens": set(toks)}
    for a, syn in ARCH_SYN.items():
        for s in syn:
            if s in raw: I["arch"][a] += 2 if s == a else 1
    for tr, syn in TRAIT_SYN.items():
        for s in syn:
            m = re.search(r"\b%s" % re.escape(s), raw)
            if not m: continue
            pre = toks[:len(tokenize(raw[:m.start()]))][-2:]
            inten, cnt, neg = 1.0, None, False
            for w in pre:
                if w in INTEN: inten = max(inten, INTEN[w])
                if w in COUNTS: cnt = COUNTS[w]
                if w in NEG: neg = True
            if neg: I["neg"].add(tr); continue
            old = I["traits"].get(tr)
            I["traits"][tr] = {"inten": max(inten, old["inten"] if old else 0),
                               "count": cnt or (old or {}).get("count")}
    for w, hsv in COLOR_WORDS.items():
        if re.search(r"\b%s" % w, raw): I["colors"].append(hsv)
    for w, v in SIZEW.items():
        if re.search(r"\b%s" % w, raw): I["size"] = v; break
    for w, v in STYLE.items():
        if re.search(r"\b%s" % w, raw): I["style"] = v; break
    for w, v in PATTERN.items():
        if re.search(r"\b%s" % w, raw): I["pattern"] = v; break
    for w, m in MOOD.items():
        if re.search(r"\b%s" % w, raw):
            I["mood"] = w; I["sharp"] += m.get("spike", 0); I["size"] *= m.get("scale", 1.0)
            I["sat"] *= m.get("sat", 1.0); I["val"] *= m.get("val", 1.0); I["pose"] = m.get("pose", 0); break
    for w, m in MATERIAL.items():
        if re.search(r"\b%s" % w, raw): I["material"] = m; break
    if any(re.search(r"\b%s" % w, raw) for w in ("spiky","sharp","spined","thorny")): I["sharp"] += 0.8
    if any(re.search(r"\b%s" % w, raw) for w in ("smooth","round","soft")): I["sharp"] -= 0.6
    I["sharp"] = clamp(I["sharp"], 0.2, 2.6)
    return I

# ============================ 3. COLOR INTELLIGENCE ============================
def clamp(x, a, b): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def hsv_hex(h, s, v):
    h %= 360; r, g, b = colorsys.hsv_to_rgb(h/360.0, clamp(s,0,1), clamp(v,0,1))
    return "#%02x%02x%02x" % (int(r*255), int(g*255), int(b*255))
def hex_hsv(hx):
    hx = hx.lstrip("#"); r, g, b = (int(hx[i:i+2],16)/255.0 for i in (0,2,4))
    h, s, v = colorsys.rgb_to_hsv(r, g, b); return h*360, s, v
def hue_dist(a, b): d = abs(a-b) % 360; return min(d, 360-d)
def lerp_hsv(c1, c2, t):
    h1,s1,v1 = c1; h2,s2,v2 = c2; d = ((h2-h1+540) % 360) - 180
    return (h1+d*t, s1+(s2-s1)*t, v1+(v2-v1)*t)
def synthesize_palette(I, rng, base_override):
    if I["colors"]: base = I["colors"][0]
    elif base_override: base = base_override
    else: base = (rng.choice([0,25,45,140,175,205,250,285,320]), 0.65, 0.6)
    h, s, v = base
    s = clamp(s*I["sat"], 0.08, 1); v = clamp(v*I["val"], 0.12, 1)
    if I["material"]:
        m = I["material"]
        if "h" in m: h = m["h"]
        s = clamp(s*m.get("s",1), 0.05, 1); v = clamp(v*m.get("v",1), 0.1, 1)
    off = rng.choice([180, 28, 120, 150])
    pal = {"A": hsv_hex(h, s*0.85, v),
           "B": hsv_hex(h+rng.choice([-25,25]), s*0.7, min(1, v*1.2)),
           "C": hsv_hex(h+off, max(0.5, s), min(1, v*1.35)),
           "S": hsv_hex(h+off+rng.choice([-30,30]), max(0.45, s*0.9), min(1, v*1.1)),
           "D": hsv_hex(h, min(1, s*1.05), max(0.1, v*0.42)),
           "L": hsv_hex(h+15, max(0.06, s*0.35), min(1, v*1.55))}
    for g in range(8):  # gradient slots for pattern painter
        t = g/7.0
        pal["G%d"%g] = hsv_hex(*lerp_hsv(hex_hsv(pal["A"]), hex_hsv(pal["S"]), t))
    return pal

# ============================ 4. ANATOMY MATH ============================
def catmull(pts, t):
    n = len(pts)-1; i = min(int(t*n), n-1); f = t*n-i
    p0,p1,p2,p3 = pts[max(i-1,0)], pts[i], pts[i+1], pts[min(i+2,n)]
    return [0.5*((2*p1[k]) + (-p0[k]+p2[k])*f + (2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*f*f +
            (-p0[k]+3*p1[k]-3*p2[k]+p3[k])*f*f*f) for k in range(3)]
def log_spiral(a, b, th): r = a*math.exp(b*th); return r*math.sin(th), r*math.cos(th)
GOLD = 137.5077640500378
def phyllotaxis(i, n, spread):
    r = spread*math.sqrt((i+0.5)/n); th = math.radians(i*GOLD)
    return r*math.sin(th), r*math.cos(th)
def taper(t, p): return (1-t)**p

# ============================ 5. PART DSL (crash-proof, connector joints) ============================
class Builder:
    def __init__(self, seed, palette, rng, sharp, scale, style):
        self.parts = []; self.names = set(); self.pal = palette; self.rng = rng
        self.sharp = sharp; self.scale = scale; self.detail = style
        self.mirrored = []; self.present = set(); self.counts = Counter(); self.root = None
    def _uniq(self, n):
        base = n; i = 2
        while n in self.names: n = "%s%d" % (base, i); i += 1
        self.names.add(n); return n
    def _emit(self, name, parent, shape, size, pos, rot, color):
        """Single-axis-safe emission: multi-axis rotations are split into connector joints."""
        axes = [i for i, v in enumerate(rot) if v]
        size = [round(v*self.scale,2) for v in size]; pos = [round(v*self.scale,2) for v in pos]
        if len(axes) <= 1:
            self.parts.append({"n":name,"p":parent,"s":shape,"sz":size,"po":pos,"ro":list(rot),"c":color})
            return name
        par = parent; p0 = pos
        for k, ax in enumerate(axes[:-1]):
            cn = self._uniq(name+"_j%d"%k)
            r = [0,0,0]; r[ax] = rot[ax]
            self.parts.append({"n":cn,"p":par,"s":"box","sz":[round(0.3*self.scale,2)]*3,
                               "po":p0,"ro":r,"c":"D"})
            par = cn; p0 = [0,0,0]
        r = [0,0,0]; r[axes[-1]] = rot[axes[-1]]
        self.parts.append({"n":name,"p":par,"s":shape,"sz":size,"po":p0,"ro":r,"c":color})
        return name
    def add(self, name, parent, shape, size, pos, rot=(0,0,0), color="A", mirror=False):
        name = self._uniq(name)
        self._emit(name, parent, shape, size, pos, rot, color)
        if mirror:
            mn = self._uniq(name+"L")
            self._emit(mn, parent, shape, size, [-pos[0],pos[1],pos[2]],
                       [rot[0],-rot[1],-rot[2]], color)
            self.mirrored.append((name, mn))
        if self.root is None and parent is None: self.root = name
        return name
    def tag(self, *t):
        for x in t: self.present.add(x)
    def count(self, k, n): self.counts[k] += n
    def yaw_chain(self, prefix, parent, deltas, sizes, colors, pos0=(0,0,0)):
        names = []; par = parent
        for i,(d,sz,c) in enumerate(zip(deltas,sizes,colors)):
            n = self.add("%s%d"%(prefix,i), par, "box", sz, pos0 if i==0 else [0,0,-sz[2]*0.9], (0,d,0), c)
            names.append(n); par = n; pos0 = (0,0,0)
        return names
    def pitch_chain(self, prefix, parent, deltas, sizes, colors, pos0=(0,0,0)):
        names = []; par = parent
        for i,(d,sz,c) in enumerate(zip(deltas,sizes,colors)):
            n = self.add("%s%d"%(prefix,i), par, "box", sz, pos0 if i==0 else [0,-sz[1]*0.85,0], (d,0,0), c)
            names.append(n); par = n; pos0 = (0,0,0)
        return names
    def ring(self, prefix, parent, n, radius, y, size, color, child=None):
        outs = []
        for i in range(n):
            az = i*360.0/n; a = math.radians(az)
            b = self.add("%s%d"%(prefix,i), parent, "box",
                         [size[0]*0.9, size[1]*0.6, size[0]*0.9],
                         [radius*math.sin(a), y, radius*math.cos(a)], (0,az,0), color)
            outs.append(b)
            if child: child(self, b, i, n)
        return outs
    def spikes_top(self, parent, n, spread, h, color="S", y=0.6):
        n = max(1, int(n*self.detail))
        for i in range(n):
            x, z = phyllotaxis(i, n, spread)
            axis = 2 if abs(x) > abs(z) else 0
            rot = [0,0,0]; rot[axis] = clamp((-x if axis==2 else z)*22, -28, 28)
            self.add("Spike%d"%i, parent, "pyramid",
                     [0.42, h*self.rng.uniform(0.7,1.3), 0.42], [x,y,z], rot, color)
    def eyes(self, parent, y, z, s, bx=0.75):
        for sx, suf in ((1,"R"),(-1,"L")):
            e = self.add("Eye"+suf, parent, "box", [s, s*1.15, s*0.4], [sx*bx, y, z], (0,0,0), "C")
            self.add("Pupil"+suf, e, "gem", [s*0.45, s*0.55, s*0.3], [0,0,-0.25], (0,0,0), "D")
        self.mirrored.append(("EyeR","EyeL"))

# ============================ 6. PATTERN PAINTER + POSE ============================
def _depths(parts):
    idx = {p["n"]: p for p in parts}; dep = {}
    def d(n):
        if n in dep: return dep[n]
        p = idx[n]["p"]; dep[n] = 0 if not p else d(p)+1; return dep[n]
    for p in parts: d(p["n"])
    return dep
def paint(B, kind, rng):
    if not kind: return 0
    touched = 0
    if kind == "stripes":
        for i,p in enumerate(B.parts):
            if p["c"] in ("A","B") and i % 5 in (0,1): p["c"] = "D"; touched += 1
    elif kind == "spots":
        for p in B.parts:
            if p["c"] == "A" and rng.random() < 0.14: p["c"] = "C"; touched += 1
    elif kind == "gradient":
        dep = _depths(B.parts); mx = max(dep.values()) or 1
        for p in B.parts:
            if p["c"] in ("A","B"):
                p["c"] = "G%d" % int(7*dep[p["n"]]/mx); touched += 1
    elif kind == "counter":
        for p in B.parts:
            if p["c"] == "A" and p["po"][1] < 0: p["c"] = "L"; touched += 1
    return touched
def apply_pose(B, deg):
    if not deg or not B.root: return
    old = B.root
    pr = B._uniq("PoseRoot")
    B.parts.append({"n":pr,"p":None,"s":"box","sz":[round(0.3*B.scale,2)]*3,
                    "po":[0,0,0],"ro":[0,0,0],"c":"D"})
    for p in B.parts:
        if p["n"] == old: p["p"] = pr; p["ro"] = [deg,0,0]; p["po"] = [0, 0.3*B.scale, 0]
    B.root = pr

# ============================ 7. CHIMERA TRAIT MODULES ============================
def feat_wings(B,I,rng,c,inten):
    kind = rng.choice(["feather","membrane"])
    for sx,suf in ((1,"R"),(-1,"L")):
        sh = B.add("Wing"+suf, B.root, "box", [1.6*inten,0.35,0.9], [sx*1.1,0.9,0.3], (0,0,sx*22), "B")
        if kind == "feather":
            par = sh
            for i in range(4):
                par = B.add("Wing%sC%d"%(suf,i), par, "box", [1.5-i*0.25,0.28,0.8-i*0.08],
                            [sx*1.0,0.05,0], (0,0,sx*12), "B" if i%2 else "A")
            for i in range(5):
                B.add("Wing%sP%d"%(suf,i), par, "wedge", [0.5,1.6-i*0.18,0.22],
                      [sx*(0.4+i*0.35),-0.5,0.2], (0,0,sx*(30+i*8)), "S")
        else:
            arm = B.add("Wing%sArm"%suf, sh, "box", [2.2*inten,0.3,0.3], [sx*1.4,0.2,0], (0,0,sx*18), "D")
            for i in range(3):
                B.add("Wing%sF%d"%(suf,i), arm, "box", [0.22,1.8-i*0.4,0.22],
                      [sx*(0.3+i*0.5),-0.8,0], (0,0,sx*(10+i*14)), "D")
            B.add("Wing%sM"%suf, arm, "wedge", [2.4*inten,1.6,0.12], [sx*0.8,-0.7,0.1], (0,0,sx*90), "L")
    B.mirrored.append(("WingR","WingL")); B.tag("wings"); B.count("wings", c or 2)
def feat_horns(B,I,rng,c,inten):
    for sx,suf in ((1,"R"),(-1,"L")):
        par = B.add("Horn"+suf, B.root, "box", [0.4,0.7,0.4], [sx*0.6,1.5,-0.4], (sx*-18,0,0), "S")
        for i in range(3):
            par = B.add("Horn%s%d"%(suf,i), par, "pyramid" if i==2 else "box",
                        [0.34-i*0.07,(0.8-i*0.15)*inten,0.34-i*0.07], [0,0.6,-0.12], (-22,0,0), "S")
    B.mirrored.append(("HornR","HornL")); B.tag("horns"); B.count("horns", c or 2)
def feat_crest(B,I,rng,c,inten):
    n = c or 5
    for i in range(n):
        B.add("Crest%d"%i, B.root, "pyramid", [0.3,(1.1-abs(i-n/2)*0.18)*inten,0.3],
              [0,1.5,-0.9+i*0.42], (-12+i*4,0,0), "S")
    B.tag("crest"); B.count("crest", n)
def feat_spikes(B,I,rng,c,inten): B.spikes_top(B.root, int((c or 6)*inten), 1.5, 1.3*inten); B.tag("spikes")
def feat_tail(B,I,rng,c,inten):
    ns = B.yaw_chain("TailX", B.root, [rng.choice([-14,14]) for _ in range(5)],
        [[1.1-i*0.14,0.9-i*0.1,1.2] for i in range(5)], ["A","B","A","B","A"], (0,0.2,1.4))
    B.add("TailFin", ns[-1], "wedge", [1.4*inten,1.6*inten,0.3], [0,0.3,-0.8], (90,0,0), "C")
    B.tag("tail"); B.count("tail",1)
def feat_claws(B,I,rng,c,inten):
    for sx,suf in ((1,"R"),(-1,"L")):
        a = B.add("ClawArm"+suf, B.root, "box", [0.6,1.4,0.6], [sx*1.5,-0.2,-0.6], (sx*16,0,0), "B")
        b = B.add("ClawArm%s2"%suf, a, "box", [0.5,1.2,0.5], [0,-1.1,-0.2], (-38,0,0), "A")
        B.add("Claw%sA"%suf, b, "wedge", [0.45,1.3*inten,0.4], [0,-1.0,-0.1], (-28,0,0), "S")
        B.add("Claw%sB"%suf, b, "wedge", [0.45,1.1*inten,0.4], [0,-0.9,0.25], (24,0,0), "S")
    B.mirrored.append(("ClawArmR","ClawArmL")); B.tag("claws"); B.count("claws", c or 2)
def feat_armor(B,I,rng,c,inten):
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Pauldron"+suf, B.root, "box", [1.1,0.5,1.1], [sx*1.3,1.2,0], (0,0,sx*10), "B")
        B.add("Pauldron%s2"%suf, B.root, "wedge", [1.2,0.6,1.2], [sx*1.35,1.55,0], (0,0,sx*10), "D")
    B.add("ChestPlate", B.root, "box", [2.2,1.4,0.4], [0,0.4,-0.9], (0,0,0), "B")
    B.add("BackPlate", B.root, "box", [2.0,1.6,0.35], [0,0.4,0.9], (0,0,0), "D")
    B.mirrored.append(("PauldronR","PauldronL")); B.tag("armor")
def feat_glow(B,I,rng,c,inten):
    n = c or 7
    for i in range(n):
        x,z = phyllotaxis(i,n,1.3)
        B.add("GlowGem%d"%i, B.root, "gem", [0.4*inten,0.6*inten,0.4*inten], [x,0.9,z], (0,0,0), "C")
    B.tag("glow")
def feat_antennae(B,I,rng,c,inten):
    for sx,suf in ((1,"R"),(-1,"L")):
        a = B.add("Antenna"+suf, B.root, "box", [0.18,1.2*inten,0.18], [sx*0.4,1.6,-0.5], (sx*-14,0,0), "D")
        B.add("Antenna%sTip"%suf, a, "gem", [0.35,0.35,0.35], [0,0.7,0], (0,0,0), "C")
    B.mirrored.append(("AntennaR","AntennaL")); B.tag("antennae")
def feat_teeth(B,I,rng,c,inten):
    n = c or 6
    for i in range(n):
        B.add("Tooth%d"%i, B.root, "pyramid", [0.18,0.5*inten,0.18],
              [-0.7+i*(1.4/max(1,n-1)),-0.55,-1.05], (180,0,0), "L")
    B.tag("teeth")
def feat_beak(B,I,rng,c,inten):
    b = B.add("Beak", B.root, "wedge", [0.8*inten,0.7,1.1*inten], [0,0.1,-1.2], (-90,0,0), "C")
    B.add("BeakHook", b, "wedge", [0.5,0.5,0.5], [0,-0.35,-0.35], (20,0,0), "D"); B.tag("beak")
def feat_mane(B,I,rng,c,inten):
    n = c or 10
    for i in range(n):
        az = i*360.0/n; a = math.radians(az)
        B.add("Frill%d"%i, B.root, "wedge", [0.5,1.2*inten,0.2],
              [1.1*math.sin(a),1.0,1.1*math.cos(a)], (0,az,0), "S")
    B.tag("mane")
def feat_shell(B,I,rng,c,inten):
    par = B.root; th = 0.0
    for i in range(7):
        x,z = log_spiral(0.25,0.22,th); s = (1.5-i*0.16)*inten
        par = B.add("Shell%d"%i, par, "box", [s,s*0.7,s], [x,0.9+i*0.22,z], (0,i*24,0), "B" if i%2 else "A")
        th += 0.9
    B.tag("shell")
def feat_blades(B,I,rng,c,inten):
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Blade"+suf, B.root, "wedge", [0.3,2.4*inten,0.7], [sx*1.5,0.2,-0.8], (0,0,sx*30), "S")
    B.mirrored.append(("BladeR","BladeL")); B.tag("blades")
def feat_fins(B,I,rng,c,inten):
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Fin"+suf, B.root, "wedge", [1.4*inten,1.1,0.25], [sx*1.3,-0.2,0.3], (0,0,sx*65), "C")
    B.add("DorsalFin", B.root, "wedge", [0.3,1.3*inten,1.4], [0,1.3,0.2], (0,0,0), "C")
    B.mirrored.append(("FinR","FinL")); B.tag("fins")
def feat_frill(B,I,rng,c,inten):
    n = c or 8
    for i in range(n):
        az = i*360.0/n; a = math.radians(az)
        B.add("Skirt%d"%i, B.root, "wedge", [0.6,1.0*inten,0.18],
              [1.2*math.sin(a),-0.8,1.2*math.cos(a)], (180,az,0), "L")
    B.tag("frill")
def feat_tentacles(B,I,rng,c,inten):
    n = c or 4
    for i in range(n):
        az = i*360.0/n+45; a = math.radians(az)
        b = B.add("ExtraTent%d"%i, B.root, "box", [0.5,1.0,0.5],
                  [1.2*math.sin(a),-1.0,1.2*math.cos(a)], (0,az,0), "A")
        B.pitch_chain("ExtraTent%d_"%i, b, [18,26,34,40],
            [[0.45,1.0,0.45],[0.38,0.9,0.38],[0.3,0.8,0.3],[0.22,0.7,0.22]], ["A","B","A","C"])
    B.tag("tentacles"); B.count("tentacles", n)
FEATS = {"wings":feat_wings,"horns":feat_horns,"crest":feat_crest,"spikes":feat_spikes,"tail":feat_tail,
 "claws":feat_claws,"armor":feat_armor,"glow":feat_glow,"antennae":feat_antennae,"teeth":feat_teeth,
 "beak":feat_beak,"mane":feat_mane,"shell":feat_shell,"blades":feat_blades,"fins":feat_fins,
 "frill":feat_frill,"tentacles":feat_tentacles}

# ============================ 8. ARCHETYPE BUILDERS (10) ============================
def b_octopus(B,I,rng):
    B.add("CoreRoot",None,"box",[2.8,2.2,2.8],[0,2.4,0],(0,0,0),"A")
    B.add("Mantle","CoreRoot","box",[2.2,1.4,2.2],[0,1.5,0.1],(0,0,0),"B")
    B.add("Mantle2","Mantle","box",[1.5,1.0,1.5],[0,1.0,0.15],(0,0,0),"A")
    B.add("Mantle3","Mantle2","box",[0.9,0.7,0.9],[0,0.7,0.1],(0,0,0),"B")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("MantleFin"+suf,"Mantle","wedge",[1.2,0.8,1.4],[sx*1.2,0.4,0],(0,0,sx*55),"C")
    B.mirrored.append(("MantleFinR","MantleFinL"))
    B.add("Head","CoreRoot","box",[2.5,1.7,2.2],[0,-0.5,0.5],(0,0,0),"A")
    B.eyes("Head",0.1,1.15,0.62,0.85)
    B.add("BeakM","Head","wedge",[0.6,0.6,0.5],[0,-0.75,1.05],(-90,0,0),"D")
    n = I["traits"].get("tentacles",{}).get("count") or int(8*B.detail)
    def suckers(b,base,i,nn):
        par = base
        for s in range(4):
            t = s/4.0
            par = b.add("Tent%d_s%d"%(i,s), par, "box",
                [0.62*taper(t,0.7)+0.12,1.15-t*0.35,0.62*taper(t,0.7)+0.12],[0,-0.95,0],(16+s*9,0,0),
                "A" if s%2 else "B")
            if s%2==0:
                b.add("Tent%d_suck%d"%(i,s), par, "gem", [0.3*(1-t)+0.12]*3, [0,-0.2,-0.42], (0,0,0), "L")
        b.add("Tent%d_tip"%i, par, "wedge", [0.3,0.6,0.3], [0,-0.6,0], (-90,0,0), "C")
    B.ring("Tent","CoreRoot",n,1.35,-1.3,[0.7,0.8,0.7],"A",child=suckers)
    B.tag("tentacles"); B.count("tentacles",n)
def b_serpent(B,I,rng):
    d = [10]+[rng.choice([-13,13])*(1 if i%2 else -1) for i in range(9)]
    sizes = [[1.5-i*0.09,1.35-i*0.08,1.6] for i in range(10)]
    ns = B.yaw_chain("Seg",None,d,sizes,["A" if i%2 else "B" for i in range(10)],(0,1.5,4.2))
    for i in range(1,9,2):
        B.add("Belly%d"%i, ns[i], "box", [sizes[i][0]*0.8,0.3,sizes[i][2]*0.8], [0,-0.75,0], (0,0,0), "L")
    head = B.add("Head",ns[-1],"box",[1.9,1.5,2.3],[0,0.25,-1.3],(0,0,0),"A")
    B.add("Snout",head,"wedge",[1.3,0.9,1.3],[0,-0.25,-1.5],(-90,0,0),"B")
    B.add("Jaw",head,"box",[1.2,0.35,1.5],[0,-0.75,-1.2],(0,0,0),"D")
    B.eyes(head,0.45,-1.05,0.5,0.72)
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("HornS"+suf,head,"pyramid",[0.35,1.5,0.35],[sx*0.7,1.0,0.5],(sx*-20,0,0),"S")
        B.add("FrillS"+suf,head,"wedge",[0.25,1.2,1.1],[sx*0.95,0.1,0.4],(0,0,sx*70),"C")
    B.mirrored += [("HornSR","HornSL"),("FrillSR","FrillSL")]
    for i in range(0,8,2):
        B.add("Dorsal%d"%i, ns[i], "wedge", [0.28,0.9,1.0], [0,0.85,0], (0,0,0), "C")
    B.add("TailFinA",ns[0],"wedge",[1.3,1.5,0.28],[0,0.2,1.2],(90,0,0),"C")
    B.tag("tail"); B.count("tail",1)
def b_fish(B,I,rng):
    B.add("CoreRoot",None,"box",[2.6,2.6,2.4],[0,2.0,0],(0,0,0),"A")
    B.add("SnoutSec","CoreRoot","box",[2.0,2.0,1.4],[0,0.05,-1.6],(0,0,0),"A")
    B.add("CaudalSec","CoreRoot","box",[1.3,1.5,1.4],[0,0.1,1.6],(0,0,0),"B")
    B.add("Belly","CoreRoot","box",[2.1,1.0,2.2],[0,-1.35,0],(0,0,0),"L")
    B.add("Lip","SnoutSec","wedge",[1.4,0.5,0.6],[0,-0.75,-0.8],(-90,0,0),"C")
    B.eyes("SnoutSec",0.5,-0.75,0.55,0.8)
    for sx,k in ((1,0),(-1,1)):
        B.add("Gill%d"%k,"CoreRoot","box",[0.12,1.2,0.7],[sx*1.32,0,0.6],(0,0,0),"D")
    n = int((4+B.sharp*4)*B.detail)
    for i in range(n):
        a = -65+i*(130.0/max(1,n-1)); r = math.radians(a)
        B.add("Dorsal%d"%i,"CoreRoot","pyramid",[0.45,rng.uniform(0.9,1.9)*B.sharp,0.45],
              [1.45*math.sin(r),1.45*math.cos(r),rng.uniform(-0.9,0.9)],(0,0,-a),"S")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Pect"+suf,"CoreRoot","wedge",[1.5,1.2,0.25],[sx*1.35,-0.5,-0.5],(0,0,sx*62),"C")
        B.add("Pelv"+suf,"CoreRoot","wedge",[1.0,0.9,0.22],[sx*0.8,-1.5,-0.6],(0,0,sx*40),"C")
    B.mirrored += [("PectR","PectL"),("PelvR","PelvL")]
    for k,az in ((0,-32),(1,0),(2,32)):
        B.add("Caudal%d"%k,"CaudalSec","wedge",[1.5,2.0,0.25],[0,0.5,1.0],(0,az,0),"C")
    B.tag("fins","tail"); B.count("tail",1)
def b_bird(B,I,rng):
    B.add("CoreRoot",None,"box",[1.9,2.1,2.5],[0,2.6,0],(0,0,0),"A")
    B.add("Keel","CoreRoot","wedge",[1.2,1.2,1.8],[0,-1.0,-0.2],(180,0,0),"L")
    neck = B.add("Neck","CoreRoot","box",[0.9,1.1,0.9],[0,1.3,-0.9],(-18,0,0),"B")
    head = B.add("Head",neck,"box",[1.25,1.25,1.3],[0,0.9,-0.2],(12,0,0),"A")
    B.eyes(head,0.15,-0.6,0.42,0.5)
    for i in range(5):
        B.add("TailF%d"%i,"CoreRoot","wedge",[0.7,1.9-abs(i-2)*0.25,0.22],
              [(i-2)*0.5,-0.3,1.5],(115,(i-2)*14,0),"C" if i%2 else "S")
    for sx,suf in ((1,"R"),(-1,"L")):
        sh = B.add("Wing"+suf,"CoreRoot","box",[1.5,0.4,1.1],[sx*1.15,0.7,0],(0,0,sx*16),"B")
        md = B.add("Wing%sMid"%suf,sh,"box",[1.4,0.32,0.9],[sx*1.0,0,0.05],(0,0,sx*12),"A")
        for i in range(5):
            B.add("Wing%sP%d"%(suf,i),md,"wedge",[0.42,1.5-i*0.16,0.2],
                  [sx*(0.35+i*0.3),-0.4,0.25],(0,0,sx*(26+i*9)),"S" if i%2 else "C")
    B.mirrored.append(("WingR","WingL"))
    for sx,suf in ((1,"R"),(-1,"L")):
        f = B.add("Femur"+suf,"CoreRoot","box",[0.6,1.2,0.7],[sx*0.65,-1.5,0],(0,0,0),"B")
        t = B.add("Tibia"+suf,f,"box",[0.45,1.2,0.5],[0,-1.1,0.1],(0,0,0),"D")
        for k in (-1,0,1):
            B.add("Tal%s%d"%(suf,k),t,"pyramid",[0.2,0.6,0.2],[k*0.25,-0.7,-0.3],(75,0,0),"D")
    B.mirrored.append(("FemurR","FemurL"))
    B.tag("wings"); B.count("wings",2)
def b_crab(B,I,rng):
    B.add("CoreRoot",None,"box",[3.4,1.6,2.6],[0,1.9,0],(0,0,0),"A")
    B.add("Dome","CoreRoot","box",[2.7,1.0,2.1],[0,1.1,0],(0,0,0),"B")
    B.add("Dome2","Dome","box",[1.8,0.7,1.4],[0,0.7,0],(0,0,0),"A")
    for i in range(6):
        x,z = phyllotaxis(i,6,1.2)
        B.add("Scute%d"%i,"Dome2","gem",[0.5,0.3,0.5],[x,0.5,z],(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        st = B.add("Stalk"+suf,"CoreRoot","box",[0.28,0.9,0.28],[sx*0.8,1.2,-1.1],(sx*10,0,0),"C")
        B.add("Eye"+suf,st,"gem",[0.5,0.5,0.5],[0,0.6,0],(0,0,0),"C")
        B.add("Pupil"+suf,"Eye"+suf,"gem",[0.22,0.22,0.22],[0,0.1,-0.28],(0,0,0),"D")
        m = B.add("Merus"+suf,"CoreRoot","box",[0.8,1.5,0.8],[sx*2.0,0.1,-0.9],(sx*24,0,0),"B")
        c = B.add("Carpus"+suf,m,"box",[0.7,1.2,0.7],[0,-1.2,-0.3],(-34,0,0),"A")
        pr = B.add("Prop"+suf,c,"box",[0.75,1.5,0.7],[0,-1.2,-0.2],(-20,0,0),"B")
        B.add("Dactyl"+suf,pr,"wedge",[0.5,1.4,0.5],[0,-1.3,-0.15],(-26,0,0),"S")
        B.add("Pollex"+suf,pr,"wedge",[0.5,1.1,0.5],[0,-1.1,0.3],(22,0,0),"S")
    B.mirrored += [("StalkR","StalkL"),("MerusR","MerusL")]
    for i in range(3):
        for sx,suf in ((1,"R"),(-1,"L")):
            l1 = B.add("Walk%d%s"%(i,suf),"CoreRoot","box",[0.45,1.5,0.45],
                       [sx*1.6,-0.6,0.7-i*0.7],(0,sx*(i-1)*26,sx*34),"B")
            l2 = B.add("Walk%d%s2"%(i,suf),l1,"box",[0.36,1.4,0.36],[0,-1.2,0],(0,0,-sx*46),"A")
            B.add("Walk%d%s3"%(i,suf),l2,"pyramid",[0.26,0.7,0.26],[0,-1.2,0],(180,0,0),"D")
    B.tag("claws"); B.count("claws",2)
def b_spider(B,I,rng):
    B.add("CoreRoot",None,"box",[2.0,1.4,2.2],[0,2.2,-0.8],(0,0,0),"A")
    ab = B.add("Abdomen","CoreRoot","box",[2.2,1.9,2.6],[0,0.5,2.0],(0,0,0),"B")
    for i in range(5):
        x,z = phyllotaxis(i,5,0.9)
        B.add("Spot%d"%i,ab,"gem",[0.4,0.25,0.4],[x,1.0,z],(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Spin"+suf,ab,"pyramid",[0.22,0.8,0.22],[sx*0.3,-0.4,1.4],(150,0,0),"D")
    hd = B.add("Head","CoreRoot","box",[1.4,1.1,1.2],[0,-0.1,-1.5],(0,0,0),"B")
    for k,(dx,dy) in enumerate(((-0.4,0.1),(-0.15,0.25),(0.15,0.25),(0.4,0.1))):
        B.add("Eye%d"%k,hd,"gem",[0.26,0.3,0.2],[dx*2,dy,-0.62],(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        ch = B.add("Chel"+suf,hd,"box",[0.4,0.7,0.5],[sx*0.35,-0.6,-0.5],(0,0,0),"D")
        B.add("Fang"+suf,ch,"pyramid",[0.2,0.8,0.2],[0,-0.6,-0.1],(168,0,0),"S")
    B.mirrored.append(("ChelR","ChelL"))
    for i in range(4):
        for sx,suf in ((1,"R"),(-1,"L")):
            a = (i-1.5)*22
            l1 = B.add("Leg%d%s"%(i,suf),"CoreRoot","box",[0.38,1.9,0.38],
                       [sx*1.0,0.3,-0.9+i*0.62],(0,sx*a,sx*52),"B")
            B.add("Leg%d%sS"%(i,suf),l1,"pyramid",[0.24,0.6,0.24],[0,0.6,0],(0,0,0),"S")
            l2 = B.add("Leg%d%s2"%(i,suf),l1,"box",[0.32,1.9,0.32],[0,-1.7,0],(0,0,-sx*58),"A")
            l3 = B.add("Leg%d%s3"%(i,suf),l2,"box",[0.26,1.5,0.26],[0,-1.4,0],(0,0,sx*24),"B")
            B.add("Leg%d%s4"%(i,suf),l3,"pyramid",[0.2,0.7,0.2],[0,-1.1,0],(180,0,0),"D")
    B.tag("teeth")
def b_golem(B,I,rng):
    B.add("HumanoidRootPart",None,"gem",[2.6,3.0,2.0],[0,3.2,0],(0,0,0),"A")
    B.add("Core","HumanoidRootPart","gem",[1.1,1.3,0.9],[0,0.1,-0.7],(0,0,0),"C")
    B.add("Frame","HumanoidRootPart","box",[3.0,1.0,1.4],[0,1.2,0],(0,0,0),"B")
    hd = B.add("Head","HumanoidRootPart","box",[1.2,1.1,1.2],[0,2.1,0],(0,0,0),"B")
    B.add("Visor",hd,"wedge",[0.9,0.4,0.3],[0,0.1,-0.65],(-90,0,0),"C")
    B.add("Brow",hd,"box",[1.3,0.3,0.5],[0,0.55,-0.5],(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        p1 = B.add("Pauldron"+suf,"HumanoidRootPart","box",[1.3,0.6,1.3],[sx*1.9,1.5,0],(0,0,sx*8),"B")
        B.add("Pauldron%s2"%suf,p1,"wedge",[1.4,0.7,1.4],[0,0.5,0],(0,0,sx*8),"D")
        a1 = B.add("Arm"+suf,"HumanoidRootPart","box",[0.9,2.2,0.9],[sx*1.9,0.2,0],(0,0,sx*6),"A")
        a2 = B.add("Fore"+suf,a1,"box",[0.8,1.8,0.8],[0,-1.8,0],(0,0,0),"B")
        B.add("Fist"+suf,a2,"box",[1.1,1.0,1.1],[0,-1.4,0],(0,0,0),"D")
        for k in range(3):
            B.add("Knuck%s%d"%(suf,k),"Fist"+suf,"pyramid",[0.22,0.5,0.22],
                  [(k-1)*0.32,-0.5,-0.5],(75,0,0),"S")
        l1 = B.add("Leg"+suf,"HumanoidRootPart","box",[1.0,2.2,1.0],[sx*0.9,-2.4,0],(0,0,0),"B")
        B.add("Foot"+suf,l1,"wedge",[1.2,0.7,1.6],[0,-1.3,-0.3],(0,0,0),"D")
    B.mirrored += [("PauldronR","PauldronL"),("ArmR","ArmL"),("LegR","LegL")]
    for i in range(4):
        x,z = phyllotaxis(i,4,0.8)
        B.add("Crys%d"%i,"HumanoidRootPart","pyramid",[0.4,1.6*B.sharp,0.4],[x,1.6,z+0.8],(-18,0,0),"S")
    B.tag("armor","glow")
def b_humanoid(B,I,rng):
    B.add("HumanoidRootPart",None,"box",[1.9,2.3,1.1],[0,3.3,0],(0,0,0),"A")
    B.add("Chest","HumanoidRootPart","box",[2.2,1.3,1.2],[0,1.0,0],(0,0,0),"B")
    B.add("ChestGem","Chest","gem",[0.5,0.6,0.3],[0,0.2,-0.65],(0,0,0),"C")
    B.add("Belt","HumanoidRootPart","box",[2.0,0.4,1.2],[0,-1.2,0],(0,0,0),"D")
    B.add("Buckle","Belt","box",[0.4,0.3,0.2],[0,0,-0.65],(0,0,0),"L")
    hd = B.add("Head","HumanoidRootPart","box",[1.15,1.2,1.15],[0,1.85,0],(0,0,0),"C")
    B.add("Jaw",hd,"box",[0.9,0.4,0.9],[0,-0.55,-0.1],(0,0,0),"D")
    B.eyes(hd,0.15,-0.6,0.3,0.38)
    for sx,suf in ((1,"R"),(-1,"L")):
        p = B.add("Pauldron"+suf,"Chest","box",[0.95,0.5,0.95],[sx*1.3,0.75,0],(0,0,sx*10),"B")
        B.add("Pauldron%s2"%suf,p,"wedge",[1.0,0.5,1.0],[0,0.4,0],(0,0,sx*10),"D")
        a1 = B.add("Arm"+suf,"Chest","box",[0.62,1.7,0.62],[sx*1.35,-0.2,0],(0,0,sx*5),"A")
        a2 = B.add("Fore"+suf,a1,"box",[0.52,1.5,0.52],[0,-1.4,0],(0,0,0),"C")
        B.add("Hand"+suf,a2,"box",[0.55,0.6,0.55],[0,-1.0,0],(0,0,0),"D")
        l1 = B.add("Leg"+suf,"HumanoidRootPart","box",[0.75,1.9,0.8],[sx*0.55,-2.2,0],(0,0,0),"A")
        l2 = B.add("Shin"+suf,l1,"box",[0.62,1.7,0.66],[0,-1.6,0],(0,0,0),"B")
        B.add("Boot"+suf,l2,"wedge",[0.75,0.6,1.3],[0,-1.0,-0.25],(0,0,0),"D")
    B.mirrored += [("PauldronR","PauldronL"),("ArmR","ArmL"),("LegR","LegL")]
    B.tag("armor")
def b_turtle(B,I,rng):
    B.add("CoreRoot",None,"box",[3.0,1.2,3.4],[0,1.6,0],(0,0,0),"L")
    sh = B.add("ShellBase","CoreRoot","box",[3.2,1.0,3.6],[0,0.9,0],(0,0,0),"A")
    s2 = B.add("Shell2",sh,"box",[2.6,0.9,3.0],[0,0.8,0],(0,0,0),"B")
    s3 = B.add("Shell3",s2,"box",[1.8,0.8,2.2],[0,0.7,0],(0,0,0),"A")
    for i in range(7):
        x,z = phyllotaxis(i,7,1.1)
        B.add("Scute%d"%i,s2,"gem",[0.6,0.3,0.6],[x,0.6,z],(0,0,0),"D")
    if B.sharp > 0.9:
        for i in range(6):
            az = i*60; a = math.radians(az)
            B.add("RimSpike%d"%i,sh,"pyramid",[0.4,0.9*B.sharp,0.4],
                  [1.7*math.sin(a),0.5,1.9*math.cos(a)],(0,0,0),"S")
    nk = B.add("Neck","CoreRoot","box",[0.9,0.9,1.0],[0,0.2,-2.0],(-14,0,0),"L")
    hd = B.add("Head",nk,"box",[1.1,1.0,1.1],[0,0.3,-0.8],(10,0,0),"L")
    B.eyes(hd,0.2,-0.55,0.34,0.42)
    B.add("BeakT",hd,"wedge",[0.5,0.4,0.5],[0,-0.2,-0.65],(-90,0,0),"C")
    for i,(sx,sz) in enumerate(((1,-1),(-1,-1),(1,1),(-1,1))):
        l1 = B.add("Flip%d"%i,"CoreRoot","box",[0.9,0.8,1.3],[sx*1.6,-0.5,sz*1.3],
                   (0,sx*sz*24,sx*20),"L")
        B.add("Flip%dC"%i,l1,"pyramid",[0.3,0.5,0.3],[0,-0.5,-0.5*sz],(0,0,0),"D")
    B.yaw_chain("Tail","CoreRoot",[12,14,16],
        [[0.6,0.6,0.8],[0.45,0.45,0.7],[0.3,0.3,0.6]],["L","L","D"],(0,-0.2,1.9))
    B.tag("shell","tail"); B.count("tail",1)
def b_jelly(B,I,rng):
    B.add("CoreRoot",None,"box",[3.0,1.2,3.0],[0,3.0,0],(0,0,0),"A")
    b2 = B.add("Bell2","CoreRoot","box",[3.4,0.9,3.4],[0,-0.7,0],(0,0,0),"B")
    b3 = B.add("Bell3",b2,"box",[2.6,0.7,2.6],[0,0.8,0],(0,0,0),"A")
    B.add("GlowCore","CoreRoot","gem",[1.0,0.8,1.0],[0,-0.2,0],(0,0,0),"C")
    for i in range(6):
        x,z = phyllotaxis(i,6,1.2)
        B.add("Spot%d"%i,b3,"gem",[0.4,0.22,0.4],[x,0.5,z],(0,0,0),"D")
    for i in range(12):
        az = i*30.0; a = math.radians(az)
        B.add("Skirt%d"%i,b2,"wedge",[0.5,0.9,0.16],
              [1.6*math.sin(a),-0.6,1.6*math.cos(a)],(180,az,0),"L")
    for i in range(4):
        az = i*90+45; a = math.radians(az)
        base = B.add("Oral%d"%i,"CoreRoot","box",[0.5,0.9,0.5],
                     [0.7*math.sin(a),-1.0,0.7*math.cos(a)],(0,az,0),"L")
        B.pitch_chain("Oral%d_"%i,base,[10,-14,12,-10],
            [[0.45,1.1,0.3],[0.4,1.0,0.26],[0.34,0.9,0.22],[0.26,0.8,0.18]],["L","C","L","C"])
    m = int(8*B.detail)
    for i in range(m):
        az = i*360.0/m; a = math.radians(az)
        base = B.add("Tent%d"%i,b2,"box",[0.22,0.7,0.22],
                     [1.5*math.sin(a),-0.8,1.5*math.cos(a)],(0,az,0),"C")
        B.pitch_chain("Tent%d_"%i,base,[8,10,12,14,16],
            [[0.18,1.2,0.18],[0.16,1.1,0.16],[0.14,1.0,0.14],[0.12,0.9,0.12],[0.1,0.8,0.1]],
            ["C","L","C","L","C"])
    B.tag("tentacles","frill","glow"); B.count("tentacles",m)
BUILDERS = {"octopus":b_octopus,"serpent":b_serpent,"fish":b_fish,"bird":b_bird,"crab":b_crab,
 "spider":b_spider,"golem":b_golem,"humanoid":b_humanoid,"turtle":b_turtle,"jelly":b_jelly}

# ============================ 9. SELF-CRITIQUE ============================
def critique(spec, I):
    rep = {}; tot = 0.0; wsum = 0.0
    def add(k, v, w):
        rep[k] = int(round(v*100)); return v*w
    want = set(I["traits"]) - I["neg"]; have = set(spec.get("traits_present", []))
    hit = len(want & have)/max(1,len(want)) if want else 1.0
    neg_pen = len(I["neg"] & have)*0.25
    tot += add("trait_match", max(0, hit-neg_pen), 0.28); wsum += 0.28
    if I["colors"]:
        ds = [max(0,1-hue_dist(ih,min(hex_hsv(h)[0] for h in spec["palette"].values()),)/90.0)
              if False else max(0,1-min(hue_dist(ih,hex_hsv(h)[0]) for h in spec["palette"].values())/90.0)
              for ih,_,_ in I["colors"]]
        tot += add("color_match", sum(ds)/len(ds), 0.20); wsum += 0.20
    else:
        tot += add("color_match", 0.85, 0.20); wsum += 0.20
    cs = 1.0
    for tr, meta in I["traits"].items():
        if meta.get("count"):
            cs *= 1.0 if spec.get("counts",{}).get(tr,0)==meta["count"] else 0.55
    tot += add("count_match", cs, 0.12); wsum += 0.12
    names = {p["n"] for p in spec["parts"]}; mir = spec.get("mirrored",[])
    ok = sum(1 for a,b in mir if a in names and b in names)/max(1,len(mir))
    tot += add("symmetry", ok, 0.10); wsum += 0.10
    n = len(spec["parts"])
    tot += add("complexity", 1.0 if 40<=n<=260 else (0.7 if 25<=n<=340 else 0.4), 0.08); wsum += 0.08
    sizes = [p["sz"][0] for p in spec["parts"]]
    tot += add("silhouette", clamp((max(sizes)-min(sizes))/max(0.001,max(sizes))/0.8,0,1), 0.07); wsum += 0.07
    tot += add("sharp_match", max(0,1-abs(I["sharp"]-spec["sharpness"])/2.0), 0.07); wsum += 0.07
    tot += add("scale_match", max(0,1-abs(I["size"]-spec["scale"])/0.8), 0.05); wsum += 0.05
    tot += add("pattern", 1.0 if (I["pattern"] and spec["meta"].get("painted")) or not I["pattern"] else 0.5,
               0.03); wsum += 0.03
    return int(round(100*tot/wsum)), rep
NAME_PRE = ["Brick","Stud","Krag","Zor","Bloxx","Torv","Pixl","Grim","Lux","Vex","Snap","Mek",
 "Vor","Quil","Rune","Ember","Frost","Thorn","Gale","Umber"]
NAME_SUF = {"octopus":"pus","serpent":"enth","fish":"ish","bird":"wing","crab":"claw","spider":"ling",
 "golem":"mok","humanoid":"guard","turtle":"shell","jelly":"meduse"}
EPITHETS = ["the Sharp","of Bricks","the Unbroken","the Studbound","the Vivid","the Ancient"]

# ============================ 10. MEMORY + EVOLUTION + SEARCH ============================
def style_vector(spec):
    hsvs = [hex_hsv(h) for h in list(spec["palette"].values())[:6]]
    return {"sharp":spec["sharpness"],"scale":spec["scale"],"parts":len(spec["parts"]),
            "sat":sum(s for _,s,_ in hsvs)/len(hsvs),"val":sum(v for _,_,v in hsvs)/len(hsvs),
            "arch":spec["archetype"]}
def tokens_of(p): return set(tokenize(p))
def memory_priors(mem, prompt):
    tk = tokens_of(prompt); acc = Counter(); styles = []; pal = None; bw = 0.0; liked = []
    for e in mem.get("entries",[]):
        et = tokens_of(e.get("prompt","")); inter = len(tk & et)
        sim = inter/max(1.0, math.sqrt(len(tk)*max(1,len(et))))
        acc[e.get("archetype","golem")] += sim; liked.append((sim,e))
        st = e.get("style")
        if st and sim > 0.15: styles.append((sim,st)); bw += sim
        if sim > 0.3 and e.get("palette"): pal = e["palette"]
    blend = {k: sum(w*s[k] for w,s in styles)/bw for k in ("sharp","scale","sat","val")} if styles else None
    return acc, blend, pal, sorted(liked, reverse=True)
def _build(I, arch, seed, feat, mpal_hsv, evolve_pal):
    rng = random.Random(seed)
    pal = dict(evolve_pal) if evolve_pal else synthesize_palette(I, rng, mpal_hsv)
    if feat.get("colors") and not evolve_pal:
        fc = feat["colors"]
        pal["A"]=fc[0]; pal["B"]=fc[min(1,len(fc)-1)]; pal["C"]=fc[min(2,len(fc)-1)]
        pal["S"]=fc[min(3,len(fc)-1)]; pal["D"]=hsv_hex(hex_hsv(fc[0])[0],0.5,0.2)
        pal["L"]=hsv_hex(hex_hsv(fc[0])[0],0.15,0.95)
        for g in range(8):
            pal["G%d"%g] = hsv_hex(*lerp_hsv(hex_hsv(pal["A"]),hex_hsv(pal["S"]),g/7.0))
    B = Builder(seed, pal, rng, I["sharp"], I["size"], I["style"])
    BUILDERS[arch](B, I, rng)
    for tr, meta in I["traits"].items():
        if tr in INHERENT.get(arch,set()) or tr in I["neg"]: continue
        FEATS.get(tr, lambda *a: None)(B, I, rng, meta.get("count"), meta.get("inten",1.0))
    painted = paint(B, I.get("pattern") or rng.choice([None,None,"stripes","spots","gradient","counter"]), rng)
    apply_pose(B, I.get("pose",0))
    spec = {"id":"m%d_%d"%(int(time.time()*1000)%100000, seed%97), "name":rng.choice(NAME_PRE)+NAME_SUF[arch],
            "archetype":arch,"variant":seed%4,"seed":seed,"sharpness":round(B.sharp,2),
            "scale":round(B.scale,2),"palette":pal,"tags":sorted(B.present),"root":B.root,
            "parts":B.parts,"mirrored":B.mirrored,"counts":dict(B.counts),
            "traits_present":sorted(B.present),
            "meta":{"scheme":"v2","painted":painted,"prompt":I.get("_prompt","")}}
    return spec
def generate(body, mem):
    t0 = time.time()
    prompt = body.get("prompt","creature"); it = int(body.get("iteration",0))
    nonce = body.get("nonce","x"); reasons = body.get("reasons",[]); feat = body.get("features") or {}
    I = parse_intent(prompt); I["_prompt"] = prompt
    mbias, blend, mpal, liked = memory_priors(mem, prompt)
    for a,w in mbias.items(): I["arch"][a] += w*1.5
    if feat.get("edges"): I["sharp"] = clamp(I["sharp"]+feat["edges"]*1.2, 0.2, 2.6)
    if blend:
        I["sharp"] = clamp(I["sharp"]*0.7+blend["sharp"]*0.3, 0.2, 2.6)
        I["size"] = I["size"]*0.8+blend["scale"]*0.2; I["sat"] = I["sat"]*0.7+blend["sat"]*0.3
    if "wrong colors" in reasons: mpal = None
    if "too many spikes" in reasons: I["sharp"] = max(0.2, I["sharp"]-1.0)
    if "not enough detail" in reasons: I["sharp"] = min(2.6, I["sharp"]+0.8)
    if "wrong creature" in reasons and I["arch"]:
        top = I["arch"].most_common(1)[0][0]; I["arch"] = Counter({a:1 for a in ARCHES if a != top})
    evolve_pal = None
    low = prompt.lower()
    if ("evolve" in low or "hybrid" in low or "mix" in low) and len(liked) >= 2:
        p1, p2 = liked[0][1], liked[1][1]
        pa, pb = p1.get("palette",{}), p2.get("palette",{})
        if pa and pb:
            evolve_pal = {k: hsv_hex(*lerp_hsv(hex_hsv(pa.get(k,"#888888")), hex_hsv(pb.get(k,"#888888")), 0.5))
                          for k in ("A","B","C","S","D","L")}
            for g in range(8):
                evolve_pal["G%d"%g] = hsv_hex(*lerp_hsv(hex_hsv(evolve_pal["A"]),hex_hsv(evolve_pal["S"]),g/7.0))
        for tr in set(p1.get("spec",{}).get("traits_present",[])) | set(p2.get("spec",{}).get("traits_present",[])):
            I["traits"].setdefault(tr, {"inten":1.0,"count":None})
        I["arch"] = Counter({p1.get("archetype","golem"):1, p2.get("archetype","fish"):1})
    K = 6 + min(6, it*2); best = None; tried = 0
    for k in range(K):
        if time.time()-t0 > BUDGET: break
        seed = zlib.crc32(("%s|%d|%s|%d"%(prompt,it,nonce,k)).encode())
        rng = random.Random(seed)
        if I["arch"]:
            arch = I["arch"].most_common(1)[0][0] if (k==0 and rng.random()<0.8) else rng.choice(list(I["arch"]) or ARCHES)
        else: arch = rng.choice(ARCHES)
        if "wrong shape" in reasons: arch = ARCHES[(ARCHES.index(arch)+k+1)%len(ARCHES)]
        try: spec = _build(I, arch, seed, feat, mpal and hex_hsv(mpal["A"]) or None, evolve_pal)
        except Exception: continue
        tried += 1
        score, rep = critique(spec, I); spec["score"] = score; spec["report"] = rep
        if best is None or score > best["score"]: best = spec
    # hill-climb refinement on the winner
    if best:
        for m in range(3):
            if time.time()-t0 > BUDGET: break
            I2 = dict(I); I2["sharp"] = clamp(I["sharp"]+random.uniform(-0.35,0.35),0.2,2.6)
            I2["size"] = clamp(I["size"]+random.uniform(-0.12,0.12),0.6,1.8)
            seed = best["seed"]+m+13
            try: cand = _build(I2, best["archetype"], seed, feat, None, evolve_pal)
            except Exception: continue
            s2, r2 = critique(cand, I2); cand["score"] = s2; cand["report"] = r2; tried += 1
            if s2 > best["score"]: best = cand
    if best is None:  # absolute fallback: never hang, never crash
        best = _build(I, "golem", 1, feat, None, None); best["score"], best["report"] = critique(best, I)
        tried = 1
    if best["score"] > 85: best["name"] += " " + random.Random(best["seed"]).choice(EPITHETS)
    best["meta"].update({"beam":K,"tried":tried,"iteration":it,
                         "seconds":round(time.time()-t0,2)})
    return best
