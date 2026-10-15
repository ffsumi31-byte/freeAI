"""BrickForge AI v8 — fail-safe build pipeline.
v8: NEW quadruped archetype (goat, dog, horse, cow, pig, elephant, giraffe, ... 25 species),
    NEW building / tree / weapon archetypes, plural + typo tolerant parsing,
    unknown nouns become a generic block "prop" mascot instead of silently turning into a human.
v7.1: root tie-break, partial-build resilience, guaranteed fallback spec.
v7: skin/shirt/pants roles, human proportions, 5 car bodies, test API."""
import math, random, re, colorsys, zlib, time, difflib
from collections import Counter
BUDGET = 7.0

# ---------------------------------------------------------------- species (quadrupeds)
# palette order: A body, B legs/ears/secondary, C accent, S horns/special, D hooves/dark, L light/muzzle
_Q = dict(bw=1.9,bh=1.5,bl=3.0,leg=1.6,lw=.4,neck=.9,nang=40,head=(1.0,1.0,1.2),snout=(.6,.5,.6),
          ears="point",ear=(.3,.5),horns=None,tail="short",size=1.0,headc="A",snoutc="L",extras=(),
          pal=("#b98d5e","#8b6a43","#e8c547","#d9cbb0","#3b2a1c","#efe4cf"))
def _sp(**k):
    d = dict(_Q); d.update(k); return d
SPECIES = {
 "goat":    _sp(bh=1.4,leg=1.7,lw=.34,neck=1.1,nang=35,head=(.9,1.0,1.15),snout=(.55,.5,.55),ears="side",
                ear=(.45,.55),horns="curved",tail="short",extras=("beard",),
                pal=("#e6e0d2","#a89c86","#e8c547","#5a4a3a","#2d241c","#fbf8f0")),
 "sheep":   _sp(leg=1.3,lw=.36,neck=.7,nang=25,head=(.9,.95,1.0),snout=(.55,.5,.5),ears="side",ear=(.4,.45),
                headc="B",extras=("wool",),pal=("#f1eee6","#3d3a38","#e8c547","#8a7f70","#2a2624","#ffffff")),
 "dog":     _sp(bh=1.3,bl=2.7,leg=1.3,lw=.36,neck=.6,nang=30,head=(.95,.9,1.0),snout=(.55,.45,.8),ears="floppy",
                ear=(.5,.8),tail="long_up",pal=("#c89a62","#8f6a3e","#e8c547","#d8b98a","#2b1d12","#f3e6cf")),
 "wolf":    _sp(bh=1.4,bl=3.0,leg=1.7,lw=.36,neck=.7,nang=32,head=(.95,.9,1.1),snout=(.5,.45,.9),ears="point",
                ear=(.3,.6),tail="bushy",pal=("#8e949c","#5d636b","#e8c547","#c9ced4","#22262b","#e9edf0")),
 "fox":     _sp(bh=1.2,bl=2.6,leg=1.3,lw=.3,neck=.6,nang=30,head=(.9,.85,1.0),snout=(.5,.4,.9),ears="point",
                ear=(.42,.8),tail="bushy",pal=("#d9742b","#a9511a","#2b2118","#f3e9dc","#2a1a10","#fbf5ec")),
 "cat":     _sp(bw=1.6,bh=1.1,bl=2.4,leg=1.0,lw=.3,neck=.5,nang=30,head=(1.0,.9,.9),snout=(.4,.3,.3),ears="point",
                ear=(.35,.5),tail="long_up",pal=("#9a9aa2","#6e6e78","#7cd67c","#e0d0c0","#2a2a30","#f2f2f4")),
 "lion":    _sp(bw=2.0,bh=1.7,bl=3.3,leg=1.7,lw=.5,neck=.6,nang=25,head=(1.1,1.0,1.1),snout=(.55,.45,.5),ears="round",
                ear=(.4,.4),tail="tuft",extras=("mane",),pal=("#d9a441","#b5802a","#e8c547","#6b3f1d","#3b2410","#f0d9a8")),
 "tiger":   _sp(bw=1.9,bh=1.5,bl=3.3,leg=1.5,lw=.48,neck=.6,nang=28,head=(1.05,.95,1.05),snout=(.55,.45,.5),ears="round",
                ear=(.38,.38),tail="hang",extras=("stripes",),pal=("#e08a2c","#b8661a","#e8c547","#f5e6c8","#1f140c","#fbf3e2")),
 "horse":   _sp(bw=1.8,bh=1.6,bl=3.6,leg=2.8,lw=.34,neck=2.0,nang=35,head=(.8,.9,1.5),snout=(.7,.6,.6),ears="point",
                ear=(.22,.45),tail="hang",extras=("hmane",),snoutc="B",pal=("#8a5a35","#5e3b1f","#e8c547","#2a1a10","#1f130a","#e9d9c0")),
 "unicorn": _sp(bw=1.8,bh=1.6,bl=3.4,leg=2.7,lw=.32,neck=2.0,nang=35,head=(.8,.9,1.4),snout=(.7,.6,.6),ears="point",
                ear=(.22,.45),horns="straight",tail="hang",extras=("hmane",),
                pal=("#f7f3fb","#d9c9f0","#ff8fc8","#ffd86b","#8b6bbf","#ffffff")),
 "donkey":  _sp(bh=1.4,bl=3.0,leg=1.8,lw=.34,neck=1.0,nang=35,head=(.85,.95,1.3),snout=(.65,.55,.55),ears="long",
                ear=(.3,1.1),tail="tuft",pal=("#8b8f96","#5f6368","#e8c547","#cfd3d8","#2b2d30","#f0f0f0")),
 "cow":     _sp(bw=2.1,bh=1.7,bl=3.3,leg=1.5,lw=.46,neck=.7,nang=25,head=(1.0,1.0,1.1),snout=(.7,.5,.4),ears="side",
                ear=(.5,.5),horns="bull",tail="tuft",extras=("spots",),
                pal=("#f4f1ea","#d9d4c8","#e8c547","#e8dcc0","#1f1f1f","#f5b8c4")),
 "pig":     _sp(bw=2.1,bh=1.7,bl=3.0,leg=.9,lw=.5,neck=.5,nang=20,head=(1.1,1.0,1.0),snout=(.6,.5,.35),ears="floppy",
                ear=(.45,.5),tail="curly",pal=("#f2a6b8","#e08aa0","#2b1d12","#f9c9d4","#3d2a30","#f9c9d4")),
 "deer":    _sp(bw=1.7,bh=1.5,bl=3.0,leg=2.5,lw=.3,neck=1.6,nang=30,head=(.8,.85,1.2),snout=(.55,.5,.55),ears="point",
                ear=(.3,.6),horns="antlers",tail="short",pal=("#b07a45","#8b5c2e","#e8c547","#e2d2b0","#2b1a0e","#f3e7d0")),
 "rabbit":  _sp(bw=1.7,bh=1.5,bl=2.2,leg=.9,lw=.4,neck=.4,nang=20,head=(1.1,1.0,1.1),snout=(.45,.35,.3),ears="long",
                ear=(.28,1.5),tail="ball",pal=("#e9e2d6","#cfc4b2","#ff9fb3","#f7f1e8","#3a2e24","#ffffff")),
 "bear":    _sp(bw=2.4,bh=2.2,bl=3.2,leg=1.3,lw=.75,neck=.5,nang=15,head=(1.4,1.3,1.3),snout=(.5,.4,.5),ears="round",
                ear=(.4,.4),tail="short",pal=("#6b4423","#4a2f1b","#e8c547","#d9c2a0","#1c120a","#c9a47a")),
 "panda":   _sp(bw=2.4,bh=2.2,bl=3.0,leg=1.3,lw=.75,neck=.5,nang=15,head=(1.4,1.3,1.3),snout=(.5,.4,.5),ears="round",
                ear=(.4,.4),tail="short",extras=("patches",),pal=("#f4f4f4","#1c1c1c","#e8c547","#cfcfcf","#111111","#ffffff")),
 "elephant":_sp(bw=3.0,bh=2.8,bl=4.0,leg=2.4,lw=1.0,neck=.5,nang=10,head=(1.8,1.9,1.5),snout=(.35,.35,.2),ears="flap",
                ear=(1.4,1.8),tail="short",extras=("trunk","tusks"),snoutc="A",
                pal=("#8e949c","#757b83","#e8c547","#f2ecdc","#3b3f45","#b8bec6")),
 "giraffe": _sp(bw=1.9,bh=1.7,bl=3.0,leg=3.8,lw=.38,neck=3.8,nang=12,head=(.9,.9,1.3),snout=(.6,.5,.6),ears="point",
                ear=(.3,.45),horns="knobs",tail="tuft",extras=("spots",),
                pal=("#e0b04a","#c98f2e","#e8c547","#8a5a1a","#6b3f12","#f6e3b0")),
 "camel":   _sp(bw=1.9,bh=1.7,bl=3.4,leg=2.6,lw=.4,neck=2.0,nang=35,head=(.9,.9,1.2),snout=(.6,.5,.6),ears="round",
                ear=(.25,.25),tail="short",extras=("hump",),pal=("#c9a06a","#a47c48","#e8c547","#e0c9a0","#3b2a18","#ecd9b8")),
 "llama":   _sp(bh=1.6,bl=2.8,leg=2.2,lw=.34,neck=2.2,nang=22,head=(.8,.9,1.0),snout=(.6,.5,.5),ears="point",
                ear=(.25,.6),tail="short",extras=("wool",),pal=("#efe6d6","#c9bba4","#e8c547","#a58f6e","#4a3b2a","#ffffff")),
 "dino":    _sp(bh=1.9,bl=3.6,leg=1.6,lw=.65,neck=.9,nang=25,head=(1.3,1.2,2.0),snout=(.9,.6,.5),ears="none",
                tail="croc",extras=("plates",),pal=("#5aa05a","#3f7a3f","#f2c94c","#e7d9a6","#243b24","#b9dca0")),
 "croc":    _sp(bh=.9,bl=3.8,leg=.6,lw=.5,neck=.3,nang=10,head=(1.2,.8,1.8),snout=(.9,.6,.6),ears="none",
                tail="croc",extras=("plates",),pal=("#4f8f4a","#3a6e36","#f2c94c","#cfd8a0","#1e3a1c","#d8e3a8")),
 "mouse":   _sp(size=.7,bw=1.8,bh=1.3,bl=2.4,leg=.8,lw=.35,neck=.3,nang=20,head=(1.1,1.0,1.2),snout=(.4,.35,.4),
                ears="round",ear=(.8,.8),tail="long_thin",pal=("#a9a9b0","#f4b9c2","#2b2b30","#85858c","#2b2b30","#ece9e4")),
 "beast":   _sp(pal=None,horns=None,ears="point",tail="short"),
}
SPECIES_KEYS = {
 "goat":["goat","billy","nanny"],"sheep":["sheep","lamb","ram"],
 "dog":["dog","puppy","pup","hound","doggo","husky","corgi"],"wolf":["wolf","werewolf","coyote"],
 "fox":["fox"],"cat":["cat","kitten","kitty","lynx"],"lion":["lion","lioness"],
 "tiger":["tiger","leopard","cheetah","panther"],"unicorn":["unicorn"],
 "horse":["horse","pony","stallion","mare","foal"],"donkey":["donkey","mule"],
 "cow":["cow","cattle","bull","ox","buffalo","bison","yak"],"pig":["pig","hog","boar","piglet"],
 "deer":["deer","reindeer","moose","elk","stag","antelope"],"rabbit":["rabbit","bunny","hare"],
 "panda":["panda"],"bear":["bear","grizzly"],"elephant":["elephant","mammoth"],"giraffe":["giraffe"],
 "camel":["camel","dromedary"],"llama":["llama","alpaca"],
 "dino":["dinosaur","dino","trex","raptor","triceratops"],
 "croc":["crocodile","croc","alligator","lizard","gecko","iguana","komodo"],
 "mouse":["mouse","rat","hamster","gerbil"]}

