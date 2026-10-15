"""BrickForge AI v5 — STYLE-DNA ENGINE.
Stud-brick aesthetic + socket attachments + ground solver + true proportions.
Context = data tables (ROOTS/MODS/THEMES/SPECIFICS). No junk parts: every part
must change silhouette, proportion, palette or function. Objects included."""
import math, random, re, colorsys, zlib, time
from collections import Counter
BUDGET = 7.0

# ================= 1. CONTEXT TABLES (this is where the 10k rows live) =================
ROOTS = {
 "humanoid": ["human","humans","man","woman","boy","girl","guy","dude","person","people","hero",
   "villain","wizard","mage","knight","soldier","ninja","pirate","doctor","teacher","driver",
   "engineer","chef","pilot","astronaut","farmer","builder","artist","musician","athlete",
   "boxer","karate","fighter","guard","police","thief","robot","cyborg","android","mech","alien"],
 "octopus": ["octopus","squid","kraken","cephalopod","ink"],
 "serpent": ["snake","serpent","dragon","wyrm","eel","viper","wyvern","cobra"],
 "fish": ["fish","shark","koi","bass","piranha","manta","goldfish","whale","dolphin"],
 "bird": ["bird","eagle","phoenix","falcon","owl","raven","parrot","hawk","duck"],
 "crab": ["crab","lobster","scorpion","shrimp","crustacean"],
 "spider": ["spider","arachnid","tarantula","weaver"],
 "golem": ["golem","titan","colossus","elemental","construct"],
 "turtle": ["turtle","tortoise","snail"],
 "jelly": ["jelly","jellyfish","medusa","blob","slime"],
 "car": ["car","vehicle","auto","sedan","coupe","truck","van","taxi","racecar"],
 "bike": ["bike","motorcycle","chopper","scooter"],
 "boat": ["boat","ship","yacht","canoe","submarine"],
 "plane": ["plane","airplane","jet","aircraft","glider"],
 "heli": ["helicopter","heli","choppercraft"],
 "tank": ["tank","warcraft","armored"]}
ARCHES = list(ROOTS)
OBJECTS = {"car","bike","boat","plane","heli","tank"}

# MODS v2: proportion/palette/ONE bold piece. No handheld junk, ever.
MODS = {
 "bald":     {"rm":["hair"],"prop":{}},
 "muscular": {"prop":{"chest":1.3,"arms":1.25}},
 "fat":      {"prop":{"chest":1.35,"limbs":1.15}},
 "skinny":   {"prop":{"chest":0.8,"limbs":0.8}},
 "cute":     {"prop":{"head":1.3,"limbs":0.8},"sharp":-0.6,"scale":0.85,"eyes":1.4},
 "tall":     {"prop":{"limbs":1.3},"scale":1.15},
 "tiny":     {"scale":0.6}, "huge": {"scale":1.5}, "giant": {"scale":1.65},
 "evil":     {"sharp":0.6,"theme":"dark","add":"brow_evil","pose":-8},
 "royal":    {"theme":"gold","add":"hg_crown"},
 "icy":      {"theme":"ice","mat":"ice","add":"hg_crystal"},
 "fire":     {"theme":"lava","mat":"lava"},
 "golden":   {"theme":"gold"}, "dark": {"theme":"dark"}, "neon": {"theme":"neon"},
 "pastel":   {"theme":"pastel"},
 "floating": {"float":True,"pose":-6},
 "sport":    {"add":"sp_spoiler","prop":{"low":0.85},"theme":"neon"},
 "offroad":  {"prop":{"wheels":1.5,"lift":1.3}},
 "karate":   {"add":"hg_headband","theme":"plain","pose":-12},
 "wizard":   {"add":"hg_pointy","theme":"mystic"},
 "knight":   {"add":"hg_helmet","theme":"steel"},
 "ninja":    {"add":"hg_mask","theme":"dark"},
 "pirate":   {"add":"hg_tricorn","theme":"sea"},
 "chef":     {"add":"hg_toque","theme":"plain"},
 "driver":   {"add":"hg_cap","theme":"race"},
 "engineer": {"add":"hg_hardhat","theme":"warn"},
 "pilot":    {"add":"hg_cap","theme":"sky"},
 "astronaut":{"add":"hg_dome","theme":"plain"},
 "doctor":   {"add":"hg_cap","theme":"plain"},
 "teacher":  {"add":"hg_glasses","theme":"plain"},
 "police":   {"add":"hg_peak","theme":"navy"},
 "wings":    {"add":"w_big"}, "horns": {"add":"h_curved"}, "cape": {"add":"cape_long"},
 "spiky":    {"sharp":0.9}, "smooth": {"sharp":-0.6}}
THEMES = {"gold":(45,.85,.75),"dark":(265,.25,.16),"neon":(310,1,.95),"ice":(195,.4,.92),
 "lava":(12,.95,.8),"plain":(210,.06,.92),"mystic":(275,.7,.55),"steel":(215,.08,.6),
 "sea":(200,.7,.5),"warn":(48,.95,.8),"sky":(205,.7,.7),"navy":(225,.8,.3),"pastel":(330,.35,.85),
 "race":(0,.85,.6)}
# SPECIFICS: exact-phrase creatures, added AFTER context is broad. Example ready:
SPECIFICS = {
 # "black floating serpent": {"root":"serpent","float":True,"sharp":1.7,
 #     "palette":{"A":"#0c0c10","B":"#17171d","C":"#ff2d55","S":"#23232b","D":"#000000","L":"#2c2c34"}},
}
COLOR_WORDS = {"red":(0,.85,.62),"crimson":(348,.9,.55),"orange":(24,.9,.62),"yellow":(52,.9,.65),
 "gold":(45,.85,.72),"green":(140,.7,.5),"teal":(172,.75,.5),"cyan":(185,.85,.65),"blue":(215,.8,.55),
 "navy":(225,.8,.3),"purple":(275,.7,.55),"pink":(330,.7,.75),"white":(0,0,.96),"black":(260,.2,.14),
 "grey":(220,.05,.55),"gray":(220,.05,.55),"brown":(25,.6,.42),"mint":(160,.45,.8)}
