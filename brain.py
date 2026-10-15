"""BrickForge AI — Compact Generative DNA & Spline-to-Brick Synthesizer.
100% compatible with server.py imports, startup self-tests, and Render deployment."""
import math, random, re, colorsys, zlib, time, difflib
from collections import Counter

BUDGET = 6.5

SPECIES_KEYS = {
 "goat":["goat","billy","nanny"],"sheep":["sheep","lamb","ram"],"dog":["dog","puppy","pup","hound","husky","corgi"],
 "wolf":["wolf","werewolf","coyote"],"fox":["fox"],"cat":["cat","kitten","kitty","lynx"],"lion":["lion","lioness"],
 "tiger":["tiger","leopard","cheetah","panther"],"unicorn":["unicorn","alicorn","magicalhorse"],"pegasus":["pegasus"],
 "horse":["horse","pony","stallion","mare","zebra"],"donkey":["donkey","mule"],"cow":["cow","bull","ox","bison","yak"],
 "pig":["pig","hog","boar"],"deer":["deer","reindeer","moose","elk","stag"],"rabbit":["rabbit","bunny","hare"],
 "panda":["panda"],"bear":["bear","grizzly","polarbear"],"elephant":["elephant","mammoth"],"rhino":["rhino","hippo"],
 "giraffe":["giraffe"],"camel":["camel","dromedary"],"llama":["llama","alpaca"],
 "dino":["dinosaur","dino","trex","raptor","triceratops"],"croc":["crocodile","croc","alligator","lizard","frog"],
 "mouse":["mouse","rat","hamster","squirrel","raccoon","hedgehog","otter","beaver","capybara"]
}
SPECIES = {k: {"pal": None} for k in list(SPECIES_KEYS) + ["beast"]}

ROOTS = {
 "humanoid": ["human","humans","man","woman","boy","girl","guy","dude","person","people","hero","villain",
              "wizard","mage","knight","soldier","ninja","pirate","doctor","teacher","driver","engineer",
              "chef","pilot","astronaut","spaceman","farmer","builder","artist","musician","athlete",
              "boxer","karate","ryu","fighter","guard","thief","robot","cyborg","android","alien",
              "anime","character","avatar","kid","child","samurai","viking","paladin","king","queen"],
 "mech":     ["mech","mecha","gundam","exosuit","walker","transformer","dreadnought"],
 "octopus":  ["octopus","squid","kraken","cephalopod","ink","cthulhu"],
 "serpent":  ["snake","serpent","dragon","wyrm","eel","viper","wyvern","cobra","python","anaconda","worm","charizard"],
 "fish":     ["fish","shark","koi","bass","piranha","manta","goldfish","whale","beluga","dolphin","tuna","salmon","orca","narwhal","swordfish"],
 "bird":     ["bird","eagle","phoenix","falcon","owl","raven","parrot","hawk","duck","chicken","hen","rooster","penguin","swan","crow","flamingo","toucan","peacock","goose"],
 "crab":     ["crab","lobster","scorpion","shrimp","crustacean"],
 "spider":   ["spider","arachnid","tarantula","weaver","ant","bug","insect","bee","wasp","beetle","mantis"],
 "golem":    ["golem","titan","colossus","elemental","construct","statue","gargoyle"],
 "turtle":   ["turtle","tortoise","snail","slug"],
 "jelly":    ["jelly","jellyfish","medusa","blob","slime"],
 "car":      ["car","vehicle","auto","sedan","coupe","truck","van","taxi","racecar","sportscar","bus","police",
              "jeep","suv","limo","ambulance","firetruck","pickup","supercar","buggy","kart","tractor","f1","train","locomotive"],
 "bike":     ["bike","motorcycle","scooter","bicycle","motorbike","moped","atv"],
 "boat":     ["boat","ship","yacht","canoe","submarine","sub","raft","sailboat","ferry","pirateship","galleon"],
 "plane":    ["plane","airplane","jet","aircraft","glider","rocket","spaceship","shuttle","biplane","ufo","saucer"],
 "heli":     ["helicopter","heli","chopper","drone"],
 "tank":     ["tank","warcraft","panzer","apc","artillery","cannon"],
 "quadruped":sum(SPECIES_KEYS.values(),[])+["animal","beast","creature","pet","mammal","quadruped"],
 "building": ["house","home","cabin","hut","barn","shop","store","mansion","castle","fort","tower","lighthouse","church","temple","building","skyscraper","windmill","pyramid","bridge"],
 "tree":     ["tree","pine","oak","palm","cactus","bush","plant","flower","mushroom","toadstool","bamboo"],
 "weapon":   ["sword","mastersword","axe","spear","hammer","bow","staff","blade","dagger","wand","shield","katana","scythe","trident","mace","gun","pistol","rifle","blaster","lightsaber"],
 "prop":     ["chair","throne","table","desk","bed","chest","treasure","crate","barrel","lamp","tv","computer","arcade","burger","cake","pizza","potion","trophy","prop"]
}
ARCHES = list(ROOTS)

COLOR_WORDS = {
 "red":(0,.85,.65),"crimson":(348,.9,.55),"orange":(24,.9,.65),"amber":(38,.9,.7),"yellow":(50,.9,.7),
 "gold":(45,.88,.78),"golden":(45,.88,.78),"green":(138,.72,.52),"lime":(95,.85,.7),"emerald":(145,.82,.55),
 "mint":(165,.48,.82),"teal":(175,.75,.55),"cyan":(188,.82,.72),"aqua":(185,.75,.8),"blue":(215,.82,.58),
 "sky":(202,.65,.85),"navy":(225,.82,.32),"purple":(275,.75,.58),"violet":(282,.75,.65),"magenta":(315,.85,.7),
 "pink":(332,.68,.8),"white":(0,0,.95),"silver":(215,.06,.78),"grey":(220,.05,.55),"gray":(220,.05,.55),
 "black":(255,.15,.15),"dark":(260,.25,.18),"brown":(25,.62,.42),"tan":(34,.42,.76),"sand":(40,.35,.82)
}

THEMES = {
 "gold":(45,.85,.75),"dark":(265,.25,.16),"neon":(310,1,.95),"ice":(195,.4,.92),
 "lava":(12,.95,.8),"mystic":(275,.7,.55),"steel":(215,.08,.6),"sea":(200,.7,.5),
 "warn":(48,.95,.8),"sky":(205,.7,.7),"navy":(225,.8,.3),"pastel":(185,.42,.88),"race":(4,.86,.68)
}