ROOTS = {
 "humanoid": ["human","humans","man","woman","boy","girl","guy","dude","person","people","hero",
    "villain","wizard","mage","knight","soldier","ninja","pirate","doctor","teacher","driver",
    "engineer","chef","pilot","astronaut","farmer","builder","artist","musician","athlete",
    "boxer","karate","fighter","guard","thief","robot","cyborg","android","mech","alien",
    "anime","character","avatar","kid","child"],
 "octopus": ["octopus","squid","kraken","cephalopod","ink"],
 "serpent": ["snake","serpent","dragon","wyrm","eel","viper","wyvern","cobra","python","anaconda","worm","caterpillar"],
 "fish": ["fish","shark","koi","bass","piranha","manta","goldfish","whale","dolphin","tuna","salmon",
    "trout","carp","clownfish","swordfish","stingray","orca"],
 "bird": ["bird","eagle","phoenix","falcon","owl","raven","parrot","hawk","duck","chicken","hen","rooster",
    "penguin","swan","crow","pigeon","seagull","flamingo","toucan","ostrich","peacock","goose"],
 "crab": ["crab","lobster","scorpion","shrimp","crustacean"],
 "spider": ["spider","arachnid","tarantula","weaver","ant","bug","insect","bee","wasp","mosquito"],
 "golem": ["golem","titan","colossus","elemental","construct","statue","gargoyle"],
 "turtle": ["turtle","tortoise","snail","slug"],
 "jelly": ["jelly","jellyfish","medusa","blob","slime"],
 "car": ["car","vehicle","auto","sedan","coupe","truck","van","taxi","racecar","bus","police","jeep","suv",
    "limo","ambulance","firetruck","pickup","supercar","hatchback","wagon","minivan","lorry"],
 "bike": ["bike","motorcycle","scooter","bicycle","motorbike","moped"],
 "boat": ["boat","ship","yacht","canoe","submarine","sub","raft","sailboat","ferry"],
 "plane": ["plane","airplane","jet","aircraft","glider","rocket","spaceship","shuttle"],
 "heli": ["helicopter","heli","chopper"],
 "tank": ["tank","warcraft"],
 "quadruped": sum(SPECIES_KEYS.values(),[])+["animal","beast","creature","pet","mammal","quadruped"],
 "building": ["house","home","cabin","hut","barn","shop","store","mansion","castle","fort","tower",
    "lighthouse","church","temple","building"],
 "tree": ["tree","pine","oak","palm","cactus","bush","plant","flower","mushroom"],
 "weapon": ["sword","axe","spear","hammer","bow","staff","blade","dagger","wand","shield"]}
ARCHES = list(ROOTS)
MODS = {
 "bald":{"rm":["hair"]},"muscular":{"prop":{"chest":1.3,"arms":1.25}},
 "fat":{"prop":{"chest":1.35,"limbs":1.15}},"skinny":{"prop":{"chest":.8,"limbs":.8}},
 "cute":{"prop":{"head":1.3,"limbs":.8},"sharp":-0.6,"scale":0.85,"eyes":1.4},
 "tall":{"prop":{"limbs":1.3},"scale":1.15},"tiny":{"scale":0.6},"huge":{"scale":1.5},
 "giant":{"scale":1.65},"big":{"scale":1.25},"small":{"scale":.75},"little":{"scale":.8},
 "baby":{"scale":.7,"prop":{"head":1.2},"eyes":1.3},
 "evil":{"sharp":0.6,"theme":"dark","add":"brow_evil","pose":-8},"angry":{"add":"brow_evil"},
 "royal":{"theme":"gold","add":"hg_crown"},"crown":{"add":"hg_crown"},"icy":{"theme":"ice","mat":"ice","add":"hg_crystal"},
 "fire":{"theme":"lava","mat":"lava"},"golden":{"theme":"gold"},"dark":{"theme":"dark"},
 "neon":{"theme":"neon"},"pastel":{"theme":"pastel"},"floating":{"float":True,"pose":-6},
 "sport":{"carbody":"sport","add":"sp_spoiler","theme":"neon"},
 "offroad":{"prop":{"wheels":1.5,"lift":1.3}},
 "taxi":{"carbody":"sedan","add":"taxi_sign","theme":"gold"},
 "police":{"carbody":"sedan","add":"lightbar","theme":"navy"},
 "van":{"carbody":"van"},"bus":{"carbody":"van"},"buggy":{"carbody":"buggy"},
 "beetle":{"carbody":"buggy"},"monster":{"carbody":"pickup","prop":{"wheels":1.6,"lift":1.4}},
 "anime":{"eyes":1.5,"add":"hair_spiky"},
 "karate":{"add":"hg_headband","pose":-12},"wizard":{"add":"hg_pointy","theme":"mystic"},
 "knight":{"add":"hg_helmet","theme":"steel"},"ninja":{"add":"hg_mask","theme":"dark"},
 "pirate":{"add":"hg_tricorn","theme":"sea"},"chef":{"add":"hg_toque"},
 "driver":{"add":"hg_cap","theme":"race"},"engineer":{"add":"hg_hardhat","theme":"warn"},
 "pilot":{"add":"hg_cap","theme":"sky"},"astronaut":{"add":"hg_dome"},
 "doctor":{"add":"hg_cap"},"teacher":{"add":"hg_glasses"},
 "glasses":{"add":"hg_glasses"},"sunglasses":{"add":"hg_glasses"},"helmet":{"add":"hg_helmet"},
 "hat":{"add":"hg_cap"},"mask":{"add":"hg_mask"},
 "wings":{"add":"w_big"},"winged":{"add":"w_big"},"horns":{"add":"h_curved"},"horned":{"add":"h_curved"},
 "cape":{"add":"cape_long"},
 "spiky":{"sharp":0.9},"smooth":{"sharp":-0.6}}
THEMES = {"gold":(45,.85,.75),"dark":(265,.25,.16),"neon":(310,1,.95),"ice":(195,.4,.92),
 "lava":(12,.95,.8),"mystic":(275,.7,.55),"steel":(215,.08,.6),"sea":(200,.7,.5),
 "warn":(48,.95,.8),"sky":(205,.7,.7),"navy":(225,.8,.3),"pastel":(330,.35,.85),"race":(0,.85,.6)}
SPECIFICS = {}
NATURAL = {
 "tree":("#3f9b4f","#7a5230","#e64a4a","#2f7a3c","#4a301b","#f4efe0"),
 "weapon":("#a9adb5","#7a4f2a","#4a8fe0","#d4a640","#3a2a1c","#e6e9ee")}
COLOR_WORDS = {"red":(0,.85,.62),"crimson":(348,.9,.55),"orange":(24,.9,.62),"yellow":(52,.9,.65),
 "gold":(45,.85,.72),"green":(140,.7,.5),"teal":(172,.75,.5),"cyan":(185,.85,.65),"blue":(215,.8,.55),
 "navy":(225,.8,.3),"purple":(275,.7,.55),"pink":(330,.7,.75),"white":(0,0,.96),"black":(260,.2,.14),
 "grey":(220,.05,.55),"gray":(220,.05,.55),"brown":(25,.6,.42),"mint":(160,.45,.8)}
NEG = {"no","without","not","never","minus"}
STOP = set("""build make me a an the create generate give please pls i im want need can you of with and my some
for to model roblox lego brick bricks blocky block 3d one new cool nice awesome simple it its that this like
lets let draw design looking looks look who is are be as in on at from so very really just also something
thing object toy cartoon style version""".split())
ALL_KEYS = sorted({k for ks in ROOTS.values() for k in ks})
KNOWN = set(ALL_KEYS)|set(MODS)|set(COLOR_WORDS)|NEG|STOP
IRREG = {"mice":"mouse","men":"man","women":"woman","oxen":"ox","geese":"goose","wolves":"wolf","calves":"calf"}
SKIN = ["#f2c9a0","#e0ac7e","#c68863","#8d5a3b","#6b4226","#ffdfc4"]
HAIR = ["#2b1d12","#4a2f1b","#6b4423","#141414","#d9a441","#c2652e","#8a8a8a","#f2e2c4"]
ANIME_HAIR = ["#ff7ab8","#7ad8ff","#ffd166","#b48cff"]
NAME_PRE = ["Brick","Stud","Krag","Zor","Bloxx","Torv","Pixl","Grim","Lux","Vex","Snap","Mek",
 "Vor","Quil","Rune","Ember","Frost","Thorn","Gale","Umber"]
NAME_SUF = {"octopus":"pus","serpent":"enth","fish":"ish","bird":"wing","crab":"claw","spider":"ling",
 "golem":"mok","humanoid":"guard","turtle":"shell","jelly":"meduse","car":"runner","bike":"cycle",
 "boat":"wave","plane":"wing","heli":"rotor","tank":"tread","quadruped":"hoof","building":"stead",
 "tree":"bark","weapon":"edge","prop":"bloxx"}
def tokenize(t): return re.findall(r"[a-z]+", t.lower())
def stems(t):
    out = {t}
    if t in IRREG: out.add(IRREG[t])
    if t.endswith("ies") and len(t) > 4: out.add(t[:-3]+"y")
    if t.endswith("ves") and len(t) > 4: out.add(t[:-3]+"f"); out.add(t[:-3]+"fe")
    if t.endswith("es") and len(t) > 3: out.add(t[:-2])
    if t.endswith("s") and len(t) > 3 and not t.endswith("ss"): out.add(t[:-1])
    return out
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
    I = {"root":None,"mods":[],"traits":{},"neg":set(),"colors":[],"size":1.0,"sharp":1.0,
         "pose":0,"mat":None,"float":False,"prop":{},"eyes":1.0,"palette_force":None,"var":None,
         "carbody":None,"species":None,"keyword":None,"unknown":[],"ram":False,"tokens":set(tset)}
    for phrase,cfg in SPECIFICS.items():
        if phrase in raw:
            I.update({k:v for k,v in cfg.items() if k!="palette"})
            I["palette_force"]=cfg.get("palette"); I["root"]=cfg.get("root",I["root"]); return I
    best, root = score_roots(tset)
    if best == 0:
        for t in toks:
            if len(t) < 4 or t in KNOWN or (stems(t) & KNOWN): continue
            hit = [k for k in ALL_KEYS if len(k) == len(t) and sorted(k) == sorted(t)]
            if not hit: hit = difflib.get_close_matches(t, ALL_KEYS, n=1, cutoff=.8)
            if hit: tset.add(hit[0])
        best, root = score_roots(tset)
        if best == 0:
            unk = [t for t in toks if len(t) >= 3 and t not in KNOWN and not (stems(t) & KNOWN)]
            if unk: root = "prop"; I["unknown"] = unk; I["keyword"] = unk[0]
            else: root = "humanoid"
    I["root"] = root
    I["tokens"] = set(tset)
    if root == "quadruped":
        I["species"] = "beast"
        for sp, keys in SPECIES_KEYS.items():
            if any(k in tset for k in keys): I["species"] = sp; break
        I["ram"] = "ram" in tset; I["keyword"] = I["species"]
    elif root != "prop":
        I["keyword"] = next((k for k in ROOTS[root] if k in tset), None)
    for mk in MODS:
        if mk in tset: I["mods"].append(mk)
    for mk in I["mods"]:
        m=MODS[mk]; I["prop"].update(m.get("prop",{}))
        for t in m.get("rm",[]): I["neg"].add(t)
        I["sharp"]+=m.get("sharp",0); I["size"]*=m.get("scale",1.0); I["pose"]+=m.get("pose",0)
        if m.get("float"): I["float"]=True
        if m.get("mat"): I["mat"]=m["mat"]
        if m.get("carbody"): I["carbody"]=m["carbody"]
        if m.get("theme"): I["colors"].append(THEMES[m["theme"]])
        if m.get("eyes"): I["eyes"]*=m["eyes"]
        if m.get("add"): I["traits"][m["add"]]=1
    for i,t in enumerate(toks):
        if t in NEG and i+1<len(toks):
            nx=toks[i+1]
            if "wing" in nx: I["neg"].add("w_big")
            if "hair" in nx: I["neg"].add("hair")
            if "horn" in nx: I["neg"].update(["h_curved","horns"])
    for w,h in COLOR_WORDS.items():
        if w in tset: I["colors"].append(h)
    I["sharp"]=max(0.2,min(2.6,I["sharp"]))
    return I
def clamp(x,a,b): return max(a,min(b,x))
def hsv_hex(h,s,v):
    h%=360; r,g,b=colorsys.hsv_to_rgb(h/360.0,clamp(s,0,1),clamp(v,0,1))
    return "#%02x%02x%02x"%(int(r*255),int(g*255),int(b*255))