NEG = {"no","without","not","never","minus"}
NAME_PRE = ["Brick","Stud","Krag","Zor","Bloxx","Torv","Pixl","Grim","Lux","Vex","Snap","Mek",
 "Vor","Quil","Rune","Ember","Frost","Thorn","Gale","Umber"]
NAME_SUF = {"octopus":"pus","serpent":"enth","fish":"ish","bird":"wing","crab":"claw","spider":"ling",
 "golem":"mok","humanoid":"guard","turtle":"shell","jelly":"meduse","car":"runner","bike":"cycle",
 "boat":"wave","plane":"wing","heli":"rotor","tank":"tread"}

# ================= 2. PARSER (deterministic root + mods + specifics) =================
def tokenize(t): return re.findall(r"[a-z]+", t.lower())
def parse_intent(prompt):
    raw = prompt.lower(); toks = tokenize(raw)
    I = {"root":None,"mods":[],"traits":{},"neg":set(),"colors":[],"size":1.0,"sharp":1.0,
         "pose":0,"mat":None,"float":False,"prop":{},"eyes":1.0,"palette_force":None,"tokens":set(toks)}
    for phrase, cfg in SPECIFICS.items():
        if phrase in raw:
            I.update({k:v for k,v in cfg.items() if k!="palette"}); I["palette_force"]=cfg.get("palette")
            I["root"]=cfg.get("root",I["root"]); return I
    best=0
    for root,keys in ROOTS.items():
        m=sum(1 for k in keys if k in toks)
        if m>best: best=m; I["root"]=root
    if not I["root"]: I["root"]="humanoid"
    for mk in MODS:
        if mk in toks: I["mods"].append(mk)
    for mk in I["mods"]:
        m=MODS[mk]
        I["prop"].update(m.get("prop",{}))
        for t in m.get("rm",[]): I["neg"].add(t)
        I["sharp"]+=m.get("sharp",0); I["size"]*=m.get("scale",1.0); I["pose"]+=m.get("pose",0)
        if m.get("float"): I["float"]=True
        if m.get("mat"): I["mat"]=m["mat"]
        if m.get("theme"): I["colors"].append(THEMES[m["theme"]])
        if m.get("eyes"): I["eyes"]*=m["eyes"]
        if m.get("add"): I["traits"][m["add"]]=1
    for i,t in enumerate(toks):
        if t in NEG and i+1<len(toks):
            nx=toks[i+1]
            if "wing" in nx: I["neg"].add("w_big")
            if "hair" in nx: I["neg"].add("hair")
            if "tail" in nx: I["neg"].add("tail")
    for w,h in COLOR_WORDS.items():
        if w in toks: I["colors"].append(h)
    I["sharp"]=max(0.2,min(2.6,I["sharp"]))
    return I

# ================= 3. MATH / COLOR =================
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
def synthesize_palette(I,rng):
    if I["palette_force"]: return dict(I["palette_force"])
    if I["colors"]: h,s,v=I["colors"][0]
    else: h,s,v=(rng.choice([0,25,45,140,175,205,250,285,320]),.65,.6)
    if I["mat"]=="metal": s,v=.15,.75
    if I["mat"]=="ice": h,s,v=195,.4,.93
    if I["mat"]=="lava": h,s,v=12,.95,.8
    off=rng.choice([180,28,120,150])
    return {"A":hsv_hex(h,s*.85,v),"B":hsv_hex(h+rng.choice([-25,25]),s*.7,min(1,v*1.2)),
      "C":hsv_hex(h+off,max(.5,s),min(1,v*1.35)),"S":hsv_hex(h+off+rng.choice([-30,30]),max(.45,s*.9),min(1,v*1.1)),
      "D":hsv_hex(h,min(1,s*1.05),max(.1,v*.4)),"L":hsv_hex(h+15,max(.06,s*.35),min(1,v*1.55))}