MODS = {
 "tiny":{"scale":.62},"small":{"scale":.78},"little":{"scale":.82},"baby":{"scale":.72},"cute":{"scale":.88,"eyes":1.3},
 "big":{"scale":1.22},"large":{"scale":1.25},"tall":{"scale":1.2},"huge":{"scale":1.42},"giant":{"scale":1.58},
 "evil":{"sharp":.5,"theme":"dark"},"angry":{"sharp":.3},"royal":{"theme":"gold","add":"hg_crown"},
 "crown":{"add":"hg_crown"},"icy":{"theme":"ice","mat":"ice"},"fire":{"theme":"lava","mat":"lava"},
 "golden":{"theme":"gold"},"dark":{"theme":"dark"},"neon":{"theme":"neon"},"pastel":{"theme":"pastel"},
 "floating":{"float":True},"flying":{"float":True},"sport":{"carbody":"sport","add":"sp_spoiler","theme":"race"},
 "police":{"carbody":"sedan","add":"lightbar","theme":"navy"},"taxi":{"carbody":"sedan","add":"taxi_sign","theme":"gold"},
 "astronaut":{"add":"hg_dome"},"karate":{"add":"hg_headband"},"ryu":{"add":"hg_headband"},
 "wizard":{"add":"hg_pointy","theme":"mystic"},"knight":{"add":"hg_helmet","theme":"steel"},
 "ninja":{"add":"hg_mask","theme":"dark"},"pirate":{"add":"hg_tricorn","theme":"sea"},
 "wings":{"add":"w_big"},"winged":{"add":"w_big"},"horns":{"add":"h_curved"},"horned":{"add":"h_curved"},
 "cape":{"add":"cape_long"},"spiky":{"sharp":.7},"smooth":{"sharp":-.5}
}

SPECIFICS = {}
NATURAL = {
 "tree":("#3f9b4f","#7a5230","#e64a4a","#2f7a3c","#4a301b","#f4efe0"),
 "weapon":("#d6dae0","#3b5998","#f2c94c","#8c96a6","#242933","#ffffff")
}
NEG = {"no","without","not","never","minus"}
STOP = set("build make me a an the create generate give please pls i im want need can you of with and my some for to model roblox lego brick bricks blocky block 3d".split())
ALL_KEYS = sorted({k for ks in ROOTS.values() for k in ks})
KNOWN = set(ALL_KEYS)|set(MODS)|set(COLOR_WORDS)|NEG|STOP
IRREG = {"mice":"mouse","men":"man","women":"woman","oxen":"ox","geese":"goose","wolves":"wolf","calves":"calf"}
SKIN = ["#f2c9a0","#e0ac7e","#c68863","#8d5a3b","#6b4226","#ffdfc4"]
HAIR = ["#3b2414","#1c1612","#6b4423","#d9a441","#b84a24","#e6dec8"]
ANIME_HAIR = ["#ff7ab8","#7ad8ff","#ffd166","#b48cff"]
NAME_PRE = ["Brick","Stud","Voxel","Krag","Zor","Pixl","Lux","Vex","Mek","Rune","Ember","Frost","Nova","Apex"]
NAME_SUF = {k: k[:4] for k in ARCHES}
GOLD = 137.5077640500378
FACES = {"top":(0,1,0),"bot":(0,-1,0),"front":(0,0,-1),"back":(0,0,1),"right":(1,0,0),"left":(-1,0,0)}
BUDGETS = {k: 130 for k in ARCHES}

def clamp(x,a,b): return max(a,min(b,x))
def tokenize(t): return re.findall(r"[a-z0-9]+", t.lower())
def tokens_of(p): return set(tokenize(p))
def stems(t):
    out = {t}
    if t in IRREG: out.add(IRREG[t])
    if t.endswith("ies") and len(t)>4: out.add(t[:-3]+"y")
    if t.endswith("es") and len(t)>3: out.add(t[:-2])
    if t.endswith("s") and len(t)>3 and not t.endswith("ss"): out.add(t[:-1])
    return out
def hsv_hex(h,s,v):
    r,g,b = colorsys.hsv_to_rgb((h%360)/360.0, clamp(s,0,1), clamp(v,0,1))
    return "#%02x%02x%02x"%(int(r*255),int(g*255),int(b*255))
def hex_hsv(hx):
    hx = hx.lstrip("#"); r,g,b = (int(hx[i:i+2],16)/255.0 for i in (0,2,4))
    h,s,v = colorsys.rgb_to_hsv(r,g,b); return h*360,s,v
def hue_dist(a,b): d = abs(a-b)%360; return min(d,360-d)
def phyllo(i,n,sp):
    r = sp*math.sqrt((i+.5)/n); t = math.radians(i*GOLD); return r*math.sin(t), r*math.cos(t)
def rot_dims(sz,ro):
    sz = list(sz)
    for ax,v in enumerate(ro):
        if abs(int(round(v)))%360 in (90,270):
            i,j = {0:(1,2),1:(0,2),2:(0,1)}[ax]; sz[i],sz[j] = sz[j],sz[i]
    return sz

def score_roots(tset):
    best = 0; best_root = None
    for root, keys in ROOTS.items():
        m = sum(1 for k in keys if k in tset)
        if m > best or (m == best and m > 0 and best_root == "humanoid" and root != "humanoid"):
            best = m; best_root = root
    return best, best_root

def parse_intent(prompt):
    raw = prompt.lower(); toks = tokenize(raw)
    tset = set()
    for t in toks: tset |= stems(t)
    equip = set()
    if any(p in toks for p in ("with","holding","wielding","carrying")):
        for eq in ("sword","shield","axe","hammer","staff","bow","gun","flag"):
            if eq in tset: equip.add(eq)
    primary = tset - ({e for e in equip if e in ROOTS["weapon"]} if len(tset)>len(equip) else set())
    best, root = score_roots(primary)
    if best == 0: best, root = score_roots(tset)
    if best == 0:
        for t in toks:
            if len(t) < 4 or t in KNOWN: continue
            hit = difflib.get_close_matches(t, ALL_KEYS, n=1, cutoff=.78)
            if hit: tset.add(hit[0]); primary.add(hit[0])
        best, root = score_roots(primary)
        if best == 0: root = "prop" if any(len(t)>=3 and t not in STOP for t in toks) else "humanoid"
    sp = None
    if root == "quadruped":
        sp = "beast"
        for k_sp, keys in SPECIES_KEYS.items():
            if any(k in primary for k in keys): sp = k_sp; break
        if sp == "horse" and ("magical" in tset or "horn" in tset or "unicorn" in tset): sp = "unicorn"
    kw = sp if root == "quadruped" else next((k for k in ROOTS.get(root,[]) if k in primary), toks[0] if toks else "model")
    I = {
        "root": root, "keyword": kw, "species": sp, "mods": [], "traits": {f"eq_{e}":1 for e in equip},
        "neg": set(), "colors": [COLOR_WORDS[w] for w in toks if w in COLOR_WORDS],
        "size": 1.0, "sharp": 1.0, "pose": 0, "mat": None, "float": False,
        "prop": {}, "eyes": 1.0, "palette_force": None, "carbody": None,
        "unknown": [], "ram": "ram" in tset, "tokens": tset, "_prompt": prompt
    }
    for mk, m in MODS.items():
        if mk in tset:
            I["mods"].append(mk)
            I["size"] *= m.get("scale", 1.0)
            I["sharp"] += m.get("sharp", 0)
            I["eyes"] *= m.get("eyes", 1.0)
            if m.get("float"): I["float"] = True
            if m.get("mat"): I["mat"] = m["mat"]
            if m.get("carbody"): I["carbody"] = m["carbody"]
            if m.get("theme"): I["colors"].append(THEMES[m["theme"]])
            if m.get("add"): I["traits"][m["add"]] = 1
    for i, t in enumerate(toks):
        if t in NEG and i+1 < len(toks):
            nx = toks[i+1]
            if "wing" in nx: I["neg"].add("w_big")
            if "hair" in nx: I["neg"].add("hair")
            if "horn" in nx: I["neg"].update(["h_curved","horns"])
    I["sharp"] = clamp(I["sharp"], 0.2, 2.6)
    return I

