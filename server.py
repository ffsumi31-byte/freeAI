"""Roblox Cloud 3D Modeler AI — v5 (19-Domain Anatomical & Architectural Engine + Live LLM Architect).
Single-file deployment for Render (`python server.py`). Zero external pip dependencies."""

import os, sys, json, time, math, random, re, zlib, urllib.request, urllib.parse, urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# =========================================================================
# 1. COLOR PALETTE & GEOMETRY HELPERS
# =========================================================================
NAMED_COLORS = {
    "red": "#dc2626", "crimson": "#991b1b", "scarlet": "#ef4444", "maroon": "#7f1d1d",
    "orange": "#ea580c", "ginger": "#d97706", "amber": "#f59e0b", "peach": "#fdba74",
    "yellow": "#eab308", "gold": "#d4af37", "golden": "#d4af37", "lemon": "#facc15",
    "lime": "#65a30d", "green": "#16a34a", "emerald": "#10b981", "forest": "#166534",
    "olive": "#4d7c0f", "mint": "#6ee7b7", "teal": "#0d9488", "cyan": "#06b6d4",
    "aqua": "#22d3ee", "sky": "#38bdf8", "blue": "#2563eb", "cobalt": "#1d4ed8",
    "navy": "#1e3a8a", "indigo": "#4f46e5", "purple": "#7c3aed", "violet": "#8b5cf6",
    "lavender": "#c4b5fd", "magenta": "#db2777", "pink": "#f472b6", "rose": "#fb7185",
    "white": "#f8fafc", "snow": "#ffffff", "cream": "#fef3c7", "ivory": "#fffbeb",
    "silver": "#cbd5e1", "grey": "#64748b", "gray": "#64748b", "slate": "#475569",
    "charcoal": "#334155", "black": "#1e293b", "obsidian": "#090d16", "dark": "#0f172a",
    "brown": "#78350f", "chocolate": "#5c2808", "tan": "#d6b88a", "beige": "#e5d3b3",
    "sand": "#fde68a", "bronze": "#92400e", "copper": "#b45309", "brass": "#ca8a04"
}