# ================= 4. BUILDER: sockets + studs + ground =================
FACES={"top":(0,1,0),"bot":(0,-1,0),"front":(0,0,-1),"back":(0,0,1),"right":(1,0,0),"left":(-1,0,0)}
class Builder:
    def __init__(self,seed,pal,rng,sharp,scale):
        self.parts=[];self.names=set();self.pal=pal;self.rng=rng;self.sharp=sharp;self.scale=scale
        self.sz={};self.mirrored=[];self.present=set();self.counts=Counter();self.root=None;self.studs=0
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
            base=[f[0]*(P[0]/2+C[0]/2-e) if f[0] else 0, f[1]*(P[1]/2+C[1]/2-e) if f[1] else 0,
                  f[2]*(P[2]/2+C[2]/2-e) if f[2] else 0]
            pos=[base[i]+off[i] for i in range(3)]
        name=self._uniq(name); self._emit(name,parent,shape,size,pos,rot,color); self.sz[name]=size
        if studs and self.studs<90:
            nx=clamp(int(size[0]/.95),1,4); nz=clamp(int(size[2]/.95),1,4)
            for gx in range(nx):
                for gz in range(nz):
                    ox=(gx-(nx-1)/2.0)*.95; oz=(gz-(nz-1)/2.0)*.95
                    self._emit(self._uniq("Stud"),"top" and name,"cylinder",(.34,.2,.34),
                               [ox,size[1]/2+.06,oz],(0,0,0),color); self.studs+=1
        if mirror:
            f2={"right":"left","left":"right"}.get(face,face)
            pos2=list(off); pos2[0]=-pos2[0]
            if f2:
                P2=P;C2=size;e2=.15*min(C2);f=FACES[f2]
                base=[f[0]*(P2[0]/2+C2[0]/2-e2) if f[0] else 0,f[1]*(P2[1]/2+C2[1]/2-e2) if f[1] else 0,
                      f[2]*(P2[2]/2+C2[2]/2-e2) if f[2] else 0]
                pos2=[base[i]+pos2[i] for i in range(3)]
            mn=self._uniq(name+"L")
            self._emit(mn,parent,shape,size,pos2,[rot[0],-rot[1],-rot[2]],color); self.sz[mn]=size
            self.mirrored.append((name,mn))
        if self.root is None and parent is None: self.root=name
        return name
    def chain(self,prefix,parent,n,sizes,colors,pitches,face="back",off0=(0,0,0)):
        par=parent;outs=[]
        for i in range(n):
            nm=self.add("%s%d"%(prefix,i),par,"box",sizes[i],face if i==0 else face,
                        off0 if i==0 else (0,0,0),(pitches[i],0,0),colors[i%len(colors)])
            outs.append(nm);par=nm;face="back"
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
    def eyes(self,parent,y,z,s,bx=.75):
        for sx,suf in ((1,"R"),(-1,"L")):
            e=self.add("Eye"+suf,parent,"box",(s,s*1.15,s*.4),None,(sx*bx,y,z),(0,0,0),"C")
            self.add("Pupil"+suf,e,"gem",(s*.45,s*.55,s*.3),None,(0,0,-.25),(0,0,0),"D")
        self.mirrored.append(("EyeR","EyeL"))
    def tag(self,*t):
        for x in t: self.present.add(x)
def ground(B):
    idx={p["n"]:p for p in B.parts}
    def ymin(n):
        p=idx[n];y=p["po"][1]-p["sz"][1]/2;par=p["p"]
        while par: y+=idx[par]["po"][1];par=idx[par]["p"]
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

# ================= 5. BOLD ADD-ONS (one piece, big read) =================
def _head(B): 
    for p in B.parts:
        if p["n"]=="Head": return "Head"
    return B.root
def add_brow_evil(B,I,r): 
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Brow"+suf,_head(B),"box",(.42,.12,.15),None,(sx*.38,.42,-.62),(0,0,sx*-18),"D")
def add_hg_crown(B,I,r):
    c=B.add("Crown",_head(B),"box",(.9,.3,.9),"top")
    for i in range(4): B.add("CrownPt%d"%i,c,"pyramid",(.22,.5,.22),"top",((i-1.5)*.28,0,0),(0,0,0),"S")
def add_hg_pointy(B,I,r):
    B.add("HatBrim",_head(B),"box",(1.5,.18,1.5),"top"); 
    B.add("HatCone","HatBrim","pyramid",(.8,1.5,.8),"top",(0,.05,0),(0,0,0),"C")
def add_hg_helmet(B,I,r): B.add("Helmet",_head(B),"box",(1.35,1.0,1.3),"top",(0,-.15,0),(0,0,0),"D")
def add_hg_mask(B,I,r): B.add("Mask",_head(B),"box",(1.0,.5,.2),"front",(0,-.05,-.02),(0,0,0),"D")
def add_hg_tricorn(B,I,r): B.add("TriBrim",_head(B),"box",(1.7,.15,1.2),"top");B.add("TriTop","TriBrim","wedge",(1.5,.4,1.0),"top",(0,.05,0),(0,0,0),"D")
def add_hg_toque(B,I,r): B.add("Toque",_head(B),"cylinder",(.9,.9,.9),"top",(0,.1,0),(0,0,0),"L")
def add_hg_cap(B,I,r):
    B.add("CapTop",_head(B),"box",(1.1,.25,1.1),"top",(0,0,-.05),(0,0,0),"C")
    B.add("CapBrim","CapTop","box",(1.0,.12,.6),"front",(0,-.1,-.2),(0,0,0),"C")
def add_hg_hardhat(B,I,r): B.add("HardHat",_head(B),"box",(1.3,.45,1.3),"top",(0,.05,0),(0,0,0),"C")
def add_hg_dome(B,I,r): B.add("Dome",_head(B),"gem",(1.5,1.5,1.5),None,(0,.1,0),(0,0,0),"L")
def add_hg_peak(B,I,r): B.add("PeakTop",_head(B),"box",(1.15,.3,1.15),"top");B.add("PeakBrim","PeakTop","box",(1.05,.1,.55),"front",(0,-.12,-.15),(0,0,0),"D")
def add_hg_glasses(B,I,r): B.add("Glasses",_head(B),"box",(1.0,.22,.15),"front",(0,.12,-.05),(0,0,0),"D")
def add_hg_headband(B,I,r): B.add("Headband",_head(B),"box",(1.25,.22,1.25),"top",(0,-.25,0),(0,0,0),"C")
def add_hg_crystal(B,I,r):
    for i in range(3): B.add("Crys%d"%i,_head(B),"pyramid",(.25,.9-i*.2,.25),"top",((i-1)*.35,.05,.2),(0,0,0),"C")
def add_w_big(B,I,r):
    for sx,suf in ((1,"R"),(-1,"L")):
        w=B.add("Wing"+suf,B.root,"box",(1.6,.35,1.0),None,(sx*1.2,1.0,.4),(0,0,sx*20),"B")
        for i in range(4):
            B.add("Wing%sP%d"%(suf,i),w,"wedge",(.45,1.6-i*.2,.22),None,(sx*(.4+i*.35),-.4,.2),(0,0,sx*(26+i*9)),"S")
    B.mirrored.append(("WingR","WingL"))
