"""BrickForge AI v11 — Studio-Grade Brick Sculpting & Static Rig Pipeline.
v11: Clean stepped brick geometry, zero random clutter, anti-flicker non-coplanar layering,
     static joint-rigged poses (Astronaut with flag, Martial Artist stance, Kraken/Octopus with
     curling suction-cup tentacles, Phoenix with layered feather wings, Speed-Champions Sports Car,
     stepped-brick Magical Horse/Unicorn + 60 species, Mech, Train, Furniture, Food, Weapons)."""
import math, random, re, colorsys, zlib, time, difflib
from collections import Counter

BUDGET = 7.5

# ---------------------------------------------------------------- species (quadrupeds & creatures)
# palette order: A body, B legs/ears/secondary, C accent, S horns/special, D hooves/dark, L light/muzzle
_Q = dict(bw=2.0,bh=1.55,bl=3.2,leg=1.7,lw=.42,neck=1.0,nang=36,head=(1.0,1.0,1.25),snout=(.62,.52,.62),
          ears="point",ear=(.3,.5),horns=None,tail="short",size=1.0,headc="A",snoutc="L",extras=(),
          pal=("#b98d5e","#8b6a43","#e8c547","#d9cbb0","#3b2a1c","#efe4cf"))
def _sp(**k):
    d = dict(_Q); d.update(k); return d

SPECIES = {
 "goat":     _sp(bh=1.4,leg=1.7,lw=.36,neck=1.15,nang=35,head=(.92,1.0,1.15),snout=(.58,.5,.58),ears="side",
                 ear=(.45,.55),horns="curved",tail="short",extras=("beard",),
                 pal=("#e6e0d2","#a89c86","#e8c547","#5a4a3a","#2d241c","#fbf8f0")),
 "ibex":     _sp(bh=1.45,leg=1.8,lw=.38,neck=1.2,nang=32,head=(.92,1.0,1.15),snout=(.58,.5,.58),ears="side",
                 ear=(.4,.5),horns="spiral",tail="short",extras=("beard",),
                 pal=("#9c8268","#6e5842","#e8c547","#3d3126","#241c15","#e6dbc8")),
 "sheep":    _sp(leg=1.35,lw=.38,neck=.75,nang=25,head=(.9,.95,1.05),snout=(.55,.5,.5),ears="side",ear=(.4,.45),
                 headc="B",extras=("wool",),pal=("#f1eee6","#3d3a38","#e8c547","#8a7f70","#2a2624","#ffffff")),
 "dog":      _sp(bh=1.35,bl=2.8,leg=1.35,lw=.38,neck=.65,nang=30,head=(.95,.92,1.05),snout=(.55,.45,.8),ears="floppy",
                 ear=(.5,.8),tail="long_up",pal=("#c89a62","#8f6a3e","#e8c547","#d8b98a","#2b1d12","#f3e6cf")),
 "husky":    _sp(bh=1.4,bl=2.95,leg=1.55,lw=.4,neck=.75,nang=32,head=(.95,.92,1.08),snout=(.54,.45,.82),ears="point",
                 ear=(.34,.62),tail="bushy",extras=("patches",),pal=("#58606b","#d8dee6","#5cc8ff","#2b3038","#1c2026","#ffffff")),
 "corgi":    _sp(bw=1.8,bh=1.25,bl=2.85,leg=.8,lw=.38,neck=.6,nang=28,head=(.95,.9,1.02),snout=(.52,.42,.75),ears="point",
                 ear=(.42,.75),tail="ball",pal=("#d98b3a","#b56b22","#2b1d12","#f5efe6","#24180e","#ffffff")),
 "wolf":     _sp(bh=1.45,bl=3.1,leg=1.7,lw=.38,neck=.75,nang=32,head=(.95,.92,1.12),snout=(.52,.45,.9),ears="point",
                 ear=(.32,.6),tail="bushy",pal=("#8e949c","#5d636b","#e8c547","#c9ced4","#22262b","#e9edf0")),
 "hyena":    _sp(bh=1.45,bl=2.9,leg=1.55,lw=.4,neck=.8,nang=22,head=(1.0,.95,1.1),snout=(.55,.5,.75),ears="round",
                 ear=(.42,.48),tail="bushy",extras=("spots","hmane"),pal=("#b89660","#7a5f36","#e8c547","#3b2c1a","#261c10","#dec89c")),
 "fox":      _sp(bh=1.25,bl=2.7,leg=1.35,lw=.32,neck=.65,nang=30,head=(.92,.88,1.02),snout=(.5,.4,.9),ears="point",
                 ear=(.42,.8),tail="bushy",pal=("#d9742b","#a9511a","#2b2118","#f3e9dc","#2a1a10","#fbf5ec")),
 "cat":      _sp(bw=1.6,bh=1.15,bl=2.5,leg=1.05,lw=.32,neck=.55,nang=30,head=(1.0,.92,.95),snout=(.42,.32,.35),ears="point",
                 ear=(.35,.5),tail="long_up",pal=("#9a9aa2","#6e6e78","#7cd67c","#e0d0c0","#2a2a30","#f2f2f4")),
 "lion":     _sp(bw=2.05,bh=1.75,bl=3.4,leg=1.75,lw=.5,neck=.65,nang=25,head=(1.12,1.05,1.15),snout=(.58,.48,.55),ears="round",
                 ear=(.4,.4),tail="tuft",extras=("mane",),pal=("#d9a441","#b5802a","#e8c547","#6b3f1d","#3b2410","#f0d9a8")),
 "tiger":    _sp(bw=1.95,bh=1.55,bl=3.4,leg=1.55,lw=.48,neck=.65,nang=28,head=(1.08,.98,1.1),snout=(.56,.46,.52),ears="round",
                 ear=(.38,.38),tail="hang",extras=("stripes",),pal=("#e08a2c","#b8661a","#e8c547","#f5e6c8","#1f140c","#fbf3e2")),
 "jaguar":   _sp(bw=1.9,bh=1.5,bl=3.3,leg=1.5,lw=.46,neck=.65,nang=28,head=(1.02,.95,1.08),snout=(.54,.44,.5),ears="round",
                 ear=(.36,.36),tail="hang",extras=("spots",),pal=("#d99b38","#a8721c","#7cd67c","#2b1e0d","#1a1106","#f5e1b8")),
 "panther":  _sp(bw=1.85,bh=1.45,bl=3.3,leg=1.55,lw=.44,neck=.65,nang=28,head=(1.0,.92,1.08),snout=(.52,.42,.5),ears="round",
                 ear=(.35,.35),tail="hang",pal=("#22222a","#15151c","#f2c94c","#383846","#0d0d12","#454554")),
 "horse":    _sp(bw=1.95,bh=1.65,bl=3.7,leg=2.6,lw=.38,neck=2.0,nang=34,head=(.88,.95,1.45),snout=(.72,.6,.65),ears="point",
                 ear=(.24,.48),tail="hang",extras=("hmane",),snoutc="L",pal=("#8a5a35","#5e3b1f","#e8c547","#2a1a10","#1f130a","#e9d9c0")),
 "zebra":    _sp(bw=1.95,bh=1.65,bl=3.6,leg=2.5,lw=.38,neck=1.85,nang=34,head=(.88,.95,1.42),snout=(.7,.6,.62),ears="point",
                 ear=(.24,.48),tail="tuft",extras=("hmane","stripes"),snoutc="D",pal=("#f2f2f2","#262626","#e8c547","#1a1a1a","#141414","#ffffff")),
 "unicorn":  _sp(bw=1.95,bh=1.65,bl=3.6,leg=2.6,lw=.38,neck=2.0,nang=34,head=(.88,.95,1.42),snout=(.72,.6,.65),ears="point",
                 ear=(.24,.48),horns="straight",tail="hang",extras=("hmane",),
                 pal=("#9be2e8","#7bc5cd","#a832a8","#f5d142","#d4af37","#e8f8fa")),
 "pegasus":  _sp(bw=1.95,bh=1.65,bl=3.6,leg=2.6,lw=.38,neck=2.0,nang=34,head=(.88,.95,1.42),snout=(.72,.6,.65),ears="point",
                 ear=(.24,.48),tail="hang",extras=("hmane","qwing"),
                 pal=("#f4f8ff","#cde0ff","#66b2ff","#ffd86b","#527acc","#ffffff")),
 "donkey":   _sp(bh=1.45,bl=3.1,leg=1.85,lw=.36,neck=1.1,nang=34,head=(.88,.95,1.32),snout=(.65,.55,.55),ears="long",
                 ear=(.3,1.1),tail="tuft",pal=("#8b8f96","#5f6368","#e8c547","#cfd3d8","#2b2d30","#f0f0f0")),
 "cow":      _sp(bw=2.15,bh=1.75,bl=3.4,leg=1.5,lw=.46,neck=.75,nang=25,head=(1.02,1.02,1.15),snout=(.72,.52,.45),ears="side",
                 ear=(.5,.5),horns="bull",tail="tuft",extras=("spots","udder"),
                 pal=("#f4f1ea","#d9d4c8","#e8c547","#e8dcc0","#1f1f1f","#f5b8c4")),
 "bison":    _sp(bw=2.5,bh=2.1,bl=3.5,leg=1.5,lw=.55,neck=.65,nang=15,head=(1.3,1.3,1.2),snout=(.7,.55,.45),ears="side",
                 ear=(.45,.45),horns="bull",tail="tuft",extras=("hump","beard"),
                 pal=("#593a22","#3d2616","#e8c547","#d9ccb4","#1f140b","#785235")),
 "pig":      _sp(bw=2.1,bh=1.7,bl=3.0,leg=.95,lw=.5,neck=.5,nang=20,head=(1.1,1.0,1.05),snout=(.6,.5,.38),ears="floppy",
                 ear=(.45,.5),tail="curly",pal=("#f2a6b8","#e08aa0","#2b1d12","#f9c9d4","#3d2a30","#f9c9d4")),
 "boar":     _sp(bw=2.1,bh=1.75,bl=3.1,leg=1.15,lw=.48,neck=.55,nang=18,head=(1.15,1.05,1.15),snout=(.65,.52,.45),ears="point",
                 ear=(.35,.45),tail="short",extras=("tusks","hmane"),pal=("#5e4938","#423225","#e8c547","#f0e6d2","#261c14","#ebe0cc")),
 "deer":     _sp(bw=1.75,bh=1.5,bl=3.1,leg=2.5,lw=.32,neck=1.65,nang=30,head=(.82,.88,1.22),snout=(.55,.5,.55),ears="point",
                 ear=(.3,.6),horns="antlers",tail="short",pal=("#b07a45","#8b5c2e","#e8c547","#e2d2b0","#2b1a0e","#f3e7d0")),
 "moose":    _sp(bw=2.2,bh=1.9,bl=3.4,leg=2.7,lw=.42,neck=1.2,nang=22,head=(1.0,1.0,1.45),snout=(.75,.65,.7),ears="side",
                 ear=(.45,.55),horns="antlers",tail="short",extras=("hump","beard"),pal=("#5e4028","#422c1b","#e8c547","#c9b38c","#24170d","#805a3b")),
 "rabbit":   _sp(bw=1.7,bh=1.5,bl=2.3,leg=.95,lw=.4,neck=.45,nang=20,head=(1.1,1.0,1.1),snout=(.45,.35,.32),ears="long",
                 ear=(.28,1.5),tail="ball",pal=("#e9e2d6","#cfc4b2","#ff9fb3","#f7f1e8","#3a2e24","#ffffff")),
 "kangaroo": _sp(bw=1.8,bh=1.6,bl=2.4,leg=2.2,lw=.46,neck=1.2,nang=12,head=(.85,.85,1.1),snout=(.55,.45,.55),ears="long",
                 ear=(.28,.95),tail="croc",pal=("#c48348","#9c622e","#2b1d12","#e6cca8","#332010","#f2dfc4")),
 "bear":     _sp(bw=2.4,bh=2.2,bl=3.3,leg=1.35,lw=.75,neck=.55,nang=15,head=(1.4,1.3,1.3),snout=(.52,.42,.52),ears="round",
                 ear=(.4,.4),tail="short",pal=("#6b4423","#4a2f1b","#e8c547","#d9c2a0","#1c120a","#c9a47a")),
 "polarbear":_sp(bw=2.5,bh=2.2,bl=3.4,leg=1.4,lw=.78,neck=.65,nang=14,head=(1.35,1.25,1.4),snout=(.52,.42,.55),ears="round",
                 ear=(.36,.36),tail="short",pal=("#f2f5f8","#dce3eb","#22262b","#ffffff","#14171a","#ffffff")),
 "panda":    _sp(bw=2.4,bh=2.2,bl=3.1,leg=1.35,lw=.75,neck=.55,nang=15,head=(1.4,1.3,1.3),snout=(.52,.42,.52),ears="round",
                 ear=(.4,.4),tail="short",extras=("patches",),pal=("#f4f4f4","#1c1c1c","#e8c547","#cfcfcf","#111111","#ffffff")),
 "koala":    _sp(size=.8,bw=2.0,bh=1.8,bl=2.2,leg=1.0,lw=.48,neck=.3,nang=10,head=(1.3,1.2,1.1),snout=(.45,.55,.35),ears="round",
                 ear=(.75,.75),tail="ball",snoutc="D",pal=("#8c949e","#68707a","#22252a","#e2e6eb","#1f2124","#ffffff")),
 "gorilla":  _sp(bw=2.6,bh=2.3,bl=2.8,leg=1.5,lw=.85,neck=.4,nang=10,head=(1.35,1.4,1.25),snout=(.65,.5,.45),ears="round",
                 ear=(.32,.32),tail="short",snoutc="B",pal=("#2b2d33","#484c56","#e09f3e","#707685","#15161a","#5c616e")),
 "monkey":   _sp(size=.82,bw=1.6,bh=1.4,bl=2.3,leg=1.5,lw=.35,neck=.5,nang=20,head=(1.1,1.0,1.0),snout=(.55,.45,.35),ears="round",
                 ear=(.55,.55),tail="long_up",pal=("#8c5832","#633b1d","#2b1a0e","#f0c8a0","#241509","#f5d6b8")),
 "elephant": _sp(bw=3.0,bh=2.8,bl=4.0,leg=2.4,lw=1.0,neck=.5,nang=10,head=(1.8,1.9,1.5),snout=(.35,.35,.2),ears="flap",
                 ear=(1.4,1.8),tail="short",extras=("trunk","tusks"),snoutc="A",
                 pal=("#8e949c","#757b83","#e8c547","#f2ecdc","#3b3f45","#b8bec6")),
 "mammoth":  _sp(bw=3.1,bh=2.9,bl=4.1,leg=2.4,lw=1.05,neck=.5,nang=10,head=(1.85,1.95,1.55),snout=(.35,.35,.2),ears="round",
                 ear=(.6,.6),tail="short",extras=("trunk","tusks","hump","wool"),snoutc="A",
                 pal=("#6e4726","#4f3118","#e8c547","#f5ead2","#29190c","#91633b")),
 "rhino":    _sp(bw=2.7,bh=2.3,bl=3.8,leg=1.6,lw=.85,neck=.6,nang=12,head=(1.35,1.3,1.55),snout=(.75,.65,.65),ears="point",
                 ear=(.32,.48),horns="rhino",tail="short",snoutc="A",
                 pal=("#7c8288","#5f656b","#e8c547","#e6dec8","#2d3033","#9aa0a6")),
 "hippo":    _sp(bw=2.8,bh=2.2,bl=3.8,leg=1.2,lw=.82,neck=.5,nang=10,head=(1.5,1.35,1.5),snout=(.95,.75,.75),ears="round",
                 ear=(.3,.3),tail="short",snoutc="B",
                 pal=("#7d6b7d","#9e829c","#e8c547","#f2e8dc","#382e38","#b89ab6")),
 "giraffe":  _sp(bw=1.95,bh=1.7,bl=3.1,leg=3.8,lw=.38,neck=3.8,nang=14,head=(.9,.9,1.3),snout=(.6,.5,.6),ears="point",
                 ear=(.3,.45),horns="knobs",tail="tuft",extras=("spots",),
                 pal=("#e0b04a","#c98f2e","#e8c547","#8a5a1a","#6b3f12","#f6e3b0")),
 "camel":    _sp(bw=1.95,bh=1.7,bl=3.4,leg=2.6,lw=.4,neck=2.0,nang=35,head=(.9,.9,1.2),snout=(.6,.5,.6),ears="round",
                 ear=(.25,.25),tail="short",extras=("hump",),pal=("#c9a06a","#a47c48","#e8c547","#e0c9a0","#3b2a18","#ecd9b8")),
 "llama":    _sp(bh=1.6,bl=2.8,leg=2.2,lw=.36,neck=2.2,nang=22,head=(.85,.9,1.05),snout=(.6,.5,.5),ears="point",
                 ear=(.25,.6),tail="short",extras=("wool",),pal=("#efe6d6","#c9bba4","#e8c547","#a58f6e","#4a3b2a","#ffffff")),
 "dino":     _sp(bh=1.9,bl=3.6,leg=1.6,lw=.65,neck=.9,nang=25,head=(1.3,1.2,2.0),snout=(.9,.6,.5),ears="none",
                 tail="croc",extras=("plates",),pal=("#5aa05a","#3f7a3f","#f2c94c","#e7d9a6","#243b24","#b9dca0")),
 "trex":     _sp(bw=2.2,bh=2.3,bl=3.6,leg=2.4,lw=.75,neck=1.1,nang=28,head=(1.5,1.45,2.2),snout=(.92,.7,.65),ears="none",
                 tail="croc",snoutc="A",pal=("#4d7c43","#36592f","#f2c94c","#f0e8d0","#1f331b","#9ab88d")),
 "triceratops":_sp(bw=2.5,bh=2.1,bl=3.7,leg=1.6,lw=.75,neck=.6,nang=12,head=(1.5,1.4,1.6),snout=(.65,.55,.65),ears="none",
                 horns="tricera",tail="croc",extras=("frill","plates"),pal=("#3b78b8","#29568a","#f2c94c","#f5f0e6","#1c3857","#8ec2f2")),
 "brachio":  _sp(bw=2.6,bh=2.4,bl=3.8,leg=3.2,lw=.85,neck=4.0,nang=18,head=(1.0,1.0,1.3),snout=(.7,.55,.55),ears="none",
                 tail="croc",pal=("#5c8f78","#416957","#f2c94c","#c2dbcf","#243b30","#a8ccc0")),
 "croc":     _sp(bh=.95,bl=3.8,leg=.65,lw=.5,neck=.35,nang=10,head=(1.2,.8,1.8),snout=(.9,.6,.6),ears="none",
                 tail="croc",extras=("plates",),pal=("#4f8f4a","#3a6e36","#f2c94c","#cfd8a0","#1e3a1c","#d8e3a8")),
 "mouse":    _sp(size=.7,bw=1.8,bh=1.3,bl=2.4,leg=.8,lw=.35,neck=.3,nang=20,head=(1.1,1.0,1.2),snout=(.4,.35,.4),
                 ears="round",ear=(.8,.8),tail="long_thin",pal=("#a9a9b0","#f4b9c2","#2b2b30","#85858c","#2b2b30","#ece9e4")),
 "squirrel": _sp(size=.75,bw=1.6,bh=1.3,bl=2.2,leg=.9,lw=.34,neck=.4,nang=22,head=(1.0,.95,1.0),snout=(.45,.38,.4),
                 ears="point",ear=(.32,.48),tail="bushy",pal=("#b8622a","#8c4518","#22160c","#e6c8a8","#26170c","#f5e4d0")),
 "raccoon":  _sp(size=.82,bw=1.9,bh=1.4,bl=2.6,leg=1.0,lw=.36,neck=.45,nang=22,head=(1.05,.95,1.05),snout=(.48,.38,.55),
                 ears="point",ear=(.35,.45),tail="bushy",extras=("patches","stripes"),pal=("#787d85","#363940","#e8c547","#d5dae0","#1a1c20","#f2f4f7")),
 "hedgehog": _sp(size=.72,bw=2.1,bh=1.6,bl=2.3,leg=.65,lw=.32,neck=.25,nang=10,head=(.95,.85,1.0),snout=(.45,.35,.55),
                 ears="round",ear=(.3,.3),tail="ball",extras=("plates",),pal=("#75563c","#c9a986","#241a12","#4a3423","#1f150e","#ebd5bc")),
 "otter":    _sp(size=.8,bw=1.6,bh=1.1,bl=3.2,leg=.75,lw=.36,neck=.65,nang=20,head=(.95,.85,1.05),snout=(.55,.4,.45),
                 ears="round",ear=(.26,.26),tail="croc",pal=("#6e4a30","#4f331f","#24170e","#ccb094","#1f130b","#e3ccb4")),
 "beaver":   _sp(size=.85,bw=2.1,bh=1.55,bl=2.8,leg=.8,lw=.42,neck=.35,nang=15,head=(1.1,1.0,1.05),snout=(.55,.45,.4),
                 ears="round",ear=(.28,.28),tail="croc",extras=("tusks",),pal=("#784b2a","#4a2e19","#24160c","#f2e2c4","#2e1c10","#cfa782")),
 "capybara": _sp(bw=2.0,bh=1.65,bl=3.0,leg=1.15,lw=.44,neck=.5,nang=15,head=(1.05,1.1,1.35),snout=(.75,.7,.55),
                 ears="round",ear=(.28,.28),tail="ball",snoutc="B",pal=("#a67446","#7a522e","#24180c","#d4aa80","#291b0e","#b88656")),
 "badger":   _sp(size=.85,bw=2.1,bh=1.35,bl=2.8,leg=.85,lw=.44,neck=.5,nang=18,head=(.95,.85,1.15),snout=(.5,.4,.6),
                 ears="round",ear=(.3,.3),tail="bushy",extras=("patches","stripes"),pal=("#4a4e54","#1f2124","#e8c547","#f0f2f5","#141517","#ffffff")),
 "skunk":    _sp(size=.78,bw=1.75,bh=1.3,bl=2.5,leg=.85,lw=.34,neck=.45,nang=20,head=(.9,.85,1.0),snout=(.48,.38,.5),
                 ears="round",ear=(.3,.3),tail="bushy",extras=("stripes",),pal=("#1f2024","#f5f7fa","#e8c547","#ffffff","#121316","#ffffff")),
 "sloth":    _sp(size=.85,bw=1.7,bh=1.4,bl=2.5,leg=1.6,lw=.36,neck=.6,nang=15,head=(1.0,.95,.95),snout=(.45,.35,.3),
                 ears="round",ear=(.22,.22),tail="short",extras=("patches",),pal=("#8c7762","#594a3c","#2b221a","#d9cbb8","#29211a","#e8dec8")),
 "griffin":  _sp(bw=2.0,bh=1.7,bl=3.3,leg=1.8,lw=.48,neck=1.1,nang=30,head=(1.1,1.05,1.25),snout=(.55,.5,.75),
                 ears="point",ear=(.35,.65),tail="tuft",extras=("qwing","mane"),snoutc="C",
                 pal=("#c98f38","#f2ead8","#ffb703","#784e18","#2b1d0c","#ffffff")),
 "cerberus": _sp(bw=2.3,bh=1.7,bl=3.3,leg=1.75,lw=.48,neck=.85,nang=28,head=(1.0,.95,1.1),snout=(.55,.48,.8),
                 ears="point",ear=(.35,.6),tail="long_up",extras=("cerb_heads","mane"),
                 pal=("#2b2628","#1a1618","#ff3333","#591818","#0f0c0d","#473c3f")),
 "beast":    _sp(pal=None,horns=None,ears="point",tail="short"),
}

