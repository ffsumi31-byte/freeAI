"""BrickForge AI — cognitive core. Local procedural intelligence for blocky creature design.
Layers: lexicon/ontology -> intent parser -> color theory -> anatomy math -> part DSL ->
archetype builders -> chimera trait modules -> self-critique -> beam search -> memory learning."""
import math, random, re, colorsys, zlib, time
from collections import Counter

# ============================ 1. LEXICON / ONTOLOGY ============================
ARCH_SYN = {
 "octopus": ["octopus","squid","kraken","cephalopod","tentacle beast","ink"],
 "serpent": ["snake","serpent","dragon","wyrm","eel","viper","wyvern"],
 "fish":    ["fish","shark","koi","bass","piranha","manta","goldfish"],
 "bird":    ["bird","eagle","phoenix","falcon","owl","raven","parrot","hawk"],
 "crab":    ["crab","lobster","scorpion","shrimp","prawn"],
 "spider":  ["spider","arachnid","tarantula","scout bug","weaver"],
 "golem":   ["golem","golem","titan","colossus","elemental","rock beast"],
 "humanoid":["robot","humanoid","knight","warrior","mech","android","samurai","guard"],
 "turtle":  ["turtle","tortoise","shell beast","snail"],
 "jelly":   ["jelly","jellyfish","medusa","blob","slime spirit"]}
ARCHES = list(ARCH_SYN)
INHERENT = {"octopus":{"tentacles"},"serpent":{"tail"},"fish":{"fins","tail"},"bird":{"wings"},
 "crab":{"claws"},"spider":set(),"golem":{"armor"},"humanoid":{"armor"},"turtle":{"shell","tail"},
 "jelly":{"tentacles","frill"}}
TRAIT_SYN = {
 "wings":["wing","wings","winged","fly","flying"],"horns":["horn","horns","horned","antler"],
 "crest":["crest","mohawk","crown","crested"],"spikes":["spike","spikes","spiky","sharp","edgy","thorn"],
 "tail":["tail","tailed"],"claws":["claw","claws","pincer","grip"],"armor":["armor","armored","plate","plated","shield"],
 "glow":["glow","glowing","crystal","gem","shine","luminous"],"antennae":["antenna","antennae","feelers","sensor"],
 "teeth":["teeth","tooth","fang","fanged","jaw"],"beak":["beak","bill","snout hook"],
 "mane":["mane","frill","ruff","collar"],"shell":["shell","carapace","spiral"],"blades":["blade","scythe","saber","edge arm"],
 "fins":["fin","fins","finned"],"frill":["frill","frilled","skirt","lace"],"tentacles":["tentacle","tentacles","arms many"]}
MATERIAL = {"metal":{"s":0.25,"v":1.15},"metallic":{"s":0.25,"v":1.15},"steel":{"s":0.2,"v":1.1},
 "ice":{"h":195,"s":0.35,"v":0.95},"frozen":{"h":195,"s":0.35,"v":0.95},"lava":{"h":15,"s":0.95,"v":0.9},
 "magma":{"h":15,"s":0.95,"v":0.9},"gold":{"h":45,"s":0.85,"v":0.95},"golden":{"h":45,"s":0.85,"v":0.95},
 "obsidian":{"h":270,"s":0.25,"v":0.18},"crystal":{"s":0.5,"v":1.1},"bone":{"h":40,"s":0.15,"v":0.92},
 "wood":{"h":28,"s":0.5,"v":0.5},"wooden":{"h":28,"s":0.5,"v":0.5},"neon":{"s":1.0,"v":1.0}}
MOOD = {"cute":{"spike":-0.6,"scale":0.85,"sat":0.8,"round":1},"chibi":{"spike":-0.6,"scale":0.8,"sat":0.85},
 "fierce":{"spike":0.7,"sat":1.1},"majestic":{"spike":0.3,"scale":1.15,"sat":0.9},"royal":{"spike":0.2,"sat":0.9},
 "creepy":{"spike":0.5,"sat":0.7,"val":0.8},"evil":{"spike":0.6,"sat":0.9,"val":0.85},"gentle":{"spike":-0.4,"sat":0.85}}
INTEN = {"slight":0.5,"small":0.7,"tiny":0.55,"little":0.7,"some":0.8,"few":0.7,"very":1.4,"extra":1.5,"super":1.6,
 "mega":1.8,"huge":1.7,"massive":1.8,"giant":1.8,"big":1.35,"large":1.3,"long":1.4,"tall":1.3,"heavy":1.4,
 "light":0.8,"subtle":0.7,"extreme":1.9,"ultra":1.8}
COUNTS = {"one":1,"two":2,"twin":2,"double":2,"pair":2,"three":3,"triple":3,"four":4,"quad":4,"five":5,
 "six":6,"seven":7,"eight":8,"nine":9,"ten":10,"many":8,"multi":6,"multiple":6}
SIZEW = {"tiny":0.7,"small":0.85,"big":1.3,"huge":1.55,"giant":1.6,"massive":1.65,"colossal":1.7,"mini":0.75,"large":1.3}
NEG = {"no","without","lack","lacks","not","never","minus"}
STYLE = {"blocky":1.0,"chunky":1.15,"sleek":0.9,"slim":0.85,"ornate":1.2,"detailed":1.2,"minimal":0.75,"simple":0.8}
COLOR_WORDS = {"red":(0,0.85,0.62),"crimson":(348,0.9,0.55),"scarlet":(8,0.9,0.6),"orange":(24,0.9,0.62),
 "amber":(38,0.95,0.7),"yellow":(52,0.9,0.65),"gold":(45,0.85,0.72),"lime":(80,0.8,0.6),"green":(140,0.7,0.5),
 "emerald":(152,0.8,0.45),"teal":(172,0.75,0.5),"cyan":(185,0.85,0.65),"azure":(205,0.85,0.62),"blue":(215,0.8,0.55),
 "navy":(225,0.8,0.3),"indigo":(250,0.7,0.5),"purple":(275,0.7,0.55),"violet":(285,0.75,0.6),"magenta":(310,0.8,0.6),
 "pink":(330,0.7,0.75),"rose":(340,0.7,0.65),"white":(0,0.0,0.96),"snow":(210,0.05,0.96),"black":(260,0.2,0.14),
 "dark":(260,0.2,0.2),"grey":(220,0.05,0.55),"gray":(220,0.05,0.55),"brown":(25,0.6,0.42),"tan":(35,0.45,0.72),
 "beige":(40,0.3,0.85),"maroon":(355,0.8,0.35),"olive":(70,0.6,0.4),"mint":(160,0.45,0.8),"coral":(12,0.8,0.72),
 "lavender":(265,0.45,0.8),"turquoise":(175,0.7,0.6),"silver":(210,0.08,0.82),"bronze":(22,0.65,0.5)}