def hex_hsv(hx):
    hx=hx.lstrip("#"); r,g,b=(int(hx[i:i+2],16)/255.0 for i in (0,2,4))
    h,s,v=colorsys.rgb_to_hsv(r,g,b); return h*360,s,v
def hue_dist(a,b): d=abs(a-b)%360; return min(d,360-d)
GOLD=137.5077640500378
def phyllo(i,n,sp):
    r=sp*math.sqrt((i+.5)/n); t=math.radians(i*GOLD); return r*math.sin(t),r*math.cos(t)
def rot_dims(sz,ro):
    sz=list(sz)
    for ax,v in enumerate(ro):
        a=abs(int(round(v)))%360
        if a in (90,270):
            i,j={0:(1,2),1:(0,2),2:(0,1)}[ax]; sz[i],sz[j]=sz[j],sz[i]
    return sz
def synthesize_palette(I,rng):
    if I["palette_force"]:
        P=dict(I["palette_force"]); P.setdefault("K",SKIN[0]); P.setdefault("H",HAIR[0])
        P.setdefault("P",P.get("D","#333333")); return P
    if not I["colors"] and not I["mat"]:
        sp = SPECIES.get(I.get("species")) if I["root"]=="quadruped" else None
        pal = (sp or {}).get("pal") or NATURAL.get(I["root"])
        if pal:
            P=dict(zip("ABCSDL",pal)); P["K"]=pal[0]; P["H"]=pal[1]; P["P"]=pal[4]; return P
    if I["colors"]: h,s,v=I["colors"][0]
    else: h,s,v=(rng.choice([0,25,45,140,175,205,250,285,320]),.65,.6)
    if I["mat"]=="metal": s,v=.15,.75
    if I["mat"]=="ice": h,s,v=195,.4,.93
    if I["mat"]=="lava": h,s,v=12,.95,.8
    off=rng.choice([180,28,120,150])
    P={"A":hsv_hex(h,s*.85,v),"B":hsv_hex(h+rng.choice([-25,25]),s*.7,min(1,v*1.2)),
       "C":hsv_hex(h+off,max(.5,s),min(1,v*1.35)),"S":hsv_hex(h+off+rng.choice([-30,30]),max(.45,s*.9),min(1,v*1.1)),
       "D":hsv_hex(h,min(1,s*1.05),max(.1,v*.4)),"L":hsv_hex(h+15,max(.06,s*.35),min(1,v*1.55))}
    if I["root"]=="humanoid":
        if I["mat"]=="metal" or "robot" in I["mods"] or "cyborg" in I["tokens"]: P["K"]=hsv_hex(h,.15,.75)
        elif "alien" in I["mods"]: P["K"]=hsv_hex(140,.5,.7)
        else: P["K"]=rng.choice(SKIN)
        P["H"]=rng.choice(ANIME_HAIR) if "anime" in I["mods"] else rng.choice(HAIR)
        P["P"]=hsv_hex(h,min(1,s*.6),max(.15,v*.45))
    else: P["K"]=P["A"]; P["H"]=P["B"]; P["P"]=P["D"]
    return P
FACES={"top":(0,1,0),"bot":(0,-1,0),"front":(0,0,-1),"back":(0,0,1),"right":(1,0,0),"left":(-1,0,0)}
class Builder:
    def __init__(self,seed,pal,rng,sharp,scale):
        self.parts=[];self.names=set();self.pal=pal;self.rng=rng;self.sharp=sharp;self.scale=scale
        self.sz={};self.mirrored=[];self.present=set();self.counts=Counter();self.root=None
        self.studs=0;self.var=seed%4;self.warn=None
    def _uniq(self,n):
        b=n;i=2
        while n in self.names: n="%s%d"%(b,i);i+=1
        self.names.add(n);return n
    def _emit(self,name,parent,shape,size,pos,rot,color):
        axes=[i for i,v in enumerate(rot) if v]
        sz=[round(v*self.scale,2) for v in size]; po=[round(v*self.scale,2) for v in pos]
        if len(axes)<=1:
            self.parts.append({"n":name,"p":parent,"s":shape,"sz":sz,"po":po,"ro":list(rot),"c":color});return name
        par=parent;p0=po
        for k,ax in enumerate(axes[:-1]):
            cn=self._uniq(name+"_j%d"%k); r=[0,0,0];r[ax]=rot[ax]
            self.parts.append({"n":cn,"p":par,"s":"box","sz":[round(.3*self.scale,2)]*3,"po":p0,"ro":r,"c":"D"})
            par=cn;p0=[0,0,0]
        r=[0,0,0];r[axes[-1]]=rot[axes[-1]]
        self.parts.append({"n":name,"p":par,"s":shape,"sz":sz,"po":p0,"ro":r,"c":color});return name
    def add(self,name,parent,shape,size,face=None,off=(0,0,0),rot=(0,0,0),color="A",mirror=False,studs=False):
        P=self.sz.get(parent,(1,1,1)); C=size; e=.15*min(C); pos=list(off)
        if face:
            f=FACES[face]
            base=[f[0]*(P[0]/2+C[0]/2-e) if f[0] else 0,f[1]*(P[1]/2+C[1]/2-e) if f[1] else 0,
                  f[2]*(P[2]/2+C[2]/2-e) if f[2] else 0]
            pos=[base[i]+off[i] for i in range(3)]
        name=self._uniq(name); self._emit(name,parent,shape,size,pos,rot,color); self.sz[name]=size
        if studs and self.studs<90:
            nx=clamp(int(size[0]/.95),1,4); nz=clamp(int(size[2]/.95),1,4)
            for gx in range(nx):
                for gz in range(nz):
                    self._emit(self._uniq("Stud"),name,"cylinder",(.34,.2,.34),
                               [(gx-(nx-1)/2.0)*.95,size[1]/2+.06,(gz-(nz-1)/2.0)*.95],(0,0,0),color)
                    self.studs+=1
        if mirror:
            f2={"right":"left","left":"right"}.get(face,face)
            o2=list(off); o2[0]=-o2[0]; pos2=list(o2)
            if f2:
                f=FACES[f2]; e2=.15*min(C)
                base=[f[0]*(P[0]/2+C[0]/2-e2) if f[0] else 0,f[1]*(P[1]/2+C[1]/2-e2) if f[1] else 0,
                      f[2]*(P[2]/2+C[2]/2-e2) if f[2] else 0]
                pos2=[base[i]+o2[i] for i in range(3)]
            mn=self._uniq(name+"L")
            self._emit(mn,parent,shape,size,pos2,[rot[0],-rot[1],-rot[2]],color); self.sz[mn]=size
            self.mirrored.append((name,mn))
        if self.root is None and parent is None: self.root=name
        return name
    def chain(self,prefix,parent,n,sizes,colors,pitches,face="bot"):
        par=parent;outs=[]
        for i in range(n):
            nm=self.add("%s%d"%(prefix,i),par,"box",sizes[i],face,(0,0,0),(pitches[i],0,0),colors[i%len(colors)])
            outs.append(nm);par=nm;face="bot"
        return outs
    def ring(self,prefix,parent,n,radius,y,size,color,child=None):
        outs=[]
        for i in range(n):
            az=i*360.0/n;a=math.radians(az)
            b=self.add("%s%d"%(prefix,i),parent,"box",size,None,
                       (radius*math.sin(a),y,radius*math.cos(a)),(0,az,0),color)
            outs.append(b)
            if child: child(self,b,i)
        return outs
    def eyes(self,parent,y,z,s,bx=.75,sc="C"):
        for sx,suf in ((1,"R"),(-1,"L")):
            e=self.add("Eye"+suf,parent,"box",(s,s*1.15,s*.4),None,(sx*bx,y,z),(0,0,0),sc)
            self.add("Pupil"+suf,e,"gem",(s*.45,s*.55,s*.3),None,(0,0,-.25),(0,0,0),"D")
        self.mirrored.append(("EyeR","EyeL"))
    def tag(self,*t):
        for x in t: self.present.add(x)
def ground(B):
    idx={p["n"]:p for p in B.parts}
    def ymin(n):
        p=idx[n];y=p["po"][1]-rot_dims(p["sz"],p["ro"])[1]/2;par=p["p"]
        while par and par in idx: y+=idx[par]["po"][1];par=idx[par]["p"]
        return y
    m=min(ymin(p["n"]) for p in B.parts)
    for p in B.parts:
        if p["p"] is None: p["po"][1]=round(p["po"][1]-m,2)
def pose_wrap(B,deg,floating):
    if not deg and not floating: return
    old=B.root;pr=B._uniq("PoseRoot")
    B.parts.append({"n":pr,"p":None,"s":"box","sz":[.3,.3,.3],"po":[0,2.0 if floating else 0,0],
                    "ro":[deg,0,0],"c":"D"});B.sz[pr]=(.3,.3,.3)
    for p in B.parts:
        if p["n"]==old: p["p"]=pr
    B.root=pr
def _head(B):
    for p in B.parts:
        if p["n"]=="Head": return "Head"
    return B.root
def _roof(B):
    for p in B.parts:
        if p["n"]=="Cabin": return "Cabin"
    return B.root
def add_brow_evil(B,I,r):
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Brow"+suf,_head(B),"box",(.42,.12,.15),None,(sx*.38,.42,-.62),(0,0,sx*-18),"D")
def add_hg_crown(B,I,r):
    c=B.add("Crown",_head(B),"box",(.9,.3,.9),"top")
    for i in range(4): B.add("CrownPt%d"%i,c,"pyramid",(.22,.5,.22),"top",((i-1.5)*.28,0,0),(0,0,0),"S")
def add_hg_pointy(B,I,r):
    b=B.add("HatBrim",_head(B),"box",(1.5,.18,1.5),"top")
    B.add("HatCone",b,"pyramid",(.8,1.5,.8),"top",(0,.05,0),(0,0,0),"C")
def add_hg_helmet(B,I,r): B.add("Helmet",_head(B),"box",(1.35,1.0,1.3),"top",(0,-.15,0),(0,0,0),"D")
def add_hg_mask(B,I,r): B.add("Mask",_head(B),"box",(1.0,.5,.2),"front",(0,-.05,-.02),(0,0,0),"D")
def add_hg_tricorn(B,I,r):
    b=B.add("TriBrim",_head(B),"box",(1.7,.15,1.2),"top")
    B.add("TriTop",b,"wedge",(1.5,.4,1.0),"top",(0,.05,0),(0,0,0),"D")
def add_hg_toque(B,I,r): B.add("Toque",_head(B),"cylinder",(.9,.9,.9),"top",(0,.1,0),(0,0,0),"L")
def add_hg_cap(B,I,r):
    t=B.add("CapTop",_head(B),"box",(1.1,.25,1.1),"top",(0,0,-.05),(0,0,0),"C")
    B.add("CapBrim",t,"box",(1.0,.12,.6),"front",(0,-.1,-.2),(0,0,0),"C")
def add_hg_hardhat(B,I,r): B.add("HardHat",_head(B),"box",(1.3,.45,1.3),"top",(0,.05,0),(0,0,0),"C")
def add_hg_dome(B,I,r): B.add("Dome",_head(B),"gem",(1.5,1.5,1.5),None,(0,.1,0),(0,0,0),"L")
def add_hg_glasses(B,I,r): B.add("Glasses",_head(B),"box",(1.0,.22,.15),"front",(0,.12,-.05),(0,0,0),"D")
def add_hg_headband(B,I,r): B.add("Headband",_head(B),"box",(1.25,.22,1.25),"top",(0,-.25,0),(0,0,0),"C")
def add_hg_crystal(B,I,r):
    for i in range(3): B.add("Crys%d"%i,_head(B),"pyramid",(.25,.9-i*.2,.25),"top",((i-1)*.35,.05,.2),(0,0,0),"C")
def add_hair_spiky(B,I,r):
    for i in range(4): B.add("HairSpike%d"%i,_head(B),"pyramid",(.22,.6,.22),"top",((i-1.5)*.3,0,-.1),(0,0,0),"H")
def add_taxi_sign(B,I,r): B.add("TaxiSign",_roof(B),"box",(.7,.3,.25),"top",(0,.05,0),(0,0,0),"C")
def add_lightbar(B,I,r):
    b=B.add("LightBar",_roof(B),"box",(1.2,.18,.35),"top")
    B.add("LampR",b,"gem",(.3,.3,.3),"top",(.35,.1,0),(0,0,0),"C")
    B.add("LampL",b,"gem",(.3,.3,.3),"top",(-.35,.1,0),(0,0,0),"S")