SPECIES_KEYS = {
 "goat":["goat","billy","nanny"],"ibex":["ibex","markhor","chamois"],
 "sheep":["sheep","lamb","ram","ewe"],"husky":["husky","malamute","samoyed"],
 "corgi":["corgi","dachshund","wiener"],"dog":["dog","puppy","pup","hound","doggo","retriever","bulldog","poodle","pug","beagle","shiba","terrier","dalmatian"],
 "wolf":["wolf","werewolf","coyote","direwolf","fenrir","jackal"],"hyena":["hyena","gnoll"],
 "fox":["fox","vixen","kitsune","fennec"],"cat":["cat","kitten","kitty","lynx","bobcat","ocelot","caracal","tabby"],
 "lion":["lion","lioness","simba","manticore","sphinx"],"tiger":["tiger","sabertooth","bengal"],
 "jaguar":["jaguar","leopard","cheetah","cougar","puma"],"panther":["panther","wakanda"],
 "unicorn":["unicorn","alicorn","magicalhorse"],"pegasus":["pegasus"],
 "zebra":["zebra"],"horse":["horse","pony","stallion","mare","foal","mustang","steed"],
 "donkey":["donkey","mule","burro"],"bison":["bison","buffalo","yak","wisent"],
 "cow":["cow","cattle","bull","ox","calf","heifer","minotaur","brahma"],
 "boar":["boar","warthog","razorback"],"pig":["pig","hog","piglet","swine","sow"],
 "moose":["moose","elk","caribou"],"deer":["deer","reindeer","stag","antelope","gazelle","impala","fawn","buck","doe"],
 "rabbit":["rabbit","bunny","hare","jackrabbit"],"kangaroo":["kangaroo","wallaby","joey"],
 "polarbear":["polarbear","polar"],"panda":["panda"],"koala":["koala","wombat"],
 "bear":["bear","grizzly","kodiak","cub","brownbear"],
 "gorilla":["gorilla","ape","orangutan","bigfoot","yeti","sasquatch","kong"],
 "monkey":["monkey","chimp","chimpanzee","baboon","macaque","lemur","gibbon"],
 "mammoth":["mammoth","mastodon"],"elephant":["elephant"],
 "rhino":["rhino","rhinoceros"],"hippo":["hippo","hippopotamus"],
 "giraffe":["giraffe","okapi"],"camel":["camel","dromedary"],
 "llama":["llama","alpaca","vicuna"],
 "triceratops":["triceratops","styracosaurus"],"brachio":["brachiosaurus","brontosaurus","diplodocus","sauropod","apatosaurus"],
 "trex":["trex","tyrannosaurus","allosaurus","spinosaurus","carnotaurus"],
 "dino":["dinosaur","dino","raptor","velociraptor","stegosaurus","ankylosaurus","iguanodon","parasaurolophus"],
 "croc":["crocodile","croc","alligator","gator","caiman","lizard","gecko","iguana","komodo","chameleon","salamander","newt","frog","toad"],
 "squirrel":["squirrel","chipmunk","marmot","groundhog","prairiedog"],
 "raccoon":["raccoon","tanuki","redpanda","coati"],"hedgehog":["hedgehog","porcupine","echidna","armadillo","pangolin"],
 "otter":["otter","ferret","weasel","mink","stoat","mongoose","meerkat"],
 "beaver":["beaver","platypus","wolverine"],"capybara":["capybara","tapir","guineapig"],
 "badger":["badger","honeybadger"],"skunk":["skunk","opossum","possum"],
 "sloth":["sloth","anteater","aardvark"],
 "griffin":["griffin","gryphon","hippogriff"],"cerberus":["cerberus","hellhound","chimera"],
 "mouse":["mouse","rat","hamster","gerbil","chinchilla","vole","lemming"]}

ROOTS = {
 "humanoid": ["human","humans","man","woman","boy","girl","guy","dude","person","people","hero",
    "villain","wizard","mage","knight","soldier","ninja","pirate","doctor","teacher","driver",
    "engineer","chef","pilot","astronaut","spaceman","cosmonaut","farmer","builder","artist","musician","athlete",
    "boxer","karate","ryu","streetfighter","martialartist","fighter","guard","thief","robot","cyborg","android","alien",
    "anime","character","avatar","kid","child","samurai","viking","gladiator","paladin","ranger",
    "archer","assassin","monk","priest","cleric","necromancer","warlock","sorcerer","bard",
    "cowboy","sheriff","detective","policeofficer","firefighter","nurse","surgeon","scientist",
    "hacker","gamer","streamer","dj","dancer","skater","surfer","sniper","commando","general",
    "king","queen","prince","princess","emperor","pharaoh","vampire","zombie","skeleton",
    "mummy","ghost","demon","angel","elf","dwarf","orc","goblin","troll","ogre","santa","clown"],
 "mech": ["mech","mecha","gundam","exosuit","powerarmor","dreadnought","titanmech","battlebot","jaeger","walker","transformer"],
 "octopus": ["octopus","squid","kraken","cephalopod","ink","cuttlefish","nautilus","cthulhu"],
 "serpent": ["snake","serpent","dragon","wyrm","eel","viper","wyvern","cobra","python","anaconda",
    "worm","caterpillar","hydra","basilisk","leviathan","lindworm","boa","mamba","rattlesnake","centipede","millipede","charizard"],
 "fish": ["fish","shark","koi","bass","piranha","manta","goldfish","whale","beluga","dolphin","tuna","salmon",
    "trout","carp","clownfish","swordfish","stingray","orca","narwhal","manatee","dugong",
    "anglerfish","pufferfish","barracuda","catfish","marlin","seahorse","axolotl","seal","walrus"],
 "bird": ["bird","eagle","phoenix","falcon","owl","raven","parrot","hawk","duck","chicken","hen","rooster",
    "penguin","swan","crow","pigeon","seagull","flamingo","toucan","ostrich","peacock","goose",
    "pelican","heron","stork","crane","hummingbird","woodpecker","vulture","condor","albatross",
    "kiwi","emu","cassowary","turkey","quail","sparrow","robin","bluejay","cardinal","canary",
    "cockatoo","macaw","harpy","thunderbird","pterodactyl","pterosaur","bat"],
 "crab": ["crab","lobster","scorpion","shrimp","crustacean","crayfish","crawfish","hermitcrab","mantisshrimp","isopod","trilobite"],
 "spider": ["spider","arachnid","tarantula","weaver","ant","bug","insect","bee","wasp","mosquito",
    "beetle","ladybug","stagbeetle","scarab","mantis","grasshopper","cricket","locust","dragonfly",
    "firefly","butterfly","moth","hornet","bumblebee","termite","cockroach","tick","mite","flea"],
 "golem": ["golem","titan","colossus","elemental","construct","statue","gargoyle","monolith","treant","ent"],
 "turtle": ["turtle","tortoise","snail","slug","terrapin","seaturtle"],
 "jelly": ["jelly","jellyfish","medusa","blob","slime","amoeba","ooze","metroid","spore","virus"],
 "car": ["car","vehicle","auto","sedan","coupe","truck","van","taxi","racecar","sportscar","bus","police","jeep","suv",
    "limo","ambulance","firetruck","pickup","supercar","hatchback","wagon","minivan","lorry","tractor",
    "bulldozer","excavator","forklift","golfcart","kart","gokart","cybertruck","musclecar","hotrod",
    "camper","rv","humvee","armoredcar","convertible","roadster","f1","formula"],
 "train": ["train","locomotive","steamtrain","bullettrain","subway","metro","tram","trolley","monorail","caboose","railcar"],
 "bike": ["bike","motorcycle","scooter","bicycle","motorbike","moped","tricycle","unicycle","chopperbike","dirtbike","atv","quadbike","segway","hoverboard","skateboard"],
 "boat": ["boat","ship","yacht","canoe","submarine","sub","raft","sailboat","ferry","cruiseship",
    "battleship","destroyer","carrier","galleon","pirateship","vikingboat","longship","kayak",
    "gondola","speedboat","jetski","hovercraft","tugboat","barge","catamaran"],
 "plane": ["plane","airplane","jet","aircraft","glider","rocket","spaceship","shuttle","biplane",
    "fighterjet","bomber","airliner","seaplane","concorde","stealth","starfighter","xwing","ufo","saucer","blimp","zeppelin","airship","drone"],
 "heli": ["helicopter","heli","chopper","gunship","chinook","gyrocopter","osprey","quadcopter"],
 "tank": ["tank","warcraft","panzer","abrams","artillery","apc","halftrack","catapult","trebuchet","ballista","cannon"],
 "quadruped": sum(SPECIES_KEYS.values(),[])+["animal","beast","creature","pet","mammal","quadruped","livestock","critter","mount"],
 "building": ["house","home","cabin","hut","barn","shop","store","mansion","castle","fort","tower",
    "lighthouse","church","temple","building","skyscraper","office","factory","warehouse","hospital",
    "school","bank","hotel","cafe","restaurant","bakery","tavern","inn","windmill","pagoda","shrine",
    "mosque","cathedral","pyramid","igloo","tent","gazebo","pavilion","bunker","outpost","citadel",
    "palace","cottage","bungalow","shed","garage","hangar","stadium","arena","colosseum","bridge","gate","arch"],
 "tree": ["tree","pine","oak","palm","cactus","bush","plant","flower","mushroom","willow","birch",
    "maple","cherryblossom","sakura","baobab","redwood","sequoia","bonsai","bamboo","fern","vine",
    "rose","sunflower","tulip","lotus","lily","orchid","daisy","dandelion","toadstool","fungus","coral","seaweed","kelp","shrub","hedge"],
 "weapon": ["sword","mastersword","axe","spear","hammer","bow","staff","blade","dagger","wand","shield","katana",
    "rapier","scimitar","claymore","broadsword","longsword","machete","halberd","glaive","lance",
    "pike","trident","pitchfork","scythe","sickle","mace","flail","morningstar","warhammer","maul",
    "club","baton","nunchaku","crossbow","slingshot","boomerang","shuriken","kunai","chakram",
    "gun","pistol","revolver","rifle","shotgun","sniperrifle","smg","minigun","blaster","lasergun",
    "raygun","plasmagun","bazooka","rocketlauncher","flamethrower","chainsaw","lightsaber","scepter","buckler","aegis"],
 "furniture": ["chair","throne","stool","bench","sofa","couch","armchair","table","desk","workbench",
    "counter","bed","bunkbed","crib","hammock","bookshelf","bookcase","cabinet","wardrobe","closet",
    "dresser","nightstand","chest","treasure","treasurechest","safe","crate","box","barrel","keg",
    "lamp","lantern","chandelier","torch","candelabra","streetlight","tv","television","monitor",
    "computer","pc","laptop","arcade","console","piano","organ","jukebox","radio","speaker","clock",
    "grandfatherclock","mirror","painting","altar","portal","stargate","fountain",
    "well","cauldron","anvil","furnace","oven","fridge","refrigerator","sink","toilet","bathtub",
    "trashcan","dumpster","mailbox","hydrant","vendingmachine","atm","campfire","bonfire","tombstone","grave","coffin","sarcophagus"],
 "food": ["food","burger","hamburger","cheeseburger","sandwich","hotdog","taco","burrito","pizza",
    "sushi","ramen","noodles","soup","salad","steak","meat","drumstick","cake","cupcake","muffin",
    "donut","doughnut","cookie","pie","croissant","bread","toast","pancake","waffle","icecream",
    "popsicle","lollipop","candy","chocolate","apple","banana","strawberry","watermelon",
    "pineapple","grape","cherry","lemon","pear","coconut","pumpkin","carrot","corn",
    "broccoli","tomato","potato","fries","cheese","egg","potion","elixir","flask","vial","bottle",
    "cup","mug","coffee","tea","chalice","goblet","trophy","medal","gemstone","coin","gift","present"]}
ARCHES = list(ROOTS)