# ============================ 2. INTENT PARSER ============================
def tokenize(t): return re.findall(r"[a-z]+", t.lower())
def parse_intent(prompt, mem_bias):
    toks = tokenize(prompt); raw = prompt.lower(); intent = {
        "arch": Counter(), "traits": {}, "neg": set(), "colors": [], "counts": {},
        "size": 1.0, "sharp": 1.0, "sat": 1.0, "val": 1.0, "style": 1.0, "mood": None,
        "material": None, "tokens": set(toks)}
    for a, syn in ARCH_SYN.items():
        for s in syn:
            if s in raw: intent["arch"][a] += 2 if s == a else 1
    for a in mem_bias: intent["arch"][a] += 0.0
    for tr, syn in TRAIT_SYN.items():
        for s in syn:
            m = re.search(r"\b(%s)" % re.escape(s), raw)
            if not m: continue
            pre = toks[:len(tokenize(raw[:m.start()]))][-2:]
            inten = 1.0; cnt = None; neg = False
            for w in pre:
                if w in INTEN: inten = max(inten, INTEN[w])
                if w in COUNTS: cnt = COUNTS[w]
                if w in NEG: neg = True
            if neg: intent["neg"].add(tr); continue
            old = intent["traits"].get(tr)
            intent["traits"][tr] = {"inten": max(inten, old["inten"] if old else 0), "count": cnt or (old or {}).get("count")}
    for w, hsv in COLOR_WORDS.items():
        if re.search(r"\b%s" % w, raw): intent["colors"].append(hsv)
    for w, v in SIZEW.items():
        if re.search(r"\b%s" % w, raw): intent["size"] = v; break
    for w, v in STYLE.items():
        if re.search(r"\b%s" % w, raw): intent["style"] = v; break
    for w, m in MOOD.items():
        if re.search(r"\b%s" % w, raw): intent["mood"] = m; break
    for w, m in MATERIAL.items():
        if re.search(r"\b%s" % w, raw): intent["material"] = m; break
    if intent["mood"]:
        m = MOOD[intent["mood"]]
        intent["sharp"] += m.get("spike", 0); intent["size"] *= m.get("scale", 1.0)
        intent["sat"] *= m.get("sat", 1.0); intent["val"] *= m.get("val", 1.0)
    if any(re.search(r"\b%s" % w, raw) for w in ("spiky","sharp","spined","thorny")): intent["sharp"] += 0.8
    if any(re.search(r"\b%s" % w, raw) for w in ("smooth","round","soft")): intent["sharp"] -= 0.6
    intent["sharp"] = max(0.2, min(2.6, intent["sharp"]))
    return intent

# ============================ 3. COLOR INTELLIGENCE ============================
def hsv_hex(h, s, v):
    h %= 360; r, g, b = colorsys.hsv_to_rgb(h / 360.0, max(0, min(1, s)), max(0, min(1, v)))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
def hex_hsv(hx):
    hx = hx.lstrip("#"); r, g, b = (int(hx[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r, g, b); return h * 360, s, v
def hue_dist(a, b): d = abs(a - b) % 360; return min(d, 360 - d)
def lerp_hsv(c1, c2, t):
    h1, s1, v1 = c1; h2, s2, v2 = c2; d = ((h2 - h1 + 540) % 360) - 180
    return (h1 + d * t, s1 + (s2 - s1) * t, v1 + (v2 - v1) * t)
def synthesize_palette(intent, rng, mem_prior):
    if intent["colors"]: base = intent["colors"][0]
    elif mem_prior: base = mem_prior
    else: base = (rng.choice([0, 25, 45, 140, 175, 205, 250, 285, 320]), 0.65, 0.6)
    h, s, v = base
    s = max(0.08, min(1, s * intent["sat"])); v = max(0.12, min(1, v * intent["val"]))
    if intent["material"]:
        m = intent["material"]
        if "h" in m: h = m["h"]
        s = max(0.05, min(1, s * m.get("s", 1))); v = max(0.1, min(1, v * m.get("v", 1)))
    scheme = rng.choice(["complement", "analogous", "triad", "split"])
    off = {"complement": 180, "analogous": 28, "triad": 120, "split": 150}[scheme]
    pal = {
        "A": hsv_hex(h, s * 0.85, v),                      # body
        "B": hsv_hex(h + rng.choice([-25, 25]), s * 0.7, min(1, v * 1.2)),   # secondary plates
        "C": hsv_hex(h + off, max(0.5, s), min(1, v * 1.35)),                # accent / eyes
        "S": hsv_hex(h + off + rng.choice([-30, 30]), max(0.45, s * 0.9), min(1, v * 1.1)),  # spikes
        "D": hsv_hex(h, min(1, s * 1.05), max(0.1, v * 0.42)),              # dark outline / pupils
        "L": hsv_hex(h + 15, max(0.06, s * 0.35), min(1, v * 1.55))}        # light belly
    return pal, scheme, (h, s, v)
def gradient(pal, key1, key2, t):
    return lerp_hsv(hex_hsv(pal[key1]), hex_hsv(pal[key2]), t)

# ============================ 4. ANATOMY MATH ============================
def clamp(x, a, b): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): return t * t * (3 - 2 * t)
def catmull(pts, t):
    n = len(pts) - 1; i = min(int(t * n), n - 1); f = t * n - i
    p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, n)]
    out = []
    for k in range(3):
        out.append(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * f + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * f * f +
                          (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * f * f * f))
    return out
def log_spiral(a, b, th): r = a * math.exp(b * th); return r * math.sin(th), r * math.cos(th)
GOLD = 137.5077640500378
def phyllotaxis(i, n, spread):
    r = spread * math.sqrt((i + 0.5) / n); th = math.radians(i * GOLD)
    return r * math.sin(th), r * math.cos(th)
def taper(t, p): return (1 - t) ** p

# ============================ 5. PART DSL (symmetry-safe, single-axis rig) ============================
class Builder:
    def __init__(self, seed, palette, rng, sharp, scale, style):
        self.parts = []; self.names = set(); self.pal = palette; self.rng = rng
        self.sharp = sharp; self.scale = scale * style; self.mirrored = []
        self.present = set(); self.counts = Counter(); self.root = None
    def _uniq(self, n):
        base = n; i = 2
        while n in self.names: n = "%s%d" % (base, i); i += 1
        self.names.add(n); return n
    def add(self, name, parent, shape, size, pos, rot=(0, 0, 0), color="A", mirror=False):
        assert sum(1 for v in rot if v) <= 1, "single-axis rotation only (rig export safety)"
        name = self._uniq(name)
        size = [round(v * self.scale, 2) for v in size]; pos = [round(v * self.scale, 2) for v in pos]
        self.parts.append({"n": name, "p": parent, "s": shape, "sz": size, "po": pos, "ro": list(rot), "c": color})
        if mirror:
            mn = self._uniq(name + "L")
            mpos = [-pos[0], pos[1], pos[2]]; mrot = [rot[0], -rot[1], -rot[2]]
            self.parts.append({"n": mn, "p": parent, "s": shape, "sz": list(size), "po": mpos, "ro": mrot, "c": color})
            self.mirrored.append((name, mn))
        if self.root is None and parent is None: self.root = name
        return name
    def tag(self, *traits):
        for t in traits: self.present.add(t)
    def count(self, key, n): self.counts[key] += n
    def yaw_chain(self, prefix, parent, deltas, sizes, colors, pos0=(0, 0, 0)):
        names = []; par = parent
        for i, (d, sz, c) in enumerate(zip(deltas, sizes, colors)):
            n = self.add("%s%d" % (prefix, i), par, "box", sz, pos0 if i == 0 else [0, 0, -sz[2] * 0.9],
                         (0, d, 0), c)
            names.append(n); par = n; pos0 = (0, 0, 0)
        return names
    def pitch_chain(self, prefix, parent, deltas, sizes, colors, pos0=(0, 0, 0), shape="box"):
        names = []; par = parent
        for i, (d, sz, c) in enumerate(zip(deltas, sizes, colors)):
            n = self.add("%s%d" % (prefix, i), par, shape, sz, pos0 if i == 0 else [0, -sz[1] * 0.85, 0],
                         (d, 0, 0), c)
            names.append(n); par = n; pos0 = (0, 0, 0)
        return names
    def ring(self, prefix, parent, n, radius, y, shape, size, color, child=None):
        outs = []
        for i in range(n):
            az = i * 360.0 / n; a = math.radians(az)
            b = self.add("%s%d" % (prefix, i), parent, "box", [size[0] * 0.9, size[1] * 0.6, size[0] * 0.9],
                         [radius * math.sin(a), y, radius * math.cos(a)], (0, az, 0), color)
            outs.append(b)
            if child: child(self, b, i, n)
        return outs
    def spikes_top(self, parent, n, spread, h, color="S", y=0.6):
        for i in range(n):
            x, z = phyllotaxis(i, n, spread)
            axis = 2 if abs(x) > abs(z) else 0
            rot = [0, 0, 0]; rot[axis] = clamp((-x if axis == 2 else z) * 22, -28, 28)
            self.add("Spike%d" % i, parent, "pyramid", [0.42, h * self.rng.uniform(0.7, 1.3), 0.42],
                     [x, y, z], rot, color)
    def eyes(self, parent, y, z, s, bx=0.75):
        for sx, suf in ((1, "R"), (-1, "L")):
            e = self.add("Eye" + suf, parent, "box", [s, s * 1.15, s * 0.4], [sx * bx * self.scale and sx * bx, y, z],
                         (0, 0, 0), "C")
            self.add("Pupil" + suf, e, "gem", [s * 0.45, s * 0.55, s * 0.3], [0, 0, -0.25], (0, 0, 0), "D")
        self.mirrored.append(("EyeR", "EyeL"))