def add_h_curved(B,I,r):
    for sx,suf in ((1,"R"),(-1,"L")):
        h=B.add("Horn"+suf,_head(B),"box",(.35,.6,.35),None,(sx*.55,.7,-.1),(sx*-16,0,0),"S")
        for i in range(2): h=B.add("Horn%s%d"%(suf,i),h,"pyramid",(.3-i*.08,.7,.3-i*.08),None,(0,.5,-.15),(-24,0,0),"S")
    B.mirrored.append(("HornR","HornL"))
def add_cape_long(B,I,r): B.add("Cape",B.root,"wedge",(.25,2.6,1.6),None,(0,.6,.75),(14,0,0),"C")
def add_sp_spoiler(B,I,r):
    w=B.add("Spoiler",B.root,"box",(2.0,.15,.6),"back",(0,.9,.2),(0,0,0),"D")
    for sx in (1,-1): B.add("SpoPost%d"%sx,B.root,"box",(.15,.6,.15),"back",(sx*.8,.5,.2),(0,0,0),"D")
ADDONS={"brow_evil":add_brow_evil,"hg_crown":add_hg_crown,"hg_pointy":add_hg_pointy,
 "hg_helmet":add_hg_helmet,"hg_mask":add_hg_mask,"hg_tricorn":add_hg_tricorn,"hg_toque":add_hg_toque,
 "hg_cap":add_hg_cap,"hg_hardhat":add_hg_hardhat,"hg_dome":add_hg_dome,"hg_peak":add_hg_peak,
 "hg_glasses":add_hg_glasses,"hg_headband":add_hg_headband,"hg_crystal":add_hg_crystal,
 "w_big":add_w_big,"h_curved":add_h_curved,"cape_long":add_cape_long,"sp_spoiler":add_sp_spoiler}

# ================= 6. BUILDERS (creatures + objects) =================
def b_humanoid(B,I,r):
    p=I["prop"]; cw=1.7*p.get("chest",1.0); lw=p.get("limbs",1.0); hw=1.25*p.get("head",1.0)
    al=1.0*lw*p.get("arms",1.0); ll=1.05*lw
    B.add("HumanoidRootPart",None,"box",(cw*.95,.55,1.0),None,(0,0,0),(0,0,0),"A",studs=True)
    torso=B.add("Chest","HumanoidRootPart","box",(cw,1.9,1.0),"top",(0,.05,0),(0,0,0),"B",studs=True)
    neck=B.add("Neck",torso,"box",(.5,.3,.5),"top")
    hd=B.add("Head",neck,"box",(hw,1.25,hw*.95),"top",(0,.05,0),(0,0,0),"A")
    B.eyes(hd,.12,-.62,.34*I["eyes"],.38*hw/1.25)
    B.add("Mouth",hd,"box",(.5,.12,.12),"front",(0,-.38,-.02),(0,0,0),"D")
    if "hair" not in I["neg"]:
        B.add("HairTop",hd,"box",(hw*1.05,.3,hw),"top",(0,0,.05),(0,0,0),"B",studs=True)
        B.add("HairBack",hd,"box",(hw*1.02,.9,.25),"back",(0,-.1,.05),(0,0,0),"B")
    for sx,suf in ((1,"R"),(-1,"L")):
        a=B.add("Arm"+suf,torso,"box",(.6*p.get("arms",1.0),al,.6),"right" if sx>0 else "left",
                (0,.75,0),(0,0,sx*6),"A",mirror=sx<0)
        f=B.add("Fore"+suf,a,"box",(.52,al*.95,.52),"bot")
        B.add("Hand"+suf,f,"box",(.5,.45,.5),"bot",(0,0,0),(0,0,0),"D")
        l=B.add("Leg"+suf,"HumanoidRootPart","box",(.72*lw,ll,.8),"bot",(sx*.5,-.1,0),(0,0,0),"A",mirror=sx<0)
        s2=B.add("Shin"+suf,l,"box",(.6*lw,ll,.66),"bot")
        B.add("Foot"+suf,s2,"wedge",(.7,.4,1.15),"bot",(0,0,-.2),(0,0,0),"D")
    B.add("Belt","HumanoidRootPart","box",(cw,0.28,1.05),None,(0,.1,0),(0,0,0),"D")
    B.tag("humanoid")
def b_octopus(B,I,r):
    B.add("CoreRoot",None,"box",(2.8,2.2,2.8),None,(0,2.4,0),(0,0,0),"A",studs=True)
    m=B.add("Mantle","CoreRoot","box",(2.2,1.4,2.2),"top",(0,.05,.1),(0,0,0),"B",studs=True)
    B.add("Mantle2",m,"box",(1.4,1.0,1.4),"top",(0,.05,.1),(0,0,0),"A")
    hd=B.add("Head","CoreRoot","box",(2.5,1.7,2.2),None,(0,-.5,.5),(0,0,0),"A")
    B.eyes(hd,.1,-1.15,.62,.85)
    def suck(b,base,i):
        par=base
        for s in range(4):
            t=s/4.0
            par=b.add("Tent%d_s%d"%(i,s),par,"box",(.62*(1-t)+.15,1.1-.2*t,.62*(1-t)+.15),"bot",(0,.05,0),(16+s*9,0,0),"A" if s%2 else "B")
        b.add("Tent%d_tip"%i,par,"wedge",(.3,.6,.3),"bot",(0,0,0),(-90,0,0),"C")
    B.ring("Tent","CoreRoot",8,1.35,-1.5,(.7,.8,.7),"A",child=suck)
    B.tag("octopus","tentacles")