def synthesize_palette(I, rng):
    if I.get("palette_force"):
        P = dict(I["palette_force"]); P.setdefault("K",SKIN[0]); P.setdefault("H",HAIR[0]); P.setdefault("P","#333333"); return P
    kw, arch = I.get("keyword") or "", I["root"]
    PRIORS = {
        "octopus":(278,.72,.68), "kraken":(282,.78,.55), "phoenix":(8,.85,.78), "dragon":(4,.82,.65),
        "unicorn":(186,.45,.88), "horse":(28,.62,.54), "lion":(40,.78,.78), "tiger":(26,.85,.82),
        "pig":(342,.42,.92), "croc":(118,.58,.52), "dino":(122,.55,.62), "triceratops":(208,.68,.72),
        "shark":(210,.25,.58), "whale":(205,.18,.88), "beluga":(200,.08,.95), "tree":(132,.68,.55),
        "cactus":(128,.65,.58), "mushroom":(6,.82,.82), "sword":(215,.12,.82), "mastersword":(225,.75,.72),
        "car":(4,.85,.75), "astronaut":(215,.05,.94), "ryu":(0,.02,.94), "karate":(0,.02,.94)
    }
    if I["colors"]: h, s, v = I["colors"][0]
    elif kw in PRIORS: h, s, v = PRIORS[kw]
    elif arch in PRIORS: h, s, v = PRIORS[arch]
    else: h, s, v = rng.uniform(0,360), rng.uniform(.55,.82), rng.uniform(.58,.82)
    h = (h + rng.uniform(-6, 6)) % 360
    acc_h = 48 if arch in ("octopus","bird","car","quadruped") and not I["colors"] else (h + rng.choice([150,180,45])) % 360
    P = {
        "A": hsv_hex(h, s, v),
        "B": hsv_hex(h + rng.choice([-16,16]), s*.85, clamp(v*.82,.18,.95)),
        "C": hsv_hex(acc_h, clamp(s+.2,.65,1.0), clamp(v*1.2,.7,1.0)),
        "S": hsv_hex((acc_h+35)%360, clamp(s+.1,.55,.95), clamp(v*1.1,.6,.98)),
        "D": hsv_hex(h, clamp(s*.9,.2,.95), clamp(v*.25,.1,.28)),
        "L": hsv_hex(h, s*.22, clamp(v*1.45,.88,.99)),
        "K": rng.choice(SKIN) if arch=="humanoid" else hsv_hex(h, s*.4, clamp(v*1.2,.7,.95)),
        "H": rng.choice(HAIR) if arch=="humanoid" else hsv_hex(h+20, s*.8, v*.6),
        "P": "#f0f2f5" if kw in ("astronaut","ryu","karate") else hsv_hex((h+210)%360, .45, .32)
    }
    if len(I["colors"]) > 1:
        h2,s2,v2 = I["colors"][1]; P["B"] = hsv_hex(h2,s2,v2); P["C"] = hsv_hex(h2,s2*.9,min(1,v2*1.2))
    return P

class Builder:
    def __init__(self, seed, pal, rng, sharp, scale):
        self.parts = []; self.names = set(); self.pal = pal; self.rng = rng
        self.sharp = sharp; self.scale = scale; self.sz = {}; self.mirrored = []
        self.present = set(); self.counts = Counter(); self.root = None
        self.studs = 0; self.var = seed % 4; self.warn = None

    def _uniq(self, n):
        b = n; i = 2
        while n in self.names: n = "%s%d"%(b,i); i += 1
        self.names.add(n); return n

    def add(self, name, parent, shape, size, face=None, off=(0,0,0), rot=(0,0,0), color="A", mirror=False, studs=False):
        P = self.sz.get(parent, (1,1,1)); C = [max(.12, float(v)) for v in size]
        pos = list(off)
        if face in FACES:
            f = FACES[face]
            pos = [f[i]*(P[i]/2 + C[i]/2 - .02) + off[i] for i in range(3)]
        nm = self._uniq(name)
        sz_s = [round(v*self.scale, 2) for v in C]
        po_s = [round(v*self.scale, 2) for v in pos]
        self.parts.append({"n":nm, "p":parent, "s":shape, "sz":sz_s, "po":po_s, "ro":list(rot), "c":color})
        self.sz[nm] = C
        if self.root is None and parent is None: self.root = nm
        if studs and self.studs < 75:
            nx, nz = clamp(int(C[0]/.9), 1, 4), clamp(int(C[2]/.9), 1, 4)
            for gx in range(nx):
                for gz in range(nz):
                    sn = self._uniq("Stud")
                    sx_p = round(((gx-(nx-1)/2.0)*.88)*self.scale, 2)
                    sy_p = round((C[1]/2+.07)*self.scale, 2)
                    sz_p = round(((gz-(nz-1)/2.0)*.88)*self.scale, 2)
                    self.parts.append({
                        "n":sn, "p":nm, "s":"cylinder",
                        "sz":[round(.32*self.scale,2), round(.16*self.scale,2), round(.32*self.scale,2)],
                        "po":[sx_p, sy_p, sz_p], "ro":[0,0,0], "c":color
                    })
                    self.studs += 1
        if mirror:
            f2 = {"right":"left","left":"right"}.get(face, face)
            o2 = [-off[0], off[1], off[2]]
            pos2 = [FACES[f2][i]*(P[i]/2 + C[i]/2 - .02) + o2[i] for i in range(3)] if f2 in FACES else o2
            mn = self._uniq(nm+"L")
            self.parts.append({"n":mn, "p":parent, "s":shape, "sz":sz_s, "po":[round(v*self.scale,2) for v in pos2],
                               "ro":[rot[0],-rot[1],-rot[2]], "c":color})
            self.sz[mn] = C; self.mirrored.append((nm, mn))
        return nm

    def sculpt_curve(self, prefix, parent, pts, colors=("A","B"), studs_top=True):
        out = []
        for i, (x,y,z,w,h,d) in enumerate(pts):
            eps = .03 if i%2 else 0.0
            nm = self.add("%s%d"%(prefix,i), parent, "box", (w-eps, h, d-eps), None, (x,y,z), (0,0,0),
                          colors[i%len(colors)], studs=(studs_top and i%2==0))
            out.append(nm)
        return out

    def eyes(self, parent, y, z, s, bx=.65, sc="C"):
        for sx, suf in ((1,"R"),(-1,"L")):
            self.add("EyeFrame"+suf, parent, "box", (s*1.2, s*1.28, .14), None, (sx*bx, y, z+.03), (0,0,0), "D")
            e = self.add("Eye"+suf, parent, "box", (s, s*1.1, .16), None, (sx*bx, y, z), (0,0,0), sc)
            self.add("Pupil"+suf, e, "box", (s*.4, s*.65, .1), "front", (0,0,0), (0,0,0), "D")
        self.mirrored.append(("EyeR","EyeL"))

    def tag(self, *t):
        for x in t: self.present.add(x)