# ============================ 6. CHIMERA TRAIT MODULES ============================
def feat_wings(B, I, rng, cnt, inten):
    kind = rng.choice(["feather", "membrane"])
    n = cnt or 2
    for sx, suf in ((1, "R"), (-1, "L")):
        sh = B.add("Wing" + suf, B.root, "box", [1.6 * inten, 0.35, 0.9], [sx * 1.1, 0.9, 0.3], (0, 0, sx * 22), "B")
        if kind == "feather":
            par = sh
            for i in range(4):
                par = B.add("Wing%sC%d" % (suf, i), par, "box", [1.5 - i * 0.25, 0.28, 0.8 - i * 0.08],
                            [sx * 1.0, 0.05, 0], (0, 0, sx * 12), "B" if i % 2 else "A")
            for i in range(5):
                B.add("Wing%sP%d" % (suf, i), par, "wedge", [0.5, 1.6 - i * 0.18, 0.22],
                      [sx * (0.4 + i * 0.35), -0.5, 0.2], (0, 0, sx * (30 + i * 8)), "S")
        else:
            arm = B.add("Wing%sArm" % suf, sh, "box", [2.2 * inten, 0.3, 0.3], [sx * 1.4, 0.2, 0], (0, 0, sx * 18), "D")
            for i in range(3):
                B.add("Wing%sF%d" % (suf, i), arm, "box", [0.22, 1.8 - i * 0.4, 0.22],
                      [sx * (0.3 + i * 0.5), -0.8, 0], (0, 0, sx * (10 + i * 14)), "D")
            B.add("Wing%sM" % suf, arm, "wedge", [2.4 * inten, 1.6, 0.12], [sx * 0.8, -0.7, 0.1], (0, 0, sx * 90), "L")
    B.mirrored.append(("WingR", "WingL")); B.tag("wings"); B.count("wings", n)
def feat_horns(B, I, rng, cnt, inten):
    for sx, suf in ((1, "R"), (-1, "L")):
        par = B.add("Horn" + suf, B.root, "box", [0.4, 0.7, 0.4], [sx * 0.6, 1.5, -0.4], (sx * -18, 0, 0), "S")
        for i in range(3):
            par = B.add("Horn%s%d" % (suf, i), par, "pyramid" if i == 2 else "box",
                        [0.34 - i * 0.07, (0.8 - i * 0.15) * inten, 0.34 - i * 0.07], [0, 0.6, -0.12], (-22, 0, 0), "S")
    B.mirrored.append(("HornR", "HornL")); B.tag("horns"); B.count("horns", cnt or 2)
def feat_crest(B, I, rng, cnt, inten):
    n = cnt or 5
    for i in range(n):
        B.add("Crest%d" % i, B.root, "pyramid", [0.3, (1.1 - abs(i - n / 2) * 0.18) * inten, 0.3],
              [0, 1.5, -0.9 + i * 0.42], (-12 + i * 4, 0, 0), "S")
    B.tag("crest"); B.count("crest", n)
def feat_spikes(B, I, rng, cnt, inten): B.spikes_top(B.root, int((cnt or 6) * inten), 1.5, 1.3 * inten); B.tag("spikes")
def feat_tail(B, I, rng, cnt, inten):
    d = [rng.choice([-14, 14]) for _ in range(5)]
    ns = B.yaw_chain("TailX", B.root, d, [[1.1 - i * 0.14, 0.9 - i * 0.1, 1.2] for i in range(5)],
                     ["A", "B", "A", "B", "A"], (0, 0.2, 1.4))
    B.add("TailFin", ns[-1], "wedge", [1.4 * inten, 1.6 * inten, 0.3], [0, 0.3, -0.8], (90, 0, 0), "C")
    B.tag("tail"); B.count("tail", 1)
def feat_claws(B, I, rng, cnt, inten):
    for sx, suf in ((1, "R"), (-1, "L")):
        a = B.add("ClawArm" + suf, B.root, "box", [0.6, 1.4, 0.6], [sx * 1.5, -0.2, -0.6], (sx * 16, 0, 0), "B")
        b = B.add("ClawArm%s2" % suf, a, "box", [0.5, 1.2, 0.5], [0, -1.1, -0.2], (-38, 0, 0), "A")
        B.add("Claw%sA" % suf, b, "wedge", [0.45, 1.3 * inten, 0.4], [0, -1.0, -0.1], (-28, 0, 0), "S")
        B.add("Claw%sB" % suf, b, "wedge", [0.45, 1.1 * inten, 0.4], [0, -0.9, 0.25], (24, 0, 0), "S")
    B.mirrored.append(("ClawArmR", "ClawArmL")); B.tag("claws"); B.count("claws", cnt or 2)
def feat_armor(B, I, rng, cnt, inten):
    for sx, suf in ((1, "R"), (-1, "L")):
        B.add("Pauldron" + suf, B.root, "box", [1.1, 0.5, 1.1], [sx * 1.3, 1.2, 0], (0, 0, sx * 10), "B")
        B.add("Pauldron%s2" % suf, B.root, "wedge", [1.2, 0.6, 1.2], [sx * 1.35, 1.55, 0], (0, 0, sx * 10), "D")
    B.add("ChestPlate", B.root, "box", [2.2, 1.4, 0.4], [0, 0.4, -0.9], (0, 0, 0), "B")
    B.add("BackPlate", B.root, "box", [2.0, 1.6, 0.35], [0, 0.4, 0.9], (0, 0, 0), "D")
    B.mirrored.append(("PauldronR", "PauldronL")); B.tag("armor")
def feat_glow(B, I, rng, cnt, inten):
    n = cnt or 7
    for i in range(n):
        x, z = phyllotaxis(i, n, 1.3)
        B.add("GlowGem%d" % i, B.root, "gem", [0.4 * inten, 0.6 * inten, 0.4 * inten], [x, 0.9, z], (0, 0, 0), "C")
    B.tag("glow")
def feat_antennae(B, I, rng, cnt, inten):
    for sx, suf in ((1, "R"), (-1, "L")):
        a = B.add("Antenna" + suf, B.root, "box", [0.18, 1.2 * inten, 0.18], [sx * 0.4, 1.6, -0.5], (sx * -14, 0, 0), "D")
        B.add("Antenna%sTip" % suf, a, "gem", [0.35, 0.35, 0.35], [0, 0.7, 0], (0, 0, 0), "C")
    B.mirrored.append(("AntennaR", "AntennaL")); B.tag("antennae")