def b_serpent(B,I,r):
    d=[10]+[r.choice([-13,13])*(1 if i%2 else -1) for i in range(9)]
    par=None;names=[]
    for i in range(10):
        sz=(1.5-i*.09,1.35-i*.08,1.6)
        n=B.add("Seg%d"%i,par if par else None,"box",sz,None if par else None,
                (0,1.5,4.2) if not par else (0,0,0),(0,d[i],0),"A" if i%2 else "B",studs=i%3==0)
        names.append(n);par=n
    hd=B.add("Head",par,"box",(1.9,1.5,2.3),"front",(0,.25,.2),(0,0,0),"A",studs=True)
    B.add("Snout",hd,"wedge",(1.3,.9,1.3),"front",(0,-.25,.2),(-90,0,0),"B")
    B.eyes(hd,.45,-1.05,.5,.72)
    for i in range(0,8,2): B.add("Dorsal%d"%i,names[i],"wedge",(.28,.9,1.0),"top",(0,.05,0),(0,0,0),"C")
    B.add("TailFin",names[0],"wedge",(1.3,1.5,.28),"back",(0,.2,-.2),(90,0,0),"C")
    B.tag("tail")
def b_fish(B,I,r):
    B.add("CoreRoot",None,"box",(2.6,2.6,2.4),None,(0,2.0,0),(0,0,0),"A",studs=True)
    sn=B.add("SnoutSec","CoreRoot","box",(2.0,2.0,1.4),"front",(0,0,.1),(0,0,0),"A")
    cs=B.add("CaudalSec","CoreRoot","box",(1.3,1.5,1.4),"back")
    B.add("Belly","CoreRoot","box",(2.1,1.0,2.2),"bot",(0,.1,0),(0,0,0),"L")
    B.eyes(sn,.5,-.75,.55,.8)
    n=int(4+B.sharp*4)
    for i in range(n):
        a=-65+i*(130.0/max(1,n-1));rd=math.radians(a)
        B.add("Dorsal%d"%i,"CoreRoot","pyramid",(.45,r.uniform(.9,1.9)*B.sharp,.45),None,
              (1.45*math.sin(rd),1.45*math.cos(rd),r.uniform(-.9,.9)),(0,0,-a),"S")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Pect"+suf,"CoreRoot","wedge",(1.5,1.2,.25),None,(sx*1.35,-.5,-.5),(0,0,sx*62),"C",mirror=sx<0)
    for k,az in ((0,-32),(1,0),(2,32)): B.add("Caudal%d"%k,cs,"wedge",(1.5,2.0,.25),"back",(0,.5,-.2),(0,az,0),"C")
    B.tag("fins","tail")