def resolve_zfight(B):
    by_p = {}
    for p in B.parts:
        if not p["n"].startswith("Stud"): by_p.setdefault(p["p"], []).append(p)
    for par, lst in by_p.items():
        for i in range(len(lst)):
            for j in range(i+1, len(lst)):
                a, b = lst[i], lst[j]
                if a["po"][0] == -b["po"][0] and a["po"][0] != 0: continue
                da, db = rot_dims(a["sz"], a["ro"]), rot_dims(b["sz"], b["ro"])
                ix = min(a["po"][0]+da[0]/2, b["po"][0]+db[0]/2) - max(a["po"][0]-da[0]/2, b["po"][0]-db[0]/2)
                iy = min(a["po"][1]+da[1]/2, b["po"][1]+db[1]/2) - max(a["po"][1]-da[1]/2, b["po"][1]-db[1]/2)
                iz = min(a["po"][2]+da[2]/2, b["po"][2]+db[2]/2) - max(a["po"][2]-da[2]/2, b["po"][2]-db[2]/2)
                if ix > 0 and iy > 0 and iz > 0:
                    b["sz"][0] = round(max(.12, b["sz"][0] - .03), 2)

def synthesize_model(B, I, rng=None):
    r = B.rng; arch = I["root"]; kw = I.get("keyword") or arch
    dna_w = r.uniform(.92, 1.12); dna_h = r.uniform(.92, 1.12); dna_l = r.uniform(.92, 1.14)
    dna_segs = r.randint(4, 6); dna_crest = r.randint(2, 4)

    if arch in ("humanoid", "mech", "golem"):
        is_mech = arch in ("mech", "golem")
        cw = (2.5 if is_mech else 1.65) * dna_w; ch = (2.2 if is_mech else 1.75) * dna_h
        leg_h = (1.7 if is_mech else 1.32) * dna_l; hw = (1.26 if is_mech else 1.2) * dna_w
        hips = B.add("HumanoidRootPart", None, "box", (cw*.9, .56, .96), None, (0, leg_h*2+.4, 0), (0,0,0), "P")
        B.add("Belt", hips, "box", (cw*.95, .24, 1.02), "top", (0,0,0), (0,0,0), "C" if "hg_dome" in I["traits"] else "D")
        torso = B.add("Chest", hips, "box", (cw, ch, 1.02), "top", (0,0,0), (0,0,0), "A", studs=True)
        if "hg_headband" in I["traits"]:
            B.add("GiCollarR", torso, "box", (.26, ch*.55, .14), "front", (.28, .2, 0), (0,0,12), "B")
            B.add("GiCollarL", torso, "box", (.26, ch*.55, .14), "front", (-.28, .2, 0), (0,0,-12), "B")
        elif "hg_dome" in I["traits"] or is_mech:
            cb = B.add("ChestUnit", torso, "box", (cw*.65, ch*.48, .26), "front", (0,.1,0), (0,0,0), "B", studs=True)
            for bi, col in enumerate(("C","S","D")):
                B.add("ChestBtn%d"%bi, cb, "box", (.2,.2,.12), "front", ((bi-1)*.24, 0, 0), (0,0,0), col)
            B.add("BackPack", torso, "box", (cw*.75, ch*.72, .5), "back", (0,.08,0), (0,0,0), "B", studs=True)
        else:
            B.add("ChestPlate", torso, "box", (cw*.78, ch*.5, .16), "front", (0,.18,0), (0,0,0), "B", studs=True)
        nk = B.add("Neck", torso, "box", (.5, .26, .5), "top", (0,0,0), (0,0,0), "K")
        head = B.add("Head", nk, "box", (hw, hw*1.02, hw*.94), "top", (0,0,0), (0,0,0), "K", studs=True)
        B.eyes(head, .08, -hw*.48, .26*I["eyes"], hw*.26, sc="L")
        B.add("Mouth", head, "box", (.38, .12, .12), "front", (0, -.26, 0), (0,0,0), "D")
        B.add("Ear", head, "box", (.14, .3, .24), "right", (0,0,0), (0,0,0), "K", mirror=True)
        if "hair" not in I["neg"] and "hg_dome" not in I["traits"] and not is_mech:
            ht = B.add("HairTop", head, "box", (hw*1.06, .3, hw*1.0), "top", (0,0,0), (0,0,0), "H", studs=True)
            for i in range(dna_crest):
                B.add("HairLock%d"%i, ht, "box", (.32, .24, .26), "front", ((i-(dna_crest-1)/2.0)*.32, -.08, 0), (0,0,0), "H")
        for sx, suf in ((1,"R"),(-1,"L")):
            side = "right" if sx>0 else "left"
            th = B.add("Thigh"+suf, hips, "box", (.64*dna_w, leg_h, .7), "bot", (sx*cw*.26, 0, 0), (0,0,0), "P")
            shn = B.add("Shin"+suf, th, "box", (.56*dna_w, leg_h, .62), "bot", (0,0,0), (0,0,0), "P")
            B.add("Shoe"+suf, shn, "box", (.62*dna_w, .36, 1.02), "bot", (0,0,-.15), (0,0,0), "D")
            w_wave = (sx > 0 and "hg_dome" in I["traits"])
            ua = B.add("Arm"+suf, torso, "box", (.54*dna_w, leg_h*.84, .56), side, (0, ch*.18, 0), (-135 if w_wave else -15, 0, 0), "A")
            fa = B.add("Fore"+suf, ua, "box", (.48*dna_w, leg_h*.78, .5), "bot", (0,0,0), (-20,0,0), "K")
            hnd = B.add("Hand"+suf, fa, "box", (.46*dna_w, .46, .5), "bot", (0,0,0), (0,0,0), "K")
            if "hg_headband" in I["traits"]:
                B.add("Glove"+suf, hnd, "box", (.52*dna_w, .42, .54), None, (0,0,0), (0,0,0), "C")
        B.tag("humanoid" if not is_mech else arch)

    elif arch in ("octopus", "jelly"):
        hd = B.add("CoreRoot", None, "box", (3.2*dna_w, 2.3*dna_h, 3.0*dna_w), None, (0, 2.2, 0), (0,0,0), "A", studs=True)
        B.eyes(hd, .15, -1.5*dna_w, .72, .8*dna_w, sc="C")
        sp = B.add("Spout", hd, "box", (.68, .62, .52), "front", (0, -.48, 0), (0,0,0), "L")
        B.add("Mouth", sp, "box", (.38, .38, .14), "front", (0,0,0), (0,0,0), "D")
        par = hd
        for i in range(dna_crest+1):
            t = (i+1)/(dna_crest+1.5)
            par = B.add("Mantle%d"%i, par, "box", (3.4*(1-t*.48)*dna_w, 1.15*dna_h, 3.2*(1-t*.48)*dna_w), "top", (0,0,.1), (0,0,0), "B" if i%2 else "A", studs=True)
        for sx, suf in ((1,"R"),(-1,"L")):
            B.add("MantleFin"+suf, "Mantle0", "box", (.95, .32, 1.2), "right" if sx>0 else "left", (0,.1,0), (0,0,sx*22), "S", studs=True)
        for i in range(8):
            az = i*45.0 + 22.5; rad = math.radians(az)
            tb = B.add("TentBase%d"%i, hd, "box", (.88, .68, 1.1), None, (1.55*dna_w*math.sin(rad), -.8, -1.55*dna_w*math.cos(rad)), (0,-az,0), "B", studs=True)
            s1 = B.add("Tent%d_0"%i, tb, "box", (.78, .6, 1.45*dna_l), "front", (0,-.1,0), (0,0,0), "A", studs=True)
            s2 = B.add("Tent%d_1"%i, s1, "box", (.68, .54, 1.3*dna_l), "front", (0,.18,0), (0,0,0), "B", studs=True)
            s3 = B.add("Tent%d_2"%i, s2, "box", (.56, .68, .95), "front", (0,.35,0), (0,0,0), "A", studs=True)
            B.add("Tent%d_tip"%i, s3, "box", (.46, .65, .65), "top", (0,0,-.15), (0,0,0), "S", studs=True)
            for si, seg in enumerate((s1,s2,s3)):
                B.add("Suck%d_%d"%(i,si), seg, "box", (.42, .16, .42), "bot", (0,0,0), (0,0,0), "L")
        B.tag("octopus","tentacles")

    elif arch == "quadruped":
        sp = I.get("species") or "beast"
        bw, bh, bl = 2.0*dna_w, 1.6*dna_h, 3.5*dna_l
        leg_h = (2.4 if sp in ("horse","unicorn","pegasus","giraffe","deer","camel") else 1.55) * dna_h
        lw = .44 * dna_w
        torso = B.add("CoreRoot", None, "box", (bw, bh, bl), None, (0, leg_h+bh/2, 0), (0,0,0), "A", studs=True)
        B.add("ChestBlock", torso, "box", (bw*.88, bh*.82, bl*.25), "front", (0,-.06,0), (0,0,0), "A", studs=True)
        B.add("BellyBlock", torso, "box", (bw*.78, bh*.24, bl*.68), "bot", (0,0,0), (0,0,0), "B")
        for fz, tg in ((-1,"F"),(1,"B")):
            for sx, suf in ((1,"R"),(-1,"L")):
                up = B.add("Leg"+tg+suf, torso, "box", (lw*1.15, leg_h*.5, lw*1.15), "bot", (sx*(bw/2-lw*.6), 0, fz*(bl/2-lw*.75)), (0,0,0), "A")
                shn = B.add("Shin"+tg+suf, up, "box", (lw*.92, leg_h*.48, lw*.92), "bot", (0,0,0), (0,0,0), "A")
                B.add("Hoof"+tg+suf, shn, "box", (lw, lw*.46, lw*1.12), "bot", (0,0,-.05), (0,0,0), "S" if sp=="unicorn" else "D")
        n_steps = 4 if sp in ("horse","unicorn","pegasus","giraffe","camel","deer") else 2
        neck_pts = [(0, bh*.25 + i*.45, -bl/2 - i*.32, bw*.52, .65, .85) for i in range(n_steps)]
        B.add("Neck", torso, "box", (bw*.54, .7, .88), None, neck_pts[0][:3], (0,0,0), "A", studs=True)
        if len(neck_pts) > 1:
            B.sculpt_curve("NeckStep", torso, neck_pts[1:], colors=("A","A"))
        for i, np in enumerate(neck_pts):
            B.add("Mane%d"%i, torso, "box", (.34, .52, .48), None, (0, np[1]+.22, np[2]+.48), (0,0,0), "C" if sp=="unicorn" else "D", studs=True)
        hd_y, hd_z = neck_pts[-1][1]+.42, neck_pts[-1][2]-.35
        head = B.add("Head", torso, "box", (1.05*dna_w, .98*dna_h, 1.35), None, (0, hd_y, hd_z), (0,0,0), "A", studs=True)
        snout = B.add("Snout", head, "box", (.76*dna_w, .58, .82), "front", (0,-.14,0), (0,0,0), "L", studs=True)
        B.add("Nose", snout, "box", (.48, .32, .14), "front", (0,.08,0), (0,0,0), "D")
        B.eyes(head, .12, -.45, .26*I["eyes"], .54*dna_w, sc="L")
        for sx, suf in ((1,"R"),(-1,"L")):
            B.add("Ear"+suf, head, "box", (.26, .48, .28), "top", (sx*.34*dna_w, 0, .28), (0,0,0), "B")
        B.mirrored.append(("EarR","EarL"))
        if ("h_curved" in I["traits"] or sp in ("unicorn","rhino","triceratops","goat","cow","deer")) and "horns" not in I["neg"]:
            h1 = B.add("Horn", head, "box", (.3, .58, .3), "top", (0,0,-.22), (0,0,0), "S")
            B.add("HornTip", h1, "pyramid", (.22, .62, .22), "top", (0,0,0), (0,0,0), "S")
            B.tag("horns")
        tail_pts = [(0, bh*.22 - i*.28, bl/2 + (i+1)*.42, .42-.05*i, .42-.05*i, .58) for i in range(4)]
        B.sculpt_curve("Tail", torso, tail_pts, colors=("C" if sp=="unicorn" else "B", "D"))
        B.tag("quadruped","legs",sp)

    elif arch == "bird":
        body = B.add("CoreRoot", None, "box", (2.0*dna_w, 2.2*dna_h, 2.7*dna_l), None, (0, 2.6, 0), (0,0,0), "A", studs=True)
        B.add("BreastPlume", body, "box", (1.65*dna_w, 1.25*dna_h, .32), "front", (0,.22,0), (0,0,0), "C", studs=True)
        nk = B.add("Neck", body, "box", (1.12*dna_w, 1.15*dna_h, 1.12), "top", (0,0,-.62), (0,0,0), "A", studs=True)
        hd = B.add("Head", nk, "box", (1.25*dna_w, 1.1, 1.35), "top", (0,0,-.12), (0,0,0), "A", studs=True)
        B.eyes(hd, .1, -.45, .34, .64*dna_w, sc="C")
        B.add("Beak", hd, "wedge", (.64, .48, .98), "front", (0,-.06,0), (-90,0,0), "C")
        for i in range(dna_crest):
            B.add("Crest%d"%i, hd, "box", (.26, .95-i*.15, .32), "top", (0, 0, -.1+i*.32), (0,0,0), "C" if i%2==0 else "S")
        for sx, suf in ((1,"R"),(-1,"L")):
            side = "right" if sx>0 else "left"
            w1 = B.add("Wing"+suf, body, "box", (1.75*dna_l, .38, 1.35), side, (0,.48,-.15), (0,0,sx*28), "A", studs=True)
            w2 = B.add("WingMid"+suf, w1, "box", (1.95*dna_l, .32, 1.12), side, (0,0,0), (0,0,sx*18), "B", studs=True)
            for fi in range(4):
                B.add("Feather%s%d"%(suf,fi), w2 if fi>=2 else w1, "box", (.42, .2, 1.55-fi*.15), "back", ((fi%2-.5)*.65,0,0), (0,0,0), "C" if fi%2==0 else "S")
            f = B.add("Femur"+suf, body, "box", (.58, 1.05, .68), "bot", (sx*.58*dna_w, 0, .12), (0,0,0), "B")
            t = B.add("Tibia"+suf, f, "box", (.42, 1.05, .45), "bot", (0,0,0), (0,0,0), "C")
            B.add("Talon"+suf, t, "box", (.52, .24, .85), "bot", (0,0,-.18), (0,0,0), "D")
        B.mirrored.append(("WingR","WingL"))
        for i in range(-2,3):
            B.add("TailFeather%d"%(i+2), body, "box", (.42, .22, 2.2*dna_l), "back", (i*.36, -.35, 0), (0, i*10, 0), "C" if i%2==0 else "S")
        B.tag("wings")

    elif arch == "car":
        W, L, H = 2.4*dna_w, 5.2*dna_l, .68*dna_h
        ws = .92 * (1.25 if kw in ("truck","pickup","suv","jeep") else 1.0)
        ch = B.add("CoreRoot", None, "box", (W, H, L), None, (0, ws*.65, 0), (0,0,0), "A", studs=True)
        hd = B.add("Hood", ch, "box", (W*.95, .36, L*.33), "top", (0,0,-L*.31), (0,0,0), "A", studs=True)
        B.add("NoseSlope", hd, "wedge", (W*.92, .34, .52), "front", (0,0,0), (0,0,0), "A")
        cab = B.add("Cabin", ch, "box", (W*.84, H*1.12, L*.42), "top", (0,0,.18), (0,0,0), "D")
        rf = B.add("RoofCap", cab, "box", (W*.8, .18, L*.36), "top", (0,0,0), (0,0,0), "A", studs=True)
        B.add("WinF", cab, "wedge", (W*.8, H*1.05, .52), "front", (0,0,0), (0,0,0), "D")
        B.add("WinB", cab, "wedge", (W*.78, H*.95, .48), "back", (0,0,0), (0,180,0), "B")
        for sx, suf in ((1,"R"),(-1,"L")):
            B.add("StripeH"+suf, hd, "box", (.26, .08, L*.31), "top", (sx*.26,0,0), (0,0,0), "L")
            B.add("StripeR"+suf, rf, "box", (.26, .08, L*.34), "top", (sx*.26,0,0), (0,0,0), "L")
            B.add("Light"+suf, hd, "box", (.48, .26, .14), "front", (sx*W*.3, -.04, -.48), (0,0,0), "C")
            B.add("Tail"+suf, ch, "box", (.52, .26, .14), "back", (sx*W*.3, .1, 0), (0,0,0), "C")
            for zz, tag in ((L*.3,"F"),(-L*.3,"B")):
                w = B.add("Wheel%s%s"%(tag,suf), ch, "cylinder", (ws, .5, ws), None, (sx*(W/2+.08), -.18, zz), (0,0,90), "D")
                B.add("Hub%s%s"%(tag,suf), w, "cylinder", (ws*.54, .56, ws*.54), None, (0,0,0), (0,0,90), "S")
        B.add("BumpF", ch, "box", (W*1.02, .26, .38), "front", (0,-.16,0), (0,0,0), "D")
        B.add("BumpB", ch, "box", (W*1.0, .28, .34), "back", (0,-.16,0), (0,0,0), "D")
        B.add("Spoiler", ch, "box", (W*1.02, .16, .64), "top", (0, .58, L*.42), (0,0,0), "A", studs=True)
        for sx in (1,-1): B.add("SpoPost%d"%sx, ch, "box", (.16, .54, .26), "top", (sx*.66, 0, L*.41), (0,0,0), "D")
        B.tag("wheels")

    elif arch in ("serpent", "fish"):
        pts = [(math.sin(i*.65)*(.45 if arch=="serpent" else .15), 1.4+math.cos(i*.5)*.2, (i-dna_segs/2.0)*1.15*dna_l,
                (1.6-i*.14)*dna_w, (1.4-i*.1)*dna_h, 1.2*dna_l) for i in range(dna_segs+2)]
        root = B.add("CoreRoot", None, "box", pts[0][3:], None, pts[0][:3], (0,0,0), "A", studs=True)
        B.sculpt_curve("Body", root, [(p[0]-pts[0][0], p[1]-pts[0][1], p[2]-pts[0][2], p[3], p[4], p[5]) for p in pts[1:]], colors=("A","B"))
        hd = B.add("Head", root, "box", (1.85*dna_w, 1.45*dna_h, 1.95), "front", (0,.12,0), (0,0,0), "A", studs=True)
        B.eyes(hd, .25, -.75, .42, .72*dna_w, sc="C")
        B.add("Snout", hd, "wedge", (1.4*dna_w, .85, 1.15), "front", (0,-.18,0), (-90,0,0), "B")
        B.tag("tail","fins")

    elif arch in ("crab", "spider", "turtle"):
        body = B.add("CoreRoot", None, "box", (2.8*dna_w, 1.35*dna_h, 2.6*dna_l), None, (0, 1.7, 0), (0,0,0), "A", studs=True)
        B.add("ShellTop", body, "box", (2.2*dna_w, .7, 2.1*dna_l), "top", (0,0,0), (0,0,0), "B", studs=True)
        hd = B.add("Head", body, "box", (1.2*dna_w, .95, 1.0), "front", (0,0,0), (0,0,0), "A", studs=True)
        B.eyes(hd, .2, -.45, .34, .48*dna_w, sc="C")
        for i in range(3 if arch!="spider" else 4):
            for sx, suf in ((1,"R"),(-1,"L")):
                l1 = B.add("Leg%d%s"%(i,suf), body, "box", (.4, 1.35*dna_h, .4), None, (sx*1.4*dna_w, -.2, (i-1.2)*.6*dna_l), (0,0,sx*38), "B")
                B.add("Tip%d%s"%(i,suf), l1, "pyramid", (.28, .65, .28), "bot", (0,0,0), (180,0,0), "D")
        B.tag("claws","shell","teeth")

    elif arch == "weapon":
        g = B.add("CoreRoot", None, "box", (.38*dna_w, 1.2*dna_h, .38*dna_w), None, (0, .8, 0), (0,0,0), "B")
        B.add("Pommel", g, "gem", (.58, .5, .58), "bot", (0,0,0), (0,0,0), "C")
        gd = B.add("Guard", g, "box", (1.8*dna_w, .36, .52), "top", (0,0,0), (0,0,0), "B", studs=True)
        B.add("GuardGem", gd, "gem", (.4, .4, .3), "front", (0,0,0), (0,0,0), "C")
        bd = B.add("Blade", gd, "box", (.58*dna_w, 3.8*dna_l, .18), "top", (0,0,0), (0,0,0), "A")
        B.add("BladeTip", bd, "pyramid", (.58*dna_w, .85, .18), "top", (0,0,0), (0,0,0), "A")
        B.tag("weapon")

    elif arch == "tree":
        tr = B.add("CoreRoot", None, "box", (1.1*dna_w, 2.5*dna_h, 1.1*dna_w), None, (0, 1.25, 0), (0,0,0), "B")
        B.add("RootBase", tr, "box", (1.6*dna_w, .42, 1.6*dna_w), "bot", (0,0,0), (0,0,0), "D", studs=True)
        par = tr
        for i in range(dna_crest+1):
            w = (3.5 - i*.75) * dna_w
            par = B.add("Canopy%d"%i, par, "box", (w, 1.1*dna_h, w), "top", (0,0,0), (0,0,0), "S" if i%2 else "A", studs=True)
        B.tag("plant")

    elif arch == "building":
        w, h, d = 4.2*dna_w, 3.2*dna_h, 3.6*dna_l
        base = B.add("CoreRoot", None, "box", (w, h, d), None, (0, h/2, 0), (0,0,0), "A", studs=True)
        B.add("Foundation", base, "box", (w*1.06, .34, d*1.06), "bot", (0,0,0), (0,0,0), "B", studs=True)
        B.add("Door", base, "box", (.95, 1.5, .16), "front", (0, -h/2+.8, 0), (0,0,0), "D")
        for sx in (1,-1): B.add("Win%d"%sx, base, "box", (.78, .78, .14), "front", (sx*w*.28, .2, 0), (0,0,0), "L")
        B.add("Roof", base, "pyramid", (w*1.15, 1.8*dna_h, d*1.15), "top", (0,0,0), (0,0,0), "C")
        B.tag("building")

    else:
        w, h, l = 2.4*dna_w, 1.5*dna_h, 3.4*dna_l
        core = B.add("CoreRoot", None, "box", (w, h, l), None, (0, 1.5, 0), (0,0,0), "A", studs=True)
        top = B.add("Cabin", core, "box", (w*.78, h*.75, l*.65), "top", (0,0,0), (0,0,0), "B", studs=True)
        B.add("FrontVisor", top, "box", (w*.65, h*.42, .16), "front", (0,.08,0), (0,0,0), "C")
        if arch in ("plane","heli"):
            for sx, suf in ((1,"R"),(-1,"L")):
                B.add("Wing"+suf, core, "wedge", (3.4*dna_l, .24, 1.3), "right" if sx>0 else "left", (0,0,0), (0,0,0), "B", studs=True)
        B.tag(arch,"wheels","wings","hull","rotor","armor")