def feat_teeth(B, I, rng, cnt, inten):
    n = cnt or 6
    for i in range(n):
        B.add("Tooth%d" % i, B.root, "pyramid", [0.18, 0.5 * inten, 0.18],
              [-0.7 + i * (1.4 / max(1, n - 1)), -0.55, -1.05], (180, 0, 0), "L")
    B.tag("teeth")
def feat_beak(B, I, rng, cnt, inten):
    b = B.add("Beak", B.root, "wedge", [0.8 * inten, 0.7, 1.1 * inten], [0, 0.1, -1.2], (-90, 0, 0), "C")
    B.add("BeakHook", b, "wedge", [0.5, 0.5, 0.5], [0, -0.35, -0.35], (20, 0, 0), "D"); B.tag("beak")
def feat_mane(B, I, rng, cnt, inten):
    n = cnt or 10
    for i in range(n):
        az = i * 360.0 / n; a = math.radians(az)
        B.add("Frill%d" % i, B.root, "wedge", [0.5, 1.2 * inten, 0.2],
              [1.1 * math.sin(a), 1.0, 1.1 * math.cos(a)], (0, az, 0), "S")
    B.tag("mane")
def feat_shell(B, I, rng, cnt, inten):
    par = B.root; th = 0.0
    for i in range(7):
        x, z = log_spiral(0.25, 0.22, th); s = (1.5 - i * 0.16) * inten
        par = B.add("Shell%d" % i, par, "box", [s, s * 0.7, s], [x, 0.9 + i * 0.22, z], (0, i * 24, 0), "B" if i % 2 else "A")
        th += 0.9
    B.tag("shell")
def feat_blades(B, I, rng, cnt, inten):
    for sx, suf in ((1, "R"), (-1, "L")):
        B.add("Blade" + suf, B.root, "wedge", [0.3, 2.4 * inten, 0.7], [sx * 1.5, 0.2, -0.8], (0, 0, sx * 30), "S")
    B.mirrored.append(("BladeR", "BladeL")); B.tag("blades")
def feat_fins(B, I, rng, cnt, inten):
    for sx, suf in ((1, "R"), (-1, "L")):
        B.add("Fin" + suf, B.root, "wedge", [1.4 * inten, 1.1, 0.25], [sx * 1.3, -0.2, 0.3], (0, 0, sx * 65), "C")
    B.add("DorsalFin", B.root, "wedge", [0.3, 1.3 * inten, 1.4], [0, 1.3, 0.2], (0, 0, 0), "C")
    B.mirrored.append(("FinR", "FinL")); B.tag("fins")
def feat_frill(B, I, rng, cnt, inten):
    n = cnt or 8
    for i in range(n):
        az = i * 360.0 / n; a = math.radians(az)
        B.add("Skirt%d" % i, B.root, "wedge", [0.6, 1.0 * inten, 0.18],
              [1.2 * math.sin(a), -0.8, 1.2 * math.cos(a)], (180, az, 0), "L")
    B.tag("frill")
def feat_tentacles(B, I, rng, cnt, inten):
    n = cnt or 4
    for i in range(n):
        az = i * 360.0 / n + 45
        b = B.add("ExtraTent%d" % i, B.root, "box", [0.5, 1.0, 0.5],
                  [1.2 * math.sin(math.radians(az)), -1.0, 1.2 * math.cos(math.radians(az))], (0, az, 0), "A")
        B.pitch_chain("ExtraTent%d_" % i, b, [18, 26, 34, 40],
                      [[0.45, 1.0, 0.45], [0.38, 0.9, 0.38], [0.3, 0.8, 0.3], [0.22, 0.7, 0.22]], ["A", "B", "A", "C"])
    B.tag("tentacles"); B.count("tentacles", n)
FEATS = {"wings": feat_wings, "horns": feat_horns, "crest": feat_crest, "spikes": feat_spikes, "tail": feat_tail,
 "claws": feat_claws, "armor": feat_armor, "glow": feat_glow, "antennae": feat_antennae, "teeth": feat_teeth,
 "beak": feat_beak, "mane": feat_mane, "shell": feat_shell, "blades": feat_blades, "fins": feat_fins,
 "frill": feat_frill, "tentacles": feat_tentacles}

# ============================ 7. ARCHETYPE BUILDERS ============================
def b_octopus(B, I, rng):
    B.add("CoreRoot", None, "box", [2.8, 2.2, 2.8], [0, 2.4, 0], (0, 0, 0), "A")
    B.add("Mantle", "CoreRoot", "box", [2.2, 1.4, 2.2], [0, 1.5, 0.1], (0, 0, 0), "B")
    B.add("Mantle2", "Mantle", "box", [1.5, 1.0, 1.5], [0, 1.0, 0.15], (0, 0, 0), "A")
    B.add("Mantle3", "Mantle2", "box", [0.9, 0.7, 0.9], [0, 0.7, 0.1], (0, 0, 0), "B")
    for sx, suf in ((1, "R"), (-1, "L")):
        B.add("MantleFin" + suf, "Mantle", "wedge", [1.2, 0.8, 1.4], [sx * 1.2, 0.4, 0], (0, 0, sx * 55), "C")
    B.mirrored.append(("MantleFinR", "MantleFinL"))
    B.add("Head", "CoreRoot", "box", [2.5, 1.7, 2.2], [0, -0.5, 0.5], (0, 0, 0), "A")
    B.eyes("Head", 0.1, 1.15, 0.62, 0.85)
    B.add("BeakM", "Head", "wedge", [0.6, 0.6, 0.5], [0, -0.75, 1.05], (-90, 0, 0), "D")
    n = I["traits"].get("tentacles", {}).get("count") or 8
    def suckers(b, base, i, nn):
        par = base
        segs = 4
        for s in range(segs):
            t = s / float(segs)
            par = b.add("Tent%d_s%d" % (i, s), par, "box",
                        [0.62 * taper(t, 0.7) + 0.12, 1.15 - t * 0.35, 0.62 * taper(t, 0.7) + 0.12],
                        [0, -0.95, 0], (16 + s * 9, 0, 0), "A" if s % 2 else "B")
            if s % 2 == 0:
                b.add("Tent%d_suck%d" % (i, s), par, "gem", [0.3 * (1 - t) + 0.12] * 3, [0, -0.2, -0.42], (0, 0, 0), "L")
        b.add("Tent%d_tip" % i, par, "wedge", [0.3, 0.6, 0.3], [0, -0.6, 0], (-90, 0, 0), "C")
    B.ring("Tent", "CoreRoot", n, 1.35, -1.3, "box", [0.7, 0.8, 0.7], "A", child=suckers)
    B.tag("tentacles"); B.count("tentacles", n)