def b_bird(B,I,r):
    B.add("CoreRoot",None,"box",(1.9,2.1,2.5),None,(0,2.6,0),(0,0,0),"A",studs=True)
    nk=B.add("Neck","CoreRoot","box",(.9,1.1,.9),"top",(0,.1,-.9),(-18,0,0),"B")
    hd=B.add("Head",nk,"box",(1.25,1.25,1.3),"top",(0,.05,-.1),(12,0,0),"A")
    B.eyes(hd,.15,-.6,.42,.5)
    B.add("Beak",hd,"wedge",(.7,.6,1.0),"front",(0,-.1,-.1),(-90,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        w=B.add("Wing"+suf,"CoreRoot","box",(1.5,.4,1.1),None,(sx*1.15,.7,0),(0,0,sx*16),"B",mirror=sx<0)
        md=B.add("Wing%sMid"%suf,w,"box",(1.4,.32,.9),"right" if sx>0 else "left")
        for i in range(5):
            B.add("Wing%sP%d"%(suf,i),md,"wedge",(.42,1.5-i*.16,.2),None,(sx*(.35+i*.3),-.4,.25),(0,0,sx*(26+i*9)),"S")
    for i in range(5):
        B.add("TailF%d"%i,"CoreRoot","wedge",(.7,1.9-abs(i-2)*.25,.22),"back",((i-2)*.5,-.3,-.2),(115,(i-2)*14,0),"C" if i%2 else "S")
    for sx,suf in ((1,"R"),(-1,"L")):
        f=B.add("Femur"+suf,"CoreRoot","box",(.6,1.2,.7),"bot",(sx*.65,.1,0),(0,0,0),"B",mirror=sx<0)
        t=B.add("Tibia"+suf,f,"box",(.45,1.2,.5),"bot")
        for k in (-1,0,1): B.add("Tal%s%d"%(suf,k),t,"pyramid",(.2,.6,.2),"bot",(k*.25,-.1,-.3),(75,0,0),"D")
    B.tag("wings")
def b_crab(B,I,r):
    B.add("CoreRoot",None,"box",(3.4,1.6,2.6),None,(0,1.9,0),(0,0,0),"A",studs=True)
    d1=B.add("Dome","CoreRoot","box",(2.7,1.0,2.1),"top",(0,.05,0),(0,0,0),"B",studs=True)
    d2=B.add("Dome2",d1,"box",(1.8,.7,1.4),"top")
    for sx,suf in ((1,"R"),(-1,"L")):
        st=B.add("Stalk"+suf,"CoreRoot","box",(.28,.9,.28),"top",(sx*.8,.1,-1.1),(sx*10,0,0),"C",mirror=sx<0)
        B.add("Eye"+suf,st,"gem",(.5,.5,.5),"top")
        m=B.add("Merus"+suf,"CoreRoot","box",(.8,1.5,.8),None,(sx*2.0,.1,-.9),(sx*24,0,0),"B",mirror=sx<0)
        c=B.add("Carpus"+suf,m,"box",(.7,1.2,.7),"bot",(0,0,-.3),(-34,0,0),"A")
        pr=B.add("Prop"+suf,c,"box",(.75,1.5,.7),"bot",(0,0,-.2),(-20,0,0),"B")
        B.add("Dactyl"+suf,pr,"wedge",(.5,1.4,.5),"bot",(0,-.1,-.15),(-26,0,0),"S")
        B.add("Pollex"+suf,pr,"wedge",(.5,1.1,.5),"bot",(0,-.1,.3),(22,0,0),"S")
    for i in range(3):
        for sx,suf in ((1,"R"),(-1,"L")):
            l1=B.add("Walk%d%s"%(i,suf),"CoreRoot","box",(.45,1.5,.45),None,(sx*1.6,-.6,.7-i*.7),(0,sx*(i-1)*26,sx*34),"B")
            l2=B.add("Walk%d%s2"%(i,suf),l1,"box",(.36,1.4,.36),"bot",(0,0,0),(0,0,-sx*46),"A")
            B.add("Walk%d%s3"%(i,suf),l2,"pyramid",(.26,.7,.26),"bot",(0,0,0),(180,0,0),"D")
    B.tag("claws")
def b_spider(B,I,r):
    B.add("CoreRoot",None,"box",(2.0,1.4,2.2),None,(0,2.2,-.8),(0,0,0),"A",studs=True)
    ab=B.add("Abdomen","CoreRoot","box",(2.2,1.9,2.6),"back",(0,.5,.6),(0,0,0),"B",studs=True)
    hd=B.add("Head","CoreRoot","box",(1.4,1.1,1.2),"front",(0,-.1,-.4),(0,0,0),"B")
    for k,(dx,dy) in enumerate(((-.4,.1),(-.15,.25),(.15,.25),(.4,.1))):
        B.add("Eye%d"%k,hd,"gem",(.26,.3,.2),"front",(dx*2,dy,-.1),(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        ch=B.add("Chel"+suf,hd,"box",(.4,.7,.5),"bot",(sx*.35,-.1,-.4),(0,0,0),"D",mirror=sx<0)
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
        p1=B.add("Pauldron"+suf,"HumanoidRootPart","box",(1.3,.6,1.3),None,(sx*1.9,1.5,0),(0,0,sx*8),"B",mirror=sx<0,studs=True)
        a1=B.add("Arm"+suf,"HumanoidRootPart","box",(.9,2.2,.9),None,(sx*1.9,.2,0),(0,0,sx*6),"A",mirror=sx<0)
        a2=B.add("Fore"+suf,a1,"box",(.8,1.8,.8),"bot")
        B.add("Fist"+suf,a2,"box",(1.1,1.0,1.1),"bot",(0,0,0),(0,0,0),"D")
        l1=B.add("Leg"+suf,"HumanoidRootPart","box",(1.0,2.2,1.0),"bot",(sx*.9,-.2,0),(0,0,0),"B",mirror=sx<0)
        B.add("Foot"+suf,l1,"wedge",(1.2,.7,1.6),"bot",(0,0,-.3),(0,0,0),"D")
    for i in range(4):
        x,z=phyllo(i,4,.8)
        B.add("Crys%d"%i,"HumanoidRootPart","pyramid",(.4,1.6*B.sharp,.4),"top",(x,.1,z+.6),(-18,0,0),"S")
    B.tag("armor","glow")
def b_turtle(B,I,r):
    B.add("CoreRoot",None,"box",(3.0,1.2,3.4),None,(0,1.6,0),(0,0,0),"L")
    sh=B.add("ShellBase","CoreRoot","box",(3.2,1.0,3.6),"top",(0,.05,0),(0,0,0),"A",studs=True)
    s2=B.add("Shell2",sh,"box",(2.6,.9,3.0),"top")
    s3=B.add("Shell3",s2,"box",(1.8,.8,2.2),"top",(0,0,0),(0,0,0),"A",studs=True)
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
    b3=B.add("Bell3","CoreRoot","box",(2.6,.7,2.6),"top",(0,0,0),(0,0,0),"A",studs=True)
    B.add("GlowCore","CoreRoot","gem",(1.0,.8,1.0),"bot",(0,.2,0),(0,0,0),"C")
    for i in range(12):
        az=i*30.0;a=math.radians(az)
        B.add("Skirt%d"%i,b2,"wedge",(.5,.9,.16),None,(1.6*math.sin(a),-.5,1.6*math.cos(a)),(180,az,0),"L")
    for i in range(8):
        az=i*45.0;a=math.radians(az)
        base=B.add("Tent%d"%i,b2,"box",(.22,.7,.22),None,(1.5*math.sin(a),-.6,1.5*math.cos(a)),(0,az,0),"C")
        B.chain("Tent%d_"%i,base,5,[(.18,1.2,.18),(.16,1.1,.16),(.14,1.0,.14),(.12,.9,.12),(.1,0.8,.1)],
                ["C","L","C","L","C"],[8,10,12,14,16])
    B.tag("tentacles","frill","glow")
def b_car(B,I,r):
    p=I["prop"]; ws=.8*p.get("wheels",1.0); lift=.3*p.get("lift",1.0)
    ch=B.add("CoreRoot",None,"box",(4.4,.8,2.2),None,(0,1.0+lift,0),(0,0,0),"A",studs=True)
    cab=B.add("Cabin",ch,"box",(2.2,.85,1.8),"top",(0,0,.2),(0,0,0),"B",studs=True)
    B.add("WinF",cab,"box",(1.9,.6,.12),"front",(0,0,-.02),(0,0,0),"D")
    B.add("WinB",cab,"box",(1.9,.6,.12),"back",(0,0,-.02),(0,0,0),"D")
    B.add("Hood",ch,"wedge",(1.6,.35,1.9),"top",(0,-.15,-1.5),(0,0,0),"A")
    for sx,suf in ((1,"R"),(-1,"L")):
        for zz,tag in ((1.5,"F"),(-1.5,"B")):
            B.add("Wheel%s%s"%(tag,suf),ch,"cylinder",(ws,.5,ws),None,(sx*1.15,-.35+lift*.3,zz),(0,0,90),"D")
        B.add("Light%s"%suf,ch,"box",(.4,.3,.15),"front",(sx*.75,.15,-.02),(0,0,0),"C",mirror=sx<0)
        B.add("Tail%s"%suf,ch,"box",(.4,.3,.15),"back",(sx*.75,.15,-.02),(0,0,0),"S",mirror=sx<0)
    B.add("BumpF",ch,"box",(4.2,.4,.3),"front",(0,-.2,-.05),(0,0,0),"D")
    B.add("BumpB",ch,"box",(4.2,.4,.3),"back",(0,-.2,-.05),(0,0,0),"D")
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
    hl=B.add("CoreRoot",None,"box",(5.0,1.1,2.4),None,(0,1.2,0),(0,0,0),"A",studs=True)
    B.add("Bow",hl,"wedge",(2.2,1.0,1.6),"front",(0,0,-.2),(0,90,0),"A")
    cab=B.add("Cabin",hl,"box",(2.0,1.0,1.6),"top",(0,0,.6),(0,0,0),"B",studs=True)
    B.add("Win",cab,"box",(1.6,.5,.12),"front",(0,0,-.02),(0,0,0),"D")
    B.add("Mast",cab,"box",(.2,2.2,.2),"top")
    B.add("Prop",hl,"cylinder",(.8,.2,.8),"back",(0,-.2,-.1),(90,0,0),"D")
    B.tag("hull")
def b_plane(B,I,r):
    fu=B.add("CoreRoot",None,"box",(1.6,1.4,5.0),None,(0,2.2,0),(0,0,0),"A",studs=True)
    B.add("Nose",fu,"wedge",(1.4,1.2,1.4),"front",(0,0,-.1),(90,0,0),"B")
    B.add("Cockpit",fu,"wedge",(1.0,.6,1.4),"top",(0,0,-1.2),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Wing"+suf,fu,"wedge",(4.0,.25,1.4),None,(sx*2.2,-.2,-.3),(0,0,sx*8),"B",mirror=sx<0)
        B.add("Stab"+suf,fu,"wedge",(1.4,.2,.8),None,(sx*.9,.5,2.4),(0,0,sx*8),"B",mirror=sx<0)
    B.add("Fin",fu,"wedge",(.2,1.6,1.2),"top",(0,0,2.2),(0,0,0),"C")
    B.tag("wings")
def b_heli(B,I,r):
    bd=B.add("CoreRoot",None,"box",(2.0,1.6,3.4),None,(0,2.0,0),(0,0,0),"A",studs=True)
    B.add("Win",bd,"box",(1.6,.8,.12),"front",(0,.2,-.02),(0,0,0),"D")
    tb=B.add("Boom",bd,"box",(.5,.5,3.0),"back",(0,.3,-.2),(0,0,0),"B")
    B.add("TRotor",tb,"wedge",(.15,1.4,.4),"right",(0,0,0),(0,0,90),"D")
    hub=B.add("Hub",bd,"cylinder",(.5,.4,.5),"top")
    for i in range(4):
        B.add("Blade%d"%i,hub,"box",(4.6,.12,.4),"top",(0,.15,0),(0,i*90,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Skid"+suf,bd,"box",(.2,.2,3.2),"bot",(sx*1.0,-.5,0),(0,0,0),"D",mirror=sx<0)
        B.add("Strut"+suf,bd,"box",(.15,.7,.15),"bot",(sx*1.0,-.2,.8),(0,0,0),"D",mirror=sx<0)
    B.tag("rotor")
def b_tank(B,I,r):
    hl=B.add("CoreRoot",None,"box",(4.0,1.0,2.6),None,(0,1.3,0),(0,0,0),"A",studs=True)
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Track"+suf,hl,"box",(4.4,.9,.7),None,(sx*1.5,-.2,0),(0,0,0),"D",mirror=sx<0)
    tu=B.add("Turret",hl,"box",(1.8,.9,2.0),"top",(0,0,-.3),(0,0,0),"B",studs=True)
    B.add("Barrel",tu,"cylinder",(.3,2.6,.3),"front",(0,.1,-.2),(90,0,0),"D")
    B.add("Hatch",tu,"box",(.7,.2,.7),"top",(0,0,.5),(0,0,0),"D")
    B.tag("armor")
BUILDERS={"humanoid":b_humanoid,"octopus":b_octopus,"serpent":b_serpent,"fish":b_fish,"bird":b_bird,
 "crab":b_crab,"spider":b_spider,"golem":b_golem,"turtle":b_turtle,"jelly":b_jelly,"car":b_car,
 "bike":b_bike,"boat":b_boat,"plane":b_plane,"heli":b_heli,"tank":b_tank}
BUDGETS={"humanoid":70,"octopus":90,"serpent":60,"fish":50,"bird":60,"crab":70,"spider":70,"golem":60,
 "turtle":50,"jelly":90,"car":45,"bike":25,"boat":30,"plane":30,"heli":35,"tank":30}

# ================= 7. CRITIQUE v5 (style + purpose + grounding) =================
def critique(spec,I):
    rep={};tot=0.0;ws=0.0
    def add(k,v,w): rep[k]=int(round(v*100));return v*w
    tot+=add("context",1.0 if spec["archetype"]==I["root"] else .15,.16);ws+=.16
    names={p["n"] for p in spec["parts"]}
    conn=all(p["p"] in names for p in spec["parts"] if p["p"])
    tot+=add("connected",1.0 if conn else .2,.10);ws+=.10
    idx={p["n"]:p for p in spec["parts"]}
    def ymin(n):
        p=idx[n];y=p["po"][1]-p["sz"][1]/2;par=p["p"]
        while par and par in idx: y+=idx[par]["po"][1];par=idx[par]["p"]
        return y
    my=min(ymin(p["n"]) for p in spec["parts"])
    ok_g=abs(my)<.4 if not I["float"] else my>1.0
    tot+=add("grounded",1.0 if ok_g else .3,.08);ws+=.08
    studs=sum(1 for p in spec["parts"] if p["n"].startswith("Stud"))
    tot+=add("style_studs",1.0 if studs>=6 else .4,.10);ws+=.10
    n=len(spec["parts"]);bud=BUDGETS.get(spec["archetype"],80)
    tot+=add("purpose",1.0 if n<=bud*1.6 else .5,.10);ws+=.10
    if I["colors"]:
        ds=[max(0,1-min(hue_dist(ih,hex_hsv(h)[0]) for h in list(spec["palette"].values())[:6])/90.0) for ih,_,_ in I["colors"]]
        tot+=add("color_match",sum(ds)/len(ds),.16);ws+=.16
    else: tot+=add("color_match",.85,.16);ws+=.16
    want=set(I["traits"]);have=set()
    for t in want:
        if any(t.split("_")[-1] in p["n"].lower() or t in p["n"].lower() for p in spec["parts"]): have.add(t)
    tot+=add("trait_match",len(want&have)/max(1,len(want)) if want else 1.0,.14);ws+=.14
    sizes=[p["sz"][0] for p in spec["parts"] if not p["n"].startswith("Stud")]
    tot+=add("silhouette",clamp((max(sizes)-min(sizes))/max(.001,max(sizes))/.8,0,1),.08);ws+=.08
    tot+=add("sharp_match",max(0,1-abs(I["sharp"]-spec["sharpness"])/2.0),.08);ws+=.08
    return int(round(100*tot/ws)),rep

# ================= 8. MEMORY + SEARCH =================
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
def _build(I,arch,seed,feat):
    rng=random.Random(seed);pal=synthesize_palette(I,rng)
    if feat.get("colors") and not I["palette_force"]:
        fc=feat["colors"];pal["A"]=fc[0];pal["B"]=fc[min(1,len(fc)-1)];pal["C"]=fc[min(2,len(fc)-1)]
        pal["S"]=fc[min(3,len(fc)-1)]
    B=Builder(seed,pal,rng,I["sharp"],I["size"])
    BUILDERS[arch](B,I,rng)
    for t in I["traits"]:
        fn=ADDONS.get(t)
        if fn and t not in I["neg"]: fn(B,I,rng)
    if not I["float"]: ground(B)
    pose_wrap(B,I["pose"],I["float"])
    return {"id":"m%d_%d"%(int(time.time()*1000)%100000,seed%97),"name":rng.choice(NAME_PRE)+NAME_SUF[arch],
      "archetype":arch,"variant":seed%4,"seed":seed,"sharpness":round(B.sharp,2),"scale":round(B.scale,2),
      "palette":pal,"tags":sorted(B.present),"root":B.root,"parts":B.parts,"mirrored":B.mirrored,
      "counts":dict(B.counts),"traits_present":sorted(B.present),
      "meta":{"scheme":"v5","mods":I["mods"],"prompt":I.get("_prompt","")}}
def generate(body,mem):
    t0=time.time();prompt=body.get("prompt","human");it=int(body.get("iteration",0))
    nonce=body.get("nonce","x");reasons=body.get("reasons",[]);feat=body.get("features") or {}
    I=parse_intent(prompt);I["_prompt"]=prompt
    mbias,blend,mpal,liked=memory_priors(mem,prompt)
    for a,w in mbias.items():
        if a==I["root"]: continue
    if blend:
        I["sharp"]=clamp(I["sharp"]*.75+blend["sharp"]*.25,.2,2.6);I["size"]*= .9+blend["scale"]*.1
    if "wrong creature" in reasons:
        I["root"]=ARCHES[(ARCHES.index(I["root"])+3)%len(ARCHES)]
    if "too many spikes" in reasons: I["sharp"]=max(.2,I["sharp"]-1.0)
    if "not enough detail" in reasons: I["sharp"]=min(2.6,I["sharp"]+.8)
    if "wrong colors" in reasons: I["palette_force"]=None;I["colors"]=[]
    K=6+min(6,it*2);best=None;tried=0
    for k in range(K):
        if time.time()-t0>BUDGET: break
        seed=zlib.crc32(("%s|%d|%s|%d"%(prompt,it,nonce,k)).encode())
        I2=dict(I);I2["sharp"]=clamp(I["sharp"]+random.Random(seed).uniform(-.15,.15),.2,2.6)
        try: spec=_build(I2,I["root"],seed,feat)
        except Exception: continue
        tried+=1;s,rep=critique(spec,I2);spec["score"]=s;spec["report"]=rep
        if best is None or s>best["score"]: best=spec
    if best:
        for m in range(3):
            if time.time()-t0>BUDGET: break
            I3=dict(I);I3["sharp"]=clamp(I["sharp"]+random.uniform(-.3,.3),.2,2.6)
            I3["size"]=clamp(I["size"]+random.uniform(-.1,.1),.5,1.8)
            seed=best["seed"]+m+13
            try: cand=_build(I3,best["archetype"],seed,feat)
            except Exception: continue
            s2,r2=critique(cand,I3);cand["score"]=s2;cand["report"]=r2;tried+=1
            if s2>best["score"]: best=cand
    if best is None:
        best=_build(I,"humanoid",1,feat);best["score"],best["report"]=critique(best,I);tried=1
    best["meta"].update({"beam":K,"tried":tried,"iteration":it,"seconds":round(time.time()-t0,2)})
    return best