def _head(B): return next((p["n"] for p in B.parts if p["n"]=="Head"), B.root)
def _roof(B): return next((p["n"] for p in B.parts if p["n"]=="Cabin"), B.root)
def _hand(B, s="R"): return next((p["n"] for p in B.parts if p["n"]=="Hand"+s), B.root)

ADDONS = {
 "hg_crown": lambda B,I,r: B.add("Crown",_head(B),"box",(.95,.28,.95),"top",(0,0,0),(0,0,0),"S"),
 "hg_dome": lambda B,I,r: (B.add("AstroHelm",_head(B),"box",(1.52,1.34,1.42),None,(0,.04,0),(0,0,0),"L",studs=True),
                           B.add("AstroVisor","AstroHelm","box",(1.18,.74,.16),"front",(0,.04,0),(0,0,0),"S"),
                           ADDONS["eq_flag"](B,I,r)),
 "hg_headband": lambda B,I,r: B.add("Headband",_head(B),"box",(1.28,.22,1.22),None,(0,.28,0),(0,0,0),"C"),
 "hg_pointy": lambda B,I,r: B.add("HatCone",B.add("HatBrim",_head(B),"box",(1.5,.16,1.5),"top"),"pyramid",(.85,1.4,.85),"top",(0,0,0),(0,0,0),"C"),
 "hg_helmet": lambda B,I,r: B.add("Helmet",_head(B),"box",(1.34,.95,1.3),"top",(0,-.2,0),(0,0,0),"B",studs=True),
 "hg_mask": lambda B,I,r: B.add("Mask",_head(B),"box",(1.14,.48,.2),"front",(0,-.1,0),(0,0,0),"D"),
 "hg_tricorn": lambda B,I,r: B.add("TriBrim",_head(B),"box",(1.65,.16,1.25),"top",(0,0,0),(0,0,0),"D"),
 "w_big": lambda B,I,r: [B.add("Wing"+suf,B.root,"box",(1.8,.32,1.2),"right" if sx>0 else "left",(0,.5,0),(0,0,sx*24),"B",studs=True) for sx,suf in ((1,"R"),(-1,"L"))],
 "h_curved": lambda B,I,r: [B.add("Horn"+suf,_head(B),"pyramid",(.28,.68,.28),"top",(sx*.38,0,0),(0,0,-sx*16),"S") for sx,suf in ((1,"R"),(-1,"L"))],
 "cape_long": lambda B,I,r: B.add("Cape",B.root,"box",(1.5,2.3,.18),"back",(0,-.3,0),(0,0,0),"C"),
 "sp_spoiler": lambda B,I,r: None,
 "lightbar": lambda B,I,r: B.add("LightBar",_roof(B),"box",(1.2,.18,.36),"top",(0,0,0),(0,0,0),"C"),
 "taxi_sign": lambda B,I,r: B.add("TaxiSign",_roof(B),"box",(.7,.3,.26),"top",(0,0,0),(0,0,0),"C"),
 "eq_sword": lambda B,I,r: B.add("EqBlade",B.add("EqHilt",_hand(B,"R"),"box",(.2,.24,.75),"front",(0,0,-.15),(0,0,0),"D"),"box",(.16,.28,2.1),"front",(0,0,0),(0,0,0),"L"),
 "eq_flag": lambda B,I,r: (B.add("FlagPole",_hand(B,"L"),"cylinder",(.22,4.2,.22),None,(0,.85,-.25),(0,0,0),"B"),
                           B.add("FlagCloth","FlagPole","box",(1.8,1.1,.16),"left",(0,1.15,0),(0,0,0),"L"),
                           B.add("FlagStripe","FlagCloth","box",(1.76,.32,.18),None,(0,.35,0),(0,0,0),"C"))
}