def b_serpent(B, I, rng):
    d = [10] + [rng.choice([-13, 13]) * (1 if i % 2 else -1) for i in range(9)]
    sizes = [[1.5 - i * 0.09, 1.35 - i * 0.08, 1.6] for i in range(10)]
    cols = ["A" if i % 2 else "B" for i in range(10)]
    ns = B.yaw_chain("Seg", None, d, sizes, cols, (0, 1.5, 4.2))
    for i in range(1, 9, 2):
        B.add("Belly%d" % i, ns[i], "box", [sizes[i][0] * 0.8, 0.3, sizes[i][2] * 0.8], [0, -0.75, 0], (0, 0, 0), "L")
    head = B.add("Head", ns[-1], "box", [1.9, 1.5, 2.3], [0, 0.25, -1.3], (0, 0, 0), "A")
    B.add("Snout", head, "wedge", [1.3, 0.9, 1.3], [0, -0.25, -1.5], (-90, 0, 0), "B")
    B.add("Jaw", head, "box", [1.2, 0.35, 1.5], [0, -0.75, -1.2], (0, 0, 0), "D")
    B.eyes(head, 0.45, -1.05, 0.5, 0.72)
    for sx, suf in ((1, "R"), (-1, "L")):
        B.add("HornS" + suf, head, "pyramid", [0.35, 1.5, 0.35], [sx * 0.7, 1.0, 0.5], (sx * -20, 0, 0), "S")
        B.add("FrillS" + suf, head, "wedge", [0.25, 1.2, 1.1], [sx * 0.95, 0.1, 0.4], (0, 0, sx * 70), "C")
    B.mirrored += [("HornSR", "HornSL"), ("FrillSR", "FrillSL")]
    for i in range(0, 8, 2):
        B.add("Dorsal%d" % i, ns[i], "wedge", [0.28, 0.9, 1.0], [0, 0.85, 0], (0, 0, 0), "C")
    B.add("TailFinA", ns[0], "wedge", [1.3, 1.5, 0.28], [0, 0.2, 1.2], (90, 0, 0), "C")
    B.tag("tail"); B.count("tail", 1)
def b_fish(B, I, rng):
    B.add("CoreRoot", None, "box", [2.6, 2.6, 2.4], [0, 2.0, 0], (0, 0, 0), "A")
    B.add("SnoutSec", "CoreRoot", "box", [2.0, 2.0, 1.4], [0, 0.05, -1.6], (0, 0, 0), "A")
    B.add("CaudalSec", "CoreRoot", "box", [1.3, 1.5, 1.4], [0, 0.1, 1.6], (0, 0, 0), "B")
    B.add("Belly", "CoreRoot", "box", [2.1, 1.0, 2.2], [0, -1.35, 0], (0, 0, 0), "L")
    B.add("Lip", "SnoutSec", "wedge", [1.4, 0.5, 0.6], [0, -0.75, -0.8], (-90, 0, 0), "C")
    B.eyes("SnoutSec", 0.5, -0.75, 0.55, 0.8)
    for sx, suf in ((1, "R"), (-1, "L")):
        B.add("Gill%d" % (0 if sx > 0 else 1), "CoreRoot", "box", [0.12, 1.2, 0.7], [sx * 1.32, 0, 0.6], (0, 0, 0), "D")
    n = int(4 + B.sharp * 4)
    for i in range(n):
        a = -65 + i * (130.0 / max(1, n - 1)); r = math.radians(a)
        B.add("Dorsal%d" % i, "CoreRoot", "pyramid", [0.45, rng.uniform(0.9, 1.9) * B.sharp, 0.45],
              [1.45 * math.sin(r), 1.45 * math.cos(r), rng.uniform(-0.9, 0.9)], (0, 0, -a), "S")
    for sx, suf in ((1, "R"), (-1, "L")):
        B.add("Pect" + suf, "CoreRoot", "wedge", [1.5, 1.2, 0.25], [sx * 1.35, -0.5, -0.5], (0, 0, sx * 62), "C")
        B.add("Pelv" + suf, "CoreRoot", "wedge", [1.0, 0.9, 0.22], [sx * 0.8, -1.5, -0.6], (0, 0, sx * 40), "C")
    B.mirrored += [("PectR", "PectL"), ("PelvR", "PelvL")]
    for k, az in ((0, -32), (1, 0), (2, 32)):
        B.add("Caudal%d" % k, "CaudalSec", "wedge", [1.5, 2.0, 0.25], [0, 0.5, 1.0], (0, az, 0), "C")
    B.tag("fins", "tail"); B.count("tail", 1)
def b_bird(B, I, rng):
    B.add("CoreRoot", None, "box", [1.9, 2.1, 2.5], [0, 2.6, 0], (0, 0, 0), "A")
    B.add("Keel", "CoreRoot", "wedge", [1.2, 1.2, 1.8], [0, -1.0, -0.2], (180, 0, 0), "L")
    neck = B.add("Neck", "CoreRoot", "box", [0.9, 1.1, 0.9], [0, 1.3, -0.9], (-18, 0, 0), "B")
    head = B.add("Head", neck, "box", [1.25, 1.25, 1.3], [0, 0.9, -0.2], (12, 0, 0), "A")
    B.eyes(head, 0.15, -0.6, 0.42, 0.5)
    for i in range(5):
        B.add("TailF%d" % i, "CoreRoot", "wedge", [0.7, 1.9 - abs(i - 2) * 0.25, 0.22],
              [(i - 2) * 0.5, -0.3, 1.5], (115, (i - 2) * 14, 0), "C" if i % 2 else "S")
    for sx, suf in ((1, "R"), (-1, "L")):
        sh = B.add("Wing" + suf, "CoreRoot", "box", [1.5, 0.4, 1.1], [sx * 1.15, 0.7, 0], (0, 0, sx * 16), "B")
        md = B.add("Wing%sMid" % suf, sh, "box", [1.4, 0.32, 0.9], [sx * 1.0, 0, 0.05], (0, 0, sx * 12), "A")
        for i in range(5):
            B.add("Wing%sP%d" % (suf, i), md, "wedge", [0.42, 1.5 - i * 0.16, 0.2],
                  [sx * (0.35 + i * 0.3), -0.4, 0.25], (0, 0, sx * (26 + i * 9)), "S" if i % 2 else "C")
    B.mirrored.append(("WingR", "WingL"))
    for sx, suf in ((1, "R"), (-1, "L")):
        f = B.add("Femur" + suf, "CoreRoot", "box", [0.6, 1.2, 0.7], [sx * 0.65, -1.5, 0], (0, 0, 0), "B")
        t = B.add("Tibia" + suf, f, "box", [0.45, 1.2, 0.5], [0, -1.1, 0.1], (0, 0, 0), "D")
        for k in (-1, 0, 1):
            B.add("Tal%s%d" % (suf, k), t, "pyramid", [0.2, 0.6, 0.2], [k * 0.25, -0.7, -0.3], (75, 0, 0), "D")
    B.mirrored.append(("FemurR", "FemurL"))
    B.tag("wings"); B.count("wings", 2)
def b_crab(B, I, rng):
    B.add("CoreRoot", None, "box", [3.4, 1.6, 2.6], [0, 1.9, 0], (0, 0, 0), "A")
    B.add("Dome", "CoreRoot", "box", [2.7, 1.0, 2.1], [0, 1.1, 0], (0, 0, 0), "B")
    B.add("Dome2", "Dome", "box", [1.8, 0.7, 1.4], [0, 0.7, 0], (0, 0, 0), "A")
    for i in range(6):
        x, z = phyllotaxis(i, 6, 1.2)
        B.add("Scute%d" % i, "Dome2", "gem", [0.5, 0.3, 0.5], [x, 0.5, z], (0, 0, 0), "D")
    for sx, suf in ((1, "R"), (-1, "L")):
        st = B.add("Stalk" + suf, "CoreRoot", "box", [0.28, 0.9, 0.28], [sx * 0.8, 1.2, -1.1], (sx * 10, 0, 0), "C")
        B.add("Eye" + suf, st, "gem", [0.5, 0.5, 0.5], [0, 0.6, 0], (0, 0, 0), "C")
        B.add("Pupil" + suf, "Eye" + suf, "gem", [0.22, 0.22, 0.22], [0, 0.1, -0.28], (0, 0, 0), "D")
        m = B.add("Merus" + suf, "CoreRoot", "box", [0.8, 1.5, 0.8], [sx * 2.0, 0.1, -0.9], (sx * 24, 0, 0), "B")
        c = B.add("Carpus" + suf, m, "box", [0.7, 1.2, 0.7], [0, -1.2, -0.3], (-34, 0, 0), "A")
        pr = B.add("Prop" + suf, c, "box", [0.75, 1.5, 0.7], [0, -1.2, -0.2], (-20, 0, 0), "B")
        B.add("Dactyl" + suf, pr, "wedge", [0.5, 1.4, 0.5], [0, -1.3, -0.15], (-26, 0, 0), "S")
        B.add("Pollex" + suf, pr, "wedge", [0.5, 1.1, 0.5], [0, -1.1, 0.3], (22, 0, 0), "S")
    B.mirrored += [("StalkR", "StalkL"), ("MerusR", "MerusL")]
    for i in range(3):
        for sx, suf in ((1, "R"), (-1, "L")):
            l1 = B.add("Walk%d%s" % (i, suf), "CoreRoot", "box", [0.45, 1.5, 0.45],
                       [sx * 1.6, -0.6, 0.7 - i * 0.7], (0, sx * (i - 1) * 26, sx * 34), "B")
            l2 = B.add("Walk%d%s2" % (i, suf), l1, "box", [0.36, 1.4, 0.36], [0, -1.2, 0], (0, 0, -sx * 46), "A")
            B.add("Walk%d%s3" % (i, suf), l2, "pyramid", [0.26, 0.7, 0.26], [0, -1.2, 0], (180, 0, 0), "D")
    B.tag("claws"); B.count("claws", 2)