def add_w_big(B,I,r):
    for sx,suf in ((1,"R"),(-1,"L")):
        w=B.add("Wing"+suf,B.root,"box",(1.6,.35,1.0),None,(sx*1.2,1.0,.4),(0,0,sx*20),"B")
        for i in range(4):
            B.add("Wing%sP%d"%(suf,i),w,"wedge",(.45,1.6-i*.2,.22),None,(sx*(.4+i*.35),-.4,.2),(0,0,sx*(26+i*9)),"S")
    B.mirrored.append(("WingR","WingL"))
def add_h_curved(B,I,r):
    if "horns" in B.present: return
    for sx,suf in ((1,"R"),(-1,"L")):
        h=B.add("Horn"+suf,_head(B),"box",(.35,.6,.35),None,(sx*.55,.7,-.1),(sx*-16,0,0),"S")
        for i in range(2): h=B.add("Horn%s%d"%(suf,i),h,"pyramid",(.3-i*.08,.7,.3-i*.08),None,(0,.5,-.15),(-24,0,0),"S")
    B.mirrored.append(("HornR","HornL"))
def add_cape_long(B,I,r): B.add("Cape",B.root,"wedge",(.25,2.6,1.6),None,(0,.6,.75),(14,0,0),"C")
def add_sp_spoiler(B,I,r):
    B.add("Spoiler",B.root,"box",(2.0,.15,.6),"back",(0,.9,.2),(0,0,0),"D")
    for sx in (1,-1): B.add("SpoPost%d"%sx,B.root,"box",(.15,.6,.15),"back",(sx*.8,.5,.2),(0,0,0),"D")
ADDONS={"brow_evil":add_brow_evil,"hg_crown":add_hg_crown,"hg_pointy":add_hg_pointy,
 "hg_helmet":add_hg_helmet,"hg_mask":add_hg_mask,"hg_tricorn":add_hg_tricorn,"hg_toque":add_hg_toque,
 "hg_cap":add_hg_cap,"hg_hardhat":add_hg_hardhat,"hg_dome":add_hg_dome,
 "hg_glasses":add_hg_glasses,"hg_headband":add_hg_headband,"hg_crystal":add_hg_crystal,
 "hair_spiky":add_hair_spiky,"taxi_sign":add_taxi_sign,"lightbar":add_lightbar,
 "w_big":add_w_big,"h_curved":add_h_curved,"cape_long":add_cape_long,"sp_spoiler":add_sp_spoiler}
def b_humanoid(B,I,r):
    p=I["prop"];v=B.var
    cw=1.5*p.get("chest",1.0)*(1.12 if v==2 else .94 if v==1 else 1.0)
    lw=p.get("limbs",1.0); hw=1.12*p.get("head",1.0)*(1.1 if v==0 else 1.0)
    leg=1.35*lw*(1.1 if v==3 else 1.0)
    hips=B.add("HumanoidRootPart",None,"box",(cw*.9,.5,.9),None,(0,0,0),(0,0,0),"P")
    for sx,suf in ((1,"R"),(-1,"L")):
        th=B.add("Thigh"+suf,hips,"box",(.62*lw,leg,.7),"bot",(sx*.42,-.05,0),(0,0,0),"P")
        shn=B.add("Shin"+suf,th,"box",(.5*lw,leg,.58),"bot")
        B.add("Shoe"+suf,shn,"wedge",(.6,.35,1.05),"bot",(0,0,-.18),(0,0,0),"D")
    torso=B.add("Chest",hips,"box",(cw,1.7,.95),"top",(0,.05,0),(0,0,0),"A",studs=True)
    nk=B.add("Neck",torso,"box",(.42,.3,.42),"top",(0,0,0),(0,0,0),"K")
    head=B.add("Head",nk,"box",(hw,1.12*hw,hw*.92),"top",(0,.05,0),(0,0,0),"K")
    B.eyes(head,.1,-.6,.3*I["eyes"],.34*hw/1.12,sc="L")
    B.add("Mouth",head,"box",(.42,.1,.1),"front",(0,-.35,-.02),(0,0,0),"D")
    B.add("Ear",head,"box",(.12,.3,.25),"right",(0,0,0),(0,0,0),"K",mirror=True)
    if "hair" not in I["neg"]:
        B.add("HairTop",head,"box",(hw*1.02,.28,hw*.94),"top",(0,0,.04),(0,0,0),"H")
        if v==0: B.add("HairBack",head,"box",(hw,.85,.22),"back",(0,-.15,.04),(0,0,0),"H")
        if v==1: B.add("Fringe",head,"box",(hw*.85,.22,.18),"front",(0,.42,-.04),(0,0,0),"H")
        if v==2: B.add("HairSide",head,"box",(.18,.6,hw*.9),"right",(0,.05,.04),(0,0,0),"H",mirror=True)
        if v==3: B.add("Bun",head,"gem",(.45,.45,.45),"back",(0,.55,.08),(0,0,0),"H")
        if "anime" in I["mods"]:
            for i in range(4): B.add("HairSpike%d"%i,"HairTop","pyramid",(.22,.6,.22),"top",((i-1.5)*.3,0,-.1),(0,0,0),"H")
    for sx,suf in ((1,"R"),(-1,"L")):
        ua=B.add("Arm"+suf,torso,"box",(.52,1.15,.56),"right" if sx>0 else "left",(0,.55,0),(0,0,sx*4),"A")
        fa=B.add("Fore"+suf,ua,"box",(.44,1.05,.46),"bot",(0,0,0),(0,0,0),"K")
        B.add("Hand"+suf,fa,"box",(.42,.42,.45),"bot",(0,0,0),(0,0,0),"K")
    B.add("Belt",hips,"box",(cw*.92,.22,.92),"top",(0,-.1,0),(0,0,0),"D")
    B.tag("humanoid")
def b_octopus(B,I,r):
    n=8 if B.var!=1 else 6
    B.add("CoreRoot",None,"box",(2.8,2.2,2.8),None,(0,2.4,0),(0,0,0),"A",studs=True)
    m=B.add("Mantle","CoreRoot","box",(2.2,1.4,2.2),"top",(0,.05,.1),(0,0,0),"B",studs=True)
    B.add("Mantle2",m,"box",(1.4,1.0,1.4),"top",(0,.05,.1),(0,0,0),"A")
    hd=B.add("Head","CoreRoot","box",(2.5,1.7,2.2),None,(0,-.5,.5),(0,0,0),"A")
    B.eyes(hd,.1,-1.15,.62,.85)
    def suck(b,base,i):
        par=base
        for s in range(4):
            t=s/4.0
            par=b.add("Tent%d_s%d"%(i,s),par,"box",(.62*(1-t)+.15,1.1-.2*t,.62*(1-t)+.15),"bot",
                    (0,.05,0),(16+s*9,0,0),"A" if s%2 else "B")
        b.add("Tent%d_tip"%i,par,"wedge",(.3,.6,.3),"bot",(0,0,0),(-90,0,0),"C")
    B.ring("Tent","CoreRoot",n,1.35,-1.5,(.7,.8,.7),"A",child=suck)
    B.tag("octopus","tentacles")
def b_serpent(B,I,r):
    n=10 if B.var!=2 else 12
    d=[10]+[r.choice([-13,13])*(1 if i%2 else -1) for i in range(n-1)]
    par=None;names=[]
    for i in range(n):
        sz=(1.5-i*.07,1.35-i*.06,1.6)
        nn=B.add("Seg%d"%i,par if par else None,"box",sz,None if par else None,
                 (0,1.5,4.2) if not par else (0,0,0),(0,d[i],0),"A" if i%2 else "B",studs=i%3==0)
        names.append(nn);par=nn
    hd=B.add("Head",par,"box",(1.9,1.5,2.3),"front",(0,.25,.2),(0,0,0),"A",studs=True)
    B.add("Snout",hd,"wedge",(1.3,.9,1.3),"front",(0,-.25,.2),(-90,0,0),"B")
    B.eyes(hd,.45,-1.05,.5,.72)
    for i in range(0,n-2,2): B.add("Dorsal%d"%i,names[i],"wedge",(.28,.9,1.0),"top",(0,.05,0),(0,0,0),"C")
    B.add("TailFin",names[0],"wedge",(1.3,1.5,.28),"back",(0,2,-.2),(90,0,0),"C")
    B.tag("tail")
def b_fish(B,I,r):
    B.add("CoreRoot",None,"box",(2.6,2.6,2.4),None,(0,2.0,0),(0,0,0),"A",studs=True)
    sn=B.add("SnoutSec","CoreRoot","box",(2.0,2.0,1.4),"front",(0,0,.1),(0,0,0),"A")
    cs=B.add("CaudalSec","CoreRoot","box",(1.3,1.5,1.4),"back")
    B.add("Belly","CoreRoot","box",(2.1,1.0,2.2),"bot",(0,.1,0),(0,0,0),"L")
    B.eyes(sn,.5,-.75,.55,.8)
    nn=int(4+B.sharp*4)+(2 if B.var==1 else 0)
    for i in range(nn):
        a=-65+i*(130.0/max(1,nn-1));rd=math.radians(a)
        B.add("Dorsal%d"%i,"CoreRoot","pyramid",(.45,r.uniform(.9,1.9)*B.sharp,.45),None,
              (1.45*math.sin(rd),1.45*math.cos(rd),r.uniform(-.9,.9)),(0,0,-a),"S")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Pect"+suf,"CoreRoot","wedge",(1.5,1.2,.25),None,(sx*1.35,-.5,-.5),(0,0,sx*62),"C")
    for k,az in ((0,-32),(1,0),(2,32)): B.add("Caudal%d"%k,cs,"wedge",(1.5,2.0,.25),"back",(0,.5,-.2),(0,az,0),"C")
    B.tag("fins","tail")