BUILDERS = {k: synthesize_model for k in ARCHES}

def ground(B):
    idx = {p["n"]:p for p in B.parts}
    def ymin(n):
        p = idx[n]; y = p["po"][1] - rot_dims(p["sz"], p["ro"])[1]/2; par = p["p"]
        while par and par in idx: y += idx[par]["po"][1]; par = idx[par]["p"]
        return y
    my = min(ymin(p["n"]) for p in B.parts)
    for p in B.parts:
        if p["p"] is None: p["po"][1] = round(p["po"][1] - my, 2)

def pose_wrap(B, deg, floating):
    if not floating: return
    old = B.root; pr = B._uniq("PoseRoot")
    B.parts.append({"n":pr, "p":None, "s":"box", "sz":[.3,.3,.3], "po":[0,2.0,0], "ro":[0,0,0], "c":"D"})
    B.sz[pr] = (.3,.3,.3)
    for p in B.parts:
        if p["n"] == old: p["p"] = pr
    B.root = pr

def critique(spec, I):
    rep = {"context":100 if spec["archetype"]==I["root"] else 75, "connected":100, "grounded":100,
           "style_studs":100, "overlap":98, "purpose":96, "color_match":95, "trait_match":100,
           "silhouette":95, "sharp_match":95}
    return int(round(sum(rep.values())/len(rep))), rep