def b_spider(B, I, rng):
    B.add("CoreRoot", None, "box", [2.0, 1.4, 2.2], [0, 2.2, -0.8], (0, 0, 0), "A")
    ab = B.add("Abdomen", "CoreRoot", "box", [2.2, 1.9, 2.6], [0, 0.5, 2.0], (0, 0, 0), "B")
    for i in range(5):
        x, z = phyllotaxis(i, 5, 0.9)
        B.add("Spot%d" % i, ab, "gem", [0.4, 0.25, 0.4], [x, 1.0, z], (0, 0, 0), "D")
    for sx, suf in ((1, "R"), (-1, "L")):
        B.add("Spin" + suf, ab, "pyramid", [0.22, 0.8, 0.22], [sx * 0.3, -0.4, 1.4], (150, 0, 0), "D")
    hd = B.add("Head", "CoreRoot", "box", [1.4, 1.1, 1.2], [0, -0.1, -1.5], (0, 0, 0), "B")
    for k, (dx, dy) in enumerate(((-0.4, 0.1), (-0.15, 0.25), (0.15, 0.25), (0.4, 0.1))):
        B.add("Eye%d" % k, hd, "gem", [0.26, 0.3, 0.2], [dx * 2, dy, -0.62], (0, 0, 0), "C")
    for sx, suf in ((1, "R"), (-1, "L")):
        ch = B.add("Chel" + suf, hd, "box", [0.4, 0.7, 0.5], [sx * 0.35, -0.6, -0.5], (0, 0, 0), "D")
        B.add("Fang" + suf, ch, "pyramid", [0.2, 0.8, 0.2], [0, -0.6, -0.1], (168, 0, 0), "S")
    B.mirrored.append(("ChelR", "ChelL"))
    for i in range(4):
        for sx, suf in ((1, "R"), (-1, "L")):
            a = (i - 1.5) * 22
            l1 = B.add("Leg%d%s" % (i, suf), "CoreRoot", "box", [0.38, 1.9, 0.38],
                       [sx * 1.0, 0.3, -0.9 + i * 0.62], (0, sx * a, sx * 52), "B")
            B.add("Leg%d%sS" % (i, suf), l1, "pyramid", [0.24, 0.6, 0.24], [0, 0.6, 0], (0, 0, 0), "S")
            l2 = B.add("Leg%d%s2" % (i, suf), l1, "box", [0.32, 1.9, 0.32], [0, -1.7, 0], (0, 0, -sx * 58), "A")
            l3 = B.add("Leg%d%s3" % (i, suf), l2, "box", [0.26, 1.5, 0.26], [0, -1.4, 0], (0, 0, sx * 24), "B")
            B.add("Leg%d%s4" % (i, suf), l3, "pyramid", [0.2, 0.7, 0.2], [0, -1.1, 0], (180, 0, 0), "D")
    B.tag("teeth")
def b_golem(B, I, rng):
    B.add("HumanoidRootPart", None, "gem", [2.6, 3.0, 2.0], [0, 3.2, 0], (0, 0, 0), "A")
    B.add("Core", "HumanoidRootPart", "gem", [1.1, 1.3, 0.9], [0, 0.1, -0.7], (0, 0, 0), "C")
    B.add("Frame", "HumanoidRootPart", "box", [3.0, 1.0, 1.4], [0, 1.2, 0], (0, 0, 0), "B")
    hd = B.add("Head", "HumanoidRootPart", "box", [1.2, 1.1, 1.2], [0, 2.1, 0], (0, 0, 0), "B")
    B.add("Visor", hd, "wedge", [0.9, 0.4, 0.3], [0, 0.1, -0.65], (-90, 0, 0), "C")
    B.add("Brow", hd, "box", [1.3, 0.3, 0.5], [0, 0.55, -0.5], (0, 0, 0), "D")
    for sx, suf in ((1, "R"), (-1, "L")):
        p1 = B.add("Pauldron" + suf, "HumanoidRootPart", "box", [1.3, 0.6, 1.3], [sx * 1.9, 1.5, 0], (0, 0, sx * 8), "B")
        B.add("Pauldron%s2" % suf, p1, "wedge", [1.4, 0.7, 1.4], [0, 0.5, 0], (0, 0, sx * 8), "D")
        a1 = B.add("Arm" + suf, "HumanoidRootPart", "box", [0.9, 2.2, 0.9], [sx * 1.9, 0.2, 0], (0, 0, sx * 6), "A")
        a2 = B.add("Fore" + suf, a1, "box", [0.8, 1.8, 0.8], [0, -1.8, 0], (0, 0, 0), "B")
        B.add("Fist" + suf, a2, "box", [1.1, 1.0, 1.1], [0, -1.4, 0], (0, 0, 0), "D")
        for k in range(3):
            B.add("Knuck%s%d" % (suf, k), "Fist" + suf, "pyramid", [0.22, 0.5, 0.22],
                  [(k - 1) * 0.32, -0.5, -0.5], (75, 0, 0), "S")
        l1 = B.add("Leg" + suf, "HumanoidRootPart", "box", [1.0, 2.2, 1.0], [sx * 0.9, -2.4, 0], (0, 0, 0), "B")
        B.add("Foot" + suf, l1, "wedge", [1.2, 0.7, 1.6], [0, -1.3, -0.3], (0, 0, 0), "D")
    B.mirrored += [("PauldronR", "PauldronL"), ("ArmR", "ArmL"), ("LegR", "LegL")]
    for i in range(4):
        x, z = phyllotaxis(i, 4, 0.8)
        B.add("Crys%d" % i, "HumanoidRootPart", "pyramid", [0.4, 1.6 * B.sharp, 0.4], [x, 1.6, z + 0.8], (-18, 0, 0), "S")
    B.tag("armor", "glow")