# Notice: No whole-model tilt (`pose` stays 0) so rigs stand upright on the ground!
MODS = {
 "bald":{"rm":["hair"]},"muscular":{"prop":{"chest":1.28,"arms":1.22}},
 "fat":{"prop":{"chest":1.32,"limbs":1.15}},"chubby":{"prop":{"chest":1.25,"limbs":1.1}},
 "skinny":{"prop":{"chest":.82,"limbs":.82}},"slim":{"prop":{"chest":.86,"limbs":.86}},
 "cute":{"prop":{"head":1.25,"limbs":.85},"sharp":-0.5,"scale":0.9,"eyes":1.3},
 "kawaii":{"prop":{"head":1.3,"limbs":.85},"sharp":-0.6,"scale":0.88,"eyes":1.35,"theme":"pastel"},
 "chibi":{"prop":{"head":1.35,"limbs":.8},"sharp":-0.5,"scale":0.85,"eyes":1.35},
 "tall":{"prop":{"limbs":1.25},"scale":1.12},"short":{"prop":{"limbs":.8},"scale":.88},
 "tiny":{"scale":0.65},"mini":{"scale":0.7},"micro":{"scale":0.6},
 "huge":{"scale":1.45},"giant":{"scale":1.6},"colossal":{"scale":1.7},"massive":{"scale":1.55},
 "big":{"scale":1.22},"large":{"scale":1.22},"small":{"scale":.78},"little":{"scale":.82},
 "baby":{"scale":.72,"prop":{"head":1.2},"eyes":1.25},"young":{"scale":.82,"prop":{"head":1.15}},
 "evil":{"sharp":0.5,"theme":"dark","add":"brow_evil"},
 "angry":{"add":"brow_evil"},"fierce":{"sharp":0.4,"add":"brow_evil"},
 "royal":{"theme":"gold","add":"hg_crown"},"king":{"theme":"gold","add":"hg_crown"},
 "queen":{"theme":"gold","add":"hg_crown"},"prince":{"theme":"gold","add":"hg_crown"},
 "princess":{"theme":"pastel","add":"hg_crown"},"crown":{"add":"hg_crown"},
 "icy":{"theme":"ice","mat":"ice","add":"hg_crystal"},"frozen":{"theme":"ice","mat":"ice","add":"hg_crystal"},
 "frost":{"theme":"ice","mat":"ice"},"crystal":{"theme":"crystal","mat":"ice","add":"hg_crystal"},
 "fire":{"theme":"lava","mat":"lava"},"fiery":{"theme":"lava","mat":"lava"},
 "flaming":{"theme":"lava","mat":"lava"},"lava":{"theme":"lava","mat":"lava"},
 "magma":{"theme":"lava","mat":"lava"},"infernal":{"theme":"lava","mat":"lava","add":"h_curved"},
 "golden":{"theme":"gold"},"silver":{"theme":"steel","mat":"metal"},
 "metallic":{"mat":"metal","theme":"steel"},"chrome":{"mat":"metal","theme":"steel"},
 "armored":{"mat":"metal","theme":"steel","prop":{"chest":1.18}},
 "dark":{"theme":"dark"},"shadow":{"theme":"dark","float":True},
 "void":{"theme":"galaxy","float":True},"galaxy":{"theme":"galaxy"},
 "cosmic":{"theme":"galaxy","float":True},"toxic":{"theme":"toxic"},
 "steampunk":{"theme":"bronze","add":"hg_glasses"},"clockwork":{"theme":"bronze","mat":"metal"},
 "cyberpunk":{"theme":"neon","add":"hg_glasses"},"cyber":{"theme":"neon","mat":"metal"},
 "futuristic":{"theme":"neon","mat":"metal"},"neon":{"theme":"neon"},"glowing":{"theme":"neon"},
 "pastel":{"theme":"pastel"},"magical":{"theme":"pastel"},
 "floating":{"float":True},"flying":{"float":True},"hovering":{"float":True},
 "sport":{"carbody":"sport","add":"sp_spoiler","theme":"race"},
 "sports":{"carbody":"sport","add":"sp_spoiler","theme":"race"},
 "racing":{"carbody":"sport","add":"sp_spoiler","theme":"race"},
 "offroad":{"prop":{"wheels":1.4,"lift":1.25}},
 "taxi":{"carbody":"sedan","add":"taxi_sign","theme":"gold"},
 "police":{"carbody":"sedan","add":"lightbar","theme":"navy"},
 "ambulance":{"carbody":"van","add":"lightbar"},
 "firetruck":{"carbody":"pickup","add":"lightbar","theme":"race"},
 "limo":{"carbody":"sedan"},"van":{"carbody":"van"},"bus":{"carbody":"van"},
 "buggy":{"carbody":"buggy"},"beetle":{"carbody":"buggy"},
 "monster":{"carbody":"pickup","prop":{"wheels":1.5,"lift":1.35}},
 "anime":{"eyes":1.35,"add":"hair_spiky"},
 "karate":{"add":"hg_headband","prop":{"chest":1.12,"arms":1.15}},
 "ryu":{"add":"hg_headband","prop":{"chest":1.15,"arms":1.18}},
 "streetfighter":{"add":"hg_headband","prop":{"chest":1.15,"arms":1.18}},
 "fighter":{"add":"hg_headband","prop":{"chest":1.12,"arms":1.15}},
 "boxer":{"prop":{"chest":1.15,"arms":1.2}},
 "samurai":{"add":"hg_helmet","theme":"race"},
 "viking":{"add":"hg_helmet","prop":{"chest":1.2}},
 "wizard":{"add":"hg_pointy","theme":"mystic"},"mage":{"add":"hg_pointy","theme":"mystic"},
 "witch":{"add":"hg_pointy","theme":"dark"},
 "knight":{"add":"hg_helmet","theme":"steel"},"paladin":{"add":"hg_helmet","theme":"gold"},
 "ninja":{"add":"hg_mask","theme":"dark"},"assassin":{"add":"hg_mask","theme":"dark"},
 "pirate":{"add":"hg_tricorn","theme":"sea"},"captain":{"add":"hg_tricorn","theme":"navy"},
 "chef":{"add":"hg_toque"},"driver":{"add":"hg_cap","theme":"race"},
 "engineer":{"add":"hg_hardhat","theme":"warn"},"builder":{"add":"hg_hardhat","theme":"warn"},
 "pilot":{"add":"hg_cap","theme":"sky"},
 "astronaut":{"add":"hg_dome"},"spaceman":{"add":"hg_dome"},"cosmonaut":{"add":"hg_dome"},
 "doctor":{"add":"hg_cap"},"teacher":{"add":"hg_glasses"},"scientist":{"add":"hg_glasses"},
 "glasses":{"add":"hg_glasses"},"sunglasses":{"add":"hg_glasses"},"goggles":{"add":"hg_glasses"},
 "helmet":{"add":"hg_helmet"},"hat":{"add":"hg_cap"},"cap":{"add":"hg_cap"},
 "tophat":{"add":"hg_toque"},"mask":{"add":"hg_mask"},
 "wings":{"add":"w_big"},"winged":{"add":"w_big"},"angel":{"add":"w_big","theme":"gold"},
 "demon":{"add":"h_curved","theme":"lava","sharp":0.4},
 "horns":{"add":"h_curved"},"horned":{"add":"h_curved"},
 "cape":{"add":"cape_long"},"cloaked":{"add":"cape_long"},
 "jetpack":{"add":"eq_jetpack"},"backpack":{"add":"eq_backpack"},
 "halo":{"add":"hg_halo"},"bearded":{"add":"eq_beard"},"beard":{"add":"eq_beard"},
 "spiky":{"sharp":0.6},"sharp":{"sharp":0.5},"smooth":{"sharp":-0.5},"round":{"sharp":-0.4}}

THEMES = {
 "gold":(45,.85,.75),"dark":(265,.25,.16),"neon":(310,1,.95),"ice":(195,.4,.92),
 "lava":(12,.95,.8),"mystic":(275,.7,.55),"steel":(215,.08,.6),"sea":(200,.7,.5),
 "warn":(48,.95,.8),"sky":(205,.7,.7),"navy":(225,.8,.3),"pastel":(185,.42,.88),
 "race":(4,.86,.68),"galaxy":(268,.82,.32),"toxic":(105,.92,.72),"bronze":(30,.72,.58),
 "crystal":(190,.55,.95),"emerald":(145,.82,.58)}

SPECIFICS = {}

NATURAL = {
 "tree":("#3f9b4f","#7a5230","#e64a4a","#2f7a3c","#4a301b","#f4efe0"),
 "weapon":("#d6dae0","#3b5998","#f2c94c","#8c96a6","#242933","#ffffff"),
 "furniture":("#8b5a2b","#6e4420","#d4a640","#a87948","#2e1d0e","#f2e6d8"),
 "food":("#d98b3a","#e63946","#f4c430","#52b788","#3b2314","#fff8eb"),
 "train":("#2b3440","#b83227","#f2c94c","#5c6b73","#161a20","#e6ecf0")}

COLOR_WORDS = {
 "red":(0,.85,.62),"crimson":(348,.9,.55),"scarlet":(5,.9,.65),"maroon":(350,.8,.35),"burgundy":(345,.8,.38),
 "ruby":(352,.88,.58),"vermilion":(12,.9,.65),"coral":(16,.72,.85),
 "orange":(24,.9,.62),"amber":(38,.92,.72),"rust":(18,.82,.48),"peach":(26,.48,.92),
 "yellow":(52,.9,.65),"gold":(45,.85,.72),"lemon":(56,.88,.85),"mustard":(46,.82,.58),
 "cream":(45,.18,.95),"ivory":(48,.12,.96),"beige":(38,.25,.85),"khaki":(42,.38,.72),"sand":(38,.35,.82),"tan":(32,.42,.75),
 "green":(140,.7,.5),"lime":(95,.85,.72),"olive":(72,.65,.45),"emerald":(145,.82,.55),
 "jade":(158,.72,.52),"forest":(132,.78,.36),"mint":(160,.45,.8),"sage":(135,.28,.65),
 "teal":(172,.75,.5),"turquoise":(176,.75,.72),"aqua":(182,.8,.75),"cyan":(185,.85,.65),
 "blue":(215,.8,.55),"sky":(202,.65,.82),"azure":(210,.85,.72),"cerulean":(200,.82,.65),"cobalt":(218,.88,.55),
 "sapphire":(222,.88,.52),"navy":(225,.8,.3),"indigo":(252,.8,.45),"periwinkle":(232,.45,.85),
 "purple":(275,.75,.58),"violet":(282,.75,.65),"lavender":(270,.35,.88),"lilac":(285,.38,.84),"plum":(292,.65,.48),
 "magenta":(312,.85,.68),"fuchsia":(318,.88,.72),"pink":(330,.7,.75),"rose":(340,.68,.78),"hotpink":(328,.88,.85),
 "white":(0,0,.96),"snow":(200,.03,.98),"pearl":(40,.06,.94),
 "silver":(215,.06,.78),"grey":(220,.05,.55),"gray":(220,.05,.55),"slate":(215,.18,.48),"charcoal":(220,.1,.26),
 "black":(260,.2,.14),"onyx":(250,.15,.12),"obsidian":(265,.28,.14),
 "brown":(25,.6,.42),"bronze":(30,.7,.52),"copper":(20,.75,.58),"chocolate":(22,.72,.34)}

NEG = {"no","without","not","never","minus","hatless","wingless","hornless"}
EQUIP_PREPS = {"with","holding","wielding","carrying","wearing","using","armed","equip","equipped"}
EQUIP_MAP = {
 "sword":"eq_sword","mastersword":"eq_sword","katana":"eq_sword","blade":"eq_sword","dagger":"eq_sword","lightsaber":"eq_sword","rapier":"eq_sword","claymore":"eq_sword",
 "shield":"eq_shield","buckler":"eq_shield","aegis":"eq_shield",
 "axe":"eq_axe","halberd":"eq_axe","scythe":"eq_axe",
 "hammer":"eq_hammer","warhammer":"eq_hammer","maul":"eq_hammer","mace":"eq_hammer",
 "staff":"eq_staff","wand":"eq_staff","scepter":"eq_staff","spear":"eq_staff","trident":"eq_staff","lance":"eq_staff",
 "bow":"eq_bow","crossbow":"eq_bow",
 "gun":"eq_gun","pistol":"eq_gun","rifle":"eq_gun","blaster":"eq_gun","shotgun":"eq_gun","lasergun":"eq_gun",
 "flag":"eq_flag","banner":"eq_flag",
 "wings":"w_big","cape":"cape_long","crown":"hg_crown","helmet":"hg_helmet","hat":"hg_cap",
 "glasses":"hg_glasses","sunglasses":"hg_glasses","mask":"hg_mask","horns":"h_curved",
 "jetpack":"eq_jetpack","backpack":"eq_backpack","halo":"hg_halo","beard":"eq_beard"}

STOP = set("""build make me a an the create generate give please pls i im want need can you of with and my some
for to model roblox lego brick bricks blocky block 3d one new cool nice awesome simple it its that this like
lets let draw design looking looks look who is are be as in on at from so very really just also something
thing object toy cartoon style version holding wielding carrying wearing armed street""".split())
ALL_KEYS = sorted({k for ks in ROOTS.values() for k in ks})
KNOWN = set(ALL_KEYS)|set(MODS)|set(COLOR_WORDS)|NEG|STOP|EQUIP_PREPS
IRREG = {"mice":"mouse","men":"man","women":"woman","oxen":"ox","geese":"goose","wolves":"wolf",
         "calves":"calf","children":"child","people":"person","teeth":"tooth","feet":"foot",
         "knives":"knife","elves":"elf","dwarves":"dwarf","leaves":"leaf","cacti":"cactus","octopi":"octopus"}
SKIN = ["#f2c9a0","#e0ac7e","#c68863","#8d5a3b","#6b4226","#ffdfc4"]
HAIR = ["#4a2f1b","#2b1d12","#6b4423","#141414","#d9a441","#c2652e","#8a8a8a","#f2e2c4"]
ANIME_HAIR = ["#ff7ab8","#7ad8ff","#ffd166","#b48cff"]
NAME_PRE = ["Brick","Stud","Krag","Zor","Bloxx","Torv","Pixl","Grim","Lux","Vex","Snap","Mek",
 "Vor","Quil","Rune","Ember","Frost","Thorn","Gale","Umber","Nova","Chrono","Aether","Volt","Titan","Apex"]
NAME_SUF = {"octopus":"pus","serpent":"enth","fish":"ish","bird":"wing","crab":"claw","spider":"ling",
 "golem":"mok","humanoid":"guard","turtle":"shell","jelly":"meduse","car":"runner","bike":"cycle",
 "boat":"wave","plane":"wing","heli":"rotor","tank":"tread","quadruped":"hoof","building":"stead",
 "tree":"bark","weapon":"edge","prop":"bloxx","mech":"prime","train":"rail","furniture":"craft","food":"bite"}

def tokenize(t): return re.findall(r"[a-z0-9]+", t.lower())
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
    for i in range(len(toks)-1):
        pair = toks[i]+toks[i+1]
        if pair in KNOWN: tset.add(pair)
    I = {"root":None,"mods":[],"traits":{},"neg":set(),"colors":[],"size":1.0,"sharp":1.0,
         "pose":0,"mat":None,"float":False,"prop":{},"eyes":1.0,"palette_force":None,"var":None,
         "carbody":None,"species":None,"keyword":None,"unknown":[],"ram":False,"tokens":set(tset)}
    for phrase,cfg in SPECIFICS.items():
        if phrase in raw:
            I.update({k:v for k,v in cfg.items() if k!="palette"})
            I["palette_force"]=cfg.get("palette"); I["root"]=cfg.get("root",I["root"]); return I
    equip_filter = set()
    primary_toks = []
    in_equip = False
    for i, t in enumerate(toks):
        st = stems(t)
        if t in EQUIP_PREPS:
            in_equip = True; continue
        if t in NEG:
            in_equip = False
        if in_equip:
            matched_eq = False
            for s in st:
                if s in EQUIP_MAP:
                    I["traits"][EQUIP_MAP[s]] = 1
                    if s in ROOTS.get("weapon", []): equip_filter.add(s)
                    matched_eq = True
            if matched_eq or t in ("and","a","an","the","two","dual") or t in COLOR_WORDS or t in MODS:
                continue
            else:
                in_equip = False
        primary_toks.append(t)
    primary_tset = set(tset) - equip_filter if primary_toks else set(tset)
    best, root = score_roots(primary_tset)
    if best == 0:
        best, root = score_roots(tset)
    if best == 0:
        for t in toks:
            if len(t) < 4 or t in KNOWN or (stems(t) & KNOWN): continue
            hit = [k for k in ALL_KEYS if len(k) == len(t) and sorted(k) == sorted(t)]
            if not hit: hit = difflib.get_close_matches(t, ALL_KEYS, n=1, cutoff=.78)
            if hit: tset.add(hit[0]); primary_tset.add(hit[0])
        best, root = score_roots(primary_tset)
        if best == 0:
            unk = [t for t in toks if len(t) >= 3 and t not in KNOWN and not (stems(t) & KNOWN)]
            if unk: root = "prop"; I["unknown"] = unk; I["keyword"] = unk[0]
            else: root = "humanoid"
    I["root"] = root
    I["tokens"] = set(tset)
    if root == "quadruped":
        I["species"] = "beast"
        for sp, keys in SPECIES_KEYS.items():
            if any(k in primary_tset for k in keys): I["species"] = sp; break
        if I["species"] == "horse" and ("magical" in tset or "horn" in tset or "unicorn" in tset):
            I["species"] = "unicorn"
        I["ram"] = "ram" in tset; I["keyword"] = I["species"]
    elif root != "prop":
        I["keyword"] = next((k for k in ROOTS[root] if k in primary_tset), None) or next((k for k in ROOTS[root] if k in tset), None)
    for mk in MODS:
        if mk in tset: I["mods"].append(mk)
    for mk in I["mods"]:
        m=MODS[mk]; I["prop"].update(m.get("prop",{}))
        for t in m.get("rm",[]): I["neg"].add(t)
        I["sharp"]+=m.get("sharp",0); I["size"]*=m.get("scale",1.0)
        if m.get("float"): I["float"]=True
        if m.get("mat"): I["mat"]=m["mat"]
        if m.get("carbody"): I["carbody"]=m["carbody"]
        if m.get("theme"): I["colors"].append(THEMES[m["theme"]])
        if m.get("eyes"): I["eyes"]*=m["eyes"]
        if m.get("add"): I["traits"][m["add"]]=1
    if "hatless" in tset: I["neg"].update(["hg_cap","hg_pointy","hg_helmet","hg_tricorn","hg_toque","hg_hardhat","hg_crown"])
    if "wingless" in tset: I["neg"].add("w_big")
    if "hornless" in tset: I["neg"].update(["h_curved","horns"])
    for i,t in enumerate(toks):
        if t in NEG and i+1<len(toks):
            nx=toks[i+1]
            if "wing" in nx: I["neg"].add("w_big")
            if "hair" in nx: I["neg"].add("hair")
            if "horn" in nx: I["neg"].update(["h_curved","horns"])
            if "hat" in nx or "helmet" in nx: I["neg"].update(["hg_cap","hg_helmet","hg_pointy"])
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

# Signature Palettes for Iconic Archetypes (Matches your screenshots!)
ICONIC_PALETTES = {
 "octopus": ("#8a3ab9","#6c2596","#ffd633","#c864ff","#1c1424","#f7ebff"),
 "kraken":  ("#68228b","#4b1566","#ffd633","#a832a8","#170d1f","#f2d9ff"),
 "phoenix": ("#c92a2a","#9e1b1b","#f5c430","#e87a24","#2b1810","#fff3c4"),
 "astronaut":("#f0f2f5","#d0d5dd","#d92d20","#f5c430","#262930","#ffffff"),
 "ryu":     ("#f2f2f0","#d92b2b","#f5c430","#242424","#171717","#ffffff"),
 "sportscar":("#d92b2b","#b01e1e","#f5c430","#e6e8ec","#1c1e24","#ffffff"),
}