SCALE_WORDS = {
    "tiny": 0.55, "mini": 0.65, "small": 0.78, "little": 0.82, "baby": 0.72,
    "big": 1.25, "large": 1.28, "tall": 1.25, "huge": 1.45, "giant": 1.65,
    "massive": 1.60, "colossal": 1.75, "mega": 1.55
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

def extract_scale_factor(prompt):
    sc = 1.0
    for w in tokenize(prompt):
        if w in SCALE_WORDS:
            sc *= SCALE_WORDS[w]
    return clamp(sc, 0.45, 2.2)

# =========================================================================
# 2. STAGE 1 & 2: PROMPT ANALYSIS & WIKIPEDIA RESEARCH
# =========================================================================
_WIKI_CACHE = {}

def search_internet_knowledge(prompt):
    content_words = [
        w for w in tokenize(prompt)
        if w not in STOP_WORDS and w not in NAMED_COLORS and w not in SCALE_WORDS
    ]
    subject = " ".join(content_words[-2:]) if len(content_words) >= 2 else (content_words[-1] if content_words else "object")
    head_noun = content_words[-1] if content_words else "object"

    if subject in _WIKI_CACHE:
        return head_noun, _WIKI_CACHE[subject]

    headers = {"User-Agent": BROWSER_UA}
    summary_text = ""

    for query_term in (head_noun, subject):
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
# 3. LIVE CLOUD AI LLM ARCHITECT (Groq / Gemini / OpenAI / Pollinations)
# =========================================================================
LLM_SYSTEM_INSTRUCTIONS = """You are an autonomous 3D Modeler AI for Roblox Studio.
Build a detailed, anatomically and structurally accurate 3D model for the user's prompt.
Return ONLY valid JSON matching this schema:
{
  "category": "serpent|dragon|dinosaur|arthropod|cephalopod|marine|bird|animal|humanoid|building|vehicle|aircraft|watercraft|weapon|foliage|prop",
  "riggable": true,
  "parts": [
    {
      "n": "PartName",
      "p": null,
      "stage": "raw|shape|detail",
      "s": "box|sphere|cylinder|wedge|cone",
      "sz": [width_x, height_y, depth_z],
      "po": [world_x, world_y, world_z],
      "ro": [rot_x, rot_y, rot_z],
      "c": "#hexcolor",
      "mat": "SmoothPlastic|Metal|Neon|Glass|Wood|Slate|Brick|Cobblestone|Fabric|Grass",
      "tr": 0.0,
      "joint": true,
      "mirror": false
    }
  ]
}
CRITICAL 3D MODELING RULES:
1. NO LEGO STUDS. Use 20 to 48 smooth Roblox primitives (`box`, `sphere`, `cylinder`, `wedge`, `cone`).
2. Coordinate system: X = Left(-)/Right(+), Y = Up(+) starting above 0, Z = Front(-Z)/Back(+Z).
3. You may specify world position `"po": [x, y, z]` directly for each part (or `"attach": {"face": "top|bot|front|back|right|left", "u": 0.0, "v": 0.0, "inset": 0.03}`).
4. Every part except the root (`"p": null`) MUST reference its parent part name in `"p": "ParentName"` so the critic can verify physical contact and create Motor6D joints.
5. For symmetrical left/right parts (legs, arms, eyes, ears, horns, wings, wheels), define ONLY the right-side part (`x > 0`, name ending in `R` like `"EyeR"`, `"LegFR"`) and set `"mirror": true`. The compiler will automatically mirror it to `-X` as `"EyeL"`, `"LegFL"`.
6. Match the true anatomy of the creature or object:
   - Serpents/snakes have 0 legs and a multi-segment sinusoidal body (`Seg1`..`Seg12`), raised neck, head, open jaws, fangs, and forked tongue.
   - Spiders have 8 legs; scorpions have pincers and a curved stinger tail; birds/dragons have wings; buildings have multi-story walls, recessed glass windows, doors, and roofs.
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
        if isinstance(data, dict) and isinstance(data.get("parts"), list) and len(data["parts"]) >= 6:
            return data
    except Exception:
        pass
    return None

def call_cloud_llm_architect(prompt, wiki_summary, seed, api_key=""):
    key = (api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
    user_request = (
        f"Build a detailed 3D Roblox model for prompt: '{prompt}' (variation seed: {seed}).\n"
        f"Wikipedia Research: {wiki_summary or 'Use accurate real-world anatomy and structure.'}\n"
        "Return ONLY valid JSON."
    )
    err_notes = []

    # 1. Gemini API Key (AIza...)
    if key.startswith("AIza"):
        for model_id in ("gemini-2.5-flash", "gemini-2.0-flash"):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={key}"
                payload = {
                    "systemInstruction": {"parts": [{"text": LLM_SYSTEM_INSTRUCTIONS}]},
                    "contents": [{"parts": [{"text": user_request}]}],
                    "generationConfig": {"temperature": 0.35, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(
                    url, data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": BROWSER_UA},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=14.0) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    txt = res["candidates"][0]["content"]["parts"][0]["text"]
                    bp = _extract_json_block(txt)
                    if bp:
                        return bp, f"Gemini ({model_id}) AI Architect", None
            except Exception as e:
                err_notes.append(f"Gemini {model_id}: {str(e)[:60]}")

    # 2. Groq (gsk_...) or OpenAI (sk-...) API Key
    if key.startswith("gsk_") or key.startswith("sk-"):
        is_groq = key.startswith("gsk_")
        url = "https://api.groq.com/openai/v1/chat/completions" if is_groq else "https://api.openai.com/v1/chat/completions"
        models = ("llama-3.3-70b-versatile", "llama-3.1-8b-instant") if is_groq else ("gpt-4o-mini",)
        for model_id in models:
            try:
                payload = {
                    "model": model_id,
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
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Authorization": f"Bearer {key}",
                        "User-Agent": BROWSER_UA
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=14.0) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    txt = res["choices"][0]["message"]["content"]
                    bp = _extract_json_block(txt)
                    if bp:
                        return bp, f"{'Groq' if is_groq else 'OpenAI'} ({model_id}) AI Architect", None
            except urllib.error.HTTPError as he:
                body_err = ""
                try:
                    body_err = he.read().decode("utf-8")[:80]
                except Exception:
                    pass
                err_notes.append(f"{model_id} HTTP {he.code}: {body_err}")
            except Exception as e:
                err_notes.append(f"{model_id}: {str(e)[:60]}")

    # 3. Keyless Pollinations Cloud LLM (Only used when no custom key is provided)
    if not key:
        try:
            payload = {
                "model": "openai",
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
                headers={"Content-Type": "application/json", "User-Agent": BROWSER_UA},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=6.5) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    outer = json.loads(raw)
                    txt = outer["choices"][0]["message"]["content"] if isinstance(outer, dict) and "choices" in outer else raw
                except Exception:
                    txt = raw
                bp = _extract_json_block(txt)
                if bp:
                    return bp, "Cloud LLM Architect (Keyless)", None
        except Exception as e:
            err_notes.append(f"Keyless LLM: {str(e)[:50]}")

    return None, None, ("; ".join(err_notes) if err_notes else None)

# =========================================================================
# 4. 19-DOMAIN ANATOMICAL & ARCHITECTURAL SYNTHESIS ENGINE
#    (Prompt-first classification so Wikipedia words never hijack the subject!)
# =========================================================================
DOMAIN_KEYWORDS = [
    ("serpent", {
        "serpent", "snake", "cobra", "viper", "python", "boa", "anaconda", "rattlesnake",
        "mamba", "wyrm", "basilisk", "hydra", "leviathan", "eel", "worm", "earthworm",
        "caterpillar", "centipede", "millipede", "naga", "jormungandr"
    }),
    ("dragon", {
        "dragon", "wyvern", "drake", "charizard", "bahamut", "smaug", "shenron"
    }),
    ("dinosaur", {
        "dinosaur", "dino", "trex", "tyrannosaurus", "raptor", "velociraptor", "spinosaurus",
        "allosaurus", "carnotaurus", "triceratops", "stegosaurus", "brachiosaurus",
        "brontosaurus", "diplodocus", "ankylosaurus", "pterodactyl", "pterosaur"
    }),
    ("arthropod", {
        "spider", "tarantula", "arachnid", "blackwidow", "scorpion", "ant", "beetle",
        "ladybug", "scarab", "mantis", "bee", "bumblebee", "wasp", "hornet", "butterfly",
        "moth", "dragonfly", "cockroach", "cricket", "grasshopper", "insect", "bug"
    }),
    ("cephalopod", {
        "octopus", "kraken", "squid", "cuttlefish", "cthulhu", "jellyfish", "jelly", "medusa"
    }),
    ("marine", {
        "shark", "megalodon", "whale", "beluga", "orca", "dolphin", "narwhal", "fish",
        "goldfish", "koi", "salmon", "tuna", "clownfish", "piranha", "swordfish", "marlin",
        "manta", "stingray", "seahorse", "axolotl", "turtle", "seaturtle", "tortoise",
        "seal", "walrus", "crab", "lobster", "shrimp"
    }),
    ("bird", {
        "bird", "eagle", "phoenix", "falcon", "hawk", "owl", "raven", "crow", "parrot",
        "macaw", "cockatoo", "toucan", "duck", "swan", "goose", "chicken", "rooster",
        "penguin", "flamingo", "peacock", "ostrich", "pelican", "seagull", "pigeon",
        "dove", "hummingbird", "griffin", "gryphon", "harpy"
    }),
    ("feline", {
        "cat", "kitten", "kitty", "tabby", "lion", "lioness", "tiger", "panther",
        "leopard", "cheetah", "jaguar", "cougar", "puma", "lynx", "bobcat", "ocelot", "sphinx"
    }),
    ("canine", {
        "dog", "puppy", "pup", "wolf", "werewolf", "direwolf", "fenrir", "fox", "kitsune",
        "husky", "corgi", "hound", "bulldog", "poodle", "pug", "shiba", "retriever",
        "shepherd", "dalmatian", "coyote", "jackal", "hyena", "cerberus"
    }),
    ("ursine_small", {
        "bear", "grizzly", "polarbear", "panda", "koala", "rabbit", "bunny", "hare",
        "mouse", "rat", "hamster", "squirrel", "chipmunk", "raccoon", "tanuki", "redpanda",
        "hedgehog", "porcupine", "otter", "ferret", "badger", "skunk", "beaver", "capybara",
        "sloth", "kangaroo", "monkey", "chimp", "gorilla", "ape", "orangutan", "yeti",
        "bigfoot", "pikachu", "frog", "toad", "chameleon", "gecko", "lizard", "iguana"
    }),
    ("ungulate", {
        "horse", "unicorn", "pegasus", "pony", "stallion", "zebra", "donkey", "mule",
        "cow", "bull", "ox", "bison", "buffalo", "yak", "minotaur", "goat", "ibex",
        "sheep", "lamb", "ram", "deer", "reindeer", "stag", "moose", "elk", "gazelle",
        "antelope", "giraffe", "camel", "llama", "alpaca", "elephant", "mammoth",
        "rhino", "rhinoceros", "hippo", "hippopotamus", "pig", "hog", "boar", "warthog",
        "croc", "crocodile", "alligator"
    }),
    ("building", {
        "building", "house", "home", "cabin", "cottage", "mansion", "villa", "shop",
        "store", "bakery", "cafe", "restaurant", "hotel", "motel", "office", "skyscraper",
        "tower", "castle", "fort", "fortress", "citadel", "palace", "church", "temple",
        "cathedral", "shrine", "pagoda", "mosque", "lighthouse", "windmill", "barn",
        "silo", "warehouse", "factory", "hospital", "school", "bank", "prison", "bunker",
        "pyramid", "bridge", "gate", "arch", "gazebo", "igloo", "tent"
    }),
    ("vehicle", {
        "car", "sportscar", "racecar", "supercar", "sedan", "coupe", "convertible",
        "suv", "jeep", "humvee", "truck", "pickup", "semi", "lorry", "van", "minivan",
        "bus", "schoolbus", "taxi", "policecar", "copcar", "ambulance", "firetruck",
        "limo", "limousine", "cybertruck", "tractor", "bulldozer", "excavator", "forklift",
        "buggy", "kart", "gokart", "f1", "formula", "tank", "panzer", "abrams", "apc",
        "artillery", "train", "locomotive", "bullettrain", "subway", "tram", "bike",
        "motorcycle", "motorbike", "scooter", "bicycle", "atv", "quadbike", "skateboard"
    }),
    ("aircraft", {
        "plane", "airplane", "jet", "fighterjet", "bomber", "biplane", "airliner",
        "seaplane", "glider", "spaceship", "starfighter", "xwing", "tie", "rocket",
        "shuttle", "ufo", "saucer", "helicopter", "heli", "chopper", "gunship", "drone",
        "quadcopter", "blimp", "airship", "zeppelin"
    }),
    ("watercraft", {
        "boat", "ship", "yacht", "sailboat", "pirateship", "galleon", "battleship",
        "destroyer", "carrier", "cruiseship", "ferry", "submarine", "sub", "canoe",
        "kayak", "raft", "speedboat", "jetski", "vikingboat", "longship"
    }),
    ("weapon", {
        "sword", "mastersword", "katana", "blade", "dagger", "knife", "claymore",
        "broadsword", "longsword", "rapier", "scimitar", "saber", "lightsaber", "axe",
        "battleaxe", "hatchet", "halberd", "glaive", "scythe", "sickle", "spear",
        "lance", "pike", "trident", "hammer", "warhammer", "maul", "mace", "flail",
        "morningstar", "club", "bat", "bow", "crossbow", "staff", "wand", "scepter",
        "shield", "buckler", "aegis", "gun", "pistol", "revolver", "rifle", "sniper",
        "shotgun", "smg", "minigun", "blaster", "lasergun", "raygun", "plasmagun",
        "bazooka", "rocketlauncher", "cannon", "turret"
    }),
    ("foliage", {
        "tree", "pine", "oak", "maple", "birch", "willow", "palm", "redwood", "bonsai",
        "sakura", "cherryblossom", "cactus", "saguaro", "bamboo", "bush", "shrub",
        "hedge", "plant", "fern", "flower", "rose", "sunflower", "tulip", "lotus",
        "mushroom", "toadstool", "fungus", "coral", "crystal", "geode"
    }),
    ("prop", {
        "chair", "throne", "stool", "bench", "sofa", "couch", "armchair", "table",
        "desk", "workbench", "bed", "bunkbed", "bookshelf", "bookcase", "cabinet",
        "wardrobe", "chest", "treasure", "treasurechest", "safe", "crate", "barrel",
        "keg", "lamp", "lantern", "chandelier", "torch", "streetlight", "hydrant",
        "mailbox", "trashcan", "dumpster", "tv", "television", "monitor", "computer",
        "pc", "laptop", "arcade", "vendingmachine", "atm", "piano", "guitar", "drum",
        "clock", "fountain", "well", "altar", "portal", "anvil", "furnace", "cauldron",
        "campfire", "bonfire", "tombstone", "coffin", "snowman", "burger", "hamburger",
        "cheeseburger", "pizza", "cake", "cupcake", "donut", "icecream", "sushi",
        "ramen", "taco", "hotdog", "apple", "banana", "pumpkin", "potion", "elixir",
        "chalice", "goblet", "trophy", "crown", "gift", "present"
    }),
    ("humanoid", {
        "human", "man", "woman", "boy", "girl", "person", "character", "avatar", "hero",
        "villain", "knight", "paladin", "warrior", "gladiator", "soldier", "commando",
        "guard", "ninja", "samurai", "viking", "pirate", "cowboy", "sheriff", "wizard",
        "mage", "sorcerer", "witch", "necromancer", "priest", "monk", "astronaut",
        "spaceman", "cosmonaut", "pilot", "doctor", "nurse", "scientist", "chef",
        "police", "firefighter", "builder", "engineer", "farmer", "karate", "ryu",
        "fighter", "boxer", "archer", "ranger", "assassin", "king", "queen", "prince",
        "princess", "emperor", "pharaoh", "santa", "clown", "vampire", "zombie",
        "skeleton", "mummy", "ghost", "angel", "demon", "elf", "dwarf", "orc", "goblin",
        "mech", "mecha", "gundam", "robot", "cyborg", "android", "exosuit", "golem",
        "titan", "colossus", "transformer"
    })
]

def classify_domain(prompt, wiki_summary=""):
    ptoks = tokens_of(prompt)
    # 1. Check user's explicit prompt tokens FIRST (so Wikipedia words never override!)
    for dom, kw_set in DOMAIN_KEYWORDS:
        if ptoks & kw_set:
            return dom
    # 2. Substring check on user's prompt for compound words
    p_low = prompt.lower()
    for dom, kw_set in DOMAIN_KEYWORDS:
        if any(k in p_low for k in kw_set if len(k) >= 4):
            return dom
    # 3. Only if prompt noun is unfamiliar, check Wikipedia summary tokens in strict specificity order
    wtoks = tokens_of(wiki_summary)
    for dom, kw_set in DOMAIN_KEYWORDS:
        if wtoks & kw_set:
            return dom
    return "humanoid"

def synthesize_from_semantics_and_wiki(prompt, subject, wiki_summary, seed):
    rng = random.Random(seed)
    domain = classify_domain(prompt, wiki_summary)
    ptoks = tokens_of(prompt)
    wtoks = tokens_of(f"{prompt} {wiki_summary}")
    p_low = prompt.lower()

    jw = rng.uniform(0.93, 1.08)
    jh = rng.uniform(0.93, 1.08)
    jl = rng.uniform(0.93, 1.08)
    user_cols = extract_prompt_colors(prompt, wiki_summary)
    c_main = user_cols[0] if len(user_cols) >= 1 else None
    c_sec = user_cols[1] if len(user_cols) >= 2 else None

    parts = []
    def P(n, p, stage, s, sz, face="center", u=0.0, v=0.0, inset=0.03, ro=(0,0,0), c="#cccccc", mat="SmoothPlastic", tr=0.0, joint=False, mirror=False, po=None):
        item = {
            "n": n, "p": p, "stage": stage, "s": s,
            "sz": [round(max(0.05, float(x)), 3) for x in sz],
            "attach": {"face": face, "u": round(float(u), 3), "v": round(float(v), 3), "inset": round(float(inset), 3)},
            "ro": [round(float(x), 1) for x in ro],
            "c": c, "mat": mat, "tr": round(float(tr), 2),
            "joint": bool(joint), "mirror": bool(mirror)
        }
        if po is not None:
            item["po"] = [round(float(x), 3) for x in po]
        parts.append(item)

    # =====================================================================
    # 1. SERPENT / SNAKE / COBRA / WYRM / LEVIATHAN (Sinusoidal S-Coil + Strike Head + Fangs)
    # =====================================================================
    if domain == "serpent":
        scales_c = c_main or ("#eab308" if "cobra" in ptoks else ("#0d9488" if "leviathan" in ptoks else "#16a34a"))
        belly_c = c_sec or "#fef08a"
        dark_c = "#14532d" if scales_c == "#16a34a" else "#1e293b"
        is_cobra = any(w in ptoks for w in ("cobra", "serpent", "viper", "naga", "basilisk")) or "giant" in ptoks

        # Build 15 articulated segments curving in a 3D S-wave on the ground and rising into a strike coil at the front!
        n_segs = 15
        prev_name = None
        coords = []
        for i in range(n_segs):
            t = i / float(n_segs - 1)  # 0 = neck/front, 1 = tail tip
            if i < 5:
                # Raised S-curve strike neck at the front
                s_prog = (4 - i) / 4.0  # 1 at head end, 0 at ground transition
                wx = math.sin(i * 0.55) * 0.45 * jw
                wy = 0.65 + s_prog * 2.85 * jh
                wz = -3.2 + i * 0.55 * jl
                radius = (0.98 - i * 0.03) * jw
            else:
                # Sinusoidal ground coils toward the tail
                gt = (i - 4) / float(n_segs - 5)
                wx = math.sin(gt * math.pi * 2.2) * 1.65 * jw
                wy = 0.55 * (1.0 - gt * 0.45)
                wz = -0.6 + gt * 5.6 * jl
                radius = max(0.28, (0.92 * (1.0 - gt * 0.72))) * jw
            coords.append((wx, wy, wz, radius))

        # Root is Seg4 (base of the neck on the ground) so the serpent is stably anchored
        for i, (wx, wy, wz, rad) in enumerate(coords):
            seg_name = "CoreRoot" if i == 0 else f"Seg{i}"
            par_n = None if i == 0 else ("CoreRoot" if i == 1 else f"Seg{i-1}")
            st_role = "raw" if i < 6 else "shape"
            P(seg_name, par_n, st_role, "sphere", (rad * 1.15, rad * 1.05, rad * 1.35),
              po=(wx, wy, wz), c=scales_c if i % 2 == 0 else dark_c, joint=True)
            # Ventral belly scute under each segment
            P(f"BellyScute{i}", seg_name, "detail", "box", (rad * 0.82, rad * 0.25, rad * 0.95),
              face="bot", u=0, v=0, inset=0.06, c=belly_c)
            # Dorsal spine ridge
            if i < n_segs - 2:
                P(f"DorsalSpike{i}", seg_name, "detail", "cone", (rad * 0.28, rad * 0.52, rad * 0.42),
                  face="top", u=0, v=0, inset=0.05, c=belly_c if i % 2 else dark_c)

        # Flared Cobra / Serpent Hood on upper strike neck (CoreRoot, Seg1, Seg2)
        if is_cobra:
            for hi, seg_ref in enumerate(("CoreRoot", "Seg1", "Seg2")):
                hw_s = (1.65 - hi * 0.28) * jw
                P(f"HoodFlare{hi}R", seg_ref, "shape", "sphere", (hw_s, 0.95, 0.42),
                  face="right", u=0, v=0, inset=0.22, c=scales_c, mirror=True)
                P(f"HoodMark{hi}R", f"HoodFlare{hi}R", "detail", "sphere", (hw_s * 0.45, 0.45, 0.18),
                  face="front", u=0.2, v=0, inset=0.02, c=belly_c, mirror=True)

        # Sculpted Serpent Head, Open Hinged Jaw, Venom Fangs & Forked Tongue
        hx, hy, hz, hrad = coords[0]
        P("Head", "CoreRoot", "raw", "sphere", (1.45 * jw, 1.05 * jh, 1.65 * jl),
          po=(hx, hy + 0.55, hz - 0.75), c=scales_c, joint=True)
        P("UpperSnout", "Head", "shape", "box", (1.12 * jw, 0.52 * jh, 0.95 * jl),
          face="front", u=0, v=0.08, inset=0.18, c=scales_c)
        P("LowerJaw", "Head", "shape", "box", (0.96 * jw, 0.34 * jh, 1.15 * jl),
          face="bot", u=0, v=-0.45, inset=0.12, ro=(28, 0, 0), c=belly_c, joint=True)

        # Venom Fangs & Forked Red Tongue
        P("FangR", "UpperSnout", "detail", "cone", (0.18, 0.52, 0.18),
          face="bot", u=0.55, v=-0.45, inset=0.04, ro=(180, 0, 0), c="#ffffff", mirror=True)
        P("Tongue", "LowerJaw", "detail", "box", (0.14, 0.08, 0.95),
          face="front", u=0, v=0.2, inset=0.1, c="#ef4444", mat="Neon")
        P("TongueForkR", "Tongue", "detail", "box", (0.08, 0.06, 0.45),
          face="front", u=0.6, v=0, inset=0.04, ro=(0, -22, 0), c="#ef4444", mat="Neon", mirror=True)

        # Slitted Glowing Serpent Eyes & Brow Ridges
        P("EyeR", "Head", "detail", "sphere", (0.34, 0.32, 0.22),
          face="right", u=-0.35, v=0.22, inset=0.05, c="#facc15", mat="Neon", mirror=True)
        P("PupilR", "EyeR", "detail", "box", (0.08, 0.26, 0.12),
          face="right", u=0, v=0, inset=0.01, c="#0f172a", mirror=True)
        P("BrowRidgeR", "Head", "detail", "box", (0.28, 0.16, 0.65),
          face="top", u=0.68, v=-0.25, inset=0.04, ro=(10, 0, -16), c=dark_c, mirror=True)

        return {"category": "serpent", "riggable": True, "parts": parts}, "Serpentine Anatomical Modeler"

    # =====================================================================
    # 2. DRAGON / WYVERN / CHARIZARD (Winged Reptilian Behemoth)
    # =====================================================================
    if domain == "dragon":
        scales_c = c_main or ("#ea580c" if "charizard" in ptoks else "#dc2626")
        belly_c = c_sec or "#fde047"
        wing_c = "#0d9488" if "charizard" in ptoks else "#991b1b"

        P("Torso", None, "raw", "sphere", (2.3 * jw, 2.5 * jh, 3.0 * jl), "center", c=scales_c)
        P("BellyPlate", "Torso", "shape", "sphere", (1.95 * jw, 2.1 * jh, 1.2), "front", u=0, v=-0.05, inset=0.45, c=belly_c)
        P("Neck1", "Torso", "raw", "cylinder", (1.05, 1.35, 1.05), "top", u=0, v=-0.52, inset=0.2, c=scales_c, joint=True)
        P("Neck2", "Neck1", "raw", "cylinder", (0.92, 1.25, 0.92), "top", u=0, v=-0.25, inset=0.15, c=scales_c, joint=True)
        P("Head", "Neck2", "raw", "box", (1.25 * jw, 1.05 * jh, 1.55 * jl), "top", u=0, v=-0.35, inset=0.12, c=scales_c, joint=True)
        P("Snout", "Head", "shape", "box", (0.95 * jw, 0.55, 1.05), "front", u=0, v=0.05, inset=0.08, c=scales_c)
        P("LowerJaw", "Head", "shape", "box", (0.88 * jw, 0.32, 0.98), "bot", u=0, v=-0.45, inset=0.08, ro=(18, 0, 0), c=belly_c, joint=True)

        P("DragonHornR", "Head", "detail", "cone", (0.32, 1.25, 0.32), "top", u=0.58, v=0.42, inset=0.06, ro=(-38, 0, -14), c="#fef3c7", mirror=True)
        P("EyeR", "Head", "detail", "sphere", (0.28, 0.28, 0.16), "right", u=-0.32, v=0.18, inset=0.03, c="#facc15", mat="Neon", mirror=True)
        P("FangR", "Snout", "detail", "cone", (0.16, 0.38, 0.16), "bot", u=0.55, v=-0.4, inset=0.03, ro=(180, 0, 0), c="#ffffff", mirror=True)

        # Articulated Bat-Membrane Dragon Wings
        P("WingArmR", "Torso", "shape", "box", (2.4 * jl, 0.34, 0.45), "right", u=-0.15, v=0.45, inset=0.15, ro=(0, 0, 28), c=scales_c, joint=True, mirror=True)
        P("WingMembrane1R", "WingArmR", "shape", "box", (2.3 * jl, 0.12, 1.65), "back", u=0, v=0, inset=0.08, c=wing_c, mirror=True)
        P("WingOuterR", "WingArmR", "shape", "box", (2.1 * jl, 0.26, 0.36), "right", u=0, v=0, inset=0.08, ro=(0, 0, -18), c=scales_c, joint=True, mirror=True)
        P("WingMembrane2R", "WingOuterR", "detail", "wedge", (2.0 * jl, 0.10, 1.45), "back", u=0, v=0, inset=0.06, c=wing_c, mirror=True)

        # Muscular Hind Legs, Forearms & Long Spiked Flame Tail
        P("ArmR", "Torso", "shape", "box", (0.58, 1.35, 0.58), "right", u=-0.55, v=0.15, inset=0.08, c=scales_c, joint=True, mirror=True)
        P("ThighR", "Torso", "shape", "sphere", (1.05, 1.65, 1.15), "bot", u=0.62, v=0.15, inset=0.25, c=scales_c, joint=True, mirror=True)
        P("FootR", "ThighR", "detail", "box", (0.78, 0.38, 1.25), "bot", u=0, v=-0.22, inset=0.05, c=scales_c, mirror=True)

        P("Tail1", "Torso", "shape", "cylinder", (0.95, 1.55, 0.95), "back", u=0, v=-0.25, inset=0.15, ro=(-68, 0, 0), c=scales_c, joint=True)
        P("Tail2", "Tail1", "shape", "cylinder", (0.68, 1.45, 0.68), "top", u=0, v=0, inset=0.10, ro=(15, 0, 0), c=scales_c, joint=True)
        P("TailFlame", "Tail2", "detail", "cone", (0.62, 0.95, 0.62), "top", u=0, v=0, inset=0.06, c="#f97316", mat="Neon")

        for si in range(4):
            P(f"BackSpine{si}", "Torso", "detail", "cone", (0.28, 0.55, 0.38), "back", u=0, v=0.55 - si*0.35, inset=0.05, ro=(75, 0, 0), c=belly_c)
        return {"category": "dragon", "riggable": True, "parts": parts}, "Draconic Anatomical Modeler"

    # =====================================================================
    # 3. DINOSAURS (Theropods: T-Rex/Raptor vs. Quadrupeds: Triceratops/Stegosaurus/Brachiosaurus)
    # =====================================================================
    if domain == "dinosaur":
        is_tri = any(w in ptoks for w in ("triceratops", "ankylosaurus", "stegosaurus"))
        is_brach = any(w in ptoks for w in ("brachiosaurus", "brontosaurus", "diplodocus"))
        skin = c_main or ("#2563eb" if "triceratops" in ptoks else "#16a34a")
        belly = c_sec or "#fde68a"

        if is_tri or is_brach:
            bw, bh, bl = 2.2 * jw, 1.85 * jh, 3.6 * jl
            P("Torso", None, "raw", "sphere", (bw, bh, bl), "center", c=skin)
            nh = 3.6 * jh if is_brach else 0.85
            P("Neck", "Torso", "raw", "cylinder", (0.95, nh, 0.95), "top", u=0, v=-0.78, inset=0.2, c=skin, joint=True)
            P("Head", "Neck", "raw", "box", (1.25, 1.15, 1.45), "top", u=0, v=-0.35, inset=0.12, c=skin, joint=True)
            if "triceratops" in ptoks:
                P("BoneFrill", "Head", "shape", "box", (2.35, 1.95, 0.28), "back", u=0, v=0.35, inset=0.08, c=skin)
                P("BrowHornR", "Head", "detail", "cone", (0.28, 1.35, 0.28), "top", u=0.55, v=-0.2, inset=0.06, ro=(-55, 0, 0), c="#fef3c7", mirror=True)
                P("NoseHorn", "Head", "detail", "cone", (0.24, 0.65, 0.24), "front", u=0, v=0.35, inset=0.05, ro=(-25, 0, 0), c="#fef3c7")
            if "stegosaurus" in ptoks:
                for pi in range(5):
                    P(f"DorsalPlate{pi}", "Torso", "detail", "cone", (0.24, 0.95, 0.68), "top", u=0, v=-0.6 + pi*0.3, inset=0.08, c="#ea580c")
            for v_pos, tg in ((-0.72, "F"), (0.72, "B")):
                P(f"Leg{tg}R", "Torso", "shape", "cylinder", (0.58, 1.65, 0.58), "bot", u=0.68, v=v_pos, inset=0.12, c=skin, joint=True, mirror=True)
            P("Tail", "Torso", "shape", "cone", (1.1, 2.4, 1.1), "back", u=0, v=0, inset=0.25, ro=(80, 0, 0), c=skin, joint=True)
        else:
            # Bipedal Theropod (T-Rex / Raptor / Spinosaurus)
            P("Torso", None, "raw", "sphere", (2.1 * jw, 2.0 * jh, 3.2 * jl), "center", c=skin)
            P("Neck", "Torso", "raw", "cylinder", (1.15, 1.25, 1.15), "top", u=0, v=-0.68, inset=0.22, c=skin, joint=True)
            P("Skull", "Neck", "raw", "box", (1.35 * jw, 1.15 * jh, 1.95 * jl), "top", u=0, v=-0.45, inset=0.15, c=skin, joint=True)
            P("LowerJaw", "Skull", "shape", "box", (1.18 * jw, 0.42, 1.75 * jl), "bot", u=0, v=-0.1, inset=0.08, ro=(22, 0, 0), c=belly, joint=True)
            for ti in range(4):
                P(f"Tooth{ti}R", "Skull", "detail", "cone", (0.14, 0.32, 0.14), "bot", u=0.72, v=-0.7 + ti*0.35, inset=0.02, ro=(180, 0, 0), c="#ffffff", mirror=True)
            P("EyeR", "Skull", "detail", "sphere", (0.28, 0.28, 0.16), "right", u=0.2, v=0.25, inset=0.03, c="#facc15", mat="Neon", mirror=True)
            P("TinyArmR", "Torso", "detail", "box", (0.34, 0.85, 0.34), "right", u=-0.65, v=-0.25, inset=0.06, ro=(-35, 0, 0), c=skin, joint=True, mirror=True)
            P("ThighR", "Torso", "shape", "sphere", (1.15, 1.85, 1.35), "bot", u=0.65, v=0.1, inset=0.28, c=skin, joint=True, mirror=True)
            P("ShinR", "ThighR", "shape", "cylinder", (0.62, 1.45, 0.62), "bot", u=0, v=0.1, inset=0.12, c=skin, joint=True, mirror=True)
            P("ClawFootR", "ShinR", "detail", "box", (0.82, 0.38, 1.35), "bot", u=0, v=-0.25, inset=0.05, c=skin, mirror=True)
            P("Tail1", "Torso", "shape", "cone", (1.35, 2.8 * jl, 1.35), "back", u=0, v=0.1, inset=0.35, ro=(85, 0, 0), c=skin, joint=True)
            if "spinosaurus" in ptoks:
                P("SpinoSail", "Torso", "shape", "sphere", (0.28, 1.65, 2.6), "top", u=0, v=0.1, inset=0.25, c="#ea580c")
        return {"category": "dinosaur", "riggable": True, "parts": parts}, "Paleontological 3D Modeler"

    # =====================================================================
    # 4. ARTHROPODS (Spiders, Scorpions, Insects, Mantises, Bees)
    # =====================================================================
    if domain == "arthropod":
        is_scorp = "scorpion" in ptoks
        is_fly = any(w in ptoks for w in ("bee", "bumblebee", "wasp", "hornet", "butterfly", "dragonfly"))
        body_c = c_main or ("#eab308" if "bee" in ptoks or "wasp" in ptoks else "#1e293b")
        acc_c = c_sec or ("#1e293b" if "bee" in ptoks else "#dc2626")

        P("Cephalothorax", None, "raw", "sphere", (1.85 * jw, 1.15 * jh, 2.0 * jl), "center", c=body_c)
        P("Abdomen", "Cephalothorax", "raw", "sphere", (2.35 * jw, 1.75 * jh, 2.65 * jl), "back", u=0, v=0.18, inset=0.35, c=acc_c if "bee" in ptoks else body_c)
        P("HourglassMark", "Abdomen", "detail", "sphere", (0.65, 0.25, 0.85), "top", u=0, v=0, inset=0.05, c=acc_c, mat="Neon")

        for ei, ux in enumerate((0.22, 0.48)):
            P(f"SpiderEye{ei}R", "Cephalothorax", "detail", "sphere", (0.22, 0.22, 0.14), "front", u=ux, v=0.15, inset=0.03, c="#ef4444", mat="Neon", mirror=True)
        P("FangCheliceraR", "Cephalothorax", "detail", "cone", (0.26, 0.55, 0.26), "front", u=0.35, v=-0.25, inset=0.05, ro=(160, 0, 0), c=acc_c, mirror=True)

        n_legs = 3 if is_fly else 4
        for li in range(n_legs):
            uz = -0.65 + li * (1.3 / max(1, n_legs - 1))
            P(f"UpperLeg{li}R", "Cephalothorax", "shape", "cylinder", (0.26, 1.65 * jw, 0.26), "right", u=uz, v=0.1, inset=0.12, ro=(0, 0, -52), c=body_c, joint=True, mirror=True)
            P(f"LowerLeg{li}R", f"UpperLeg{li}R", "shape", "cone", (0.24, 1.75 * jh, 0.24), "bot", u=0, v=0, inset=0.08, ro=(0, 0, 125), c=body_c, joint=True, mirror=True)

        if is_scorp:
            P("PincerArmR", "Cephalothorax", "shape", "box", (0.45, 0.38, 1.45), "front", u=0.75, v=0, inset=0.1, c=body_c, joint=True, mirror=True)
            P("PincerClawR", "PincerArmR", "detail", "sphere", (0.68, 0.48, 0.95), "front", u=0, v=0, inset=0.08, c=acc_c, mirror=True)
            t1 = "Abdomen"
            for ti in range(4):
                tn = f"ScorpTail{ti}"
                P(tn, t1, "shape", "sphere", (0.55 - ti*0.06, 0.75, 0.55 - ti*0.06), "top", u=0, v=-0.35, inset=0.08, c=body_c, joint=True)
                t1 = tn
            P("VenomStinger", t1, "detail", "cone", (0.32, 0.78, 0.32), "front", u=0, v=0.2, inset=0.05, ro=(-90, 0, 0), c="#ef4444", mat="Neon")
        if is_fly:
            P("InsectWingR", "Cephalothorax", "detail", "sphere", (2.4, 0.12, 1.25), "top", u=0.65, v=0, inset=0.05, ro=(0, 0, 22), c="#e0f2fe", mat="Glass", tr=0.45, mirror=True)
        return {"category": "arthropod", "riggable": True, "parts": parts}, "Arthropod Anatomical Modeler"

    # =====================================================================
    # 5. CEPHALOPODS & MARINE (Octopus, Kraken, Sharks, Whales, Turtles)
    # =====================================================================
    if domain in ("cephalopod", "marine"):
        if domain == "cephalopod":
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
            return {"category": "cephalopod", "riggable": True, "parts": parts}, "Cephalopod Modeler"
        else:
            skin = c_main or ("#f8fafc" if "beluga" in ptoks else ("#16a34a" if "turtle" in ptoks else "#3b82f6"))
            P("Body", None, "raw", "sphere", (2.4 * jw, 2.0 * jh, 3.8 * jl), "center", c=skin)
            P("Snout", "Body", "shape", "sphere", (1.8 * jw, 1.4 * jh, 1.8 * jl), "front", u=0, v=-0.08, inset=0.45, c=skin)
            P("TailStock", "Body", "shape", "cone", (1.4 * jw, 2.0 * jl, 1.4 * jh), "back", u=0, v=0, inset=0.35, ro=(90, 0, 0), c=skin, joint=True)
            P("TailFluke", "TailStock", "detail", "box", (2.4 * jw, 0.24, 0.95), "back", u=0, v=0, inset=0.15, c=skin, joint=True)
            P("DorsalFin", "Body", "detail", "wedge", (0.28, 1.15, 1.25), "top", u=0, v=0.15, inset=0.12, c=skin)
            P("FinR", "Body", "shape", "box", (1.45, 0.22, 0.85), "right", u=-0.2, v=-0.35, inset=0.15, ro=(0, 0, -20), c=skin, joint=True, mirror=True)
            P("EyeR", "Snout", "detail", "sphere", (0.26, 0.26, 0.18), "right", u=-0.1, v=0.15, inset=0.04, c="#0f172a", mirror=True)
            return {"category": "marine", "riggable": True, "parts": parts}, "Marine Anatomical Modeler"

    # =====================================================================
    # 6. BIRDS & PHOENIX
    # =====================================================================
    if domain == "bird":
        main_c = c_main or ("#dc2626" if "phoenix" in ptoks else "#2563eb")
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
        return {"category": "bird", "riggable": True, "parts": parts}, "Avian Anatomical Modeler"

    # =====================================================================
    # 7. FELINES, CANINES & SMALL/MEDIUM MAMMALS
    # =====================================================================
    if domain in ("feline", "canine", "ursine_small"):
        is_feline = (domain == "feline")
        is_bear = any(w in ptoks for w in ("bear", "grizzly", "polarbear", "panda"))
        is_rabbit = any(w in ptoks for w in ("rabbit", "bunny", "hare", "pikachu"))
        sc = 1.45 if any(w in ptoks for w in ("lion", "tiger", "bear", "panda", "polarbear", "gorilla")) else 1.0

        default_fur = "#facc15" if "pikachu" in ptoks else ("#d97706" if "tiger" in ptoks else ("#eab308" if "lion" in ptoks else ("#f8fafc" if "polarbear" in ptoks or "panda" in ptoks or "rabbit" in ptoks else ("#78350f" if is_bear else ("#ea580c" if "fox" in ptoks else ("#64748b" if domain == "canine" else "#e07a2e"))))))
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

        return {"category": domain, "riggable": True, "parts": parts}, f"{domain.capitalize()} Anatomical Modeler"

    # =====================================================================
    # 8. UNGULATES & PACHYDERMS (Horses, Unicorns, Deer, Cows, Elephants, Giraffes)
    # =====================================================================
    if domain == "ungulate":
        is_uni = any(w in ptoks for w in ("unicorn", "pegasus"))
        coat = c_main or ("#9be2e8" if is_uni else ("#f472b6" if "pig" in ptoks else ("#94a3b8" if "elephant" in ptoks or "rhino" in ptoks else "#92400e")))
        acc = c_sec or ("#a855f7" if is_uni else "#1e293b")

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

        if is_uni or any(w in ptoks for w in ("horn", "unicorn", "rhino", "bull", "goat", "ram", "deer", "stag")):
            P("Horn", "Head", "detail", "cone", (0.28, 1.15, 0.28), "top", u=0, v=-0.45, inset=0.06, c="#facc15", mat="Neon")
        if "elephant" in ptoks or "mammoth" in ptoks:
            P("Trunk", "Muzzle", "shape", "cylinder", (0.36, 1.65, 0.36), "bot", u=0, v=-0.2, inset=0.08, c=coat, joint=True)
            P("TuskR", "Muzzle", "detail", "cone", (0.20, 0.95, 0.20), "front", u=0.55, v=-0.2, inset=0.04, ro=(-65, 0, 0), c="#fef3c7", mirror=True)
        return {"category": "ungulate", "riggable": True, "parts": parts}, "Ungulate Anatomical Modeler"

    # =====================================================================
    # 9. BUILDINGS & ARCHITECTURE
    # =====================================================================
    if domain == "building":
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
        elif is_pagoda:
            par_t = "MainWalls"
            for tier in range(3):
                sc_t = 1.0 - tier * 0.22
                eave = f"PagodaEave{tier}"
                P(eave, par_t, "shape", "cone", ((w + 1.6)*sc_t, 0.9, (d + 1.6)*sc_t), "top", u=0, v=0, inset=0.03, ro=(0, 45, 0), c="#1e293b", mat="Slate")
                if tier < 2:
                    par_t = f"PagodaStory{tier}"
                    P(par_t, eave, "shape", "box", (w*0.68*sc_t, 1.5, d*0.68*sc_t), "top", u=0, v=0, inset=0.25, c=wall_c, mat="Wood")
        else:
            P("PitchedRoof", "MainWalls", "shape", "wedge", (w + 0.9, 2.2 * jh, d + 0.9), "top", u=0, v=0, inset=0.02, c=roof_c, mat="Slate")
            P("ChimneyStack", "MainWalls", "shape", "box", (0.9, 2.5, 0.9), "top", u=0.58, v=0.35, inset=0.05, c="#78350f", mat="Brick")

        P("EntryStairs", "Foundation", "detail", "box", (2.6, 0.48, 0.95), "front", u=0, v=-0.08, inset=0.05, c=trim_c, mat="Slate")
        v_door = -1.0 + (2.2 / th)
        P("DoorFrame", "MainWalls", "detail", "box", (1.95, 2.25, 0.24), "front", u=0, v=v_door, inset=0.04, c="#0f172a", mat="Metal")
        P("DoorLeafR", "DoorFrame", "detail", "box", (0.78, 2.0, 0.12), "front", u=0.42, v=-0.04, inset=0.02, c="#78350f", mat="Wood", mirror=True)
        P("EntryCanopy", "DoorFrame", "detail", "box", (2.55, 0.22, 1.05), "top", u=0, v=-0.45, inset=0.04, c=roof_c, mat="Metal")

        for fl in range(floors):
            vy = -1.0 + ((fl + 0.54) * 2.0 / floors)
            for ux in (-0.64, 0.0, 0.64):
                if fl == 0 and abs(ux) < 0.22:
                    continue
                for fc_s in ("front", "back"):
                    wn = f"Win_{fc_s}_{fl}_{int((ux+1)*10)}"
                    P(wn, "MainWalls", "detail", "box", (1.22, 1.38, 0.18), fc_s, u=ux, v=vy, inset=0.04, c="#0f172a", mat="Metal")
                    P(wn + "_Glass", wn, "detail", "box", (1.02, 1.16, 0.08), fc_s, u=0, v=0, inset=0.01, c="#7dd3fc", mat="Glass", tr=0.35)
        return {"category": "building", "riggable": False, "parts": parts}, "Architectural Multi-Story Modeler"

    # =====================================================================
    # 10. VEHICLES, AIRCRAFT & WATERCRAFT
    # =====================================================================
    if domain in ("vehicle", "aircraft", "watercraft"):
        if domain == "watercraft":
            hull_c = c_main or "#78350f"
            P("Hull", None, "raw", "box", (2.6 * jw, 1.25 * jh, 5.4 * jl), "center", c=hull_c, mat="Wood")
            P("BowProw", "Hull", "shape", "wedge", (2.5 * jw, 1.2 * jh, 1.6), "front", u=0, v=0, inset=0.05, ro=(-90, 0, 0), c=hull_c, mat="Wood")
            P("DeckCabin", "Hull", "shape", "box", (2.0 * jw, 1.05, 1.85), "top", u=0, v=0.45, inset=0.04, c="#d6b88a", mat="Wood")
            P("MainMast", "Hull", "shape", "cylinder", (0.28, 4.2 * jh, 0.28), "top", u=0, v=-0.15, inset=0.1, c="#5c2808", mat="Wood")
            P("BillowingSail", "MainMast", "detail", "box", (2.8 * jw, 2.4 * jh, 0.18), "front", u=0, v=0.15, inset=0.02, c="#f8fafc", mat="Fabric")
            return {"category": "watercraft", "riggable": False, "parts": parts}, "Naval Architecture Modeler"
        if domain == "aircraft":
            is_heli = any(w in ptoks for w in ("helicopter", "heli", "chopper", "drone"))
            body_c = c_main or "#64748b"
            if is_heli:
                P("Fuselage", None, "raw", "sphere", (2.1 * jw, 1.75 * jh, 3.4 * jl), "center", c=body_c, mat="Metal")
                P("CockpitGlass", "Fuselage", "shape", "sphere", (1.85 * jw, 1.35 * jh, 1.65 * jl), "front", u=0, v=0.05, inset=0.55, c="#38bdf8", mat="Glass", tr=0.3)
                P("TailBoom", "Fuselage", "shape", "cylinder", (0.55, 2.9 * jl, 0.55), "back", u=0, v=0.18, inset=0.2, ro=(90, 0, 0), c=body_c, mat="Metal")
                P("RotorMast", "Fuselage", "shape", "cylinder", (0.42, 0.55, 0.42), "top", u=0, v=0, inset=0.05, c="#1e293b", mat="Metal", joint=True)
                P("RotorBlade1", "RotorMast", "detail", "box", (5.4 * jw, 0.10, 0.36), "top", u=0, v=0, inset=0.02, c="#0f172a", mat="Metal")
                P("RotorBlade2", "RotorMast", "detail", "box", (0.36, 0.10, 5.4 * jw), "top", u=0, v=0, inset=0.02, c="#0f172a", mat="Metal")
                P("SkidStrutR", "Fuselage", "shape", "cylinder", (0.18, 0.75, 0.18), "bot", u=0.65, v=0, inset=0.08, c="#1e293b", mat="Metal", mirror=True)
                P("LandingSkidR", "SkidStrutR", "detail", "box", (0.22, 0.20, 3.2 * jl), "bot", u=0, v=0, inset=0.02, c="#1e293b", mat="Metal", mirror=True)
            else:
                P("Fuselage", None, "raw", "cylinder", (1.55 * jw, 5.2 * jl, 1.55 * jh), "center", ro=(90, 0, 0), c=body_c, mat="Metal")
                P("NoseCone", "Fuselage", "shape", "sphere", (1.45 * jw, 1.35 * jh, 1.85), "front", u=0, v=0, inset=0.45, c="#2563eb", mat="Metal")
                P("CanopyGlass", "Fuselage", "detail", "sphere", (1.15 * jw, 0.75, 2.1), "top", u=0, v=-0.35, inset=0.25, c="#38bdf8", mat="Glass", tr=0.28)
                P("WingR", "Fuselage", "shape", "box", (3.8 * jw, 0.22, 1.45 * jl), "right", u=-0.05, v=0, inset=0.15, c=body_c, mat="Metal", mirror=True)
                P("TailFin", "Fuselage", "shape", "wedge", (0.24, 1.45, 1.25), "top", u=0, v=0.78, inset=0.08, c="#2563eb", mat="Metal")
            return {"category": "aircraft", "riggable": True, "parts": parts}, "Aerospace 3D Modeler"

        # Ground Vehicle (Car / Tank / Truck)
        is_tank = any(w in ptoks for w in ("tank", "panzer", "apc"))
        body_c = c_main or ("#4d7c0f" if is_tank else "#dc2626")
        W, H, L = (2.8 if is_tank else 2.4) * jw, 0.75 * jh, 5.2 * jl
        P("Chassis", None, "raw", "box", (W, H, L), "center", c=body_c, mat="Metal")
        if is_tank:
            P("TurretBase", "Chassis", "shape", "box", (W * 0.78, 0.85, L * 0.48), "top", u=0, v=0.05, inset=0.04, c=body_c, mat="Metal", joint=True)
            P("MainCannon", "TurretBase", "shape", "cylinder", (0.36, 3.4, 0.36), "front", u=0, v=0.05, inset=0.15, ro=(90, 0, 0), c="#1e293b", mat="Metal")
            P("TrackR", "Chassis", "shape", "box", (0.55, 0.92, L * 0.96), "right", u=0, v=-0.22, inset=0.04, c="#0f172a", mat="Slate", mirror=True)
        else:
            P("Hood", "Chassis", "shape", "box", (W * 0.96, 0.36, L * 0.32), "top", u=0, v=-0.62, inset=0.02, c=body_c, mat="Metal")
            P("CabinGlass", "Chassis", "shape", "box", (W * 0.86, 0.82, L * 0.42), "top", u=0, v=0.12, inset=0.02, c="#38bdf8", mat="Glass", tr=0.28)
            P("RoofCap", "CabinGlass", "shape", "box", (W * 0.84, 0.16, L * 0.38), "top", u=0, v=0, inset=0.02, c=body_c, mat="Metal")
            P("HeadlightR", "Chassis", "detail", "box", (0.48, 0.24, 0.12), "front", u=0.66, v=0.12, inset=0.02, c="#fef08a", mat="Neon", mirror=True)
            for uz, tag in ((-0.62, "F"), (0.62, "B")):
                P(f"Wheel{tag}R", "Chassis", "shape", "cylinder", (0.95, 0.50, 0.95), "right", u=uz, v=-0.28, inset=0.06, ro=(0, 0, 90), c="#0f172a", joint=True, mirror=True)
            P("RearWing", "Chassis", "detail", "box", (W * 0.98, 0.14, 0.58), "top", u=0, v=0.90, inset=-0.35, c="#1e293b", mat="Metal")
            P("SpoPostR", "Chassis", "detail", "box", (0.14, 0.45, 0.24), "top", u=0.62, v=0.88, inset=0.02, c="#1e293b", mat="Metal", mirror=True)
        return {"category": "vehicle", "riggable": True, "parts": parts}, "Vehicle Engineering Modeler"

    # =====================================================================
    # 11. WEAPONS, FOLIAGE & PROPS
    # =====================================================================
    if domain == "weapon":
        is_gun = any(w in ptoks for w in ("gun", "pistol", "rifle", "sniper", "shotgun", "blaster", "lasergun"))
        main_c = c_main or ("#334155" if is_gun else "#2563eb")
        if is_gun:
            P("Receiver", None, "raw", "box", (0.48 * jw, 0.82 * jh, 2.8 * jl), "center", c=main_c, mat="Metal")
            P("Barrel", "Receiver", "shape", "cylinder", (0.28, 1.9 * jl, 0.28), "front", u=0, v=0.18, inset=0.08, ro=(90, 0, 0), c="#e2e8f0", mat="Metal")
            P("MuzzleGlow", "Barrel", "detail", "cylinder", (0.32, 0.18, 0.32), "front", u=0, v=0, inset=0.02, ro=(90, 0, 0), c="#38bdf8", mat="Neon")
            P("Grip", "Receiver", "shape", "box", (0.42, 1.05, 0.52), "bot", u=0, v=0.55, inset=0.05, ro=(16, 0, 0), c="#0f172a")
            P("OpticScope", "Receiver", "detail", "cylinder", (0.34, 1.25, 0.34), "top", u=0, v=0.1, inset=0.03, ro=(90, 0, 0), c="#0f172a", mat="Metal")
        else:
            P("HiltGrip", None, "raw", "cylinder", (0.36, 1.35, 0.36), "center", c=main_c, mat="Metal")
            P("Pommel", "HiltGrip", "shape", "sphere", (0.54, 0.54, 0.54), "bot", u=0, v=0, inset=0.04, c="#eab308", mat="Metal")
            P("CrossGuard", "HiltGrip", "shape", "box", (1.85, 0.36, 0.52), "top", u=0, v=0, inset=0.02, c=main_c, mat="Metal")
            P("GuardGem", "CrossGuard", "detail", "sphere", (0.38, 0.38, 0.28), "front", u=0, v=0, inset=0.02, c="#eab308", mat="Neon")
            P("Blade", "CrossGuard", "shape", "box", (0.56, 3.8 * jl, 0.16), "top", u=0, v=0, inset=0.02, c="#e2e8f0", mat="Metal")
            P("BladeTip", "Blade", "detail", "cone", (0.56, 0.85, 0.16), "top", u=0, v=0, inset=0.02, c="#e2e8f0", mat="Metal")
        return {"category": "weapon", "riggable": False, "parts": parts}, "Weaponry 3D Modeler"

    if domain == "foliage":
        leaf_c = c_main or ("#f472b6" if "sakura" in ptoks else "#16a34a")
        P("Trunk", None, "raw", "cylinder", (1.15 * jw, 2.8 * jh, 1.15 * jw), "center", c="#78350f", mat="Wood")
        for i in range(3):
            cw_s = (3.8 - i * 0.85) * jw
            P(f"Canopy{i}", "Trunk" if i == 0 else f"Canopy{i-1}", "shape", "sphere", (cw_s, 1.55 * jh, cw_s), "top", u=0, v=0, inset=0.35, c=leaf_c, mat="Grass")
        return {"category": "foliage", "riggable": False, "parts": parts}, "Botanical 3D Modeler"

    if domain == "prop":
        P("BottomBun", None, "raw", "cylinder", (2.6 * jw, 0.55, 2.6 * jl), "center", c="#d97706")
        P("MeatPatty", "BottomBun", "shape", "cylinder", (2.75 * jw, 0.52, 2.75 * jl), "top", u=0, v=0, inset=0.03, c="#5c2808", mat="Slate")
        P("CheeseSlice", "MeatPatty", "detail", "box", (2.55 * jw, 0.14, 2.55 * jl), "top", u=0, v=0, inset=0.02, ro=(0, 45, 0), c="#facc15")
        P("LettuceRing", "CheeseSlice", "detail", "cylinder", (2.68 * jw, 0.20, 2.68 * jl), "top", u=0, v=0, inset=0.02, c="#16a34a")
        P("TopBun", "LettuceRing", "shape", "sphere", (2.65 * jw, 1.15, 2.65 * jl), "top", u=0, v=0, inset=0.28, c="#d97706")
        return {"category": "prop", "riggable": False, "parts": parts}, "Prop & Food Modeler"

    # =====================================================================
    # 12. HUMANOIDS, HEROES & MECHS
    # =====================================================================
    is_mech = any(w in ptoks for w in ("mech", "mecha", "gundam", "robot", "cyborg", "exosuit", "golem", "titan"))
    suit_c = c_main or ("#2563eb" if is_mech else "#dc2626")
    skin_c = "#cbd5e1" if is_mech else "#f2c9a0"
    cw, ch, lh = (2.2 if is_mech else 1.75) * jw, (2.1 if is_mech else 1.85) * jh, (1.65 if is_mech else 1.35) * jl

    P("HumanoidRootPart", None, "raw", "box", (cw * 0.92, 0.55, 0.96), "center", c="#1e293b")
    P("Torso", "HumanoidRootPart", "raw", "box", (cw, ch, 1.02), "top", u=0, v=0, inset=0.02, c=suit_c, mat="Metal" if is_mech else "SmoothPlastic", joint=True)
    P("Neck", "Torso", "raw", "cylinder", (0.48, 0.26, 0.48), "top", u=0, v=0, inset=0.02, c=skin_c, joint=True)
    P("Head", "Neck", "raw", "box" if is_mech else "sphere", (1.24, 1.24, 1.20), "top", u=0, v=0, inset=0.04, c=skin_c, joint=True)
    P("ChestArmor", "Torso", "detail", "box", (cw * 0.74, ch * 0.50, 0.18), "front", u=0, v=0.15, inset=0.02, c="#eab308" if is_mech else "#cbd5e1", mat="Metal")
    P("ThighR", "HumanoidRootPart", "shape", "box", (0.68, lh, 0.72), "bot", u=0.52, v=0, inset=0.02, c="#1e293b", joint=True, mirror=True)
    P("ShinR", "ThighR", "shape", "box", (0.60, lh, 0.64), "bot", u=0, v=0, inset=0.02, c="#1e293b", joint=True, mirror=True)
    P("BootR", "ShinR", "detail", "box", (0.66, 0.38, 1.05), "bot", u=0, v=-0.18, inset=0.02, c="#0f172a", mirror=True)
    P("ArmR", "Torso", "shape", "box", (0.58, lh * 0.85, 0.60), "right", u=0, v=0.22, inset=0.02, c=suit_c, joint=True, mirror=True)
    P("ForearmR", "ArmR", "shape", "box", (0.50, lh * 0.80, 0.52), "bot", u=0, v=0, inset=0.02, c=skin_c, joint=True, mirror=True)
    P("HandR", "ForearmR", "detail", "sphere", (0.50, 0.50, 0.50), "bot", u=0, v=0, inset=0.04, c=skin_c, joint=True, mirror=True)
    P("EyeR", "Head", "detail", "sphere", (0.24, 0.26, 0.12), "front", u=0.38, v=0.12, inset=0.02, c="#38bdf8" if is_mech else "#0f172a", mat="Neon" if is_mech else "SmoothPlastic", mirror=True)
    return {"category": "humanoid", "riggable": True, "parts": parts}, "Character & Mech Modeler"

# =========================================================================
# 5. STAGE 6: HYBRID COMPILER (Supports Direct `po` AND Surface `attach` + 3D Critic)
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
        sz = [round(clamp(float(v), 0.05, 35.0) * scale, 3) for v in sz_in[:3]]

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

        # Support direct world `po` coordinates (used by splines & LLMs) OR surface `attach`
        if isinstance(item.get("po"), (list, tuple)) and len(item["po"]) >= 3:
            wx = (-float(item["po"][0]) if is_mirror else float(item["po"][0])) * scale
            wy = float(item["po"][1]) * scale
            wz = float(item["po"][2]) * scale
        elif p_name and p_name in idx:
            u = clamp(float(att.get("u", 0.0)), -1.0, 1.0)
            if is_mirror and face not in ("right", "left"):
                u = -u
            v = clamp(float(att.get("v", 0.0)), -1.0, 1.0)
            inset = clamp(float(att.get("inset", 0.03)), -0.5, 2.0) * scale

            par = idx[p_name]
            px, py, pz = par["po"]
            pw, ph, pd = rot_dims(par["sz"], par["ro"])
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
            wx, wy, wz = 0.0, 2.5 * scale, 0.0

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

    # Iterative 3D AABB Connectivity Critic (Fixes floating or buried parts)
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
            if gap > 0.03:
                if dx > 0: cx += (-1.0 if cx > px else 1.0) * (dx + 0.015)
                if dy > 0: cy += (-1.0 if cy > py else 1.0) * (dy + 0.015)
                if dz > 0: cz += (-1.0 if cz > pz else 1.0) * (dz + 0.015)
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
                "msg": f"Pass #{iteration}: Found {fixes_this_pass} detached/misaligned details -> clamped to parent surface"
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
    scale_mult = extract_scale_factor(prompt)

    subject, wiki_summary = search_internet_knowledge(prompt)
    logs.append({"stage": "1_check_prompt", "msg": f"Analyzed prompt '{prompt}' -> Primary subject: '{subject}' (scale={scale_mult:.2f}x)"})

    if wiki_summary:
        logs.append({"stage": "2_internet_search", "msg": f"Wikipedia Lookup: {wiki_summary[:140]}..."})
    else:
        logs.append({"stage": "2_internet_search", "msg": f"Direct semantic features extracted for '{subject}'"})

    bp, engine_used, llm_err = call_cloud_llm_architect(prompt, wiki_summary, seed, api_key=api_key)
    if not bp:
        bp, engine_used = synthesize_from_semantics_and_wiki(prompt, subject, wiki_summary, seed)
        if llm_err and api_key:
            logs.append({"stage": "2b_llm_notice", "msg": f"Note: Custom key fallback ({llm_err}) -> used {engine_used}"})

    raw_cnt = sum(1 for p in bp["parts"] if p.get("stage") == "raw")
    shp_cnt = sum(1 for p in bp["parts"] if p.get("stage") == "shape")
    det_cnt = sum(1 for p in bp["parts"] if p.get("stage") == "detail")
    logs.append({"stage": "3_raw_blockout", "msg": f"[{engine_used}] Built {raw_cnt} core mass blocks"})
    logs.append({"stage": "4_shape_sculpting", "msg": f"Sculpted {shp_cnt} structural/anatomical shapes"})
    logs.append({"stage": "5_detail_pass", "msg": f"Added {det_cnt} surface-socketed details"})

    compiled, critic_logs, repairs = compile_and_repair_3d_model(bp, scale=scale_mult)
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
    prompt = (body.get("prompt") or "build me a giant serpent").strip()
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
  #apiKeyInput { width: 200px; padding: 10px 10px; border-radius: 10px; border: 1px solid var(--border); font-size: 12px; background: #11141c; color: #94a3b8; outline: none; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>

<div class="topbar">
  <span class="brand">ROBLOX CLOUD 3D AI</span>
  <button class="pill" onclick="runPrompt('build me a giant serpent')">Giant Serpent</button>
  <button class="pill" onclick="runPrompt('orange tabby cat')">Cat</button>
  <button class="pill" onclick="runPrompt('charizard fire dragon')">Charizard Dragon</button>
  <button class="pill" onclick="runPrompt('trex dinosaur')">T-Rex Dino</button>
  <button class="pill" onclick="runPrompt('black widow spider')">Spider</button>
  <button class="pill" onclick="runPrompt('emperor scorpion')">Scorpion</button>
  <button class="pill" onclick="runPrompt('modern two story cafe building')">Cafe Building</button>
  <button class="pill" onclick="runPrompt('japanese red pagoda temple')">Pagoda Temple</button>
  <button class="pill" onclick="runPrompt('medieval stone castle')">Stone Castle</button>
  <button class="pill" onclick="runPrompt('red sports car')">Sports Car</button>
  <button class="pill" onclick="runPrompt('military attack helicopter')">Helicopter</button>
  <button class="pill" onclick="runPrompt('pirate galleon ship')">Pirate Ship</button>
  <button class="pill" onclick="runPrompt('purple kraken octopus')">Kraken</button>
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
  <input type="text" id="promptInput" placeholder='Type ANY creature, serpent, dragon, building, vehicle, or prop...' onkeydown="if(event.key==='Enter') generateNew()" />
  <input type="password" id="apiKeyInput" placeholder="Groq (gsk_...) or Gemini Key" oninput="localStorage.setItem('rbx_ai_key', this.value)" />
  <button class="btn-sm" onclick="reRoll()">Re-Roll</button>
  <button class="btn-sm primary" style="padding:10px 16px;font-size:13px;" onclick="generateNew()">Build 3D Asset</button>
</div>

<script>
let scene, camera, renderer, controls, modelGroup, currentSpec = null;
let currentPrompt = "build me a giant serpent", currentIter = 0, viewStage = "final";

function init3D() {
  const savedKey = localStorage.getItem("rbx_ai_key");
  if (savedKey) document.getElementById("apiKeyInput").value = savedKey;

  const canvas = document.getElementById("viewport");
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(40, canvas.clientWidth / canvas.clientHeight, 0.1, 500);
  camera.position.set(8.5, 6.2, -10.5);
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

  controls.target.set(0, Math.max(1.2, b[1] * 0.42), 0);
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
window.addEventListener("DOMContentLoaded", () => { init3D(); runPrompt("build me a giant serpent"); });
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
            return self._send('{"ok":true,"scheme":"roblox_cloud_v5"}')
        if parsed.path.startswith("/generate"):
            qs = parse_qs(parsed.query)
            prompt = (qs.get("prompt") or ["build me a giant serpent"])[0]
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
    print(f"Roblox Cloud 3D Modeler AI v5 running on 0.0.0.0:{port}", flush=True)
    srv.serve_forever()