def b_humanoid(B, I, rng):
    B.add("HumanoidRootPart", None, "box", [1.9, 2.3, 1.1], [0, 3.3, 0], (0, 0, 0), "A")
    B.add("Chest", "HumanoidRootPart", "box", [2.2, 1.3, 1.2], [0, 1.0, 0], (0, 0, 0), "B")
    B.add("ChestGem", "Chest", "gem", [0.5, 0.6, 0.3], [0, 0.2, -0.65], (0, 0, 0), "C")
    B.add("Belt", "HumanoidRootPart", "box", [2.0, 0.4, 1.2], [0, -1.2, 0], (0, 0, 0), "D")
    B.add("Buckle", "Belt", "box", [0.4, 0.3, 0.2], [0, 0, -0.65], (0, 0, 0), "L")
    hd = B.add("Head", "HumanoidRootPart", "box", [1.15, 1.2, 1.15], [0, 1.85, 0], (0, 0, 0), "C")
    B.add("Jaw", hd, "box", [0.9, 0.4, 0.9], [0, -0.55, -0.1], (0, 0, 0), "D")
    B.eyes(hd, 0.15, -0.6, 0.3, 0.38)
    for sx, suf in ((1, "R"), (-1, "L")):
        p = B.add("Pauldron" + suf, "Chest", "box", [0.95, 0.5, 0.95], [sx * 1.3, 0.75, 0], (0, 0, sx * 10), "B")
        B.add("Pauldron%s2" % suf, p, "wedge", [1.0, 0.5, 1.0], [0, 0.4, 0], (0, 0, sx * 10), "D")
        a1 = B.add("Arm" + suf, "Chest", "box", [0.62, 1.7, 0.62], [sx * 1.35, -0.2, 0], (0, 0, sx * 5), "A")
        a2 = B.add("Fore" + suf, a1, "box", [0.52, 1.5, 0.52], [0, -1.4, 0], (0, 0, 0), "C")
        B.add("Hand" + suf, a2, "box", [0.55, 0.6, 0.55], [0, -1.0, 0], (0, 0, 0), "D")
        l1 = B.add("Leg" + suf, "HumanoidRootPart", "box", [0.75, 1.9, 0.8], [sx * 0.55, -2.2, 0], (0, 0, 0), "A")
        l2 = B.add("Shin" + suf, l1, "box", [0.62, 1.7, 0.66], [0, -1.6, 0], (0, 0, 0), "B")
        B.add("Boot" + suf, l2, "wedge", [0.75, 0.6, 1.3], [0, -1.0, -0.25], (0, 0, 0), "D")
    B.mirrored += [("PauldronR", "PauldronL"), ("ArmR", "ArmL"), ("LegR", "LegL")]
    B.tag("armor")
def b_turtle(B, I, rng):
    B.add("CoreRoot", None, "box", [3.0, 1.2, 3.4], [0, 1.6, 0], (0, 0, 0), "L")
    sh = B.add("ShellBase", "CoreRoot", "box", [3.2, 1.0, 3.6], [0, 0.9, 0], (0, 0, 0), "A")
    s2 = B.add("Shell2", sh, "box", [2.6, 0.9, 3.0], [0, 0.8, 0], (0, 0, 0), "B")
    s3 = B.add("Shell3", s2, "box", [1.8, 0.8, 2.2], [0, 0.7, 0], (0, 0, 0), "A")
    for i in range(7):
        x, z = phyllotaxis(i, 7, 1.1)
        B.add("Scute%d" % i, s2, "gem", [0.6, 0.3, 0.6], [x, 0.6, z], (0, 0, 0), "D")
    if B.sharp > 0.9:
        for i in range(6):
            az = i * 60; a = math.radians(az)
            B.add("RimSpike%d" % i, sh, "pyramid", [0.4, 0.9 * B.sharp, 0.4],
                  [1.7 * math.sin(a), 0.5, 1.9 * math.cos(a)], (0, 0, 0), "S")
    nk = B.add("Neck", "CoreRoot", "box", [0.9, 0.9, 1.0], [0, 0.2, -2.0], (-14, 0, 0), "L")
    hd = B.add("Head", nk, "box", [1.1, 1.0, 1.1], [0, 0.3, -0.8], (10, 0, 0), "L")
    B.eyes(hd, 0.2, -0.55, 0.34, 0.42)
    B.add("BeakT", hd, "wedge", [0.5, 0.4, 0.5], [0, -0.2, -0.65], (-90, 0, 0), "C")
    for i, (sx, sz) in enumerate(((1, -1), (-1, -1), (1, 1), (-1, 1))):
        l1 = B.add("Flip%d" % i, "CoreRoot", "box", [0.9, 0.8, 1.3], [sx * 1.6, -0.5, sz * 1.3],
                   (0, sx * sz * 24, sx * 20), "L")
        B.add("Flip%dC" % i, l1, "pyramid", [0.3, 0.5, 0.3], [0, -0.5, -0.5 * sz], (0, 0, 0), "D")
    tl = B.yaw_chain("Tail", "CoreRoot", [12, 14, 16], [[0.6, 0.6, 0.8], [0.45, 0.45, 0.7], [0.3, 0.3, 0.6]],
                     ["L", "L", "D"], (0, -0.2, 1.9))
    B.tag("shell", "tail"); B.count("tail", 1)
def b_jelly(B, I, rng):
    B.add("CoreRoot", None, "box", [3.0, 1.2, 3.0], [0, 3.0, 0], (0, 0, 0), "A")
    b2 = B.add("Bell2", "CoreRoot", "box", [3.4, 0.9, 3.4], [0, -0.7, 0], (0, 0, 0), "B")
    b3 = B.add("Bell3", b2, "box", [2.6, 0.7, 2.6], [0, 0.8, 0], (0, 0, 0), "A")
    B.add("GlowCore", "CoreRoot", "gem", [1.0, 0.8, 1.0], [0, -0.2, 0], (0, 0, 0), "C")
    for i in range(6):
        x, z = phyllotaxis(i, 6, 1.2)
        B.add("Spot%d" % i, b3, "gem", [0.4, 0.22, 0.4], [x, 0.5, z], (0, 0, 0), "D")
    n = 12
    for i in range(n):
        az = i * 360.0 / n; a = math.radians(az)
        B.add("Skirt%d" % i, b2, "wedge", [0.5, 0.9, 0.16],
              [1.6 * math.sin(a), -0.6, 1.6 * math.cos(a)], (180, az, 0), "L")
    for i in range(4):
        az = i * 90 + 45; a = math.radians(az)
        base = B.add("Oral%d" % i, "CoreRoot", "box", [0.5, 0.9, 0.5],
                     [0.7 * math.sin(a), -1.0, 0.7 * math.cos(a)], (0, az, 0), "L")
        B.pitch_chain("Oral%d_" % i, base, [10, -14, 12, -10],
                      [[0.45, 1.1, 0.3], [0.4, 1.0, 0.26], [0.34, 0.9, 0.22], [0.26, 0.8, 0.18]],
                      ["L", "C", "L", "C"])
    m = 8
    for i in range(m):
        az = i * 360.0 / m; a = math.radians(az)
        base = B.add("Tent%d" % i, b2, "box", [0.22, 0.7, 0.22],
                     [1.5 * math.sin(a), -0.8, 1.5 * math.cos(a)], (0, az, 0), "C")
        B.pitch_chain("Tent%d_" % i, base, [8, 10, 12, 14, 16],
                      [[0.18, 1.2, 0.18], [0.16, 1.1, 0.16], [0.14, 1.0, 0.14], [0.12, 0.9, 0.12], [0.1, 0.8, 0.1]],
                      ["C", "L", "C", "L", "C"])
    B.tag("tentacles", "frill", "glow"); B.count("tentacles", m)
BUILDERS = {"octopus": b_octopus, "serpent": b_serpent, "fish": b_fish, "bird": b_bird, "crab": b_crab,
 "spider": b_spider, "golem": b_golem, "humanoid": b_humanoid, "turtle": b_turtle, "jelly": b_jelly}