def synthesize_palette(I,rng):
    if I["palette_force"]:
        P=dict(I["palette_force"]); P.setdefault("K",SKIN[0]); P.setdefault("H",HAIR[0])
        P.setdefault("P",P.get("D","#333333")); return P
    kw = I.get("keyword") or ""
    if not I["colors"] and not I["mat"]:
        if kw in ICONIC_PALETTES:
            pal = ICONIC_PALETTES[kw]
            P=dict(zip("ABCSDL",pal))
            P["K"]=SKIN[0] if I["root"]=="humanoid" else pal[0]
            P["H"]=HAIR[0] if I["root"]=="humanoid" else pal[1]
            P["P"]="#f0f0f0" if kw in ("astronaut","ryu") else pal[4]
            return P
        if I["root"]=="octopus":
            pal = ICONIC_PALETTES["octopus"]
            P=dict(zip("ABCSDL",pal)); P["K"]=pal[0]; P["H"]=pal[1]; P["P"]=pal[4]; return P
        if I["root"]=="bird" and kw in ("phoenix","firebird"):
            pal = ICONIC_PALETTES["phoenix"]
            P=dict(zip("ABCSDL",pal)); P["K"]=pal[0]; P["H"]=pal[1]; P["P"]=pal[4]; return P
        sp = SPECIES.get(I.get("species")) if I["root"]=="quadruped" else None
        pal = (sp or {}).get("pal") or NATURAL.get(I["root"])
        if pal:
            P=dict(zip("ABCSDL",pal)); P["K"]=pal[0]; P["H"]=pal[1]; P["P"]=pal[4]; return P
    if I["colors"]: h,s,v=I["colors"][0]
    else: h,s,v=(rng.choice([0,12,42,140,175,205,265,280,320]),.72,.65)
    if I["mat"]=="metal": s,v=.15,.75
    if I["mat"]=="ice": h,s,v=195,.4,.93
    if I["mat"]=="lava": h,s,v=12,.95,.8
    off=rng.choice([180,35,120,150])
    P={"A":hsv_hex(h,s*.88,v),"B":hsv_hex(h+rng.choice([-18,18]),s*.78,min(1,v*1.15)),
       "C":hsv_hex(48 if I["root"] in ("octopus","bird","car") else h+off,max(.65,s),min(1,v*1.35)),
       "S":hsv_hex(h+off+rng.choice([-25,25]),max(.5,s*.9),min(1,v*1.12)),
       "D":hsv_hex(h,min(1,s*1.05),max(.1,v*.32)),"L":hsv_hex(h+10,max(.05,s*.25),min(1,v*1.65))}
    if I["root"]=="humanoid":
        if kw in ("astronaut","spaceman","cosmonaut"):
            P["A"]="#f0f2f5"; P["B"]="#d8dde6"; P["C"]="#d92d20"; P["S"]="#f5c430"; P["D"]="#262930"; P["L"]="#ffffff"
            P["K"]=SKIN[0]; P["H"]=HAIR[0]; P["P"]="#f0f2f5"
            return P
        if kw in ("karate","ryu","streetfighter","martialartist","fighter"):
            P["A"]="#f2f2f0"; P["B"]="#d92b2b"; P["C"]="#d92b2b"; P["S"]="#f5c430"; P["D"]="#1c1c1c"; P["L"]="#ffffff"
            P["K"]="#e0ac7e"; P["H"]="#4a2f1b"; P["P"]="#f2f2f0"
            return P
        if I["mat"]=="metal" or "robot" in I["mods"] or "cyborg" in I["tokens"] or "android" in I["tokens"]: P["K"]=hsv_hex(h,.15,.75)
        elif "alien" in I["mods"] or "orc" in I["tokens"] or "goblin" in I["tokens"] or "zombie" in I["tokens"]: P["K"]=hsv_hex(130,.55,.65)
        elif "skeleton" in I["tokens"]: P["K"]="#ece8dc"
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
            self.parts.append({"n":cn,"p":par,"s":"box","sz":[round(.28*self.scale,2)]*3,"po":p0,"ro":r,"c":"D"})
            par=cn;p0=[0,0,0]
        r=[0,0,0];r[axes[-1]]=rot[axes[-1]]
        self.parts.append({"n":name,"p":par,"s":shape,"sz":sz,"po":p0,"ro":r,"c":color});return name
    def add(self,name,parent,shape,size,face=None,off=(0,0,0),rot=(0,0,0),color="A",mirror=False,studs=False):
        P=self.sz.get(parent,(1,1,1)); C=size
        # Tight brick contact offset (0.04) prevents deep volume overlap & eliminates Studio surface Z-fighting!
        e=min(.05, .08*min(C)); pos=list(off)
        if face:
            f=FACES[face]
            base=[f[0]*(P[0]/2+C[0]/2-e) if f[0] else 0,f[1]*(P[1]/2+C[1]/2-e) if f[1] else 0,
                  f[2]*(P[2]/2+C[2]/2-e) if f[2] else 0]
            pos=[base[i]+off[i] for i in range(3)]
        name=self._uniq(name); self._emit(name,parent,shape,size,pos,rot,color); self.sz[name]=size
        if studs and self.studs<85:
            nx=clamp(int(size[0]/.95),1,4); nz=clamp(int(size[2]/.95),1,4)
            for gx in range(nx):
                for gz in range(nz):
                    self._emit(self._uniq("Stud"),name,"cylinder",(.34,.18,.34),
                               [(gx-(nx-1)/2.0)*.95,size[1]/2+.06,(gz-(nz-1)/2.0)*.95],(0,0,0),color)
                    self.studs+=1
        if mirror:
            f2={"right":"left","left":"right"}.get(face,face)
            o2=list(off); o2[0]=-o2[0]; pos2=list(o2)
            if f2:
                f=FACES[f2]
                base=[f[0]*(P[0]/2+C[0]/2-e) if f[0] else 0,f[1]*(P[1]/2+C[1]/2-e) if f[1] else 0,
                      f[2]*(P[2]/2+C[2]/2-e) if f[2] else 0]
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
    def eyes(self,parent,y,z,s,bx=.75,sc="C",framed=True):
        for sx,suf in ((1,"R"),(-1,"L")):
            if framed:
                B_fr=self.add("EyeFrame"+suf,parent,"box",(s*1.22,s*1.32,s*.32),None,(sx*bx,y,z+.04),(0,0,0),"D")
            e=self.add("Eye"+suf,parent,"box",(s,s*1.12,s*.38),None,(sx*bx,y,z),(0,0,0),sc)
            self.add("Pupil"+suf,e,"box",(s*.38,s*.68,s*.22),None,(0,0,-.18),(0,0,0),"D")
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
    # Never tilt the whole model off-axis; only elevate vertically when floating=True
    if not floating: return
    old=B.root;pr=B._uniq("PoseRoot")
    B.parts.append({"n":pr,"p":None,"s":"box","sz":[.3,.3,.3],"po":[0,2.0,0],"ro":[0,0,0],"c":"D"})
    B.sz[pr]=(.3,.3,.3)
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
def _hand(B, side="R"):
    target = "Hand" + side
    for p in B.parts:
        if p["n"]==target: return target
    return B.root
def _chest(B):
    for p in B.parts:
        if p["n"] in ("Chest","CoreRoot","HumanoidRootPart"): return p["n"]
    return B.root

# ---------------------------------------------------------------- Sculpted Addons & Equipment
def add_brow_evil(B,I,r):
    hd=_head(B); hsz=B.sz.get(hd,(1.2,1.2,1.2))
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Brow"+suf,hd,"box",(hsz[0]*.36,hsz[1]*.11,.18),None,(sx*hsz[0]*.28,hsz[1]*.26,-hsz[2]*.52),(0,0,sx*-16),"D")
def add_hg_crown(B,I,r):
    c=B.add("Crown",_head(B),"box",(.96,.28,.96),"top",(0,0,0),(0,0,0),"S")
    for i in range(4):
        B.add("CrownPt%d"%i,c,"pyramid",(.22,.45,.22),"top",((i-1.5)*.24,0,-.32),(0,0,0),"C")
def add_hg_halo(B,I,r):
    B.add("Halo",_head(B),"cylinder",(1.25,.14,1.25),"top",(0,.45,0),(0,0,0),"C")
def add_hg_pointy(B,I,r):
    b=B.add("HatBrim",_head(B),"box",(1.55,.16,1.55),"top",(0,0,0),(0,0,0),"D")
    m=B.add("HatBand",b,"box",(1.05,.22,1.05),"top",(0,0,0),(0,0,0),"S")
    B.add("HatCone",m,"pyramid",(.92,1.45,.92),"top",(0,0,0),(0,0,0),"C")
def add_hg_helmet(B,I,r):
    hm=B.add("Helmet",_head(B),"box",(1.36,.95,1.32),"top",(0,-.22,0),(0,0,0),"B",studs=True)
    B.add("HelmCrest",hm,"box",(.24,.32,1.15),"top",(0,0,0),(0,0,0),"S")
    B.add("HelmVisor",hm,"box",(1.18,.26,.18),"front",(0,-.12,0),(0,0,0),"D")
def add_hg_mask(B,I,r):
    B.add("Mask",_head(B),"box",(1.18,.52,.22),"front",(0,-.12,0),(0,0,0),"D")
def add_hg_tricorn(B,I,r):
    b=B.add("TriBrim",_head(B),"box",(1.72,.16,1.28),"top",(0,0,0),(0,0,0),"D")
    B.add("TriTop",b,"wedge",(1.48,.42,1.05),"top",(0,0,0),(0,0,0),"B")
def add_hg_toque(B,I,r):
    b=B.add("ToqueBase",_head(B),"box",(1.15,.22,1.15),"top",(0,0,0),(0,0,0),"L")
    B.add("Toque",b,"cylinder",(1.02,.85,1.02),"top",(0,0,0),(0,0,0),"L")
def add_hg_cap(B,I,r):
    t=B.add("CapTop",_head(B),"box",(1.22,.28,1.18),"top",(0,0,0),(0,0,0),"C",studs=True)
    B.add("CapBrim",t,"box",(1.12,.12,.58),"front",(0,-.08,-.12),(0,0,0),"C")
def add_hg_hardhat(B,I,r):
    h=B.add("HardHat",_head(B),"box",(1.34,.42,1.34),"top",(0,0,0),(0,0,0),"C",studs=True)
    B.add("HatRidge",h,"box",(.28,.16,1.22),"top",(0,0,0),(0,0,0),"S")
def add_hg_dome(B,I,r):
    # Full sculpted Astronaut Helmet (like Screenshot 2!)
    hd=_head(B)
    hm=B.add("AstroHelm",hd,"box",(1.58,1.38,1.48),None,(0,.06,0),(0,0,0),"L",studs=True)
    B.add("AstroVisor",hm,"box",(1.22,.78,.16),"front",(0,.04,0),(0,0,0),"S")
    for sx,suf in ((1,"R"),(-1,"L")):
        ear=B.add("HelmEar"+suf,hm,"cylinder",(.36,.18,.36),"right" if sx>0 else "left",(0,.05,0),(0,0,90),"B")
        B.add("HelmLamp"+suf,ear,"cylinder",(.24,.12,.24),"front",(0,0,0),(90,0,0),"S")