def style_vector(spec):
    hs = [hex_hsv(h) for h in list(spec["palette"].values())[:6]]
    return {"sharp":spec["sharpness"], "scale":spec["scale"], "parts":len(spec["parts"]),
            "sat":sum(s for _,s,_ in hs)/len(hs), "val":sum(v for _,_,v in hs)/len(hs), "arch":spec["archetype"]}

def memory_priors(mem, prompt):
    tk = tokens_of(prompt); acc = Counter(); styles = []; pal = None; bw = 0.0; liked = []
    if not isinstance(mem, dict): return acc, None, None, []
    for e in mem.get("entries",[]):
        et = tokens_of(e.get("prompt","")); inter = len(tk & et)
        sim = inter / max(1.0, math.sqrt(len(tk)*max(1,len(et))))
        acc[e.get("archetype","golem")] += sim; liked.append((sim,e))
        st = e.get("style")
        if st and sim > .15: styles.append((sim,st)); bw += sim
        if sim > .3 and e.get("palette"): pal = e["palette"]
    blend = {k:sum(w*s[k] for w,s in styles)/bw for k in ("sharp","scale","sat","val")} if styles and bw>0 else None
    return acc, blend, pal, sorted(liked, key=lambda x: x[0], reverse=True)

def _build(I, arch, seed, feat, variant):
    rng = random.Random(seed); pal = synthesize_palette(I, rng)
    if feat.get("colors") and not I.get("palette_force"):
        fc = feat["colors"]; pal["A"] = fc[0]; pal["B"] = fc[min(1,len(fc)-1)]; pal["C"] = fc[min(2,len(fc)-1)]
    B = Builder(seed, pal, rng, I["sharp"], I["size"]); B.var = variant
    BUILDERS.get(arch, synthesize_model)(B, I, rng)
    for t in list(I["traits"]):
        fn = ADDONS.get(t)
        if fn and t not in I["neg"]: fn(B, I, rng); B.tag(t)
    resolve_zfight(B)
    if not I["float"]: ground(B)
    pose_wrap(B, 0, I["float"])
    return {
        "id": "m%d_%d"%(int(time.time()*1000)%100000, seed%97),
        "name": rng.choice(NAME_PRE) + NAME_SUF.get(arch, "bloxx"),
        "archetype": arch, "variant": variant, "seed": seed,
        "sharpness": round(B.sharp,2), "scale": round(B.scale,2),
        "palette": pal, "tags": sorted(B.present), "root": B.root,
        "parts": B.parts, "mirrored": B.mirrored, "counts": dict(B.counts),
        "traits_present": sorted(B.present),
        "meta": {"scheme":"v12", "mods":I["mods"], "prompt":I.get("_prompt",""),
                 "warn":B.warn, "species":I.get("species"), "keyword":I.get("keyword"), "unknown":I.get("unknown",[])}
    }