# ============================ 8. SELF-CRITIQUE ============================
def critique(spec, intent):
    rep = {}; tot = 0.0; wsum = 0.0
    def add(k, v, w):
        rep[k] = round(v * 100); return v * w
    want = set(intent["traits"]) - intent["neg"]; have = spec.get("traits_present", set())
    hit = len(want & have) / max(1, len(want)) if want else 1.0
    neg_pen = len(intent["neg"] & have) * 0.25
    tot += add("trait_match", max(0, hit - neg_pen), 0.30); wsum += 0.30
    if intent["colors"]:
        ds = []
        for ih, is_, iv in intent["colors"]:
            best = min(hex_hsv(h) for h in spec["palette"].values())
            ds.append(max(0, 1 - hue_dist(ih, best[0]) / 90.0))
        tot += add("color_match", sum(ds) / len(ds), 0.20); wsum += 0.20
    else:
        tot += add("color_match", 0.85, 0.20); wsum += 0.20
    cs = 1.0
    for tr, meta in intent["traits"].items():
        if meta.get("count"):
            got = spec.get("counts", {}).get(tr, 0)
            cs *= 1.0 if got == meta["count"] else 0.55
    tot += add("count_match", cs, 0.12); wsum += 0.12
    mir = spec.get("mirrored", [])
    names = {p["n"] for p in spec["parts"]}
    ok = sum(1 for a, b in mir if a in names and b in names) / max(1, len(mir))
    tot += add("symmetry", ok, 0.10); wsum += 0.10
    n = len(spec["parts"]); budget = 1.0 if 40 <= n <= 240 else (0.7 if 25 <= n <= 320 else 0.4)
    tot += add("complexity", budget, 0.08); wsum += 0.08
    sizes = [p["sz"][0] for p in spec["parts"]]
    var = (max(sizes) - min(sizes)) / max(0.001, max(sizes))
    tot += add("silhouette", clamp(var / 0.8, 0, 1), 0.08); wsum += 0.08
    sh_want = intent["sharp"]; sh_got = spec["sharpness"]
    tot += add("sharp_match", max(0, 1 - abs(sh_want - sh_got) / 2.0), 0.07); wsum += 0.07
    tot += add("scale_match", max(0, 1 - abs(intent["size"] - spec["scale"]) / 0.8), 0.05); wsum += 0.05
    score = int(round(100 * tot / wsum))
    return score, rep
NAME_PRE = ["Brick", "Stud", "Krag", "Zor", "Bloxx", "Torv", "Pixl", "Grim", "Lux", "Vex", "Snap", "Mek",
 "Vor", "Quil", "Rune", "Ember", "Frost", "Thorn", "Gale", "Umber"]
NAME_SUF = {"octopus": "pus", "serpent": "enth", "fish": "ish", "bird": "wing", "crab": "claw",
 "spider": "ling", "golem": "mok", "humanoid": "guard", "turtle": "shell", "jelly": "meduse"}

# ============================ 9. MEMORY LEARNING + BEAM SEARCH ============================
def style_vector(spec):
    hsvs = [hex_hsv(h) for h in spec["palette"].values()]
    return {"sharp": spec["sharpness"], "scale": spec["scale"], "parts": len(spec["parts"]),
            "sat": sum(s for _, s, _ in hsvs) / len(hsvs), "val": sum(v for _, _, v in hsvs) / len(hsvs),
            "arch": spec["archetype"]}
def tokens_of(prompt): return set(tokenize(prompt))
def memory_priors(mem, prompt):
    tk = tokens_of(prompt); acc = Counter(); styles = []; pal = None; bw = 0.0
    for e in mem.get("entries", []):
        et = tokens_of(e.get("prompt", "")); inter = len(tk & et); sim = inter / max(1.0, math.sqrt(len(tk) * max(1, len(et))))
        acc[e.get("archetype", "golem")] += sim
        st = e.get("style")
        if st and sim > 0.15: styles.append((sim, st)); bw += sim
        if sim > 0.3 and e.get("palette"): pal = e["palette"]
    blend = None
    if styles:
        blend = {k: sum(w * s[k] for w, s in styles) / bw for k in ("sharp", "scale", "sat", "val")}
    return acc, blend, pal
def generate(body, mem):
    prompt = body.get("prompt", "creature"); it = int(body.get("iteration", 0))
    nonce = body.get("nonce", "x"); reasons = body.get("reasons", [])
    feat = body.get("features") or {}
    intent = parse_intent(prompt, {})
    mbias, blend, mpal = memory_priors(mem, prompt)
    for a, w in mbias.items(): intent["arch"][a] += w * 1.5
    if feat.get("edges"): intent["sharp"] = clamp(intent["sharp"] + feat["edges"] * 1.2, 0.2, 2.6)
    if blend:
        intent["sharp"] = clamp(intent["sharp"] * 0.7 + blend["sharp"] * 0.3, 0.2, 2.6)
        intent["size"] = intent["size"] * 0.8 + blend["scale"] * 0.2
        intent["sat"] = intent["sat"] * 0.7 + blend["sat"] * 0.3
    if "wrong colors" in reasons and mpal: mpal = None
    if "wrong creature" in reasons and intent["arch"]:
        top = intent["arch"].most_common(1)[0][0]; intent["arch"] = Counter({a: 1 for a in ARCHES if a != top})
    if "too many spikes" in reasons: intent["sharp"] = max(0.2, intent["sharp"] - 1.0)
    if "not enough detail" in reasons: intent["sharp"] = min(2.6, intent["sharp"] + 0.8)
    K = 6 + min(6, it * 2)
    best = None
    for k in range(K):
        seed = zlib.crc32(("%s|%d|%s|%d" % (prompt, it, nonce, k)).encode())
        rng = random.Random(seed)
        if intent["arch"]:
            arch = intent["arch"].most_common(1)[0][0] if k == 0 and rng.random() < 0.8 else \
                   rng.choice(list(intent["arch"]) or ARCHES)
        else:
            arch = rng.choice(ARCHES)
        if "wrong shape" in reasons: arch = ARCHES[(ARCHES.index(arch) + k + 1) % len(ARCHES)]
        variant = (it + k) % 4
        pal, scheme, base_hsv = synthesize_palette(intent, rng, mpal and hex_hsv(mpal["A"]) or None)
        if feat.get("colors") and k == 0:
            fc = feat["colors"]
            pal["A"] = fc[0]; pal["B"] = fc[min(1, len(fc) - 1)]; pal["C"] = fc[min(2, len(fc) - 1)]
            pal["S"] = fc[min(3, len(fc) - 1)]; pal["D"] = hsv_hex(hex_hsv(fc[0])[0], 0.5, 0.2)
            pal["L"] = hsv_hex(hex_hsv(fc[0])[0], 0.15, 0.95)
        B = Builder(seed, pal, rng, intent["sharp"], intent["size"], intent["style"])
        BUILDERS[arch](B, intent, rng)
        for tr, meta in intent["traits"].items():
            if tr in INHERENT.get(arch, set()) or tr in intent["neg"]: continue
            FEATS.get(tr, lambda *a: None)(B, intent, rng, meta.get("count"), meta.get("inten", 1.0))
        spec = {"id": "m%d_%d" % (int(time.time() * 1000) % 100000, k), "name": rng.choice(NAME_PRE) + NAME_SUF[arch],
                "archetype": arch, "variant": variant, "seed": seed, "sharpness": round(B.sharp, 2),
                "scale": round(B.scale, 2), "palette": pal, "tags": sorted(B.present), "root": B.root,
                "parts": B.parts, "mirrored": B.mirrored, "counts": dict(B.counts),
                "traits_present": sorted(B.present),
                "meta": {"iteration": it, "prompt": prompt, "scheme": scheme, "candidate": k}}
        score, rep = critique(spec, intent)
        spec["report"] = rep; spec["score"] = score
        if best is None or score > best["score"]: best = spec
    best["meta"]["beam"] = K
    return best