def add_hg_glasses(B,I,r):
    g=B.add("GlassesBridge",_head(B),"box",(1.12,.12,.14),"front",(0,.14,0),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Lens"+suf,g,"box",(.42,.26,.12),None,(sx*.32,-.02,-.04),(0,0,0),"C")
def add_hg_headband(B,I,r):
    # Sculpted Martial Arts Headband with rear knot & tails (like Ryu in Screenshot 3!)
    hd=_head(B); hsz=B.sz.get(hd,(1.25,1.25,1.15))
    hb=B.add("Headband",hd,"box",(hsz[0]*1.06,.24,hsz[2]*1.06),None,(0,hsz[1]*.22,0),(0,0,0),"C")
    kn=B.add("BandKnot",hb,"box",(.28,.28,.24),"back",(0,0,0),(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("BandTail"+suf,kn,"box",(.18,.62,.14),"bot",(sx*.14,0,.05),(0,0,sx*18),"C")
def add_hg_crystal(B,I,r):
    for i in range(3): B.add("Crys%d"%i,_head(B),"pyramid",(.26,.85-i*.18,.26),"top",((i-1)*.34,0,0),(0,0,0),"C")
def add_hair_spiky(B,I,r):
    for i in range(4): B.add("HairSpike%d"%i,_head(B),"pyramid",(.26,.58,.28),"top",((i-1.5)*.28,0,-.08),(0,0,0),"H")
def add_taxi_sign(B,I,r): B.add("TaxiSign",_roof(B),"box",(.75,.32,.28),"top",(0,0,0),(0,0,0),"C")
def add_lightbar(B,I,r):
    b=B.add("LightBar",_roof(B),"box",(1.28,.16,.38),"top")
    B.add("LampR",b,"box",(.45,.18,.32),"top",(.36,0,0),(0,0,0),"C")
    B.add("LampL",b,"box",(.45,.18,.32),"top",(-.36,0,0),(0,0,0),"S")
def add_w_big(B,I,r):
    for sx,suf in ((1,"R"),(-1,"L")):
        w=B.add("Wing"+suf,B.root,"box",(1.6,.35,1.0),None,(sx*1.2,1.0,.4),(0,0,sx*20),"B")
        for i in range(4):
            B.add("Wing%sP%d"%(suf,i),w,"wedge",(.45,1.6-i*.2,.22),None,(sx*(.4+i*.35),-.4,.2),(0,0,sx*(26+i*9)),"S")
    B.mirrored.append(("WingR","WingL"))
def add_h_curved(B,I,r):
    if "horns" in B.present: return
    for sx,suf in ((1,"R"),(-1,"L")):
        h=B.add("Horn"+suf,_head(B),"box",(.32,.58,.32),"top",(sx*.42,0,-.08),(0,0,-sx*16),"S")
        B.add("Horn%sTip"%suf,h,"pyramid",(.26,.62,.26),"top",(0,0,0),(0,0,-sx*12),"S")
    B.mirrored.append(("HornR","HornL"))
def add_cape_long(B,I,r): B.add("Cape",_chest(B),"box",(1.55,2.4,.18),"back",(0,-.35,.08),(8,0,0),"C")
def add_sp_spoiler(B,I,r):
    if any(p["n"]=="Spoiler" for p in B.parts): return
    for sx in (1,-1): B.add("SpoPost%d"%sx,B.root,"box",(.16,.55,.24),"back",(sx*.72,.35,-.25),(0,0,0),"D")
    sp=B.add("Spoiler",B.root,"box",(2.15,.16,.62),"back",(0,.68,-.25),(0,0,0),"A")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("SpoWinglet"+suf,sp,"box",(.12,.38,.68),"right" if sx>0 else "left",(0,0,0),(0,0,0),"D")
def add_eq_sword(B,I,r):
    h=B.add("EqHilt",_hand(B,"R"),"box",(.18,.22,.72),"front",(0,0,-.15),(0,0,0),"D")
    g=B.add("EqGuard",h,"box",(.72,.24,.18),"front",(0,0,0),(0,0,0),"S")
    B.add("EqBlade",g,"box",(.14,.28,2.15),"front",(0,0,-.1),(0,0,0),"L")
def add_eq_shield(B,I,r):
    s=B.add("EqShield",_hand(B,"L"),"box",(.2,1.55,1.25),"left",(-.05,0,-.1),(0,0,0),"S")
    B.add("EqBoss",s,"gem",(.25,.5,.5),"left",(0,0,0),(0,0,0),"C")
def add_eq_axe(B,I,r):
    s=B.add("EqShaft",_hand(B,"R"),"box",(.18,.18,2.2),"front",(0,0,-.5),(0,0,0),"B")
    B.add("EqAxeHd",s,"wedge",(.22,1.1,.8),"front",(0,.2,.2),(0,0,0),"L")
def add_eq_hammer(B,I,r):
    s=B.add("EqShaft",_hand(B,"R"),"box",(.2,.2,2.1),"front",(0,0,-.5),(0,0,0),"B")
    B.add("EqHamHd",s,"box",(.9,.9,.55),"front",(0,0,.15),(0,0,0),"D")
def add_eq_staff(B,I,r):
    s=B.add("EqStaff",_hand(B,"R"),"box",(.18,2.8,.18),None,(0,.4,-.25),(0,0,0),"B")
    B.add("EqOrb",s,"gem",(.5,.5,.5),"top",(0,0,0),(0,0,0),"C")
def add_eq_bow(B,I,r):
    B.add("EqBow",_hand(B,"L"),"box",(.16,1.8,.45),"front",(0,0,-.2),(0,0,0),"B")
def add_eq_gun(B,I,r):
    g=B.add("EqGun",_hand(B,"R"),"box",(.22,.35,.95),"front",(0,.05,-.2),(0,0,0),"D")
    B.add("EqMuzzle",g,"cylinder",(.16,.3,.16),"front",(0,.05,0),(90,0,0),"C")
def add_eq_flag(B,I,r):
    # Handheld Flagpole + Multi-Stripe Flag (Matches Astronaut in Screenshot 2!)
    hnd=_hand(B,"L")
    pole=B.add("FlagPole",hnd,"cylinder",(.22,4.4,.22),None,(0,.8,-.25),(0,0,0),"B")
    B.add("FlagFinial",pole,"gem",(.38,.38,.38),"top",(0,0,0),(0,0,0),"S")
    fl=B.add("FlagBoard",pole,"box",(1.85,1.15,.16),"left",(0,1.2,0),(0,0,0),"L")
    B.add("FlagCanton",fl,"box",(.75,.62,.2),None,(.52,.24,0),(0,0,0),"#1d4ed8" if False else "D")
    B.add("FlagStripeTop",fl,"box",(1.05,.28,.18),None,(-.38,.38,0),(0,0,0),"C")
    B.add("FlagStripeBot",fl,"box",(1.82,.32,.18),None,(0,-.38,0),(0,0,0),"C")
def add_eq_jetpack(B,I,r):
    jp=B.add("Jetpack",_chest(B),"box",(1.15,1.25,.48),"back",(0,.1,0),(0,0,0),"B",studs=True)
    for sx,suf in ((1,"R"),(-1,"L")):
        t=B.add("JetThr"+suf,jp,"cylinder",(.38,1.1,.38),None,(sx*.38,0,.18),(0,0,0),"D")
        B.add("JetFlm"+suf,t,"pyramid",(.3,.5,.3),"bot",(0,0,0),(180,0,0),"S")
def add_eq_backpack(B,I,r):
    B.add("Backpack",_chest(B),"box",(1.18,1.28,.55),"back",(0,.08,0),(0,0,0),"B",studs=True)
def add_eq_beard(B,I,r):
    B.add("FullBeard",_head(B),"box",(.92,.55,.32),"front",(0,-.38,0),(0,0,0),"H")

ADDONS={
 "brow_evil":add_brow_evil,"hg_crown":add_hg_crown,"hg_halo":add_hg_halo,"hg_pointy":add_hg_pointy,
 "hg_helmet":add_hg_helmet,"hg_mask":add_hg_mask,"hg_tricorn":add_hg_tricorn,"hg_toque":add_hg_toque,
 "hg_cap":add_hg_cap,"hg_hardhat":add_hg_hardhat,"hg_dome":add_hg_dome,
 "hg_glasses":add_hg_glasses,"hg_headband":add_hg_headband,"hg_crystal":add_hg_crystal,
 "hair_spiky":add_hair_spiky,"taxi_sign":add_taxi_sign,"lightbar":add_lightbar,
 "w_big":add_w_big,"h_curved":add_h_curved,"cape_long":add_cape_long,"sp_spoiler":add_sp_spoiler,
 "eq_sword":add_eq_sword,"eq_shield":add_eq_shield,"eq_axe":add_eq_axe,"eq_hammer":add_eq_hammer,
 "eq_staff":add_eq_staff,"eq_bow":add_eq_bow,"eq_gun":add_eq_gun,"eq_flag":add_eq_flag,
 "eq_jetpack":add_eq_jetpack,"eq_backpack":add_eq_backpack,"eq_beard":add_eq_beard}

# ---------------------------------------------------------------- Studio-Grade Archetype Builders
def b_humanoid(B,I,r):
    p=I["prop"]; v=B.var; kw=I.get("keyword") or "human"
    is_astro = kw in ("astronaut","spaceman","cosmonaut") or "hg_dome" in I["traits"]
    is_martial = kw in ("karate","ryu","streetfighter","martialartist","fighter","boxer","monk") or "hg_headband" in I["traits"]
    cw=1.65*p.get("chest",1.0)*(1.08 if v==2 else .96 if v==1 else 1.0)
    lw=p.get("limbs",1.0); hw=1.24*p.get("head",1.0)
    leg=1.35*lw
    hips=B.add("HumanoidRootPart",None,"box",(cw*.92,.55,.96),None,(0,0,0),(0,0,0),"P")
    B.add("Belt",hips,"box",(cw*.96,.24,1.02),"top",(0,-.08,0),(0,0,0),"C" if is_astro else "D")
    if is_martial:
        # Hanging karate black-belt knot & sashes (Matches Ryu in Screenshot 3!)
        kn=B.add("BeltKnot",hips,"box",(.32,.32,.24),"front",(0,.16,0),(0,0,0),"D")
        B.add("BeltSashR",kn,"box",(.22,.85,.14),"bot",(.1,0,0),(0,0,-10),"D")
        B.add("BeltSashL",kn,"box",(.22,.75,.14),"bot",(-.1,0,0),(0,0,8),"D")
    # Articulated Legs with natural stance
    for sx,suf in ((1,"R"),(-1,"L")):
        hip_ang = (-16 if sx>0 else 12) if is_martial else 0
        hip_rot = (hip_ang, 0, sx*(10 if is_martial else 0))
        th=B.add("Thigh"+suf,hips,"box",(.68*lw,leg*.92,.76),"bot",(sx*cw*.26,0,0),(hip_rot[0],0,0),"P")
        if is_astro:
            B.add("LegStripe"+suf,th,"box",(.72*lw,.22,.8),"bot",(0,.35,0),(0,0,0),"C")
        shn=B.add("Shin"+suf,th,"box",(.62*lw,leg*.92,.68),"bot",(0,0,0),(18 if (is_martial and sx>0) else 0,0,0),"P")
        if is_martial:
            # Bare martial arts feet with sculpted toes (Screenshot 3)
            ft=B.add("Shoe"+suf,shn,"box",(.64*lw,.32,1.02),"bot",(0,0,-.16),(0,0,0),"K")
            for ti in (-1,0,1):
                B.add("Toe%s%d"%(suf,ti),ft,"box",(.18,.22,.22),"front",(ti*.2,-.04,0),(0,0,0),"K")
        else:
            sh=B.add("Shoe"+suf,shn,"box",(.68*lw,.38,1.08),"bot",(0,0,-.16),(0,0,0),"D")
            B.add("ShoeSole"+suf,sh,"box",(.72*lw,.12,1.12),"bot",(0,0,0),(0,0,0),"B")
    # Sculpted Torso
    torso=B.add("Chest",hips,"box",(cw,1.78,1.02),"top",(0,.08,0),(0,0,0),"A",studs=True)
    if is_martial:
        # Open V-neck karate gi exposing muscular chest skin (Screenshot 3)
        B.add("ChestSkin",torso,"box",(cw*.46,.82,.14),"front",(0,.36,0),(0,0,0),"K")
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("GiLapel"+suf,torso,"box",(.24,.95,.18),"front",(sx*cw*.24,.32,0),(0,0,sx*14),"A")
    elif is_astro:
        # Astronaut Chest Control Box with colored buttons & life-support pack (Screenshot 2)
        cb=B.add("ChestBox",torso,"box",(cw*.68,.78,.28),"front",(0,.1,0),(0,0,0),"B",studs=True)
        B.add("BtnR",cb,"box",(.22,.22,.12),"front",(.22,.12,0),(0,0,0),"C")
        B.add("BtnM",cb,"box",(.22,.22,.12),"front",(0,.12,0),(0,0,0),"S")
        B.add("BtnL",cb,"box",(.22,.22,.12),"front",(-.22,.12,0),(0,0,0),"D")
        B.add("LifePack",torso,"box",(cw*.78,1.35,.52),"back",(0,.12,0),(0,0,0),"B",studs=True)
        I["traits"]["eq_flag"]=1
    else:
        B.add("Collar",torso,"box",(cw*.58,.24,1.06),"top",(0,-.06,0),(0,0,0),"B")
    nk=B.add("Neck",torso,"box",(.52,.28,.52),"top",(0,0,0),(0,0,0),"K")
    head=B.add("Head",nk,"box",(hw,hw*1.02,hw*.94),"top",(0,0,0),(0,0,0),"K",studs=is_astro)
    B.eyes(head,.08,-hw*.48,.28*I["eyes"],hw*.27,sc="L",framed=False)
    B.add("Nose",head,"box",(.18,.18,.14),"front",(0,-.04,0),(0,0,0),"K")
    B.add("Mouth",head,"box",(.42,.14,.12),"front",(0,-.28,0),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Brow"+suf,head,"box",(.34,.1,.14),"front",(sx*hw*.26,.28,0),(0,0,sx*(-12 if is_martial else 0)),"H")
    B.add("Ear",head,"box",(.14,.32,.26),"right",(0,0,0),(0,0,0),"K",mirror=True)
    # Multi-layered Sculpted Brick Hair (unless wearing full dome helmet or bald)
    if "hair" not in I["neg"] and not is_astro:
        ht=B.add("HairTop",head,"box",(hw*1.06,.32,hw*1.02),"top",(0,0,0),(0,0,0),"H",studs=True)
        B.add("HairCrown",ht,"box",(hw*.86,.24,hw*.82),"top",(0,0,0),(0,0,0),"H")
        B.add("HairBack",head,"box",(hw*1.04,.78,.24),"back",(0,.08,0),(0,0,0),"H")
        B.add("HairSide",head,"box",(.18,.58,hw*.92),"right",(0,.16,0),(0,0,0),"H",mirror=True)
        for i in range(3):
            B.add("Fringe%d"%i,ht,"box",(.34,.24,.22),"front",((i-1)*.36,-.12,0),(0,0,0),"H")
    # Articulated Arms & Hands with Role-Specific Rigging
    for sx,suf in ((1,"R"),(-1,"L")):
        if is_astro and sx>0:
            # Astronaut waving right arm (Screenshot 2)
            ua=B.add("Arm"+suf,torso,"box",(.56,1.1,.58),"right",(0,.52,0),(-135,0,0),"A")
            B.add("ArmBand"+suf,ua,"box",(.6,.2,.62),"bot",(0,.25,0),(0,0,0),"C")
            fa=B.add("Fore"+suf,ua,"box",(.5,1.0,.52),"bot",(0,0,0),(-25,0,0),"A")
            B.add("Hand"+suf,fa,"box",(.48,.48,.52),"bot",(0,0,0),(0,0,0),"K")
        elif is_martial:
            # Martial artist guard stance (Screenshot 3)
            ua=B.add("Arm"+suf,torso,"box",(.58,1.05,.6),"right" if sx>0 else "left",(0,.45,-.1),(-45,0,0),"K")
            fa=B.add("Fore"+suf,ua,"box",(.52,1.0,.54),"bot",(0,0,-.15),(-65,0,0),"K")
            B.add("GloveCuff"+suf,fa,"box",(.58,.28,.58),"bot",(0,.2,0),(0,0,0),"C")
            B.add("Hand"+suf,fa,"box",(.62,.58,.64),"bot",(0,0,0),(0,0,0),"K")
            B.add("GloveWrap"+suf,"Hand"+suf,"box",(.66,.52,.68),None,(0,0,-.04),(0,0,0),"C")
        else:
            arm_pitch = -28 if (sx<0 and is_astro) else (-18 if sx>0 else -8)
            ua=B.add("Arm"+suf,torso,"box",(.56,1.12,.58),"right" if sx>0 else "left",(0,.48,0),(arm_pitch,0,0),"A")
            if is_astro:
                B.add("ArmBand"+suf,ua,"box",(.6,.2,.62),"bot",(0,.25,0),(0,0,0),"C")
            fa=B.add("Fore"+suf,ua,"box",(.48,1.02,.5),"bot",(0,0,0),(-20 if sx>0 else -10,0,0),"A" if is_astro else "K")
            B.add("Hand"+suf,fa,"box",(.46,.46,.5),"bot",(0,0,0),(0,0,0),"K")
    if kw in ("knight","paladin","samurai","viking","gladiator","soldier","guard"):
        B.add("ArmorPlate",torso,"box",(cw*.84,1.12,.18),"front",(0,.12,0),(0,0,0),"S",studs=True)
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("ShoulderPad"+suf,torso,"box",(.72,.42,.82),"right" if sx>0 else "left",(0,.65,0),(0,0,0),"S",studs=True)
    B.tag("humanoid")

def b_octopus(B,I,r):
    # Matches Screenshot 1 (Purple Blocky Octopus) & Screenshot 4 (Kraken)
    n=8
    # Core Head Block with expressive framed yellow eyes & siphon mouth
    hd=B.add("CoreRoot",None,"box",(3.2,2.4,3.0),None,(0,2.2,0),(0,0,0),"A",studs=True)
    B.eyes(hd,.18,-1.52,.78,.82,sc="C",framed=True)
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("OctoBrow"+suf,hd,"box",(.92,.22,.28),None,(sx*.82,.72,-1.48),(0,0,sx*-12),"B")
    sp=B.add("Spout",hd,"box",(.72,.68,.55),"front",(0,-.52,0),(0,0,0),"L")
    B.add("Mouth",sp,"box",(.42,.42,.18),"front",(0,-.05,0),(0,0,0),"D")
    # Stepped Tapered Mantle Tiers (like Screenshot 1 & 4)
    m1=B.add("Mantle",hd,"box",(3.5,1.5,3.3),"top",(0,0,.15),(0,0,0),"A",studs=True)
    m2=B.add("MantleMid",m1,"box",(2.9,1.35,2.8),"top",(0,0,.12),(0,0,0),"B",studs=True)
    m3=B.add("MantleTop",m2,"box",(2.1,1.1,2.1),"top",(0,0,.08),(0,0,0),"A",studs=True)
    B.add("MantleApex",m3,"pyramid",(1.3,.85,1.3),"top",(0,0,0),(0,0,0),"D")
    # Lateral Mantle Ear-Fins & Kraken Texture Spots
    for sx,suf in ((1,"R"),(-1,"L")):
        fin=B.add("MantleFin"+suf,m2,"box",(.95,.32,1.25),"right" if sx>0 else "left",(0,.1,.15),(0,0,sx*24),"S",studs=True)
        B.add("MantleFinTip"+suf,fin,"wedge",(.65,.26,.95),"right" if sx>0 else "left",(0,0,0),(0,0,sx*18),"D")
        B.add("MantleSpot"+suf,m1,"box",(.48,.48,.22),"front",(sx*.95,.15,0),(0,0,0),"S")
    # 8 Sweeping Curved Tentacles with Underside Suction Cups
    def build_tentacle(b,base,i):
        # Sweeps outward along the ground and curls upward at the tip!
        s1=b.add("Tent%d_s0"%i,base,"box",(.82,.65,1.55),"front",(0,-.15,0),(18,0,0),"A",studs=True)
        b.add("Suck%d_0"%i,s1,"box",(.48,.18,.48),"bot",(0,0,-.15),(0,0,0),"L")
        s2=b.add("Tent%d_s1"%i,s1,"box",(.72,.58,1.45),"front",(0,0,0),(-12,0,0),"B",studs=True)
        b.add("Suck%d_1"%i,s2,"box",(.42,.18,.42),"bot",(0,0,0),(0,0,0),"L")
        s3=b.add("Tent%d_s2"%i,s2,"box",(.6,.5,1.2),"front",(0,0,0),(-38,0,0),"A",studs=True)
        b.add("Suck%d_2"%i,s3,"box",(.36,.16,.36),"bot",(0,0,0),(0,0,0),"L")
        tip=b.add("Tent%d_tip"%i,s3,"box",(.48,.42,.85),"front",(0,0,0),(-42,0,0),"S")
        b.add("Suck%d_3"%i,tip,"box",(.28,.14,.28),"bot",(0,0,0),(0,0,0),"L")
    for i in range(n):
        az = i * (360.0 / n) + 22.5
        rad = math.radians(az)
        base=B.add("TentBase%d"%i,hd,"box",(.92,.75,1.15),None,(1.55*math.sin(rad),-.85,-1.55*math.cos(rad)),(0,-az,0),"B",studs=True)
        build_tentacle(B,base,i)
    B.tag("octopus","tentacles")

def b_bird(B,I,r):
    # Matches Screenshot 5 (Phoenix with swept multi-feather wings, gold breastplate & crest)
    body=B.add("CoreRoot",None,"box",(2.1,2.2,2.8),None,(0,2.7,0),(0,0,0),"A",studs=True)
    # Sculpted Golden Breastplate Plumage
    br1=B.add("BreastTop",body,"box",(1.75,1.15,.35),"front",(0,.35,0),(0,0,0),"C",studs=True)
    B.add("BreastLow",br1,"box",(1.35,.95,.28),"bot",(0,0,.04),(0,0,0),"S")
    B.add("BackPlume",body,"box",(1.85,.35,2.4),"top",(0,0,.15),(0,0,0),"B",studs=True)
    # Tapered Neck, Head, Hooked Beak & Multi-Feather Crest
    nk=B.add("Neck",body,"box",(1.15,1.25,1.15),"top",(0,0,-.65),(0,0,0),"A",studs=True)
    B.add("NeckCollar",nk,"box",(1.32,.35,1.28),"bot",(0,.15,0),(0,0,0),"C")
    hd=B.add("Head",nk,"box",(1.3,1.15,1.4),"top",(0,0,-.15),(0,0,0),"A",studs=True)
    B.eyes(hd,.12,-.52,.38,.58,sc="C",framed=True)
    bk=B.add("Beak",hd,"wedge",(.68,.52,1.05),"front",(0,-.05,0),(-90,0,0),"C")
    B.add("BeakTip",bk,"pyramid",(.45,.45,.38),"bot",(0,-.1,-.2),(180,0,0),"S")
    # Fanning Head Crest Feathers
    for i,(dy,dz,ang) in enumerate(((.35,-.1,-22),(.22,.28,-42),(.05,.62,-62))):
        B.add("Crest%d"%i,hd,"box",(.28,1.15-i*.12,.32),"top",(0,dy,dz),(ang,0,0),"C" if i%2==0 else "S")
    # Swept-Up Multi-Tiered Wings with Layered Primary Feathers (Screenshot 5)
    for sx,suf in ((1,"R"),(-1,"L")):
        side = "right" if sx>0 else "left"
        w1=B.add("Wing"+suf,body,"box",(1.8,.42,1.35),side,(0,.55,-.2),(0,0,sx*32),"A",studs=True)
        B.add("WingCovert"+suf,w1,"box",(1.55,.24,.95),"top",(0,0,-.12),(0,0,0),"C")
        w2=B.add("Wing%sMid"%suf,w1,"box",(2.1,.36,1.15),side,(0,0,0),(0,0,sx*18),"B",studs=True)
        w3=B.add("Wing%sTip"%suf,w2,"box",(1.8,.28,.85),side,(0,0,-.1),(0,0,sx*12),"C")
        for i in range(6):
            parent_w = w1 if i<2 else (w2 if i<4 else w3)
            lx = (i%2 - .5)*.75
            B.add("Wing%sP%d"%(suf,i),parent_w,"box",(.42,.22,1.65-i*.12),"back",(lx,0,0),(0,sx*(8+i*5),0),"C" if i%2==0 else "S")
    # Long Fanned Tail Feathers
    tb=B.add("TailBase",body,"box",(1.5,.55,1.2),"back",(0,-.35,0),(-14,0,0),"B",studs=True)
    nf=5
    for i in range(nf):
        k = i - nf//2
        tf=B.add("TailF%d"%i,tb,"box",(.44,.22,2.4-abs(k)*.25),"back",(k*.36,0,0),(0,k*12,0),"A" if i%2 else "B")
        B.add("TailTip%d"%i,tf,"box",(.38,.18,.95),"back",(0,0,0),(0,0,0),"C" if i%2==0 else "S")
    # Articulated Legs & 3-Toed Talons
    for sx,suf in ((1,"R"),(-1,"L")):
        f=B.add("Femur"+suf,body,"box",(.62,1.05,.72),"bot",(sx*.62,0,.15),(0,0,0),"B")
        t=B.add("Tibia"+suf,f,"box",(.44,1.1,.48),"bot",(0,0,0),(0,0,0),"C")
        ankle=B.add("Ankle"+suf,t,"box",(.52,.24,.62),"bot",(0,0,-.1),(0,0,0),"C")
        for k in (-1,0,1):
            B.add("Tal%s%d"%(suf,k),ankle,"box",(.16,.2,.55),"front",(k*.18,-.02,0),(0,k*-12,0),"D")
    B.tag("wings")

def b_car(B,I,r):
    # Matches Screenshot 6 (Speed-Champions Sports Car with dual racing stripes, fenders, cabin pillars & spoiler)
    p=I["prop"]; kw=I.get("keyword") or "car"
    body=I.get("carbody") or ("van" if kw in ("van","bus","ambulance","minivan") else
         "pickup" if kw in ("truck","pickup","firetruck","lorry") else
         "buggy" if kw in ("buggy","kart","gokart","atv") else
         "sport" if kw in ("sportscar","racecar","supercar","sport","f1","coupe") or B.var in (0,1) else
         {2:"sedan",3:"pickup"}[B.var])
    ws=.92*p.get("wheels",1.0); lift=.25*p.get("lift",1.0)
    low={"sport":.88,"buggy":1.0,"pickup":1.15,"van":1.2,"sedan":.95}[body]
    L={"sport":5.2,"sedan":5.0,"buggy":4.0,"pickup":5.2,"van":5.2}[body]; W=2.4
    # Main Sculpted Chassis
    ch=B.add("CoreRoot",None,"box",(W,.68*low,L),None,(0,.85*low+lift,0),(0,0,0),"A",studs=True)
    B.add("FloorPan",ch,"box",(W*.92,.22,L*.88),"bot",(0,0,0),(0,0,0),"D")
    # Stepped Front Hood, Racing Stripes, Splitter & Headlights (Screenshot 6)
    hd=B.add("Hood",ch,"box",(W*.96,.38,L*.34),"top",(0,0,-L*.31),(0,0,0),"A",studs=True)
    B.add("NoseSlope",hd,"wedge",(W*.92,.36,.55),"front",(0,-.02,0),(0,0,0),"A")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("HoodStripe"+suf,hd,"box",(.28,.08,L*.32),"top",(sx*.26,0,0),(0,0,0),"L")
        B.add("Light"+suf,hd,"box",(.52,.28,.16),"front",(sx*(W*.32),-.06,-.45),(0,0,0),"C")
        B.add("FenderF"+suf,ch,"box",(.24,.48,1.35),"right" if sx>0 else "left",(0,.18,-L*.3),(0,0,0),"A")
        B.add("FenderB"+suf,ch,"box",(.24,.52,1.35),"right" if sx>0 else "left",(0,.2,L*.3),(0,0,0),"A")
        B.add("Skirt"+suf,ch,"box",(.18,.32,L*.42),"right" if sx>0 else "left",(0,-.14,0),(0,0,0),"D")
        B.add("SideVent"+suf,ch,"box",(.14,.34,.85),"right" if sx>0 else "left",(0,.12,.15),(0,0,0),"B")
        B.add("Tail"+suf,ch,"box",(.55,.28,.16),"back",(sx*(W*.32),.12,0),(0,0,0),"C")
    B.add("Grille",ch,"box",(W*.52,.28,.18),"front",(0,0,0),(0,0,0),"D")
    B.add("BumpF",ch,"box",(W*1.04,.26,.42),"front",(0,-.2,0),(0,0,0),"D")
    B.add("BumpB",ch,"box",(W*1.02,.32,.36),"back",(0,-.18,0),(0,0,0),"D")
    # Cabin, Angled Windshield, Roof Stripes & Rear Louvers
    if body=="van":
        cab=B.add("Cabin",ch,"box",(W*.94,1.45,L*.68),"top",(0,0,.35),(0,0,0),"A",studs=True)
        B.add("WinF",cab,"box",(W*.82,.62,.16),"front",(0,.28,0),(0,0,0),"D")
    else:
        cl = 2.15 if body!="buggy" else 1.55
        cab=B.add("Cabin",ch,"box",(W*.86,.78*low,cl),"top",(0,0,.22),(0,0,0),"D")
        rf=B.add("RoofCap",cab,"box",(W*.82,.18,cl*.88),"top",(0,0,.05),(0,0,0),"A",studs=True)
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("RoofStripe"+suf,rf,"box",(.26,.08,cl*.84),"top",(sx*.26,0,0),(0,0,0),"L")
        B.add("WinF",cab,"wedge",(W*.82,.72*low,.55),"front",(0,-.02,0),(0,0,0),"D")
        B.add("WinB",cab,"wedge",(W*.78,.65*low,.55),"back",(0,-.04,0),(0,180,0),"B")
    if body=="pickup":
        B.add("Bed",ch,"box",(W*.94,.55,1.55),"top",(0,0,1.65),(0,0,0),"B",studs=True)
    # 4 Corner Wheels + Recessed Metallic Hubs
    for sx,suf in ((1,"R"),(-1,"L")):
        for zz,tag in ((L*.3,"F"),(-L*.3,"B")):
            w=B.add("Wheel%s%s"%(tag,suf),ch,"cylinder",(ws,.52,ws),None,(sx*(W/2+.08),-.22,zz),(0,0,90),"D")
            B.add("Hub%s%s"%(tag,suf),w,"cylinder",(ws*.56,.58,ws*.56),None,(0,0,0),(0,0,90),"S")
    # Multi-Part Rear Racing Wing (Screenshot 6)
    if body=="sport" or "sp_spoiler" in I["traits"]:
        for sx in (1,-1):
            B.add("SpoPost%d"%sx,ch,"box",(.16,.58,.28),"top",(sx*.68,0,L*.42),(0,0,0),"D")
        sp=B.add("Spoiler",ch,"box",(W*1.02,.16,.68),"top",(0,.62,L*.44),(0,0,0),"A",studs=True)
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("SpoEnd"+suf,sp,"box",(.12,.42,.74),"right" if sx>0 else "left",(0,0,0),(0,0,0),"D")
    B.tag("wheels")

def b_quadruped(B,I,r):
    # Matches Screenshot 7 (Magical Horse / Unicorn with stepped brick body, anatomical legs, flowing mane & spiral horn)
    sp=I.get("species") or "beast"; S=SPECIES.get(sp) or SPECIES["beast"]
    p=I["prop"]; v=B.var%4; k=S["size"]; ex=S["extras"]
    ch=p.get("chest",1.0); lm=p.get("limbs",1.0); hf=p.get("head",1.0)
    bw=S["bw"]*k*ch; bh=S["bh"]*k*(ch**.5); bl=S["bl"]*k
    leg=S["leg"]*k*lm; lw=S["lw"]*k*lm
    hw,hh,hl=[x*k*hf for x in S["head"]]
    # Stepped Brick Torso Sculpting (eliminates flat single-box look!)
    torso=B.add("CoreRoot",None,"box",(bw,bh,bl),None,(0,leg*.98+bh/2,0),(0,0,0),"A",studs=True)
    B.add("ChestSculpt",torso,"box",(bw*.88,bh*.82,bl*.28),"front",(0,-.06,0),(0,0,0),"A",studs=True)
    B.add("BellySculpt",torso,"box",(bw*.78,bh*.24,bl*.68),"bot",(0,0,0),(0,0,0),"B")
    B.add("CroupSculpt",torso,"box",(bw*.86,bh*.22,bl*.36),"top",(0,0,bl*.26),(0,0,0),"A",studs=True)
    # 4 Multi-Segment Anatomical Legs (Thigh -> Knee -> Shin -> Hoof)
    for fz,tg in ((-1,"F"),(1,"B")):
        for sx,suf in ((1,"R"),(-1,"L")):
            up_ang = (-8 if fz<0 else 10) if sx>0 else (6 if fz<0 else -6)
            up=B.add("Leg"+tg+suf,torso,"box",(lw*1.18,leg*.48,lw*1.22),"bot",
                     (sx*(bw/2-lw*.62),0,fz*(bl/2-lw*.78)),(up_ang,0,0),"A")
            kn=B.add("Knee"+tg+suf,up,"box",(lw*1.02,lw*.45,lw*1.05),"bot",(0,0,0),(0,0,0),"B")
            lo=B.add("Shin"+tg+suf,kn,"box",(lw*.86,leg*.46,lw*.88),"bot",(0,0,0),(-up_ang,0,0),"A")
            hoof_col = "S" if sp in ("unicorn","pegasus") else "D"
            B.add("Hoof"+tg+suf,lo,"box",(lw*.96,lw*.48,lw*1.16),"bot",(0,0,-lw*.08),(0,0,0),hoof_col)
    # Stepped Angled Neck + Sculpted Head & Tapered Muzzle
    ang=math.radians(S["nang"]); nl=S["neck"]*k; nw=min(hw*.82,bw*.58)
    nb_y=bh*.22; nb_z=-(bl/2-nw*.35)
    B.add("NeckBase",torso,"box",(nw*1.12,nl*.45,nw*1.18),"top",(0,0,-bl*.36),(0,0,0),"A",studs=True)
    B.add("Neck",torso,"box",(nw,nl,nw*1.06),None,
          (0,nb_y+nl/2*math.cos(ang),nb_z-nl/2*math.sin(ang)),(-S["nang"],0,0),"A")
    ty=nb_y+nl*math.cos(ang); tz=nb_z-nl*math.sin(ang)
    head=B.add("Head",torso,"box",(hw,hh,hl),None,(0,ty+hh*.14,tz-hl*.24),(0,0,0),S["headc"],studs=True)
    sn=S["snout"]; sw,sh,sl=hw*sn[0],hh*sn[1],hl*sn[2]
    snout=B.add("Snout",head,"box",(sw,sh,sl),"front",(0,-hh*.14,0),(12,0,0),S["snoutc"],studs=True)
    B.add("Jaw",snout,"box",(sw*.86,sh*.38,sl*.88),"bot",(0,0,.04),(0,0,0),S["headc"])
    B.add("Nose",snout,"box",(sw*.62,sh*.42,.14*k),"front",(0,sh*.12,0),(0,0,0),"D")
    B.eyes(head,hh*.14,-hl*.48,(.18+.09*hw)*I["eyes"],hw*.38,sc="L",framed=True)
    # Ears
    et=S["ears"]; ew,eh=S["ear"][0]*k,S["ear"][1]*k
    for sx,suf in ((1,"R"),(-1,"L")):
        side="right" if sx>0 else "left"
        if et in ("point","long"):
            B.add("Ear"+suf,head,"box",(ew,eh,ew*.65),"top",(sx*hw*.32,0,hl*.22),(0,0,-sx*10),"B")
        elif et=="side":
            B.add("Ear"+suf,head,"box",(eh,.16*k,ew),side,(0,hh*.2,hl*.12),(0,0,-sx*12),"B")
        elif et=="floppy":
            B.add("Ear"+suf,head,"box",(ew*.42,eh,ew),side,(0,-eh*.15,hl*.12),(0,0,0),"B")
        elif et=="round":
            B.add("Ear"+suf,head,"box",(ew,ew,ew*.65),"top",(sx*hw*.36,0,hl*.18),(0,0,0),"B")
        elif et=="flap":
            B.add("Ear"+suf,head,"box",(.22*k,eh,ew),side,(0,0,hl*.12),(0,0,0),"B")
    if et!="none": B.mirrored.append(("EarR","EarL"))
    # Horns (Multi-tier Golden Spiral Horn for Unicorn, Triceratops Horns, Antlers, etc.)
    ht=S["horns"]
    if sp=="sheep" and I.get("ram"): ht="curved"
    if "horns" in I["neg"]: ht=None
    if ht:
        if ht=="straight":
            # Multi-segment tapered Unicorn Horn (Matches Screenshot 7!)
            h1=B.add("Horn",head,"box",(.32*k,.65*k,.32*k),"top",(0,0,-hl*.22),(-28,0,0),"S")
            h2=B.add("HornMid",h1,"box",(.24*k,.6*k,.24*k),"top",(0,0,0),(0,0,0),"S")
            B.add("HornTip",h2,"pyramid",(.18*k,.55*k,.18*k),"top",(0,0,0),(0,0,0),"S")
        elif ht=="rhino":
            B.add("RhinoHorn1",snout,"pyramid",(.34*k,.95*k,.34*k),"top",(0,0,-.1),(-20,0,0),"S")
            B.add("RhinoHorn2",head,"pyramid",(.24*k,.52*k,.24*k),"top",(0,0,-.35),(-12,0,0),"S")
        elif ht=="tricera":
            B.add("NoseHorn",snout,"pyramid",(.24*k,.55*k,.24*k),"top",(0,0,0),(-15,0,0),"S")
            for sx,suf in ((1,"R"),(-1,"L")):
                B.add("Horn"+suf,head,"pyramid",(.28*k,1.3*k,.28*k),"top",(sx*hw*.32,0,-.2),(-48,0,-sx*10),"S")
            B.mirrored.append(("HornR","HornL"))
        else:
            for sx,suf in ((1,"R"),(-1,"L")):
                side="right" if sx>0 else "left"
                if ht in ("curved","spiral"):
                    h=B.add("Horn"+suf,head,"box",(.22*k,.85*k,.22*k),"top",(sx*hw*.28,0,hl*.12),(22,0,sx*8),"S")
                    B.add("Horn%sTip"%suf,h,"pyramid",(.18*k,.75*k,.18*k),"top",(0,0,0),(28,0,0),"S")
                elif ht=="bull":
                    h=B.add("Horn"+suf,head,"box",(hw*.38,.2*k,.2*k),side,(0,hh*.25,0),(0,0,0),"S")
                    B.add("Horn%sTip"%suf,h,"pyramid",(.18*k,.62*k,.18*k),"top",(sx*.05,0,0),(0,0,0),"S")
                elif ht=="antlers":
                    h=B.add("Horn"+suf,head,"box",(.16*k,1.05*k,.16*k),"top",(sx*hw*.26,0,0),(0,0,-sx*20),"S")
                    for i in range(2):
                        B.add("Horn%sP%d"%(suf,i),h,"box",(.14*k,.58*k,.14*k),None,(sx*.14*k,(i-.5)*.5*k,0),(0,0,-sx*28),"S")
                elif ht=="knobs":
                    h=B.add("Horn"+suf,head,"box",(.18*k,.58*k,.18*k),"top",(sx*hw*.24,0,0),(0,0,0),"S")
                    B.add("Horn%sTip"%suf,h,"gem",(.28*k,.28*k,.28*k),"top",(0,0,0),(0,0,0),"D")
            B.mirrored.append(("HornR","HornL"))
        B.tag("horns")
    # Cascading Stepped Tail (Matches Screenshot 7!)
    tt=S["tail"]; tyy=bh*.22
    tcol = "C" if sp in ("unicorn","pegasus") else "D"
    def tchain(n,w,l,pitch,cols):
        par=None
        for i in range(n):
            f=1-.1*i
            if i==0: par=B.add("Tail",torso,"box",(w,w,l),"back",(0,tyy,0),(pitch,0,0),cols[0],studs=True)
            else: par=B.add("Tail%d"%i,par,"box",(w*f,w*f,l),"back",(0,0,0),(pitch*.65,0,0),cols[i%len(cols)])
        return par
    if tt=="short": tchain(2,.38*k,.55*k,-22,["A","B"])
    elif tt=="long_up": tchain(4,.32*k,.72*k,-14,["A","B"])
    elif tt=="hang": tchain(4,.38*k,.82*k,-24,[tcol])
    elif tt=="bushy": tchain(3,.72*k,.92*k,-28,["A","A","L"])
    elif tt=="tuft":
        e=tchain(3,.24*k,.72*k,-18,["A"]); B.add("TailTuft",e,"box",(.42*k,.42*k,.52*k),"back",(0,0,0),(0,0,0),"D")
    elif tt=="curly": tchain(3,.22*k,.32*k,-42,["L"])
    elif tt=="ball": B.add("Tail",torso,"gem",(.62*k,.62*k,.62*k),"back",(0,tyy,0),(0,0,0),"L")
    elif tt=="croc": tchain(5,bh*.62,bl*.22,-6,["A","B"])
    elif tt=="long_thin": tchain(4,.14*k,.8*k,-8,["B"])
    # Species Extras (Stepped Flowing Mane for Horses/Unicorns, Frills, Plates, Trunks)
    if "beard" in ex: B.add("Beard",head,"box",(hw*.24,hh*.58,hw*.22),"bot",(0,0,-hl*.32),(0,0,0),"L")
    if "mane" in ex: B.add("Mane",head,"box",(hw*1.68,hh*1.62,hl*.58),"back",(0,0,hl*.1),(0,0,0),"S",studs=True)
    if "frill" in ex:
        fr=B.add("Frill",head,"box",(hw*1.95,hh*1.75,.26*k),"back",(0,hh*.32,0),(0,0,0),"A",studs=True)
        for i in range(5):
            B.add("FrillSpike%d"%i,fr,"pyramid",(.28*k,.42*k,.24*k),"top",((i-2)*hw*.38,0,0),(0,0,0),"S")
    if "udder" in ex: B.add("Udder",torso,"box",(bw*.45,.35*k,bl*.25),"bot",(0,0,bl*.15),(0,0,0),"L")
    if "qwing" in ex:
        for sx,suf in ((1,"R"),(-1,"L")):
            w=B.add("QWing"+suf,torso,"box",(1.9,.28,1.35),"right" if sx>0 else "left",(0,bh*.35,-.25),(0,0,sx*26),"L",studs=True)
            B.add("QWingTip"+suf,w,"wedge",(1.5,.22,1.05),"right" if sx>0 else "left",(0,0,0),(0,0,sx*16),"C")
    if "cerb_heads" in ex:
        for sx,suf in ((1,"R"),(-1,"L")):
            shd=B.add("SideHead"+suf,torso,"box",(hw*.85,hh*.85,hl*.85),None,(sx*bw*.48,ty,tz),(0,sx*-18,0),"A")
            B.add("SideSnout"+suf,shd,"box",(sw*.8,sh*.8,sl*.8),"front",(0,-hh*.1,0),(0,0,0),"B")
    if "hmane" in ex:
        mcol = "C" if sp in ("unicorn","pegasus") else "D"
        for i in range(4):
            t_f = i / 3.0
            my = nb_y + nl*(1.0 - t_f*.75)*math.cos(ang) + hh*.2
            mz = nb_z - nl*(1.0 - t_f*.75)*math.sin(ang) + .32*k
            B.add("Mane%d"%i,torso,"box",(.32*k,.55*k,.48*k),None,(0,my,mz),(-S["nang"],0,0),mcol,studs=True)
        B.add("Forelock",head,"box",(.32*k,.32*k,.42*k),"top",(0,0,-hl*.12),(0,0,0),mcol)
    if "hump" in ex: B.add("Hump",torso,"box",(bw*.72,bh*.68,bl*.28),"top",(0,0,bl*.05),(0,0,0),"B",studs=True)
    if "spots" in ex:
        for i,(x,z) in enumerate([(-.26,-.28),(.24,.05),(-.18,.3),(.28,-.32)][:4]):
            B.add("Spot%d"%i,torso,"box",(bw*.32,.08,bl*.18),"top",(x*bw,0,z*bl),(0,0,0),"D")
    if "stripes" in ex:
        for i in range(5):
            B.add("Stripe%d"%i,torso,"box",(bw*.88,.08,bl*.08),"top",(0,0,(i-2)*bl*.18),(0,0,0),"D")
    if "plates" in ex:
        for i in range(5):
            B.add("Plate%d"%i,torso,"pyramid",(bw*.28,bh*.48,bl*.14),"top",(0,0,(i-2)*bl*.18),(0,0,0),"S")
    if "wool" in ex:
        for i in range(3):
            B.add("Wool%d"%i,torso,"box",(bw*.82,bh*.32,bl*.26),"top",(0,0,(i-1)*bl*.28),(0,0,0),"L",studs=True)
        B.add("WoolHead",head,"box",(hw*.92,hh*.38,hl*.52),"top",(0,0,hl*.1),(0,0,0),"A")
    if "patches" in ex:
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("Patch"+suf,head,"box",(hw*.32,hh*.32,.12*k),"front",(sx*hw*.28,hh*.12,0),(0,0,0),"B")
    if "trunk" in ex:
        t1=B.add("Trunk",head,"box",(hw*.4,hh*.5,hw*.35),"front",(0,-hh*.1,0),(0,0,0),"A")
        t2=B.add("Trunk2",t1,"box",(hw*.34,hh*.5,hw*.3),"bot",(0,0,-.05),(-12,0,0),"A")
        B.add("Trunk3",t2,"box",(hw*.28,hh*.45,hw*.26),"bot",(0,0,-.05),(-14,0,0),"A")
    if "tusks" in ex:
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("Tusk"+suf,head,"pyramid",(.22*k,.92*k,.22*k),"front",(sx*hw*.3,-hh*.3,0),(-70,0,0),"L")
    B.tag("quadruped","legs",sp)

def b_mech(B,I,r):
    v=B.var
    hips=B.add("CoreRoot",None,"box",(2.4,.8,1.6),None,(0,3.2,0),(0,0,0),"D",studs=True)
    torso=B.add("Torso",hips,"box",(3.0,2.4,2.0),"top",(0,.08,0),(0,0,0),"A",studs=True)
    B.add("Cockpit",torso,"wedge",(1.8,1.3,.6),"front",(0,.2,0),(0,0,0),"C")
    B.add("Reactor",torso,"gem",(.85,.85,.35),"front",(0,-.42,0),(0,0,0),"S")
    head=B.add("Head",torso,"box",(1.3,1.0,1.2),"top",(0,0,-.1),(0,0,0),"B",studs=True)
    B.add("Visor",head,"box",(1.12,.34,.18),"front",(0,.05,0),(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("VFin"+suf,head,"wedge",(.2,.78,.38),"top",(sx*.42,0,-.18),(0,0,sx*-28),"S")
        pauld=B.add("Pauldron"+suf,torso,"box",(1.38,1.05,1.55),"right" if sx>0 else "left",(0,.72,0),(0,0,0),"B",studs=True)
        if v%2==0:
            B.add("Cannon"+suf,pauld,"cylinder",(.44,2.1,.44),"top",(0,.15,-.35),(75,0,0),"D")
        ua=B.add("Arm"+suf,pauld,"box",(.82,1.55,.82),"bot",(0,0,0),(0,0,0),"A")
        fa=B.add("Fore"+suf,ua,"box",(.92,1.55,.96),"bot",(0,0,-.08),(-18,0,0),"B")
        B.add("Hand"+suf,fa,"box",(.72,.72,.78),"bot",(0,0,0),(0,0,0),"D")
        th=B.add("Thigh"+suf,hips,"box",(1.0,1.75,1.1),"bot",(sx*.82,0,0),(0,0,0),"B")
        sh=B.add("Shin"+suf,th,"box",(1.12,1.95,1.28),"bot",(0,0,0),(0,0,0),"A",studs=True)
        B.add("Knee"+suf,sh,"wedge",(.86,.75,.38),"front",(0,.48,0),(0,0,0),"S")
        B.add("Foot"+suf,sh,"wedge",(1.25,.68,1.95),"bot",(0,0,-.32),(0,0,0),"D")
    jp=B.add("ThrusterPack",torso,"box",(1.75,1.55,.78),"back",(0,.18,0),(0,0,0),"D",studs=True)
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Booster"+suf,jp,"cylinder",(.52,1.1,.52),"bot",(sx*.48,0,.1),(14,0,0),"S")
    B.tag("mech","armor","robot")

def b_serpent(B,I,r):
    kw=I.get("keyword") or "serpent"
    n=10 if B.var!=2 else 12
    d=[10]+[r.choice([-12,12])*(1 if i%2 else -1) for i in range(n-1)]
    par=None;names=[]
    for i in range(n):
        sz=(1.5-i*.07,1.35-i*.06,1.6)
        nn=B.add("Seg%d"%i,par if par else None,"box",sz,None if par else None,
                 (0,1.5,4.2) if not par else (0,0,0),(0,d[i],0),"A" if i%2 else "B",studs=i%2==0)
        names.append(nn);par=nn
    hd=B.add("Head",par,"box",(1.9,1.5,2.2),"front",(0,.22,0),(0,0,0),"A",studs=True)
    B.add("Snout",hd,"wedge",(1.35,.88,1.25),"front",(0,-.22,0),(-90,0,0),"B")
    B.eyes(hd,.38,-.95,.48,.7,sc="C",framed=True)
    if kw in ("dragon","wyvern","wyrm","hydra","charizard"):
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("DrgHorn"+suf,hd,"pyramid",(.34,1.05,.34),"top",(sx*.52,0,.28),(-24,0,0),"S")
            w=B.add("DrgWing"+suf,names[min(3,len(names)-1)],"box",(2.2,.28,1.35),"right" if sx>0 else "left",(0,.5,0),(0,0,sx*22),"B",studs=True)
            B.add("DrgWingTip"+suf,w,"wedge",(1.8,.22,1.15),"right" if sx>0 else "left",(0,0,0),(0,0,sx*15),"S")
    for i in range(0,n-2,2): B.add("Dorsal%d"%i,names[i],"wedge",(.28,.85,.95),"top",(0,0,0),(0,0,0),"C")
    B.add("TailFin",names[0],"wedge",(1.25,1.45,.28),"back",(0,.18,0),(90,0,0),"C")
    B.tag("tail")

def b_fish(B,I,r):
    kw=I.get("keyword") or "fish"
    body=B.add("CoreRoot",None,"box",(2.4,2.4,2.8),None,(0,2.0,0),(0,0,0),"A",studs=True)
    sn=B.add("SnoutSec",body,"box",(1.9,1.85,1.35),"front",(0,-.05,0),(0,0,0),"A",studs=True)
    if kw in ("swordfish","narwhal","marlin"):
        B.add("TuskBill",sn,"pyramid",(.28,2.1,.28),"front",(0,0,0),(-90,0,0),"L")
    cs=B.add("CaudalSec",body,"box",(1.35,1.45,1.4),"back",(0,0,0),(0,0,0),"B",studs=True)
    B.add("Belly",body,"box",(2.0,.45,2.4),"bot",(0,0,0),(0,0,0),"L")
    B.eyes(sn,.38,-.58,.5,.78,sc="C",framed=True)
    B.add("DorsalFin",body,"wedge",(.32,1.35,1.65),"top",(0,0,.15),(0,0,0),"S")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Pect"+suf,body,"wedge",(1.45,.26,1.1),"right" if sx>0 else "left",(0,-.38,-.35),(0,0,sx*-22),"C")
    for k,dy in ((-1,-.55),(1,.55)):
        B.add("Caudal%d"%(k+1),cs,"wedge",(.28,1.35,1.45),"back",(0,dy,0),(k*24,0,0),"C")
    B.tag("fins","tail")

def b_crab(B,I,r):
    kw=I.get("keyword") or "crab"
    B.add("CoreRoot",None,"box",(3.4,1.5,2.6),None,(0,1.9,0),(0,0,0),"A",studs=True)
    d1=B.add("Dome","CoreRoot","box",(2.7,.65,2.1),"top",(0,0,0),(0,0,0),"B",studs=True)
    B.add("Dome2",d1,"box",(1.8,.45,1.4),"top",(0,0,0),(0,0,0),"A",studs=True)
    for sx,suf in ((1,"R"),(-1,"L")):
        st=B.add("Stalk"+suf,"CoreRoot","box",(.28,.75,.28),"top",(sx*.8,0,-1.05),(0,0,0),"C")
        B.add("Eye"+suf,st,"gem",(.48,.48,.48),"top",(0,0,0),(0,0,0),"D")
        m=B.add("Merus"+suf,"CoreRoot","box",(.78,1.4,.78),None,(sx*1.95,.1,-.85),(0,0,sx*24),"B")
        c=B.add("Carpus"+suf,m,"box",(.68,1.15,.68),"bot",(0,0,-.25),(-32,0,0),"A")
        pr=B.add("Prop"+suf,c,"box",(.75,1.45,.7),"bot",(0,0,-.18),(-18,0,0),"B",studs=True)
        B.add("Dactyl"+suf,pr,"wedge",(.48,1.35,.48),"bot",(0,0,-.15),(-24,0,0),"S")
        B.add("Pollex"+suf,pr,"wedge",(.48,1.05,.48),"bot",(0,0,.28),(20,0,0),"S")
    for i in range(3):
        for sx,suf in ((1,"R"),(-1,"L")):
            l1=B.add("Walk%d%s"%(i,suf),"CoreRoot","box",(.44,1.45,.44),None,(sx*1.6,-.55,.7-i*.7),(0,0,sx*34),"B")
            l2=B.add("Walk%d%s2"%(i,suf),l1,"box",(.36,1.35,.36),"bot",(0,0,0),(0,0,-sx*46),"A")
            B.add("Walk%d%s3"%(i,suf),l2,"pyramid",(.26,.65,.26),"bot",(0,0,0),(180,0,0),"D")
    if kw=="scorpion":
        t=B.chain("ScorpTail","CoreRoot",4,[(.65,.65,.8),(.55,.55,.8),(.45,.45,.8),(.38,.38,.7)],["A","B"],[28,32,35,38],face="back")
        B.add("Stinger",t[-1],"pyramid",(.35,.8,.35),"bot",(0,0,0),(150,0,0),"C")
    B.tag("claws")

def b_spider(B,I,r):
    B.add("CoreRoot",None,"box",(2.0,1.4,2.2),None,(0,2.2,-.8),(0,0,0),"A",studs=True)
    B.add("Abdomen","CoreRoot","box",(2.3,1.85,2.6),"back",(0,.35,0),(0,0,0),"B",studs=True)
    hd=B.add("Head","CoreRoot","box",(1.45,1.1,1.2),"front",(0,-.08,0),(0,0,0),"B",studs=True)
    for k,(dx,dy) in enumerate(((-.38,.1),(-.14,.24),(.14,.24),(.38,.1))):
        B.add("Eye%d"%k,hd,"gem",(.24,.28,.18),"front",(dx*1.8,dy,0),(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        ch=B.add("Chel"+suf,hd,"box",(.38,.65,.48),"bot",(sx*.34,0,-.32),(0,0,0),"D")
        B.add("Fang"+suf,ch,"pyramid",(.2,.72,.2),"bot",(0,0,0),(168,0,0),"S")
    for i in range(4):
        for sx,suf in ((1,"R"),(-1,"L")):
            l1=B.add("Leg%d%s"%(i,suf),"CoreRoot","box",(.38,1.85,.38),None,(sx*1.0,.25,-.9+i*.62),(0,0,sx*52),"B")
            l2=B.add("Leg%d%s2"%(i,suf),l1,"box",(.32,1.85,.32),"bot",(0,0,0),(0,0,-sx*58),"A")
            l3=B.add("Leg%d%s3"%(i,suf),l2,"box",(.26,1.45,.26),"bot",(0,0,0),(0,0,sx*24),"B")
            B.add("Leg%d%s4"%(i,suf),l3,"pyramid",(.2,.65,.2),"bot",(0,0,0),(180,0,0),"D")
    B.tag("teeth")

def b_golem(B,I,r):
    torso=B.add("HumanoidRootPart",None,"box",(2.8,2.8,2.0),None,(0,3.2,0),(0,0,0),"A",studs=True)
    B.add("ChestSlab",torso,"box",(2.4,1.6,.35),"front",(0,.35,0),(0,0,0),"B",studs=True)
    B.add("Core","ChestSlab","gem",(.95,1.1,.32),"front",(0,0,0),(0,0,0),"C")
    hd=B.add("Head",torso,"box",(1.35,1.15,1.25),"top",(0,0,0),(0,0,0),"B",studs=True)
    B.add("Visor",hd,"box",(1.05,.32,.18),"front",(0,.08,0),(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        p=B.add("Pauldron"+suf,torso,"box",(1.35,.75,1.45),"right" if sx>0 else "left",(0,.85,0),(0,0,0),"B",studs=True)
        a1=B.add("Arm"+suf,p,"box",(.92,1.95,.92),"bot",(0,0,0),(0,0,0),"A")
        a2=B.add("Fore"+suf,a1,"box",(1.05,1.75,1.05),"bot",(0,0,0),(-14,0,0),"B",studs=True)
        B.add("Fist"+suf,a2,"box",(1.15,1.0,1.15),"bot",(0,0,0),(0,0,0),"D")
        l1=B.add("Leg"+suf,torso,"box",(1.05,2.1,1.1),"bot",(sx*.85,0,0),(0,0,0),"B")
        B.add("Foot"+suf,l1,"wedge",(1.2,.7,1.65),"bot",(0,0,-.28),(0,0,0),"D")
    B.tag("armor","glow")

def b_turtle(B,I,r):
    B.add("CoreRoot",None,"box",(3.0,1.1,3.4),None,(0,1.6,0),(0,0,0),"L")
    sh=B.add("ShellBase","CoreRoot","box",(3.2,.85,3.6),"top",(0,0,0),(0,0,0),"A",studs=True)
    s2=B.add("Shell2",sh,"box",(2.5,.75,2.9),"top",(0,0,0),(0,0,0),"B",studs=True)
    B.add("Shell3",s2,"box",(1.7,.65,2.1),"top",(0,0,0),(0,0,0),"A",studs=True)
    nk=B.add("Neck","CoreRoot","box",(.88,.85,.95),"front",(0,0,0),(-12,0,0),"L")
    hd=B.add("Head",nk,"box",(1.08,.95,1.1),"front",(0,.1,0),(10,0,0),"L",studs=True)
    B.eyes(hd,.18,-.52,.32,.42,sc="C",framed=True)
    for i,(sx,sz) in enumerate(((1,-1),(-1,-1),(1,1),(-1,1))):
        B.add("Flip%d"%i,"CoreRoot","box",(.88,.75,1.25),None,(sx*1.58,-.45,sz*1.25),(0,0,sx*18),"L",studs=True)
    B.chain("Tail","CoreRoot",3,[(.58,.55,.75),(.44,.42,.65),(.3,.28,.55)],["L","L","D"],[10,12,14])
    B.tag("shell","tail")

def b_jelly(B,I,r):
    B.add("CoreRoot",None,"box",(3.0,1.2,3.0),None,(0,3.0,0),(0,0,0),"A",studs=True)
    b2=B.add("Bell2","CoreRoot","box",(3.4,.85,3.4),"bot",(0,0,0),(0,0,0),"B",studs=True)
    B.add("Bell3","CoreRoot","box",(2.4,.75,2.4),"top",(0,0,0),(0,0,0),"A",studs=True)
    B.add("GlowCore","CoreRoot","gem",(1.0,.8,1.0),"bot",(0,.2,0),(0,0,0),"C")
    for i in range(12):
        az=i*30.0;a=math.radians(az)
        B.add("Skirt%d"%i,b2,"wedge",(.48,.85,.18),None,(1.58*math.sin(a),-.48,1.58*math.cos(a)),(180,az,0),"L")
    nt=8
    for i in range(nt):
        az=i*360.0/nt;a=math.radians(az)
        base=B.add("Tent%d"%i,b2,"box",(.24,.7,.24),None,(1.35*math.sin(a),-.55,1.35*math.cos(a)),(0,az,0),"C")
        B.chain("Tent%d_"%i,base,5,[(.2,1.15,.2),(.18,1.05,.18),(.16,.95,.16),(.14,.85,.14),(.12,.75,.12)],
                ["C","L","C","L","C"],[8,10,12,14,16])
    B.tag("tentacles","frill","glow")

def b_train(B,I,r):
    kw=I.get("keyword") or "train"
    ch=B.add("CoreRoot",None,"box",(2.3,.6,5.8),None,(0,1.0,0),(0,0,0),"D",studs=True)
    if kw in ("bullettrain","monorail","subway","metro"):
        bd=B.add("Coach",ch,"box",(2.18,1.5,5.2),"top",(0,0,.2),(0,0,0),"A",studs=True)
        B.add("NoseCone",bd,"wedge",(2.12,1.4,1.6),"front",(0,-.04,0),(-90,0,0),"B")
        B.add("CockpitWin",bd,"box",(1.72,.45,.16),"front",(0,.35,0),(0,0,0),"C")
    else:
        cab=B.add("Cabin",ch,"box",(2.2,2.0,1.9),"top",(0,0,1.7),(0,0,0),"B",studs=True)
        B.add("CabRoof",cab,"box",(2.36,.24,2.08),"top",(0,0,0),(0,0,0),"D",studs=True)
        blr=B.add("Boiler",ch,"cylinder",(1.72,3.4,1.72),"top",(0,.2,-.9),(90,0,0),"A")
        B.add("Smokestack",blr,"cylinder",(.48,1.1,.48),"top",(0,.3,-1.0),(0,0,0),"D")
        B.add("Headlamp",blr,"gem",(.45,.45,.3),"front",(0,.2,-1.6),(0,0,0),"C")
        B.add("Cowcatcher",ch,"wedge",(2.18,.68,.88),"front",(0,-.08,0),(-90,0,0),"S")
    for sx,suf in ((1,"R"),(-1,"L")):
        for i,zz in enumerate((-2.0,0.0,2.0)):
            B.add("TrWheel%d%s"%(i,suf),ch,"cylinder",(.86,.3,0.86),None,(sx*1.18,-.28,zz),(0,0,90),"C")
    B.tag("wheels","train")

def b_bike(B,I,r):
    fr=B.add("CoreRoot",None,"box",(.55,.72,2.25),None,(0,1.2,0),(0,0,0),"A",studs=True)
    for zz,tag in ((-1.3,"F"),(1.3,"B")):
        w=B.add("Wheel%s"%tag,fr,"cylinder",(1.12,.36,1.12),None,(0,-.48,zz),(0,0,90),"D")
        B.add("Hub%s"%tag,w,"cylinder",(.56,.42,.56),None,(0,0,0),(0,0,90),"S")
    B.add("Fork",fr,"box",(.24,1.0,.24),"front",(0,-.28,-.18),(20,0,0),"B")
    B.add("Bar",fr,"box",(1.42,.2,.2),"top",(0,.22,-.88),(0,0,0),"D")
    B.add("Seat",fr,"box",(.62,.26,.92),"top",(0,0,.68),(0,0,0),"B")
    B.tag("wheels")

def b_boat(B,I,r):
    kw=I.get("keyword") or "boat"
    hl=B.add("CoreRoot",None,"box",(2.5,1.1,5.0),None,(0,1.2,0),(0,0,0),"A",studs=True)
    B.add("Bow",hl,"pyramid",(2.46,1.05,1.65),"front",(0,-.02,0),(-90,0,0),"A")
    cab=B.add("Cabin",hl,"box",(1.85,1.05,1.85),"top",(0,0,.55),(0,0,0),"B",studs=True)
    B.add("Win",cab,"box",(1.45,.48,.14),"front",(0,.1,0),(0,0,0),"D")
    if B.var!=1 or kw in ("sailboat","pirateship","galleon","yacht"):
        m=B.add("Mast",cab,"box",(.24,2.4,.24),"top",(0,0,0),(0,0,0),"D")
        if kw in ("sailboat","pirateship","galleon"):
            B.add("MainSail",m,"box",(2.2,1.6,.16),"front",(0,.1,0),(0,0,0),"L")
    B.add("Prop",hl,"cylinder",(.8,.22,.8),"back",(0,-.2,0),(90,0,0),"D")
    B.tag("hull")

def b_plane(B,I,r):
    kw=I.get("keyword") or "plane"
    if kw in ("ufo","saucer"):
        disc=B.add("CoreRoot",None,"cylinder",(4.4,.7,4.4),None,(0,2.4,0),(0,0,0),"A",studs=True)
        B.add("Dome",disc,"gem",(2.2,1.3,2.2),"top",(0,0,0),(0,0,0),"C")
        B.ring("UfoLight",disc,8,1.9,-.1,(.35,.2,.35),"S")
        B.tag("wings"); return
    fu=B.add("CoreRoot",None,"box",(1.65,1.4,5.0),None,(0,2.2,0),(0,0,0),"A",studs=True)
    B.add("Nose",fu,"pyramid",(1.58,1.4,1.35),"front",(0,0,0),(-90,0,0),"B")
    B.add("Cockpit",fu,"wedge",(1.15,.65,1.45),"top",(0,0,-1.15),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Wing"+suf,fu,"wedge",(3.8,.26,1.45),"right" if sx>0 else "left",(0,-.15,-.25),(0,0,sx*6),"B",studs=True)
        B.add("Stab"+suf,fu,"wedge",(1.35,.22,.85),"right" if sx>0 else "left",(0,.35,2.05),(0,0,sx*6),"B")
    B.add("Fin",fu,"wedge",(.24,1.55,1.25),"top",(0,0,1.85),(0,0,0),"C")
    B.tag("wings")

def b_heli(B,I,r):
    bd=B.add("CoreRoot",None,"box",(2.0,1.6,3.4),None,(0,2.0,0),(0,0,0),"A",studs=True)
    B.add("Win",bd,"box",(1.62,.78,.14),"front",(0,.18,0),(0,0,0),"D")
    tb=B.add("Boom",bd,"box",(.55,.55,2.9),"back",(0,.28,0),(0,0,0),"B",studs=True)
    B.add("TRotor",tb,"wedge",(.16,1.35,.42),"right",(0,0,1.1),(0,0,90),"D")
    hub=B.add("Hub",bd,"cylinder",(.52,.42,.52),"top",(0,0,0),(0,0,0),"D")
    for i in range(4): B.add("Blade%d"%i,hub,"box",(4.6,.12,.38),"top",(0,0,0),(0,i*90,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        st=B.add("Strut"+suf,bd,"box",(.18,.68,.18),"bot",(sx*.85,0,0),(0,0,0),"D")
        B.add("Skid"+suf,st,"box",(.22,.22,3.2),"bot",(0,0,0),(0,0,0),"D")
    B.tag("rotor")

def b_tank(B,I,r):
    hl=B.add("CoreRoot",None,"box",(2.8,1.0,4.2),None,(0,1.3,0),(0,0,0),"A",studs=True)
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Track"+suf,hl,"box",(.72,.92,4.4),"right" if sx>0 else "left",(0,-.18,0),(0,0,0),"D",studs=True)
    tu=B.add("Turret",hl,"box",(2.0,.92,2.2),"top",(0,0,.15),(0,0,0),"B",studs=True)
    B.add("Barrel",tu,"cylinder",(.34,2.8,.34),"front",(0,.05,0),(90,0,0),"D")
    B.add("Hatch",tu,"box",(.72,.22,.72),"top",(0,0,.35),(0,0,0),"D")
    B.tag("armor")

def b_building(B,I,r):
    kw=I.get("keyword") or "house"; v=B.var%4
    if kw=="pyramid":
        p=B.add("CoreRoot",None,"pyramid",(5.2,3.8,5.2),None,(0,1.9,0),(0,0,0),"A",studs=True)
        B.add("Gate",p,"box",(1.1,1.3,.4),"front",(0,-1.25,1.0),(0,0,0),"D")
        B.tag("building"); return
    if kw in ("bridge","arch","gate"):
        top=B.add("CoreRoot",None,"box",(5.0,.8,2.2),None,(0,2.8,0),(0,0,0),"A",studs=True)
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("Pillar"+suf,top,"box",(1.1,2.6,2.0),"bot",(sx*1.8,0,0),(0,0,0),"B",studs=True)
        B.tag("building"); return
    tower=kw in ("tower","lighthouse","windmill","skyscraper")
    castle=kw in ("castle","fort","citadel","palace")
    tall=tower or kw in ("church","temple","cathedral","pagoda")
    w=3.2 if tower else 3.8 if tall else 4.6; h=6.0 if kw=="skyscraper" else 5.0 if tower else 3.2 if tall else 2.6; d=w if tall else 3.8
    base=B.add("CoreRoot",None,"box",(w,h,d),None,(0,h/2,0),(0,0,0),"A",studs=True)
    B.add("Foundation",base,"box",(w*1.06,.32,d*1.06),"bot",(0,0,0),(0,0,0),"B",studs=True)
    B.add("Door",base,"box",(.96,1.52,.16),"front",(0,-h/2+.82,0),(0,0,0),"D")
    for sx in (1,-1):
        B.add("Window%d"%(1 if sx>0 else 2),base,"box",(.76,.76,.14),"front",(sx*w*.28,h*.12+(.9 if tall else 0),0),(0,0,0),"L")
    if kw=="windmill":
        hub=B.add("MillHub",base,"cylinder",(.45,.45,.45),"front",(0,h*.28,0),(90,0,0),"D")
        for i in range(4):
            B.add("Sail%d"%i,hub,"box",(3.4,.38,.12),None,(0,0,-.15),(0,0,i*90+45),"L")
    if castle:
        for sx,a in ((1,"R"),(-1,"L")):
            for sz,b in ((-1,"F"),(1,"B")):
                t=B.add("Turret"+a+b,base,"box",(1.35,h*.6+1.4,1.35),None,(sx*w/2,.7,sz*d/2),(0,0,0),"B",studs=True)
                B.add("Turret%s%sCap"%(a,b),t,"pyramid",(1.68,1.15,1.68),"top",(0,0,0),(0,0,0),"C")
        for i in range(5):
            B.add("Merlon%d"%i,base,"box",(.5,.48,.48),"top",((i-2)*.85,0,-(d/2-.32)),(0,0,0),"B",studs=True)
            B.add("MerlonB%d"%i,base,"box",(.5,.48,.48),"top",((i-2)*.85,0,(d/2-.32)),(0,0,0),"B",studs=True)
    else:
        top=base
        if kw=="lighthouse": top=B.add("Lamp",base,"gem",(1.35,1.15,1.35),"top",(0,0,0),(0,0,0),"C")
        B.add("Roof",top,"pyramid",(1.75,1.05,1.75) if kw=="lighthouse" else (w*1.16,1.7+(1.1 if tall else 0),d*1.16),
              "top",(0,0,0),(0,0,0),"C")
        if not tall and v!=1: B.add("Chimney",base,"box",(.58,1.25,.58),"top",(w*.28,.45,0),(0,0,0),"B",studs=True)
    B.tag("building")

def b_tree(B,I,r):
    kw=I.get("keyword") or "tree"; v=B.var%4
    if kw=="cactus":
        t=B.add("CoreRoot",None,"box",(1.15,3.5,1.15),None,(0,1.75,0),(0,0,0),"A",studs=True)
        for sx,suf in ((1,"R"),(-1,"L")):
            a=B.add("Arm"+suf,t,"box",(.92,.58,.58),"right" if sx>0 else "left",(0,.25+v*.15,0),(0,0,0),"A",studs=True)
            B.add("ArmUp"+suf,a,"box",(.56,1.35,.56),"top",(sx*.14,0,0),(0,0,0),"S",studs=True)
    elif kw in ("mushroom","toadstool","fungus"):
        stem=B.add("CoreRoot",None,"box",(1.15,1.65,1.15),None,(0,.82,0),(0,0,0),"L")
        cap=B.add("Cap",stem,"box",(3.1,.95,3.1),"top",(0,0,0),(0,0,0),"C",studs=True)
        B.add("CapTop",cap,"box",(2.1,.55,2.1),"top",(0,0,0),(0,0,0),"C",studs=True)
        for i in range(4):
            x,z=phyllo(i,4,1.0); B.add("Dot%d"%i,cap,"box",(.48,.14,.48),"top",(x,0,z),(0,0,0),"L")
    elif kw in ("flower","plant","rose","sunflower","tulip","lotus","lily","orchid","daisy"):
        st=B.add("CoreRoot",None,"box",(.32,2.4,.32),None,(0,1.2,0),(0,0,0),"S")
        hd=B.add("Bloom",st,"gem",(.82,.52,.82),"top",(0,0,0),(0,0,0),"L")
        B.ring("Petal",hd,6,.72,0,(.52,.22,.56),"C")
        for sx,suf in ((1,"R"),(-1,"L")): B.add("Leaf"+suf,st,"wedge",(.72,.24,.42),"right" if sx>0 else "left",(0,-.28,0),(0,0,sx*18),"A")
    elif kw=="palm":
        t0=B.add("CoreRoot",None,"box",(.82,1.6,.82),None,(0,.8,0),(0,0,0),"B")
        t1=B.add("Trunk1",t0,"box",(.72,1.6,.72),"top",(0,0,0),(8,0,0),"D")
        t2=B.add("Trunk2",t1,"box",(.62,1.6,.62),"top",(0,0,0),(8,0,0),"B")
        crown=B.add("Crown",t2,"gem",(.92,.6,.92),"top",(0,0,0),(0,0,0),"D")
        B.ring("Frond",crown,6,.92,.1,(.62,.16,1.85),"A")
    elif kw in ("bush","shrub","hedge"):
        b=B.add("CoreRoot",None,"box",(2.6,1.35,2.6),None,(0,.68,0),(0,0,0),"A",studs=True)
        B.add("Bush2",b,"box",(1.85,.95,1.85),"top",(0,0,0),(0,0,0),"S",studs=True)
    else:
        # Layered Stepped Brick Tree (like the tree preview in Screenshot 4!)
        tr=B.add("CoreRoot",None,"box",(1.05,2.5,1.05),None,(0,1.25,0),(0,0,0),"B")
        B.add("RootFlare",tr,"box",(1.55,.45,1.55),"bot",(0,0,0),(0,0,0),"D",studs=True)
        f1=B.add("Leaf1",tr,"box",(3.4,1.25,3.4),"top",(0,0,0),(0,0,0),"A",studs=True)
        f2=B.add("Leaf2",f1,"box",(2.6,1.15,2.6),"top",(0,0,0),(0,0,0),"S",studs=True)
        f3=B.add("Leaf3",f2,"box",(1.7,1.0,1.7),"top",(0,0,0),(0,0,0),"A",studs=True)
        if kw=="pine": B.add("Tip",f3,"pyramid",(1.25,1.45,1.25),"top",(0,0,0),(0,0,0),"S")
        if v==1:
            for sx,sz in ((1,1),(-1,1),(1,-1),(-1,-1)):
                B.add("Fruit%d_%d"%(sx,sz),f1,"box",(.38,.38,.38),"bot",(sx*1.15,0,sz*1.15),(0,0,0),"C")
    B.tag("plant")

def b_weapon(B,I,r):
    kw=I.get("keyword") or "sword"
    if kw in ("shield","buckler","aegis"):
        s=B.add("CoreRoot",None,"box",(2.4,3.0,.35),None,(0,1.5,0),(0,0,0),"A",studs=True)
        B.add("Rim",s,"box",(2.65,.32,.42),"top",(0,0,0),(0,0,0),"S",studs=True)
        B.add("Emblem",s,"gem",(1.0,1.0,.32),"front",(0,0,0),(0,0,0),"C")
        B.tag("weapon"); return
    if kw in ("gun","pistol","revolver","rifle","shotgun","sniperrifle","smg","blaster","lasergun","raygun","plasmagun"):
        body=B.add("CoreRoot",None,"box",(.56,.86,2.8),None,(0,1.6,0),(0,0,0),"A",studs=True)
        B.add("Grip",body,"box",(.48,1.1,.56),"bot",(0,0,.85),(18,0,0),"D")
        B.add("Barrel",body,"cylinder",(.34,1.65,.34),"front",(0,.12,0),(90,0,0),"S")
        B.add("Scope",body,"cylinder",(.28,1.1,.28),"top",(0,0,.2),(90,0,0),"C")
        B.tag("weapon"); return
    if kw in ("axe","hammer","warhammer","maul","mace","spear","trident","halberd","scythe","staff","wand","scepter","bow","crossbow"):
        ln=2.6 if kw=="wand" else 4.2
        h=B.add("CoreRoot",None,"box",(.24 if kw=="wand" else .34,ln,.24 if kw=="wand" else .34),None,(0,ln/2,0),(0,0,0),"B")
        if kw in ("axe","halberd"):
            hd=B.add("AxeHead",h,"box",(1.35,1.05,.32),"top",(.48,-.75,0),(0,0,0),"A",studs=True)
            B.add("AxeEdge",hd,"box",(.36,1.32,.26),"right",(0,0,0),(0,0,0),"S")
        elif kw=="scythe":
            B.add("ScytheBlade",h,"wedge",(2.2,.45,.22),"top",(.95,-.15,0),(0,0,-12),"L")
        elif kw in ("hammer","warhammer","maul","mace"):
            B.add("HammerHead",h,"box",(1.65,.95,.95),"top",(0,-.25,0),(0,0,0),"A",studs=True)
        elif kw in ("spear","trident"):
            c=B.add("Collar",h,"box",(.52,.32,.52),"top",(0,0,0),(0,0,0),"S")
            B.add("SpearTip",c,"pyramid",(.5,1.35,.5),"top",(0,0,0),(0,0,0),"L")
            if kw=="trident":
                for sx,suf in ((1,"R"),(-1,"L")):
                    B.add("Prong"+suf,c,"pyramid",(.28,1.0,.28),"top",(sx*.45,0,0),(0,0,0),"L")
        elif kw in ("bow","crossbow"):
            B.add("BowTop",h,"box",(.24,1.2,.24),"top",(0,-.1,-.3),(-25,0,0),"B")
            B.add("BowBot",h,"box",(.24,1.2,.24),"bot",(0,.1,-.3),(25,0,0),"B")
            B.add("String",h,"box",(.08,ln,.08),None,(0,0,.5),(0,0,0),"L")
        else: B.add("Orb",h,"gem",(.92,.92,.92),"top",(0,0,0),(0,0,0),"C")
        B.tag("weapon"); return
    # Sculpted Master Sword / Broadsword
    bl=2.2 if kw=="dagger" else 3.8
    g=B.add("CoreRoot",None,"box",(.36,1.15,.36),None,(0,.58,0),(0,0,0),"B")
    B.add("Pommel",g,"gem",(.56,.48,.56),"bot",(0,0,0),(0,0,0),"C")
    gd=B.add("Guard",g,"box",(1.75,.34,.48),"top",(0,0,0),(0,0,0),"B",studs=True)
    B.add("GuardGem",gd,"gem",(.38,.38,.28),"front",(0,0,0),(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("GuardWing"+suf,gd,"wedge",(.45,.48,.44),"right" if sx>0 else "left",(0,.08,0),(0,0,sx*18),"B")
    bd=B.add("Blade",gd,"box",(.58,bl,.18),"top",(0,0,0),(0,0,0),"A")
    B.add("BladeTip",bd,"pyramid",(.58,.85,.18),"top",(0,0,0),(0,0,0),"A")
    B.add("Fuller",bd,"box",(.18,bl*.72,.24),None,(0,-.2,0),(0,0,0),"L")
    B.tag("weapon")

def b_furniture(B,I,r):
    kw=I.get("keyword") or "chair"
    if kw in ("chest","treasure","treasurechest","crate","box"):
        base=B.add("CoreRoot",None,"box",(2.8,1.4,1.9),None,(0,.7,0),(0,0,0),"A",studs=True)
        lid=B.add("Lid",base,"box",(2.86,.72,1.96),"top",(0,0,0),(0,0,0),"B",studs=True)
        B.add("Lock",lid,"box",(.46,.56,.22),"front",(0,-.28,0),(0,0,0),"C")
    elif kw in ("table","desk","workbench","counter"):
        top=B.add("CoreRoot",None,"box",(3.6,.36,2.4),None,(0,1.9,0),(0,0,0),"A",studs=True)
        for sx,a in ((1,"R"),(-1,"L")):
            for sz,b in ((-1,"F"),(1,"B")):
                B.add("TblLeg"+a+b,top,"box",(.32,1.8,.32),"bot",(sx*1.5,0,sz*.95),(0,0,0),"B")
    elif kw in ("bed","bunkbed","crib"):
        fr=B.add("CoreRoot",None,"box",(2.8,.58,4.2),None,(0,.7,0),(0,0,0),"B",studs=True)
        mt=B.add("Mattress",fr,"box",(2.6,.42,3.8),"top",(0,0,.12),(0,0,0),"C",studs=True)
        B.add("Pillow",mt,"box",(2.0,.32,.85),"top",(0,0,-1.32),(0,0,0),"L")
        B.add("Headboard",fr,"box",(2.84,1.65,.32),"front",(0,.52,0),(0,0,0),"A",studs=True)
    elif kw in ("tv","television","monitor","computer","pc","arcade"):
        st=B.add("CoreRoot",None,"box",(1.45,.32,1.25),None,(0,.16,0),(0,0,0),"D",studs=True)
        nk=B.add("Neck",st,"box",(.42,.62,.42),"top",(0,0,0),(0,0,0),"D")
        scr=B.add("Screen",nk,"box",(3.2,2.1,.42),"top",(0,0,0),(0,0,0),"A",studs=True)
        B.add("Display",scr,"box",(2.88,1.78,.14),"front",(0,0,0),(0,0,0),"C")
    else:
        seat=B.add("CoreRoot",None,"box",(2.0,.36,2.0),None,(0,1.3,0),(0,0,0),"A",studs=True)
        back=B.add("Backrest",seat,"box",(2.04,2.2,.36),"back",(0,.92,0),(0,0,0),"B",studs=True)
        if kw=="throne":
            B.add("Crest",back,"pyramid",(.82,.82,.36),"top",(0,0,0),(0,0,0),"C")
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("Armrest"+suf,seat,"box",(.32,.68,1.82),"right" if sx>0 else "left",(0,.34,0),(0,0,0),"S",studs=True)
            for sz,b in ((-1,"F"),(1,"B")):
                B.add("ChrLeg"+suf+b,seat,"box",(.28,1.25,.28),"bot",(sx*.8,0,sz*.8),(0,0,0),"D")
    B.tag("furniture")

def b_food(B,I,r):
    kw=I.get("keyword") or "burger"
    if kw in ("potion","elixir","flask","vial","bottle"):
        bd=B.add("CoreRoot",None,"gem",(2.0,2.2,2.0),None,(0,1.1,0),(0,0,0),"C")
        nk=B.add("Neck",bd,"cylinder",(.76,.8,.76),"top",(0,0,0),(0,0,0),"L")
        B.add("Cork",nk,"cylinder",(.86,.45,.86),"top",(0,0,0),(0,0,0),"A",studs=True)
    elif kw in ("cake","cupcake","pie"):
        base=B.add("CoreRoot",None,"cylinder",(2.8,1.3,2.8),None,(0,.65,0),(0,0,0),"A",studs=True)
        top=B.add("Frosting",base,"cylinder",(2.62,.5,2.62),"top",(0,0,0),(0,0,0),"L",studs=True)
        c=B.add("Candle",top,"cylinder",(.26,.9,.26),"top",(0,0,0),(0,0,0),"C")
        B.add("Flame",c,"pyramid",(.28,.45,.28),"top",(0,0,0),(0,0,0),"S")
    else:
        bot=B.add("CoreRoot",None,"cylinder",(2.6,.55,2.6),None,(0,.3,0),(0,0,0),"A",studs=True)
        pat=B.add("Patty",bot,"cylinder",(2.72,.5,2.72),"top",(0,0,0),(0,0,0),"D")
        chs=B.add("Cheese",pat,"box",(2.52,.18,2.52),"top",(0,0,0),(0,45,0),"C")
        let=B.add("Lettuce",chs,"cylinder",(2.66,.25,2.66),"top",(0,0,0),(0,0,0),"S")
        B.add("BunTop",let,"box",(2.48,.75,2.48),"top",(0,0,0),(0,0,0),"A",studs=True)
    B.tag("food")

def b_prop(B,I,r):
    B.add("CoreRoot",None,"box",(2.6,2.2,2.2),None,(0,1.1,0),(0,0,0),"A",studs=True)
    top=B.add("Top","CoreRoot","box",(2.0,1.6,1.8),"top",(0,0,0),(0,0,0),"B",studs=True)
    B.eyes(top,.12,-.92,.4*I["eyes"],.5,sc="L",framed=True)
    B.add("Mouth",top,"box",(.7,.14,.12),"front",(0,-.35,0),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Nub"+suf,"CoreRoot","box",(.5,1.0,.5),"right" if sx>0 else "left",(0,-.1,0),(0,0,sx*-10),"S")
    B.add("Antenna",top,"box",(.16,.8,.16),"top",(0,0,0),(0,0,0),"D")
    B.tag("prop")

BUILDERS={
 "humanoid":b_humanoid,"mech":b_mech,"octopus":b_octopus,"serpent":b_serpent,"fish":b_fish,
 "bird":b_bird,"crab":b_crab,"spider":b_spider,"golem":b_golem,"turtle":b_turtle,"jelly":b_jelly,
 "car":b_car,"train":b_train,"bike":b_bike,"boat":b_boat,"plane":b_plane,"heli":b_heli,"tank":b_tank,
 "quadruped":b_quadruped,"building":b_building,"tree":b_tree,"weapon":b_weapon,
 "furniture":b_furniture,"food":b_food,"prop":b_prop}

BUDGETS={
 "humanoid":105,"mech":115,"octopus":135,"serpent":90,"fish":75,"bird":115,"crab":95,"spider":95,"golem":90,
 "turtle":75,"jelly":120,"car":95,"train":85,"bike":45,"boat":55,"plane":55,"heli":55,"tank":55,
 "quadruped":125,"building":85,"tree":60,"weapon":50,"furniture":55,"food":45,"prop":45}

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
    n=len(spec["parts"]);bud=BUDGETS.get(spec["archetype"],100)
    tot+=add("purpose",1.0 if n<=bud*1.7 else .5,.08);ws+=.08
    if I["colors"]:
        ds=[max(0,1-min(hue_dist(ih,hex_hsv(h)[0]) for h in list(spec["palette"].values())[:6])/90.0) for ih,_,_ in I["colors"]]
        tot+=add("color_match",sum(ds)/len(ds),.14);ws+=.14
    else: tot+=add("color_match",.92,.14);ws+=.14
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
    return {"id":"m%d_%d"%(int(time.time()*1000)%100000,seed%97),
      "name":random.Random(seed).choice(NAME_PRE)+NAME_SUF.get(arch,"bloxx"),
      "archetype":arch,"variant":variant,"seed":seed,"sharpness":round(B.sharp,2),"scale":round(B.scale,2),
      "palette":pal,"tags":sorted(B.present),"root":B.root,"parts":B.parts,"mirrored":B.mirrored,
      "counts":dict(B.counts),"traits_present":sorted(B.present),
      "meta":{"scheme":"v11","mods":I["mods"],"prompt":I.get("_prompt",""),"warn":B.warn,
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
    pose_wrap(B,0,I["float"])
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
    out.append(("budget",len(P)<=BUDGETS.get(spec["archetype"],110)*1.7))
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
    K=8+min(8,it*2);best=None;tried=0
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
        for m in range(4):
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