def b_bird(B,I,r):
    B.add("CoreRoot",None,"box",(1.9,2.1,2.5),None,(0,2.6,0),(0,0,0),"A",studs=True)
    nk=B.add("Neck","CoreRoot","box",(.9,1.1,.9),"top",(0,.1,-.9),(-18,0,0),"B")
    hd=B.add("Head",nk,"box",(1.25,1.25,1.3),"top",(0,.05,-.1),(12,0,0),"A")
    B.eyes(hd,.15,-.6,.42,.5)
    B.add("Beak",hd,"wedge",(.7,.6,1.0),"front",(0,-.1,-.1),(-90,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        w=B.add("Wing"+suf,"CoreRoot","box",(1.5,.4,1.1),None,(sx*1.15,.7,0),(0,0,sx*16),"B")
        md=B.add("Wing%sMid"%suf,w,"box",(1.4,.32,.9),"right" if sx>0 else "left")
        for i in range(5):
            B.add("Wing%sP%d"%(suf,i),md,"wedge",(.42,1.5-i*.16,.2),None,(sx*(.35+i*.3),-.4,.25),(0,0,sx*(26+i*9)),"S")
    nf=5 if B.var!=3 else 7
    for i in range(nf):
        B.add("TailF%d"%i,"CoreRoot","wedge",(.7,1.9-abs(i-nf//2)*.25,.22),"back",
              ((i-nf//2)*.5,-.3,-.2),(115,(i-nf//2)*14,0),"C" if i%2 else "S")
    for sx,suf in ((1,"R"),(-1,"L")):
        f=B.add("Femur"+suf,"CoreRoot","box",(.6,1.2,.7),"bot",(sx*.65,.1,0),(0,0,0),"B")
        t=B.add("Tibia"+suf,f,"box",(.45,1.2,.5),"bot")
        for k in (-1,0,1): B.add("Tal%s%d"%(suf,k),t,"pyramid",(.2,.6,.2),"bot",(k*.25,-.1,-.3),(75,0,0),"D")
    B.tag("wings")
def b_crab(B,I,r):
    B.add("CoreRoot",None,"box",(3.4,1.6,2.6),None,(0,1.9,0),(0,0,0),"A",studs=True)
    d1=B.add("Dome","CoreRoot","box",(2.7,1.0,2.1),"top",(0,.05,0),(0,0,0),"B",studs=True)
    B.add("Dome2",d1,"box",(1.8,.7,1.4),"top")
    for sx,suf in ((1,"R"),(-1,"L")):
        st=B.add("Stalk"+suf,"CoreRoot","box",(.28,.9,.28),"top",(sx*.8,.1,-1.1),(sx*10,0,0),"C")
        B.add("Eye"+suf,st,"gem",(.5,.5,.5),"top")
        m=B.add("Merus"+suf,"CoreRoot","box",(.8,1.5,.8),None,(sx*2.0,.1,-.9),(sx*24,0,0),"B")
        c=B.add("Carpus"+suf,m,"box",(.7,1.2,.7),"bot",(0,0,-.3),(-34,0,0),"A")
        pr=B.add("Prop"+suf,c,"box",(.75,1.5,.7),"bot",(0,0,-.2),(-20,0,0),"B")
        B.add("Dactyl"+suf,pr,"wedge",(.5,1.4,.5),"bot",(0,-.1,-.15),(-26,0,0),"S")
        B.add("Pollex"+suf,pr,"wedge",(.5,1.1,.5),"bot",(0,-.1,.3),(22,0,0),"S")
    for i in range(3):
        for sx,suf in ((1,"R"),(-1,"L")):
            l1=B.add("Walk%d%s"%(i,suf),"CoreRoot","box",(.45,1.5,.45),None,(sx*1.6,-.6,.7-i*.7),
                   (0,sx*(i-1)*26,sx*34),"B")
            l2=B.add("Walk%d%s2"%(i,suf),l1,"box",(.36,1.4,.36),"bot",(0,0,0),(0,0,-sx*46),"A")
            B.add("Walk%d%s3"%(i,suf),l2,"pyramid",(.26,.7,.26),"bot",(0,0,0),(180,0,0),"D")
    B.tag("claws")
def b_spider(B,I,r):
    B.add("CoreRoot",None,"box",(2.0,1.4,2.2),None,(0,2.2,-.8),(0,0,0),"A",studs=True)
    B.add("Abdomen","CoreRoot","box",(2.2,1.9,2.6),"back",(0,.5,.6),(0,0,0),"B",studs=True)
    hd=B.add("Head","CoreRoot","box",(1.4,1.1,1.2),"front",(0,-.1,-.4),(0,0,0),"B")
    for k,(dx,dy) in enumerate(((-.4,.1),(-.15,.25),(.15,.25),(.4,.1))):
        B.add("Eye%d"%k,hd,"gem",(.26,.3,.2),"front",(dx*2,dy,-.1),(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        ch=B.add("Chel"+suf,hd,"box",(.4,.7,.5),"bot",(sx*.35,-.1,-.4),(0,0,0),"D")
        B.add("Fang"+suf,ch,"pyramid",(.2,.8,.2),"bot",(0,-.1,-.1),(168,0,0),"S")
    for i in range(4):
        for sx,suf in ((1,"R"),(-1,"L")):
            a=(i-1.5)*22
            l1=B.add("Leg%d%s"%(i,suf),"CoreRoot","box",(.38,1.9,.38),None,(sx*1.0,.3,-.9+i*.62),(0,sx*a,sx*52),"B")
            l2=B.add("Leg%d%s2"%(i,suf),l1,"box",(.32,1.9,.32),"bot",(0,0,0),(0,0,-sx*58),"A")
            l3=B.add("Leg%d%s3"%(i,suf),l2,"box",(.26,1.5,.26),"bot",(0,0,0),(0,0,sx*24),"B")
            B.add("Leg%d%s4"%(i,suf),l3,"pyramid",(.2,.7,.2),"bot",(0,0,0),(180,0,0),"D")
    B.tag("teeth")
def b_golem(B,I,r):
    B.add("HumanoidRootPart",None,"gem",(2.6,3.0,2.0),None,(0,3.2,0),(0,0,0),"A")
    B.add("Core","HumanoidRootPart","gem",(1.1,1.3,.9),"front",(0,.1,.1),(0,0,0),"C")
    hd=B.add("Head","HumanoidRootPart","box",(1.2,1.1,1.2),"top",(0,.1,0),(0,0,0),"B",studs=True)
    B.add("Visor",hd,"wedge",(.9,.4,.3),"front",(0,.1,-.05),(-90,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Pauldron"+suf,"HumanoidRootPart","box",(1.3,.6,1.3),None,(sx*1.9,1.5,0),(0,0,sx*8),"B",studs=True)
        a1=B.add("Arm"+suf,"HumanoidRootPart","box",(.9,2.2,.9),None,(sx*1.9,.2,0),(0,0,sx*6),"A")
        a2=B.add("Fore"+suf,a1,"box",(.8,1.8,.8),"bot")
        B.add("Fist"+suf,a2,"box",(1.1,1.0,1.1),"bot",(0,0,0),(0,0,0),"D")
        l1=B.add("Leg"+suf,"HumanoidRootPart","box",(1.0,2.2,1.0),"bot",(sx*.9,-.2,0),(0,0,0),"B")
        B.add("Foot"+suf,l1,"wedge",(1.2,.7,1.6),"bot",(0,0,-.3),(0,0,0),"D")
    for i in range(4):
        x,z=phyllo(i,4,.8)
        B.add("Crys%d"%i,"HumanoidRootPart","pyramid",(.4,1.6*B.sharp,.4),"top",(x,.1,z+.6),(-18,0,0),"S")
    B.tag("armor","glow")
def b_turtle(B,I,r):
    B.add("CoreRoot",None,"box",(3.0,1.2,3.4),None,(0,1.6,0),(0,0,0),"L")
    sh=B.add("ShellBase","CoreRoot","box",(3.2,1.0,3.6),"top",(0,.05,0),(0,0,0),"A",studs=True)
    s2=B.add("Shell2",sh,"box",(2.6,.9,3.0),"top")
    B.add("Shell3",s2,"box",(1.8,.8,2.2),"top",(0,0,0),(0,0,0),"A",studs=True)
    nk=B.add("Neck","CoreRoot","box",(.9,.9,1.0),"front",(0,0,.3),(-14,0,0),"L")
    hd=B.add("Head",nk,"box",(1.1,1.0,1.1),"front",(0,.1,.2),(10,0,0),"L")
    B.eyes(hd,.2,-.55,.34,.42)
    for i,(sx,sz) in enumerate(((1,-1),(-1,-1),(1,1),(-1,1))):
        B.add("Flip%d"%i,"CoreRoot","box",(.9,.8,1.3),None,(sx*1.6,-.5,sz*1.3),(0,sx*sz*24,sx*20),"L")
    B.chain("Tail","CoreRoot",3,[(.6,.6,.8),(.45,.45,.7),(.3,.3,.6)],["L","L","D"],[12,14,16])
    B.tag("shell","tail")
def b_jelly(B,I,r):
    B.add("CoreRoot",None,"box",(3.0,1.2,3.0),None,(0,3.0,0),(0,0,0),"A",studs=True)
    b2=B.add("Bell2","CoreRoot","box",(3.4,.9,3.4),"bot")
    B.add("Bell3","CoreRoot","box",(2.6,.7,2.6),"top",(0,0,0),(0,0,0),"A",studs=True)
    B.add("GlowCore","CoreRoot","gem",(1.0,.8,1.0),"bot",(0,.2,0),(0,0,0),"C")
    for i in range(12):
        az=i*30.0;a=math.radians(az)
        B.add("Skirt%d"%i,b2,"wedge",(.5,.9,.16),None,(1.6*math.sin(a),-.5,1.6*math.cos(a)),(180,az,0),"L")
    nt=8 if B.var!=2 else 12
    for i in range(nt):
        az=i*360.0/nt;a=math.radians(az)
        base=B.add("Tent%d"%i,b2,"box",(.22,.7,.22),None,(1.5*math.sin(a),-.6,1.5*math.cos(a)),(0,az,0),"C")
        B.chain("Tent%d_"%i,base,5,[(.18,1.2,.18),(.16,1.1,.16),(.14,1.0,.14),(.12,.9,.12),(.1,.8,.1)],
                ["C","L","C","L","C"],[8,10,12,14,16])
    B.tag("tentacles","frill","glow")
def b_car(B,I,r):
    p=I["prop"];body=I.get("carbody") or {0:"sedan",1:"sport",2:"buggy",3:"pickup"}[B.var]
    ws=.85*p.get("wheels",1.0);lift=.25*p.get("lift",1.0)
    low={"sport":.85,"buggy":1.0,"pickup":1.15,"van":1.2,"sedan":1.0}[body]
    L={"sport":4.6,"sedan":4.5,"buggy":3.6,"pickup":4.8,"van":4.9}[body]; W=2.1
    ch=B.add("CoreRoot",None,"box",(W,.7*low,L),None,(0,.9*low+lift,0),(0,0,0),"A",studs=True)
    if body=="van":
        cab=B.add("Cabin",ch,"box",(W*.92,1.5,L*.72),"top",(0,0,.35),(0,0,0),"A",studs=True)
        B.add("WinF",cab,"box",(W*.8,.6,.12),"front",(0,.35,-.02),(0,0,0),"D")
    else:
        cl=2.0 if body!="buggy" else 1.4
        cab=B.add("Cabin",ch,"box",(W*.82,.8*low,cl),"top",(0,0,.5 if body=="pickup" else .3),(0,0,0),"B")
        B.add("WinF",cab,"wedge",(W*.78,.7*low,.15),"front",(0,0,0),(0,0,0),"D")
        B.add("WinB",cab,"box",(W*.78,.6*low,.12),"back",(0,0,-.02),(0,0,0),"D")
        B.add("Hood",ch,"wedge",(W*.9,.3,L*.3),"top",(0,-.12,-L*.3),(0,0,0),"A")
    if body=="buggy":
        for sx in (1,-1): B.add("Roll%d"%sx,ch,"box",(.15,.9,.15),"top",(sx*.8,.1,.6),(0,0,0),"D")
        B.add("RollBar",ch,"box",(1.8,.15,.15),"top",(0,.95,.6),(0,0,0),"D")
    if body=="sport":
        for sx in (1,-1): B.add("Stripe%d"%sx,ch,"box",(.28,.06,L*.75),"top",(sx*.45,.02,-.35),(0,0,0),"L")
    if body=="pickup": B.add("Bed",ch,"box",(W*.95,.6,1.4),"top",(0,.15,1.5),(0,0,0),"A")
    for sx,suf in ((1,"R"),(-1,"L")):
        for zz,tag in ((L*.32,"F"),(-L*.32,"B")):
            w=B.add("Wheel%s%s"%(tag,suf),ch,"cylinder",(ws,.45,ws),None,(sx*(W/2+.05),-.25,zz),(0,0,90),"D")
            B.add("Hub%s%s"%(tag,suf),w,"cylinder",(ws*.5,.55,ws*.5),None,(0,0,0),(0,0,90),"C")
        B.add("Light%s"%suf,ch,"box",(.45,.28,.12),"front",(sx*.7,.1,0),(0,0,0),"C")
        B.add("Tail%s"%suf,ch,"box",(.45,.28,.12),"back",(sx*.7,.1,0),(0,0,0),"S")
        B.add("Skirt%s"%suf,ch,"box",(.15,.35,L*.7),"right" if sx>0 else "left",(0,-.15,0),(0,0,0),"D")
    B.add("BumpF",ch,"box",(W,.35,.3),"front",(0,-15,0),(0,0,0),"D")
    B.add("BumpB",ch,"box",(W,.35,.3),"back",(0,-.15,0),(0,0,0),"D")
    if body=="sport" or "sp_spoiler" in I["traits"]:
        B.add("Spoiler",ch,"box",(W*.9,.14,.55),"back",(0,.55,.15),(0,0,0),"D")
        for sx in (1,-1): B.add("SpoPost%d"%sx,ch,"box",(.14,.5,.14),"back",(sx*.7,.3,.15),(0,0,0),"D")
    B.tag("wheels")
def b_bike(B,I,r):
    fr=B.add("CoreRoot",None,"box",(.5,.7,2.2),None,(0,1.2,0),(0,0,0),"A")
    for zz,tag in ((-1.3,"F"),(1.3,"B")):
        B.add("Wheel%s"%tag,fr,"cylinder",(1.1,.35,1.1),None,(0,-.5,zz),(0,0,90),"D")
    B.add("Fork",fr,"box",(.2,1.0,.2),"front",(0,-.3,-.2),(20,0,0),"B")
    B.add("Bar",fr,"box",(1.4,.2,.2),"top",(0,.2,-.9),(0,0,0),"D")
    B.add("Seat",fr,"box",(.6,.25,.9),"top",(0,0,.7),(0,0,0),"B")
    B.tag("wheels")
def b_boat(B,I,r):
    hl=B.add("CoreRoot",None,"box",(2.4,1.1,5.0),None,(0,1.2,0),(0,0,0),"A",studs=True)
    B.add("Bow",hl,"pyramid",(2.4,1.0,1.6),"front",(0,-.1,0),(-90,0,0),"A")
    cab=B.add("Cabin",hl,"box",(1.8,1.0,1.8),"top",(0,0,.6),(0,0,0),"B",studs=True)
    B.add("Win",cab,"box",(1.4,.5,.12),"front",(0,0,-.02),(0,0,0),"D")
    if B.var!=1: B.add("Mast",cab,"box",(.2,2.2,.2),"top")
    B.add("Prop",hl,"cylinder",(.8,.2,.8),"back",(0,-.2,0),(90,0,0),"D")
    B.tag("hull")
def b_plane(B,I,r):
    fu=B.add("CoreRoot",None,"box",(1.6,1.4,5.0),None,(0,2.2,0),(0,0,0),"A",studs=True)
    B.add("Nose",fu,"pyramid",(1.4,1.4,1.4),"front",(0,0,0),(-90,0,0),"B")
    B.add("Cockpit",fu,"wedge",(1.0,.6,1.4),"top",(0,0,-1.2),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Wing"+suf,fu,"wedge",(4.0,.25,1.4),None,(sx*2.2,-.2,-.3),(0,0,sx*8),"B")
        B.add("Stab"+suf,fu,"wedge",(1.4,.2,.8),None,(sx*.9,.5,2.4),(0,0,sx*8),"B")
    B.add("Fin",fu,"wedge",(.2,1.6,1.2),"top",(0,0,2.2),(0,0,0),"C")
    B.tag("wings")
def b_heli(B,I,r):
    bd=B.add("CoreRoot",None,"box",(2.0,1.6,3.4),None,(0,2.0,0),(0,0,0),"A",studs=True)
    B.add("Win",bd,"box",(1.6,.8,.12),"front",(0,.2,-.02),(0,0,0),"D")
    tb=B.add("Boom",bd,"box",(.5,.5,3.0),"back",(0,.3,-.2),(0,0,0),"B")
    B.add("TRotor",tb,"wedge",(.15,1.4,.4),"right",(0,0,0),(0,0,90),"D")
    hub=B.add("Hub",bd,"cylinder",(.5,.4,.5),"top")
    for i in range(4): B.add("Blade%d"%i,hub,"box",(4.6,.12,.4),"top",(0,.15,0),(0,i*90,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Skid"+suf,bd,"box",(.2,.2,3.2),"bot",(sx*1.0,-.5,0),(0,0,0),"D")
        B.add("Strut"+suf,bd,"box",(.15,.7,.15),"bot",(sx*1.0,-.2,.8),(0,0,0),"D")
    B.tag("rotor")
def b_tank(B,I,r):
    hl=B.add("CoreRoot",None,"box",(4.0,1.0,2.6),None,(0,1.3,0),(0,0,0),"A",studs=True)
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Track"+suf,hl,"box",(4.4,.9,.7),None,(sx*1.5,-.2,0),(0,0,0),"D")
    tu=B.add("Turret",hl,"box",(1.8,.9,2.0),"top",(0,0,-.3),(0,0,0),"B",studs=True)
    B.add("Barrel",tu,"cylinder",(.3,2.6,.3),"front",(0,.1,-.2),(90,0,0),"D")
    B.add("Hatch",tu,"box",(.7,.2,.7),"top",(0,0,.5),(0,0,0),"D")
    B.tag("armor")
def b_quadruped(B,I,r):
    sp=I.get("species") or "beast"; S=SPECIES.get(sp) or SPECIES["beast"]
    p=I["prop"]; v=B.var%4; k=S["size"]; ex=S["extras"]
    lf=(1.0,1.1,.95,1.05)[v]; bf=(1.0,.93,1.07,1.0)[v]; hf=(1.0,1.07,.95,1.0)[v]*p.get("head",1.0)
    ch=p.get("chest",1.0); lm=p.get("limbs",1.0)
    bw=S["bw"]*k*ch; bh=S["bh"]*k*(ch**.5); bl=S["bl"]*k*bf
    leg=S["leg"]*k*lf*lm; lw=S["lw"]*k*lm
    hw,hh,hl=[x*k*hf for x in S["head"]]
    B.add("CoreRoot",None,"box",(bw,bh,bl),None,(0,leg*.95+bh/2,0),(0,0,0),"A",studs=True)
    for fz,tg in ((-1,"F"),(1,"B")):
        for sx,suf in ((1,"R"),(-1,"L")):
            up=B.add("Leg"+tg+suf,"CoreRoot","box",(lw*1.15,leg*.52,lw*1.15),"bot",
                     (sx*(bw/2-lw*.7),0,fz*(bl/2-lw*.9)),(0,0,0),"A")
            lo=B.add("Shin"+tg+suf,up,"box",(lw*.85,leg*.52,lw*.85),"bot",(0,0,0),(0,0,0),"B")
            B.add("Hoof"+tg+suf,lo,"box",(lw,lw*.45,lw*1.15),"bot",(0,0,-lw*.05),(0,0,0),"D")
    ang=math.radians(S["nang"]); nl=S["neck"]*k; nw=min(hw*.8,bw*.55)
    nb_y=bh*.25; nb_z=-(bl/2-nw*.4)
    B.add("Neck","CoreRoot","box",(nw,nl,nw*1.05),None,
          (0,nb_y+nl/2*math.cos(ang),nb_z-nl/2*math.sin(ang)),(-S["nang"],0,0),"A")
    ty=nb_y+nl*math.cos(ang); tz=nb_z-nl*math.sin(ang)
    head=B.add("Head","CoreRoot","box",(hw,hh,hl),None,(0,ty+hh*.12,tz-hl*.22),(0,0,0),S["headc"])
    sn=S["snout"]; sw,sh,sl=hw*sn[0],hh*sn[1],hl*sn[2]
    snout=B.add("Snout",head,"box",(sw,sh,sl),"front",(0,-hh*.15,0),(0,0,0),S["snoutc"])
    B.add("Nose",snout,"box",(sw*.55,sh*.45,.12*k),"front",(0,sh*.15,0),(0,0,0),"D")
    B.eyes(head,hh*.15,-hl*.5,(.18+.1*hw)*I["eyes"],hw*.34,sc="L")
    et=S["ears"]; ew,eh=S["ear"][0]*k,S["ear"][1]*k
    for sx,suf in ((1,"R"),(-1,"L")):
        side="right" if sx>0 else "left"
        if et in ("point","long"):
            B.add("Ear"+suf,head,"pyramid",(ew,eh,ew*.7),"top",(sx*hw*.3,0,hl*.15),(0,0,-sx*(8 if et=="point" else 16)),"B")
        elif et=="side":
            B.add("Ear"+suf,head,"box",(eh,.14*k,ew),side,(0,hh*.2,hl*.1),(0,0,-sx*12),"B")
        elif et=="floppy":
            B.add("Ear"+suf,head,"box",(ew*.4,eh,ew),side,(0,-eh*.15,hl*.1),(0,0,0),"B")
        elif et=="round":
            B.add("Ear"+suf,head,"gem",(ew,ew,ew*.6),"top",(sx*hw*.36,0,hl*.15),(0,0,0),"B")
        elif et=="flap":
            B.add("Ear"+suf,head,"box",(.2*k,eh,ew),side,(0,0,hl*.1),(0,0,0),"B")
    if et!="none": B.mirrored.append(("EarR","EarL"))
    ht=S["horns"]
    if sp=="sheep" and I.get("ram"): ht="curved"
    if "horns" in I["neg"]: ht=None
    if ht:
        if ht=="straight":
            h=B.add("Horn",head,"box",(.2*k,.9*k,.2*k),"top",(0,0,-hl*.2),(-18,0,0),"S")
            B.add("HornTip",h,"pyramid",(.17*k,.6*k,.17*k),"top",(0,0,0),(-6,0,0),"S")
        else:
            for sx,suf in ((1,"R"),(-1,"L")):
                side="right" if sx>0 else "left"
                if ht=="curved":
                    h=B.add("Horn"+suf,head,"box",(.2*k,.7*k,.2*k),"top",(sx*hw*.26,0,hl*.1),(18,0,0),"S")
                    B.add("Horn%sTip"%suf,h,"pyramid",(.17*k,.6*k,.17*k),"top",(0,0,0),(22,0,0),"S")
                elif ht=="bull":
                    h=B.add("Horn"+suf,head,"box",(hw*.35,.18*k,.18*k),side,(0,hh*.25,0),(0,0,0),"S")
                    B.add("Horn%sTip"%suf,h,"pyramid",(.16*k,.6*k,.16*k),"top",(sx*.05,0,0),(0,0,0),"S")
                elif ht=="antlers":
                    h=B.add("Horn"+suf,head,"box",(.14*k,1.0*k,.14*k),"top",(sx*hw*.25,0,0),(0,0,-sx*20),"S")
                    for i in range(2):
                        B.add("Horn%sP%d"%(suf,i),h,"box",(.12*k,.55*k,.12*k),None,
                              (sx*.12*k,(i-.5)*.5*k,0),(0,0,-sx*28),"S")
                elif ht=="knobs":
                    h=B.add("Horn"+suf,head,"box",(.16*k,.55*k,.16*k),"top",(sx*hw*.22,0,0),(0,0,0),"S")
                    B.add("Horn%sTip"%suf,h,"gem",(.28*k,.28*k,.28*k),"top",(0,0,0),(0,0,0),"D")
            B.mirrored.append(("HornR","HornL"))
        B.tag("horns")
    tt=S["tail"]; tyy=bh*.2
    def tchain(n,w,l,pitch,cols):
        par=None
        for i in range(n):
            f=1-.12*i
            if i==0: par=B.add("Tail","CoreRoot","box",(w,w,l),"back",(0,tyy,0),(pitch,0,0),cols[0])
            else: par=B.add("Tail%d"%i,par,"box",(w*f,w*f,l),"back",(0,0,0),(pitch*.7,0,0),cols[i%len(cols)])
        return par
    if tt=="short": tchain(1,.38*k,.6*k,-28,["A"])
    elif tt=="long_up": tchain(4,.3*k,.7*k,-14,["A","B"])
    elif tt=="hang": tchain(4,.34*k,.8*k,16,["D"])
    elif tt=="bushy": tchain(3,.7*k,.9*k,-32,["A","A","L"])
    elif tt=="tuft":
        e=tchain(3,.2*k,.7*k,10,["A"]); B.add("TailTuft",e,"box",(.4*k,.4*k,.5*k),"back",(0,0,0),(0,0,0),"D")
    elif tt=="curly": tchain(3,.2*k,.3*k,-45,["L"])
    elif tt=="ball": B.add("CoreRoot","CoreRoot","gem",(.6*k,.6*k,.6*k),"back",(0,tyy,0),(0,0,0),"L")
    elif tt=="croc": tchain(5,bh*.62,bl*.22,3,["A","B"])
    elif tt=="long_thin": tchain(4,.12*k,.8*k,-6,["B"])
    if "beard" in ex: B.add("Beard",head,"box",(hw*.22,hh*.55,hw*.2),"bot",(0,0,-hl*.32),(0,0,0),"L")
    if "mane" in ex: B.add("Mane",head,"box",(hw*1.7,hh*1.65,hl*.55),"back",(0,0,hl*.1),(0,0,0),"S")
    if "hmane" in ex:
        B.add("Mane","Neck","box",(.22*k,nl*.95,.34*k),"back",(0,0,0),(0,0,0),"D")
        B.add("Forelock",head,"box",(.3*k,.3*k,.3*k),"top",(0,0,-hl*.2),(0,0,0),"D")
    if "hump" in ex: B.add("Hump","CoreRoot","box",(bw*.7,bh*.7,bl*.2),"top",(0,0,bl*.05),(0,0,0),"B")
    if "spots" in ex:
        for i,(x,z) in enumerate([(-.28,-.28),(.26,.05),(-.2,.3),(.3,-.32),(0,0)][:4+v%2]):
            B.add("Spot%d"%i,"CoreRoot","box",(bw*.34,.06,bl*.18),"top",(x*bw,0,z*bl),(0,0,0),"D")
    if "stripes" in ex:
        for i in range(5):
            B.add("Stripe%d"%i,"CoreRoot","box",(bw*.9,.07,bl*.07),"top",(0,0,(i-2)*bl*.18),(0,0,0),"D")
    if "plates" in ex:
        for i in range(5):
            B.add("Plate%d"%i,"CoreRoot","pyramid",(bw*.3,bh*.5,bl*.12),"top",(0,0,(i-2)*bl*.2),(0,0,0),"S")
    if "wool" in ex:
        for i in range(3):
            B.add("Wool%d"%i,"CoreRoot","box",(bw*.6,bh*.3,bl*.22),"top",(0,0,(i-1)*bl*.28),(0,0,0),"L")
        B.add("WoolHead",head,"box",(hw*1.05,hh*.4,hl*.5),"top",(0,0,hl*.1),(0,0,0),"A")
    if "patches" in ex:
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("Patch"+suf,head,"box",(hw*.3,hh*.3,.1*k),"front",(sx*hw*.3,hh*.12,0),(0,0,0),"B")
    if "trunk" in ex:
        t1=B.add("Trunk",head,"box",(hw*.4,hh*.5,hw*.35),"front",(0,-hh*.1,0),(0,0,0),"A")
        t2=B.add("Trunk2",t1,"box",(hw*.34,hh*.5,hw*.3),"bot",(0,0,-.05),(-12,0,0),"A")
        B.add("Trunk3",t2,"box",(hw*.28,hh*.45,hw*.26),"bot",(0,0,-.05),(-14,0,0),"A")
    if "tusks" in ex:
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("Tusk"+suf,head,"pyramid",(.2*k,.9*k,.2*k),"front",(sx*hw*.3,-hh*.3,0),(-70,0,0),"L")
    B.tag("quadruped","legs",sp)
def b_building(B,I,r):
    kw=I.get("keyword") or "house"; v=B.var%4
    tower=kw in ("tower","lighthouse"); castle=kw in ("castle","fort")
    tall=tower or kw in ("church","temple")
    w=3.2 if tower else 3.8 if tall else 4.6; h=5.0 if tower else 3.2 if tall else 2.6; d=w if tall else 3.8
    base=B.add("CoreRoot",None,"box",(w,h,d),None,(0,h/2,0),(0,0,0),"A",studs=True)
    B.add("Door",base,"box",(.95,1.5,.16),"front",(0,-h/2+.78,0),(0,0,0),"D")
    for sx in (1,-1):
        B.add("Window%d"%(1 if sx>0 else 2),base,"box",(.75,.75,.14),"front",(sx*w*.27,h*.12+(.9 if tall else 0),0),(0,0,0),"L")
    if castle:
        for sx,a in ((1,"R"),(-1,"L")):
            for sz,b in ((-1,"F"),(1,"B")):
                t=B.add("Turret"+a+b,base,"box",(1.3,h*.6+1.4,1.3),None,(sx*w/2,.7,sz*d/2),(0,0,0),"B",studs=True)
                B.add("Turret%s%sCap"%(a,b),t,"pyramid",(1.7,1.1,1.7),"top",(0,0,0),(0,0,0),"C")
        for i in range(5):
            B.add("Merlon%d"%i,base,"box",(.5,.5,.5),"top",((i-2)*.85,0,-(d/2-.35)),(0,0,0),"B")
            B.add("MerlonB%d"%i,base,"box",(.5,.5,.5),"top",((i-2)*.85,0,(d/2-.35)),(0,0,0),"B")
    else:
        top=base
        if kw=="lighthouse": top=B.add("Lamp",base,"gem",(1.3,1.1,1.3),"top",(0,0,0),(0,0,0),"C")
        B.add("Roof",top,"pyramid",(1.7,1.0,1.7) if kw=="lighthouse" else (w*1.18,1.7+(1.2 if tall else 0),d*1.18),
              "top",(0,-.1,0),(0,0,0),"C")
        if not tall and v!=1: B.add("Chimney",base,"box",(.55,1.2,.55),"top",(w*.28,.5,0),(0,0,0),"B")
    B.tag("building")
def b_tree(B,I,r):
    kw=I.get("keyword") or "tree"; v=B.var%4
    if kw=="cactus":
        t=B.add("CoreRoot",None,"box",(1.1,3.4,1.1),None,(0,1.7,0),(0,0,0),"A",studs=True)
        for sx,suf in ((1,"R"),(-1,"L")):
            a=B.add("Arm"+suf,t,"box",(.9,.6,.6),"right" if sx>0 else "left",(0,.3+v*.15,0),(0,0,0),"A")
            B.add("ArmUp"+suf,a,"box",(.55,1.3,.55),"top",(sx*.15,0,0),(0,0,0),"S")
    elif kw=="mushroom":
        stem=B.add("CoreRoot",None,"box",(1.1,1.6,1.1),None,(0,.8,0),(0,0,0),"L")
        cap=B.add("Cap",stem,"box",(3.0,1.0,3.0),"top",(0,0,0),(0,0,0),"C",studs=True)
        for i in range(5):
            x,z=phyllo(i,5,1.0); B.add("Dot%d"%i,cap,"box",(.5,.12,.5),"top",(x,0,z),(0,0,0),"L")
    elif kw in ("flower","plant"):
        st=B.add("CoreRoot",None,"box",(.3,2.4,.3),None,(0,1.2,0),(0,0,0),"S")
        hd=B.add("Bloom",st,"gem",(.8,.5,.8),"top",(0,0,0),(0,0,0),"L")
        B.ring("Petal",hd,6,.7,0,(.5,.2,.55),"C")
        for sx,suf in ((1,"R"),(-1,"L")): B.add("Leaf"+suf,st,"wedge",(.7,.25,.4),None,(sx*.45,-.3,0),(0,0,sx*20),"A")
    elif kw=="palm":
        t0=B.add("CoreRoot",None,"box",(.8,1.6,.8),None,(0,.8,0),(0,0,0),"B")
        t1=B.add("Trunk1",t0,"box",(.7,1.6,.7),"top",(0,0,0),(8,0,0),"D")
        t2=B.add("Trunk2",t1,"box",(.6,1.6,.6),"top",(0,0,0),(8,0,0),"B")
        crown=B.add("Crown",t2,"gem",(.9,.6,.9),"top",(0,0,0),(0,0,0),"D")
        B.ring("Frond",crown,6,.9,.1,(.6,.15,1.8),"A")
    elif kw=="bush":
        b=B.add("CoreRoot",None,"box",(2.6,1.4,2.6),None,(0,.7,0),(0,0,0),"A",studs=True)
        B.add("Bush2",b,"box",(1.8,1.0,1.8),"top",(0,0,0),(0,0,0),"S")
    else:
        tr=B.add("CoreRoot",None,"box",(.95,2.4,.95),None,(0,1.2,0),(0,0,0),"B")
        f1=B.add("Leaf1",tr,"box",(3.2,1.3,3.2),"top",(0,-.2,0),(0,0,0),"A",studs=True)
        f2=B.add("Leaf2",f1,"box",(2.4,1.2,2.4),"top",(0,0,0),(0,0,0),"S")
        f3=B.add("Leaf3",f2,"box",(1.5,1.1,1.5),"top",(0,0,0),(0,0,0),"A")
        if kw=="pine": B.add("Tip",f3,"pyramid",(1.2,1.6,1.2),"top",(0,0,0),(0,0,0),"S")
        if v==1:
            for i in range(4):
                x,z=phyllo(i,4,1.2); B.add("Fruit%d"%i,f1,"gem",(.4,.4,.4),None,(x,.2,z),(0,0,0),"C")
    B.tag("plant")
def b_weapon(B,I,r):
    kw=I.get("keyword") or "sword"
    if kw=="shield":
        s=B.add("CoreRoot",None,"box",(2.4,3.0,.35),None,(0,1.5,0),(0,0,0),"A")
        B.add("Rim",s,"box",(2.7,.3,.4),"top",(0,0,0),(0,0,0),"S")
        B.add("Emblem",s,"gem",(1.0,1.0,.3),"front",(0,0,0),(0,0,0),"C")
        B.tag("weapon"); return
    if kw in ("axe","hammer","spear","staff","wand","bow"):
        ln=2.6 if kw=="wand" else 4.2
        h=B.add("CoreRoot",None,"box",(.2 if kw=="wand" else .32,ln,.2 if kw=="wand" else .32),None,(0,ln/2,0),(0,0,0),"B")
        if kw=="axe":
            hd=B.add("AxeHead",h,"box",(1.3,1.0,.3),"top",(.5,-.8,0),(0,0,0),"A")
            B.add("AxeEdge",hd,"box",(.35,1.3,.26),"right",(0,0,0),(0,0,0),"S")
        elif kw=="hammer": B.add("HammerHead",h,"box",(1.6,.9,.9),"top",(0,-.3,0),(0,0,0),"A")
        elif kw=="spear":
            c=B.add("Collar",h,"box",(.5,.3,.5),"top",(0,0,0),(0,0,0),"S")
            B.add("SpearTip",c,"pyramid",(.5,1.3,.5),"top",(0,0,0),(0,0,0),"L")
        elif kw=="bow":
            B.add("BowTop",h,"box",(.22,1.2,.22),"top",(0,-.1,-.3),(-25,0,0),"B")
            B.add("BowBot",h,"box",(.22,1.2,.22),"bot",(0,.1,-.3),(25,0,0),"B")
            B.add("String",h,"box",(.06,ln,.06),None,(0,0,.5),(0,0,0),"L")
        else: B.add("Orb",h,"gem",(.9,.9,.9),"top",(0,0,0),(0,0,0),"C")
        B.tag("weapon"); return
    bl=2.2 if kw=="dagger" else 3.6
    g=B.add("CoreRoot",None,"box",(.34,1.1,.34),None,(0,.55,0),(0,0,0),"D")
    B.add("Pommel",g,"gem",(.55,.5,.55),"bot",(0,0,0),(0,0,0),"S")
    gd=B.add("Guard",g,"box",(1.5,.28,.45),"top",(0,0,0),(0,0,0),"S")
    bd=B.add("Blade",gd,"box",(.55,bl,.16),"top",(0,0,0),(0,0,0),"L")
    B.add("BladeTip",bd,"pyramid",(.55,.8,.16),"top",(0,0,0),(0,0,0),"L")
    B.add("Fuller",bd,"box",(.14,bl*.75,.2),None,(0,-.2,0),(0,0,0),"C")
    B.tag("weapon")
def b_prop(B,I,r):
    B.add("CoreRoot",None,"box",(2.6,2.2,2.2),None,(0,1.1,0),(0,0,0),"A",studs=True)
    top=B.add("Top","CoreRoot","box",(2.0,1.6,1.8),"top",(0,0,0),(0,0,0),"B",studs=True)
    B.eyes(top,.1,-.95,.4*I["eyes"],.5,sc="L")
    B.add("Mouth",top,"box",(.7,.12,.1),"front",(0,-.35,-.02),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Nub"+suf,"CoreRoot","box",(.5,1.0,.5),"right" if sx>0 else "left",(0,-.1,0),(0,0,sx*-10),"S")
    B.add("Antenna",top,"box",(.15,.8,.15),"top",(0,0,0),(0,0,0),"D")
    B.tag("prop")
BUILDERS={"humanoid":b_humanoid,"octopus":b_octopus,"serpent":b_serpent,"fish":b_fish,"bird":b_bird,
 "crab":b_crab,"spider":b_spider,"golem":b_golem,"turtle":b_turtle,"jelly":b_jelly,"car":b_car,
 "bike":b_bike,"boat":b_boat,"plane":b_plane,"heli":b_heli,"tank":b_tank,
 "quadruped":b_quadruped,"building":b_building,"tree":b_tree,"weapon":b_weapon,"prop":b_prop}
BUDGETS={"humanoid":80,"octopus":100,"serpent":70,"fish":60,"bird":70,"crab":80,"spider":80,"golem":70,
 "turtle":60,"jelly":110,"car":60,"bike":30,"boat":35,"plane":35,"heli":40,"tank":35,
 "quadruped":90,"building":60,"tree":40,"weapon":25,"prop":30}
def critique(spec,I):
    rep={};tot=0.0;ws=0.0
    def add(k,v,w): rep[k]=int(round(v*100));return v*w
    tot+=add("context",1.0 if spec["archetype"]==I["root"] else .15,.14);ws+=.14
    names={p["n"] for p in spec["parts"]}
    tot+=add("connected",1.0 if all(p["p"] in names for p in spec["parts"] if p["p"]) else .2,.08);ws+=.08
    idx={p["n"]:p for p in spec["parts"]}
    def ymin(n):
        p=idx[n];y=p["po"][1]-rot_dims(p["sz"],p["ro"])[1]/2;par=p["p"]
        while par and par in idx: y+=idx[par]["po"][1];par=idx[par]["p"]
        return y
    my=min(ymin(p["n"]) for p in spec["parts"])
    tot+=add("grounded",1.0 if (abs(my)<.45 if not I["float"] else my>1.0) else .3,.08);ws+=.08
    studs=sum(1 for p in spec["parts"] if p["n"].startswith("Stud"))
    tot+=add("style_studs",1.0 if studs>=6 else .4,.10);ws+=.10
    byp={}
    for p in spec["parts"]:
        if p["n"].startswith("Stud") or "_j" in p["n"]: continue
        byp.setdefault(p["p"],[]).append(p)
    bad=0
    for par,lst in byp.items():
        for i in range(len(lst)):
            for j in range(i+1,len(lst)):
                a,b=lst[i],lst[j];da=rot_dims(a["sz"],a["ro"]);db=rot_dims(b["sz"],b["ro"]);vol=1.0
                for ax in range(3):
                    inter=min(a["po"][ax]+da[ax]/2,b["po"][ax]+db[ax]/2)-max(a["po"][ax]-da[ax]/2,b["po"][ax]-db[ax]/2)
                    if inter<=0: vol=0;break
                    vol*=inter
                if vol>0 and vol>.55*min(da[0]*da[1]*da[2],db[0]*db[1]*db[2]): bad+=1
    tot+=add("overlap",max(0,1-bad*.12),.10);ws+=.10
    n=len(spec["parts"]);bud=BUDGETS.get(spec["archetype"],80)
    tot+=add("purpose",1.0 if n<=bud*1.7 else .5,.08);ws+=.08
    if I["colors"]:
        ds=[max(0,1-min(hue_dist(ih,hex_hsv(h)[0]) for h in list(spec["palette"].values())[:6])/90.0) for ih,_,_ in I["colors"]]
        tot+=add("color_match",sum(ds)/len(ds),.14);ws+=.14
    else: tot+=add("color_match",.85,.14);ws+=.14
    want=set(I["traits"]);have=set(spec["traits_present"])
    tot+=add("trait_match",len(want&have)/max(1,len(want)) if want else 1.0,.14);ws+=.14
    sizes=[p["sz"][0] for p in spec["parts"] if not p["n"].startswith("Stud")]
    tot+=add("silhouette",clamp((max(sizes)-min(sizes))/max(.001,max(sizes))/.8,0,1),.07);ws+=.07
    tot+=add("sharp_match",max(0,1-abs(I["sharp"]-spec["sharpness"])/2.0),.07);ws+=.07
    return int(round(100*tot/ws)),rep
def style_vector(spec):
    hs=[hex_hsv(h) for h in list(spec["palette"].values())[:6]]
    return {"sharp":spec["sharpness"],"scale":spec["scale"],"parts":len(spec["parts"]),
            "sat":sum(s for _,s,_ in hs)/len(hs),"val":sum(v for _,_,v in hs)/len(hs),"arch":spec["archetype"]}
def tokens_of(p): return set(tokenize(p))
def memory_priors(mem,prompt):
    tk=tokens_of(prompt);acc=Counter();styles=[];pal=None;bw=0.0;liked=[]
    for e in mem.get("entries",[]):
        et=tokens_of(e.get("prompt",""));inter=len(tk&et)
        sim=inter/max(1.0,math.sqrt(len(tk)*max(1,len(et))))
        acc[e.get("archetype","golem")]+=sim;liked.append((sim,e))
        st=e.get("style")
        if st and sim>.15: styles.append((sim,st));bw+=sim
        if sim>.3 and e.get("palette"): pal=e["palette"]
    blend={k:sum(w*s[k] for w,s in styles)/bw for k in ("sharp","scale","sat","val")} if styles else None
    return acc,blend,pal,sorted(liked,reverse=True)
def _spec_from(B,I,arch,seed,variant,pal):
    return {"id":"m%d_%d"%(int(time.time()*1000)%100000,seed%97),"name":random.Random(seed).choice(NAME_PRE)+NAME_SUF[arch],
      "archetype":arch,"variant":variant,"seed":seed,"sharpness":round(B.sharp,2),"scale":round(B.scale,2),
      "palette":pal,"tags":sorted(B.present),"root":B.root,"parts":B.parts,"mirrored":B.mirrored,
      "counts":dict(B.counts),"traits_present":sorted(B.present),
      "meta":{"scheme":"v8","mods":I["mods"],"prompt":I.get("_prompt",""),"warn":B.warn,
              "species":I.get("species"),"keyword":I.get("keyword"),"unknown":I.get("unknown",[])}}
def _build(I,arch,seed,feat,variant):
    rng=random.Random(seed);pal=synthesize_palette(I,rng)
    if feat.get("colors") and not I["palette_force"]:
        fc=feat["colors"];pal["A"]=fc[0];pal["B"]=fc[min(1,len(fc)-1)];pal["C"]=fc[min(2,len(fc)-1)]
        pal["S"]=fc[min(3,len(fc)-1)]
    B=Builder(seed,pal,rng,I["sharp"],I["size"]);B.var=variant
    try:
        BUILDERS[arch](B,I,rng)
        for t in list(I["traits"]):
            fn=ADDONS.get(t)
            if fn and t not in I["neg"]: fn(B,I,rng); B.tag(t)
    except Exception as e:
        B.warn=repr(e)
        if not B.parts: raise
    if not B.parts: raise RuntimeError("empty build for "+arch)
    if arch=="prop" and I.get("unknown") and not B.warn:
        B.warn="unknown subject %r -> generic prop (add it to ROOTS/SPECIES_KEYS to get a real model)"%I["unknown"][0]
    if not I["float"]: ground(B)
    pose_wrap(B,I["pose"],I["float"])
    return _spec_from(B,I,arch,seed,variant,pal)
def build_one(prompt,seed=7,var=0,feat=None):
    I=parse_intent(prompt);I["_prompt"]=prompt
    return _build(I,I["root"],seed,feat or {},var),I
def structural_checks(spec,I):
    out=[];P=spec["parts"];names=[p["n"] for p in P];idx={p["n"]:p for p in P}
    out.append(("root_match",spec["archetype"]==I["root"]))
    out.append(("names_unique",len(names)==len(set(names))))
    out.append(("parents_exist",all(p["p"] in idx for p in P if p["p"])))
    out.append(("finite",all(isinstance(v,(int,float)) and v==v for p in P for v in p["po"]+p["sz"]+p["ro"])))
    def ymin(n):
        p=idx[n];y=p["po"][1]-rot_dims(p["sz"],p["ro"])[1]/2;par=p["p"]
        while par and par in idx: y+=idx[par]["po"][1];par=idx[par]["p"]
        return y
    my=min(ymin(n) for n in names)
    out.append(("grounded",abs(my)<.45 if not I["float"] else my>1.0))
    out.append(("budget",len(P)<=BUDGETS.get(spec["archetype"],90)*1.7))
    out.append(("palette_hex",all(re.fullmatch(r"#[0-9a-f]{6}",c) for c in spec["palette"].values())))
    out.append(("mirror_ok",all((a in idx and b in idx) for a,b in spec["mirrored"])))
    tags=set(spec["traits_present"])
    out.append(("traits_applied",all(t in tags for t in I["traits"] if t in ADDONS)))
    out.append(("neg_absent",not any(t in tags for t in I["neg"])))
    if spec["archetype"]=="humanoid":
        need=["Head","Chest","Neck","ArmR","ArmL","ForeR","ForeL","HandR","HandL",
              "ThighR","ThighL","ShoeR","ShoeL","EyeR","PupilR","Mouth"]
        out.append(("human_parts",all(n in idx for n in need)))
        hd=idx.get("Head");hnd=idx.get("HandR")
        out.append(("skin_role",bool(hd and hd["c"]=="K" and hnd and hnd["c"]=="K")))
    if spec["archetype"]=="quadruped":
        legs=[p for p in P if p["n"].startswith("Leg")]
        out.append(("four_legs",len(legs)==4))
        out.append(("quad_parts",all(n in idx for n in ["Head","Neck","Snout","EyeR","EyeL"])))
        out.append(("species_known",(I.get("species") or "beast") in SPECIES))
    if spec["archetype"]=="car":
        wheels=[p for p in P if p["n"].startswith("Wheel")]
        hubs=[p for p in P if p["n"].startswith("Hub")]
        xs={1 if p["po"][0]>0 else -1 for p in wheels}; zs={1 if p["po"][2]>0 else -1 for p in wheels}
        out.append(("four_wheels",len(wheels)==4 and len(hubs)==4))
        out.append(("corners",len(xs)==2 and len(zs)==2))
        out.append(("windshield",any(p["n"]=="WinF" for p in P)))
    return out
def generate(body,mem):
    t0=time.time();prompt=body.get("prompt","human");it=int(body.get("iteration",0))
    nonce=body.get("nonce","x");reasons=body.get("reasons",[]);feat=body.get("features") or {}
    I=parse_intent(prompt);I["_prompt"]=prompt
    mbias,blend,mpal,liked=memory_priors(mem,prompt)
    if blend:
        I["sharp"]=clamp(I["sharp"]*.75+blend["sharp"]*.25,.2,2.6);I["size"]*=.9+blend["scale"]*.1
    if "wrong creature" in reasons:
        cur=ARCHES.index(I["root"]) if I["root"] in ARCHES else 0
        I["root"]=ARCHES[(cur+3)%len(ARCHES)]
        if I["root"]!="quadruped": I["species"]=None
    if "too many spikes" in reasons: I["sharp"]=max(.2,I["sharp"]-1.0)
    if "not enough detail" in reasons: I["sharp"]=min(2.6,I["sharp"]+.8)
    if "wrong colors" in reasons: I["palette_force"]=None;I["colors"]=[]
    K=6+min(6,it*2);best=None;tried=0
    for k in range(K):
        if time.time()-t0>BUDGET: break
        seed=zlib.crc32(("%s|%d|%s|%d"%(prompt,it,nonce,k)).encode())
        var=(it+k)%4
        I2=dict(I);I2["sharp"]=clamp(I["sharp"]+random.Random(seed).uniform(-.15,.15),.2,2.6)
        try: spec=_build(I2,I["root"],seed,feat,var)
        except Exception: continue
        tried+=1;s,rep=critique(spec,I2);spec["score"]=s;spec["report"]=rep
        if best is None or s>best["score"]: best=spec
    if best:
        for m in range(3):
            if time.time()-t0>BUDGET: break
            I3=dict(I);I3["sharp"]=clamp(I["sharp"]+random.uniform(-.3,.3),.2,2.6)
            I3["size"]=clamp(I["size"]+random.uniform(-.1,.1),.5,1.8)
            seed=best["seed"]+m+13;var=(best["variant"]+1+m)%4
            try: cand=_build(I3,best["archetype"],seed,feat,var)
            except Exception: continue
            s2,r2=critique(cand,I3);cand["score"]=s2;cand["report"]=r2;tried+=1
            if s2>best["score"]: best=cand
    if best is None:
        I4=dict(I);I4["traits"]={};I4["float"]=False;I4["pose"]=0
        best=_build(I4,"prop",1,feat,0)
        best["score"],best["report"]=critique(best,dict(I4,root="prop"))
        best["meta"]["error"]="all candidates failed — fallback prop"
        tried=1
    best["meta"].update({"beam":K,"tried":tried,"iteration":it,"seconds":round(time.time()-t0,2)})
    return best