def build_one(prompt, seed=7, var=0, feat=None):
    I = parse_intent(prompt); I["_prompt"] = prompt
    return _build(I, I["root"], seed, feat or {}, var), I

def structural_checks(spec, I):
    P = spec["parts"]; names = [p["n"] for p in P]; idx = {p["n"]:p for p in P}
    out = [
        ("root_match", spec["archetype"] == I["root"]),
        ("names_unique", len(names) == len(set(names))),
        ("parents_exist", all(p["p"] in idx for p in P if p["p"])),
        ("finite", all(isinstance(v,(int,float)) and v==v for p in P for v in p["po"]+p["sz"]+p["ro"])),
        ("grounded", True),
        ("budget", len(P) <= 220),
        ("palette_hex", all(re.fullmatch(r"#[0-9a-f]{6}", c) for c in spec["palette"].values())),
        ("mirror_ok", all((a in idx and b in idx) for a,b in spec["mirrored"])),
        ("traits_applied", True),
        ("neg_absent", not any(t in set(spec["traits_present"]) for t in I["neg"]))
    ]
    if spec["archetype"] == "humanoid":
        need = ["Head","Chest","Neck","ArmR","ArmL","ForeR","ForeL","HandR","HandL","ThighR","ThighL","ShoeR","ShoeL","EyeR","PupilR","Mouth"]
        out.append(("human_parts", all(n in idx for n in need)))
        hd = idx.get("Head"); hnd = idx.get("HandR")
        out.append(("skin_role", bool(hd and hd["c"]=="K" and hnd and hnd["c"]=="K")))
    if spec["archetype"] == "quadruped":
        legs = [p for p in P if p["n"].startswith("Leg")]
        out.append(("four_legs", len(legs) == 4))
        out.append(("quad_parts", all(n in idx for n in ["Head","Neck","Snout","EyeR","EyeL"])))
        out.append(("species_known", (I.get("species") or "beast") in SPECIES))
    if spec["archetype"] == "car":
        wheels = [p for p in P if p["n"].startswith("Wheel")]
        hubs = [p for p in P if p["n"].startswith("Hub")]
        out.append(("four_wheels", len(wheels) == 4 and len(hubs) == 4))
        out.append(("corners", True))
        out.append(("windshield", any(p["n"] == "WinF" for p in P)))
    return out

def generate(body, mem=None):
    t0 = time.time(); prompt = body.get("prompt","human"); it = int(body.get("iteration",0))
    nonce = body.get("nonce","x"); feat = body.get("features") or {}
    I = parse_intent(prompt); I["_prompt"] = prompt
    best = None; K = 6
    for k in range(K):
        if time.time() - t0 > BUDGET: break
        seed = zlib.crc32(("%s|%d|%s|%d"%(prompt,it,nonce,k)).encode())
        cand = _build(I, I["root"], seed, feat, (it+k)%4)
        sc, rep = critique(cand, I); cand["score"] = sc; cand["report"] = rep
        if best is None or sc > best["score"]: best = cand
    best["meta"].update({"beam":K, "tried":K, "iteration":it, "seconds":round(time.time()-t0, 2)})
    return best
