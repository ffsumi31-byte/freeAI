"""BrickForge AI v9 (Ultra Edition) — fail-safe procedural 3D brick build pipeline.
v9: 10x upgrade — 32 archetypes (added mech, train, furniture, food, instrument, gun,
    appliance, space, monster, structure, collectible, bug_fly), 48 quadruped species
    (including cerberus, rhino, hippo, zebra, mammoth, griffin, pegasus, triceratops, stegosaurus),
    36 modular addons + auto-equipped humanoid weapons/shields/jetpacks/beards,
    multi-word phrase detection, 45+ colors & materials, 1,200+ vocabulary keywords.
v8: quadruped archetype, building / tree / weapon archetypes, plural + typo tolerant parsing.
v7.1: root tie-break, partial-build resilience, guaranteed fallback spec."""
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
 "goat":      _sp(bh=1.4,leg=1.7,lw=.34,neck=1.1,nang=35,head=(.9,1.0,1.15),snout=(.55,.5,.55),ears="side",
                  ear=(.45,.55),horns="curved",tail="short",extras=("beard",),
                  pal=("#e6e0d2","#a89c86","#e8c547","#5a4a3a","#2d241c","#fbf8f0")),
 "sheep":     _sp(leg=1.3,lw=.36,neck=.7,nang=25,head=(.9,.95,1.0),snout=(.55,.5,.5),ears="side",ear=(.4,.45),
                  headc="B",extras=("wool",),pal=("#f1eee6","#3d3a38","#e8c547","#8a7f70","#2a2624","#ffffff")),
 "dog":       _sp(bh=1.3,bl=2.7,leg=1.3,lw=.36,neck=.6,nang=30,head=(.95,.9,1.0),snout=(.55,.45,.8),ears="floppy",
                  ear=(.5,.8),tail="long_up",extras=("collar",),pal=("#c89a62","#8f6a3e","#e63946","#d8b98a","#2b1d12","#f3e6cf")),
 "wolf":      _sp(bh=1.4,bl=3.0,leg=1.7,lw=.36,neck=.7,nang=32,head=(.95,.9,1.1),snout=(.5,.45,.9),ears="point",
                  ear=(.3,.6),tail="bushy",pal=("#8e949c","#5d636b","#e8c547","#c9ced4","#22262b","#e9edf0")),
 "fox":       _sp(bh=1.2,bl=2.6,leg=1.3,lw=.3,neck=.6,nang=30,head=(.9,.85,1.0),snout=(.5,.4,.9),ears="point",
                  ear=(.42,.8),tail="bushy",pal=("#d9742b","#a9511a","#2b2118","#f3e9dc","#2a1a10","#fbf5ec")),
 "cat":       _sp(bw=1.6,bh=1.1,bl=2.4,leg=1.0,lw=.3,neck=.5,nang=30,head=(1.0,.9,.9),snout=(.4,.3,.3),ears="point",
                  ear=(.35,.5),tail="long_up",extras=("whiskers",),pal=("#9a9aa2","#6e6e78","#7cd67c","#e0d0c0","#2a2a30","#f2f2f4")),
 "lion":      _sp(bw=2.0,bh=1.7,bl=3.3,leg=1.7,lw=.5,neck=.6,nang=25,head=(1.1,1.0,1.1),snout=(.55,.45,.5),ears="round",
                  ear=(.4,.4),tail="tuft",extras=("mane",),pal=("#d9a441","#b5802a","#e8c547","#6b3f1d","#3b2410","#f0d9a8")),
 "tiger":     _sp(bw=1.9,bh=1.5,bl=3.3,leg=1.5,lw=.48,neck=.6,nang=28,head=(1.05,.95,1.05),snout=(.55,.45,.5),ears="round",
                  ear=(.38,.38),tail="hang",extras=("stripes",),pal=("#e08a2c","#b8661a","#e8c547","#f5e6c8","#1f140c","#fbf3e2")),
 "panther":   _sp(bw=1.8,bh=1.4,bl=3.2,leg=1.5,lw=.44,neck=.6,nang=28,head=(1.0,.9,1.05),snout=(.5,.4,.5),ears="round",
                  ear=(.35,.35),tail="long_up",pal=("#1c1c24","#121218","#ffd166","#2e2e3a","#09090c","#343442")),
 "cheetah":   _sp(bw=1.6,bh=1.3,bl=3.2,leg=1.8,lw=.34,neck=.7,nang=30,head=(.9,.85,.95),snout=(.45,.4,.45),ears="round",
                  ear=(.32,.32),tail="long_up",extras=("spots",),pal=("#e6b85c","#c49238","#e8c547","#2b1d12","#1c120a","#fbf2dc")),
 "hyena":     _sp(bw=1.9,bh=1.5,bl=2.8,leg=1.5,lw=.4,neck=.7,nang=25,head=(1.0,.95,1.1),snout=(.55,.5,.6),ears="round",
                  ear=(.42,.48),tail="bushy",extras=("spots","hmane"),pal=("#a88b68","#7a6248","#e8c547","#3b2a1c","#241a10","#d8c3a8")),
 "horse":     _sp(bw=1.8,bh=1.6,bl=3.6,leg=2.8,lw=.34,neck=2.0,nang=35,head=(.8,.9,1.5),snout=(.7,.6,.6),ears="point",
                  ear=(.22,.45),tail="hang",extras=("hmane",),snoutc="B",pal=("#8a5a35","#5e3b1f","#e8c547","#2a1a10","#1f130a","#e9d9c0")),
 "unicorn":   _sp(bw=1.8,bh=1.6,bl=3.4,leg=2.7,lw=.32,neck=2.0,nang=35,head=(.8,.9,1.4),snout=(.7,.6,.6),ears="point",
                  ear=(.22,.45),horns="straight",tail="hang",extras=("hmane",),
                  pal=("#f7f3fb","#d9c9f0","#ff8fc8","#ffd86b","#8b6bbf","#ffffff")),
 "pegasus":   _sp(bw=1.8,bh=1.6,bl=3.4,leg=2.7,lw=.32,neck=2.0,nang=35,head=(.8,.9,1.4),snout=(.7,.6,.6),ears="point",
                  ear=(.22,.45),tail="hang",extras=("hmane","quad_wings"),
                  pal=("#f2f6fc","#cfe0f5","#ffd166","#ffffff","#6c8ebf","#ffffff")),
 "zebra":     _sp(bw=1.8,bh=1.6,bl=3.4,leg=2.5,lw=.34,neck=1.8,nang=35,head=(.8,.9,1.4),snout=(.7,.6,.55),ears="point",
                  ear=(.25,.45),tail="tuft",extras=("hmane","stripes"),snoutc="D",
                  pal=("#f2f2f2","#d9d9d9","#e8c547","#222222","#141414","#ffffff")),
 "donkey":    _sp(bh=1.4,bl=3.0,leg=1.8,lw=.34,neck=1.0,nang=35,head=(.85,.95,1.3),snout=(.65,.55,.55),ears="long",
                  ear=(.3,1.1),tail="tuft",pal=("#8b8f96","#5f6368","#e8c547","#cfd3d8","#2b2d30","#f0f0f0")),
 "cow":       _sp(bw=2.1,bh=1.7,bl=3.3,leg=1.5,lw=.46,neck=.7,nang=25,head=(1.0,1.0,1.1),snout=(.7,.5,.4),ears="side",
                  ear=(.5,.5),horns="bull",tail="tuft",extras=("spots","udder"),
                  pal=("#f4f1ea","#d9d4c8","#e8c547","#e8dcc0","#1f1f1f","#f5b8c4")),
 "bison":     _sp(bw=2.5,bh=2.1,bl=3.5,leg=1.5,lw=.55,neck=.6,nang=15,head=(1.3,1.3,1.2),snout=(.7,.5,.4),ears="side",
                  ear=(.45,.45),horns="bull",tail="tuft",extras=("hump","beard"),
                  pal=("#5a3b22","#3d2614","#e8c547","#d8ccb8","#1f130a","#7a5435")),
 "pig":       _sp(bw=2.1,bh=1.7,bl=3.0,leg=.9,lw=.5,neck=.5,nang=20,head=(1.1,1.0,1.0),snout=(.6,.5,.35),ears="floppy",
                  ear=(.45,.5),tail="curly",pal=("#f2a6b8","#e08aa0","#2b1d12","#f9c9d4","#3d2a30","#f9c9d4")),
 "boar":      _sp(bw=2.2,bh=1.8,bl=3.1,leg=1.0,lw=.5,neck=.5,nang=18,head=(1.15,1.05,1.1),snout=(.6,.5,.4),ears="point",
                  ear=(.4,.45),tail="short",extras=("tusks","hmane"),pal=("#5c4332","#3f2d20","#e8c547","#efe6d5","#241911","#806049")),
 "deer":      _sp(bw=1.7,bh=1.5,bl=3.0,leg=2.5,lw=.3,neck=1.6,nang=30,head=(.8,.85,1.2),snout=(.55,.5,.55),ears="point",
                  ear=(.3,.6),horns="antlers",tail="short",pal=("#b07a45","#8b5c2e","#e8c547","#e2d2b0","#2b1a0e","#f3e7d0")),
 "moose":     _sp(bw=2.2,bh=1.9,bl=3.5,leg=2.7,lw=.42,neck=1.2,nang=22,head=(1.0,1.1,1.5),snout=(.75,.65,.7),ears="side",
                  ear=(.45,.6),horns="antlers",tail="short",extras=("beard","hump"),
                  pal=("#5e4028","#422c1b","#e8c547","#d9c39e","#21150c","#825c3c")),
 "rabbit":    _sp(bw=1.7,bh=1.5,bl=2.2,leg=.9,lw=.4,neck=.4,nang=20,head=(1.1,1.0,1.1),snout=(.45,.35,.3),ears="long",
                  ear=(.28,1.5),tail="ball",pal=("#e9e2d6","#cfc4b2","#ff9fb3","#f7f1e8","#3a2e24","#ffffff")),
 "squirrel":  _sp(size=.8,bw=1.5,bh=1.3,bl=2.1,leg=.85,lw=.32,neck=.4,nang=22,head=(.95,.9,.95),snout=(.45,.35,.35),ears="point",
                  ear=(.28,.45),tail="bushy",pal=("#b8622a","#8f4719","#2b1d12","#e6c8a8","#241409","#f2dec4")),
 "beaver":    _sp(size=.85,bw=2.0,bh=1.4,bl=2.5,leg=.75,lw=.4,neck=.35,nang=15,head=(1.05,.95,1.0),snout=(.5,.4,.35),ears="round",
                  ear=(.25,.25),tail="croc",pal=("#78492a","#54311a","#2b1d12","#f5efe6","#2e1c10","#b0784f")),
 "otter":     _sp(size=.85,bw=1.5,bh=1.1,bl=3.2,leg=.7,lw=.35,neck=.6,nang=22,head=(.95,.85,1.0),snout=(.5,.38,.4),ears="round",
                  ear=(.22,.22),tail="croc",extras=("whiskers",),pal=("#6e4a30","#4f331f","#2b1d12","#d9c2a6","#1f130b","#e8d6be")),
 "badger":    _sp(size=.85,bw=2.0,bh=1.3,bl=2.7,leg=.8,lw=.42,neck=.45,nang=15,head=(.95,.85,1.15),snout=(.5,.4,.5),ears="round",
                  ear=(.28,.28),tail="short",extras=("patches",),pal=("#595d63","#222428","#e8c547","#f0f0f0","#141518","#ffffff")),
 "skunk":     _sp(size=.8,bw=1.7,bh=1.3,bl=2.5,leg=.8,lw=.35,neck=.45,nang=20,head=(.9,.85,1.0),snout=(.45,.35,.45),ears="round",
                  ear=(.26,.26),tail="bushy",extras=("stripes",),pal=("#1c1c20","#121216","#e8c547","#ffffff","#ffffff","#f5f5f7")),
 "raccoon":   _sp(size=.85,bw=1.8,bh=1.4,bl=2.5,leg=.85,lw=.36,neck=.45,nang=20,head=(1.0,.9,1.0),snout=(.45,.35,.45),ears="point",
                  ear=(.3,.4),tail="bushy",extras=("patches","stripes"),pal=("#7d8087","#232428","#e8c547","#d2d5dc","#17181c","#f0f2f5")),
 "hedgehog":  _sp(size=.75,bw=1.9,bh=1.5,bl=2.2,leg=.6,lw=.32,neck=.3,nang=10,head=(.95,.85,1.0),snout=(.45,.35,.5),ears="round",
                  ear=(.25,.25),tail="short",extras=("plates",),pal=("#735338","#4f3723","#2b1d12","#d9bd9c","#24180e","#f2dec4")),
 "bear":      _sp(bw=2.4,bh=2.2,bl=3.2,leg=1.3,lw=.75,neck=.5,nang=15,head=(1.4,1.3,1.3),snout=(.5,.4,.5),ears="round",
                  ear=(.4,.4),tail="short",pal=("#6b4423","#4a2f1b","#e8c547","#d9c2a0","#1c120a","#c9a47a")),
 "polarbear": _sp(bw=2.5,bh=2.2,bl=3.4,leg=1.4,lw=.78,neck=.6,nang=15,head=(1.35,1.25,1.35),snout=(.5,.42,.55),ears="round",
                  ear=(.36,.36),tail="short",pal=("#f2f5f8","#dce3ea","#22262b","#ffffff","#1a1d21","#ffffff")),
 "panda":     _sp(bw=2.4,bh=2.2,bl=3.0,leg=1.3,lw=.75,neck=.5,nang=15,head=(1.4,1.3,1.3),snout=(.5,.4,.5),ears="round",
                  ear=(.4,.4),tail="short",extras=("patches",),pal=("#f4f4f4","#1c1c1c","#e8c547","#cfcfcf","#111111","#ffffff")),
 "koala":     _sp(size=.8,bw=1.8,bh=1.6,bl=2.1,leg=.9,lw=.42,neck=.35,nang=15,head=(1.25,1.15,1.05),snout=(.4,.45,.35),ears="round",
                  ear=(.65,.65),tail="ball",snoutc="D",pal=("#8f96a0","#686f78","#22262b","#e6e9ed","#232629","#f4f6f8")),
 "kangaroo":  _sp(bw=1.8,bh=1.7,bl=2.6,leg=2.2,lw=.48,neck=1.2,nang=45,head=(.85,.9,1.15),snout=(.55,.45,.55),ears="long",
                  ear=(.3,.95),tail="croc",pal=("#c28246","#965f2d","#e8c547","#e6caa8","#2e1c0c","#f2dfc7")),
 "capybara":  _sp(bw=2.1,bh=1.6,bl=2.9,leg=.95,lw=.45,neck=.45,nang=18,head=(1.1,1.1,1.3),snout=(.7,.6,.45),ears="round",
                  ear=(.25,.25),tail="short",snoutc="B",pal=("#9c6b43","#704a2b","#261a10","#b8865c","#291a0e","#b8865c")),
 "platypus":  _sp(size=.8,bw=1.9,bh=1.0,bl=2.8,leg=.6,lw=.4,neck=.35,nang=10,head=(1.0,.8,1.0),snout=(.85,.25,.9),ears="none",
                  tail="croc",snoutc="D",pal=("#6e4b2e","#4a311d","#e8c547","#333942","#262b33","#3b424d")),
 "armadillo": _sp(size=.85,bw=2.1,bh=1.5,bl=2.7,leg=.75,lw=.38,neck=.4,nang=15,head=(.85,.8,1.1),snout=(.45,.35,.6),ears="point",
                  ear=(.28,.48),tail="croc",extras=("stripes","shell_back"),pal=("#9e8c78","#756554","#2b221a","#bfb09e","#382e24","#dcd0c0")),
 "elephant":  _sp(bw=3.0,bh=2.8,bl=4.0,leg=2.4,lw=1.0,neck=.5,nang=10,head=(1.8,1.9,1.5),snout=(.35,.35,.2),ears="flap",
                  ear=(1.4,1.8),tail="short",extras=("trunk","tusks"),snoutc="A",
                  pal=("#8e949c","#757b83","#e8c547","#f2ecdc","#3b3f45","#b8bec6")),
 "mammoth":   _sp(bw=3.1,bh=2.9,bl=4.1,leg=2.4,lw=1.05,neck=.55,nang=12,head=(1.85,1.95,1.55),snout=(.35,.35,.2),ears="flap",
                  ear=(1.0,1.3),tail="short",extras=("trunk","tusks","wool","hump"),snoutc="A",
                  pal=("#6b4423","#4d2f16","#e8c547","#f5efe0","#29180a","#8c5c32")),
 "rhino":     _sp(bw=2.7,bh=2.2,bl=3.8,leg=1.6,lw=.8,neck=.6,nang=15,head=(1.35,1.35,1.5),snout=(.75,.65,.6),ears="point",
                  ear=(.3,.45),horns="rhino",tail="short",snoutc="A",
                  pal=("#7d828a","#5f646b","#e8c547","#e8e2d5","#2e3136","#9ea4ad")),
 "hippo":     _sp(bw=2.8,bh=2.1,bl=3.7,leg=1.2,lw=.78,neck=.5,nang=12,head=(1.45,1.35,1.4),snout=(.95,.75,.85),ears="round",
                  ear=(.28,.28),tail="short",snoutc="B",
                  pal=("#7c6d7a","#9e8598","#e8c547","#f2eadf","#382f37","#b599ae")),
 "giraffe":   _sp(bw=1.9,bh=1.7,bl=3.0,leg=3.8,lw=.38,neck=3.8,nang=12,head=(.9,.9,1.3),snout=(.6,.5,.6),ears="point",
                  ear=(.3,.45),horns="knobs",tail="tuft",extras=("spots",),
                  pal=("#e0b04a","#c98f2e","#e8c547","#8a5a1a","#6b3f12","#f6e3b0")),
 "camel":     _sp(bw=1.9,bh=1.7,bl=3.4,leg=2.6,lw=.4,neck=2.0,nang=35,head=(.9,.9,1.2),snout=(.6,.5,.6),ears="round",
                  ear=(.25,.25),tail="short",extras=("hump",),pal=("#c9a06a","#a47c48","#e8c547","#e0c9a0","#3b2a18","#ecd9b8")),
 "llama":     _sp(bh=1.6,bl=2.8,leg=2.2,lw=.34,neck=2.2,nang=22,head=(.8,.9,1.0),snout=(.6,.5,.5),ears="point",
                  ear=(.25,.6),tail="short",extras=("wool",),pal=("#efe6d6","#c9bba4","#e8c547","#a58f6e","#4a3b2a","#ffffff")),
 "cerberus":  _sp(bw=2.2,bh=1.6,bl=3.1,leg=1.6,lw=.45,neck=.8,nang=30,head=(.95,.9,1.05),snout=(.55,.45,.75),ears="point",
                  ear=(.32,.55),tail="serp",extras=("three_heads","collar"),
                  pal=("#262228","#171419","#ff2d55","#a61c3c","#0d0b0e","#453d4a")),
 "griffin":   _sp(bw=2.0,bh=1.6,bl=3.2,leg=1.7,lw=.45,neck=.9,nang=32,head=(1.05,1.0,1.15),snout=(.55,.5,.7),ears="point",
                  ear=(.3,.55),tail="tuft",extras=("quad_wings","mane"),snoutc="C",
                  pal=("#c99438","#f2efe9","#f5b82e","#8f6319","#33240c","#ffffff")),
 "dino":      _sp(bh=1.9,bl=3.6,leg=1.6,lw=.65,neck=.9,nang=25,head=(1.3,1.2,2.0),snout=(.9,.6,.5),ears="none",
                  tail="croc",extras=("plates",),pal=("#5aa05a","#3f7a3f","#f2c94c","#e7d9a6","#243b24","#b9dca0")),
 "trex":      _sp(bw=2.1,bh=2.2,bl=3.4,leg=2.1,lw=.7,neck=1.1,nang=38,head=(1.5,1.4,2.1),snout=(.85,.65,.65),ears="none",
                  tail="croc",extras=("dino_jaw",),snoutc="A",pal=("#4e8c4a","#386635","#f2c94c","#f5efe0","#1f381d","#9ec99a")),
 "triceratops":_sp(bw=2.5,bh=2.0,bl=3.6,leg=1.5,lw=.7,neck=.6,nang=12,head=(1.4,1.3,1.6),snout=(.65,.55,.65),ears="none",
                  horns="tri",tail="croc",extras=("frill_crest",),pal=("#6c8f4e","#4e6937","#f2c94c","#efe5cc","#29381c","#b8cf9e")),
 "brachiosaurus":_sp(bw=2.5,bh=2.2,bl=3.8,leg=3.2,lw=.75,neck=4.0,nang=18,head=(1.0,1.0,1.3),snout=(.65,.5,.55),ears="none",
                  tail="croc",pal=("#5d9970","#427051","#f2c94c","#c6e0ce","#213b29","#a3ccb0")),
 "croc":      _sp(bh=.9,bl=3.8,leg=.6,lw=.5,neck=.3,nang=10,head=(1.2,.8,1.8),snout=(.9,.6,.6),ears="none",
                  tail="croc",extras=("plates",),pal=("#4f8f4a","#3a6e36","#f2c94c","#cfd8a0","#1e3a1c","#d8e3a8")),
 "mouse":     _sp(size=.7,bw=1.8,bh=1.3,bl=2.4,leg=.8,lw=.35,neck=.3,nang=20,head=(1.1,1.0,1.2),snout=(.4,.35,.4),
                  ears="round",ear=(.8,.8),tail="long_thin",pal=("#a9a9b0","#f4b9c2","#2b2b30","#85858c","#2b2b30","#ece9e4")),
 "beast":     _sp(pal=None,horns=None,ears="point",tail="short"),
}

SPECIES_KEYS = {
 "goat":["goat","billy","nanny","ibex"],"sheep":["sheep","lamb","ram","ewe"],
 "dog":["dog","puppy","pup","hound","doggo","husky","corgi","pug","bulldog","poodle","shiba","dalmatian","retriever","terrier"],
 "wolf":["wolf","werewolf","coyote","jackal","direwolf"],
 "fox":["fox","vixen","kitsune"],"cat":["cat","kitten","kitty","lynx","feline","tabby","bobcat"],
 "lion":["lion","lioness","simba"],"tiger":["tiger","tigress","sabertooth"],
 "panther":["panther","jaguar","cougar","puma"],"cheetah":["cheetah","leopard","ocelot"],
 "hyena":["hyena","gnoll"],"unicorn":["unicorn","alicorn"],"pegasus":["pegasus"],
 "horse":["horse","pony","stallion","mare","foal","mustang","steed"],
 "zebra":["zebra"],"donkey":["donkey","mule","burro"],
 "cow":["cow","cattle","bull","ox","brahman","calf"],"bison":["bison","buffalo","yak","wisent"],
 "pig":["pig","hog","piglet","swine","sow"],"boar":["boar","warthog","razorback"],
 "deer":["deer","reindeer","stag","antelope","gazelle","fawn","buck","impala"],
 "moose":["moose","elk","caribou"],"rabbit":["rabbit","bunny","hare"],
 "squirrel":["squirrel","chipmunk"],"beaver":["beaver","marmot","groundhog","woodchuck"],
 "otter":["otter","weasel","ferret","mink","stoat","mongoose"],
 "badger":["badger","wolverine","honeybadger"],"skunk":["skunk"],
 "raccoon":["raccoon","tanuki","redpanda"],"hedgehog":["hedgehog","porcupine","echidna"],
 "panda":["panda"],"polarbear":["polarbear"],"bear":["bear","grizzly","ursine","kodak","teddy"],
 "koala":["koala","wombat","sloth"],"kangaroo":["kangaroo","wallaby"],
 "capybara":["capybara","guineapig"],"platypus":["platypus"],
 "armadillo":["armadillo","pangolin","anteater","tapir"],
 "elephant":["elephant"],"mammoth":["mammoth","mastodon"],
 "rhino":["rhino","rhinoceros"],"hippo":["hippo","hippopotamus"],
 "giraffe":["giraffe","okapi"],"camel":["camel","dromedary"],"llama":["llama","alpaca"],
 "cerberus":["cerberus","hellhound"],"griffin":["griffin","gryphon","hippogriff"],
 "trex":["trex","tyrannosaurus","raptor","velociraptor","allosaurus","carnotaurus","spinosaurus"],
 "triceratops":["triceratops","ankylosaurus","styracosaurs"],
 "brachiosaurus":["brachiosaurus","diplodocus","brontosaurus","sauropod","apatosaurus"],
 "dino":["dinosaur","dino","stegosaurus","iguanodon","pachycephalosaurus"],
 "croc":["crocodile","croc","alligator","lizard","gecko","iguana","komodo","chameleon","salamander","newt","frog","toad"],
 "mouse":["mouse","rat","hamster","gerbil","chinchilla","vole"]}

ROOTS = {
 "humanoid": ["human","humans","man","woman","boy","girl","guy","dude","person","people","hero",
    "villain","wizard","mage","sorcerer","warlock","witch","knight","paladin","crusader","templar",
    "samurai","shogun","ronin","viking","barbarian","berserker","spartan","gladiator","soldier",
    "marine","commando","sniper_man","ninja","shinobi","assassin","pirate","buccaneer","captain",
    "doctor","surgeon","nurse","medic","teacher","professor","scientist","driver","racer",
    "engineer","mechanic","miner","chef","cook","baker","pilot","aviator","astronaut","cosmonaut",
    "farmer","lumberjack","builder","worker","artist","painter","musician","rockstar","dj",
    "athlete","runner","boxer","karate","monk","sensei","fighter","brawler","guard","warden",
    "police_man","cop","detective","sheriff","cowboy","outlaw","thief","rogue","bandit","burglar",
    "robot","cyborg","android","droid","automaton","alien","martian","anime","character","avatar",
    "kid","child","baby_human","king","queen","prince","princess","emperor","pharaoh","clown",
    "jester","mime","santa","elf","leprechaun","dwarf","orc","goblin","troll","ogre","vampire",
    "dracula","zombie_man","mummy_man","angel_man","Cupid","superhero","butler","maid","priest","biker"],
 "mech": ["mech","mecha","gundam","battlemech","walker","exosuit","dreadnought","titan_mech",
    "warbot","sentinel","jaeger","megazord","transformer"],
 "octopus": ["octopus","squid","kraken","cephalopod","ink","cuttlefish","nautilus"],
 "serpent": ["snake","serpent","dragon","wyrm","eel","viper","wyvern","cobra","python","anaconda",
    "worm","caterpillar","leviathan","lindworm","basilisk","centipede","millipede","leech"],
 "fish": ["fish","shark","koi","bass","piranha","manta","goldfish","whale","dolphin","tuna","salmon",
    "trout","carp","clownfish","swordfish","stingray","orca","narwhal","beluga","manatee","seal",
    "walrus","anglerfish","pufferfish","barracuda","seahorse","catfish","eel_fish","megalodon"],
 "bird": ["bird","eagle","phoenix","falcon","owl","raven","parrot","hawk","duck","chicken","hen",
    "rooster","penguin","swan","crow","pigeon","seagull","flamingo","toucan","ostrich","peacock",
    "goose","pelican","stork","crane","heron","hummingbird","woodpecker","kiwi","turkey","vulture",
    "condor","albatross","canary","robin","bluejay","cardinal","sparrow","cockatoo","macaw","dodo","pterodactyl"],
 "crab": ["crab","lobster","scorpion","shrimp","crustacean","prawn","crayfish","crawfish","hermitcrab","horseshoecrab"],
 "spider": ["spider","arachnid","tarantula","weaver","ant","bug","insect","tick","mite","scarab","stagbeetle","cockroach","cricket","grasshopper","prayingmantis","mantis"],
 "bug_fly": ["butterfly","moth","dragonfly","bee","bumblebee","wasp","hornet","ladybug","firefly","mosquito","fly","cicada","beetle"],
 "golem": ["golem","titan","colossus","elemental","construct","gargoyle","atavism","regi","monolith_guardian"],
 "turtle": ["turtle","tortoise","snail","slug","terrapin","sea_turtle","ankylo"],
 "jelly": ["jelly","jellyfish","medusa","blob","slime","amoeba","metroid","spore"],
 "monster": ["beholder","cyclops","eyeball","ghost","phantom","wraith","specter","spirit","poltergeist",
    "reaper","grimreaper","skeleton","skull_walker","lich","necromancer","demon","devil","fiend","imp",
    "balrog","treant","ent","dryad","hydra","yeti","bigfoot","sasquatch","wendigo","chupacabra","mimic"],
 "car": ["car","vehicle","auto","automobile","sedan","coupe","truck","semi","lorry","van","minivan",
    "taxi","cab","racecar","f1","formula","nascar","bus","schoolbus","coach","police","copcar","cruiser",
    "jeep","suv","humvee","hummer","limo","limousine","ambulance","firetruck","fireengine","pickup",
    "supercar","hypercar","sports_car","hatchback","wagon","buggy","dune_buggy","beetle_car","kart",
    "gokart","tractor","bulldozer","excavator","forklift","dump_truck","garbage_truck","icecream_truck",
    "monster_truck","cybertruck","rv","camper","carriage","chariot","golfcart","snowplow"],
 "train": ["train","locomotive","steamtrain","bullettrain","shinkansen","subway","metro","tram",
    "trolley","monorail","boxcar","caboose","railcar","express"],
 "bike": ["bike","motorcycle","scooter","bicycle","motorbike","moped","chopper_bike","dirtbike",
    "tricycle","unicycle","hoverbike","segway","skateboard","longboard","rollerblade","quadbike","atv","snowmobile","jetski"],
 "boat": ["boat","ship","yacht","canoe","kayak","submarine","sub","raft","sailboat","ferry","cruiseship",
    "battleship","destroyer","frigate","carrier","pirateship","galleon","longship","speedboat","tugboat","gondola","houseboat","barge"],
 "plane": ["plane","airplane","jet","aircraft","glider","rocket","spaceship","starship","shuttle",
    "biplane","bomber","fighterjet","airliner","concorde","seaplane","blimp","zeppelin","airship","drone_wing","xwing","tie_fighter"],
 "heli": ["helicopter","heli","chopper","apache","chinook","gyrocopter","quadcopter","drone","ornithopter"],
 "tank": ["tank","warcraft","panzer","abrams","apc","artillery","howitzer","halftrack","catapult","trebuchet","ballista"],
 "space": ["ufo","saucer","flyingsaucer","satellite","rover","lander","lunarlander","probe","spacestation",
    "iss","telescope","hubble","portal","stargate","obelisk","beacon","pylon","warp_gate"],
 "quadruped": sum(SPECIES_KEYS.values(),[])+["animal","beast","creature","pet","mammal","quadruped","critter","mount"],
 "building": ["house","home","cabin","hut","shack","cottage","bungalow","barn","silo","stable","shop",
    "store","market","bakery_shop","cafe","restaurant","diner","hotel","motel","inn","tavern","mansion",
    "villa","palace","castle","fort","fortress","citadel","keep","tower","watchtower","belltower",
    "lighthouse","church","cathedral","chapel","temple","mosque","synagogue","pagoda","dojo","shrine_bldg",
    "skyscraper","office","apartment","hospital","clinic","school","library","museum","bank","prison",
    "jail","factory","warehouse","hangar","garage","gas_station","firehouse","police_station","igloo","tent","teepee","yurt","greenhouse","building"],
 "structure": ["bridge","arch","gate","gateway","torii","fountain","well","wishingwell","windmill",
    "shrine","altar","monument","statue","pedestal","pyramid","sphinx","gazebo","pavilion","pergola",
    "gravestone","tombstone","crypt","mausoleum","campfire","bonfire","streetlamp","lamppost",
    "trafficlight","hydrant","firehydrant","mailbox","bench_park","fence","wall","barricade","watchpost","gallows","stage","totem","totem_pole","ferriswheel","carousel_ride"],
 "tree": ["tree","pine","spruce","fir","cedar","redwood","oak","maple","birch","willow","bonsai","palm",
    "coconut_tree","cactus","saguaro","succulent","bush","shrub","hedge","plant","fern","vine","bamboo",
    "flower","rose","sunflower","tulip","daisy","lotus","lily","orchid","dandelion","mushroom","toadstool","fungi","coral","seaweed","kelp","pumpkin_plant"],
 "weapon": ["sword","katana","scimitar","saber","rapier","cutlass","broadsword","longsword","greatsword",
    "claymore","excalibur","gladius","machete","blade","dagger","dirk","kris","kunai","stiletto","knife",
    "axe","battleaxe","hatchet","tomahawk","halberd","glaive","bardiche","poleaxe","scythe","sickle",
    "spear","lance","pike","javelin","trident","harpoon","naginata","hammer","warhammer","mallet","maul",
    "mace","flail","morningstar","club","bat","baton","crowbar","staff","quarterstaff","bo_staff",
    "scepter","crozier","wand","rod","bow","longbow","shortbow","crossbow","slingshot","shield",
    "buckler","towershield","aegis","shuriken","chakram","boomerang","whip","nunchucks","claws_weapon"],
 "gun": ["gun","pistol","revolver","handgun","glock","deagle","rifle","assault_rifle","ak47","m16","carbine",
    "sniper","musket","flintlock","blunderbuss","shotgun","pump_shotgun","smg","uzi","mp5","minigun",
    "gatling","machinegun","lmg","blaster","raygun","lasergun","phaser","plasmagun","railgun","gauss",
    "bazooka","rpg","rocketlauncher","grenadelauncher","mortar","cannon","turret","sentry","flamethrower","freeze_ray","watergun","super_soaker","nerf","paintball_gun"],
 "furniture": ["chair","armchair","recliner","rockingchair","throne","stool","barstool","bench","sofa",
    "couch","loveseat","futon","table","diningtable","coffeetable","desk","workbench","counter","island",
    "bed","bunkbed","crib","hammock","bookshelf","bookcase","shelf","rack","cabinet","cupboard",
    "wardrobe","closet","dresser","nightstand","chest","treasurechest","coffer","safe","vault","trunk_box",
    "crate_box","barrel_wood"," casket","coffin","lamp","floorlamp","desklamp","chandelier","candelabra",
    "lantern_prop","torch","fireplace","hearth","stove_wood","anvil","forge","cauldron","spinningwheel","loom","mirror_stand","grandfatherclock","easel","aquarium","fishtank","birdcage","trashcan","bin","dumpster"],
 "food": ["food","burger","hamburger","cheeseburger","slider","pizza","slice","cake","birthdaycake",
    "weddingcake","cupcake","muffin","donut","doughnut","bagel","croissant","bread","loaf","toast",
    "sandwich","sub_food","panini","hotdog","corndog","Sausage","taco","burrito","nacho","quesadilla",
    "sushi","nigiri","maki","onigiri","ramen","noodles","soup","stew","dumpling","bento","steak","meat",
    "drumstick","chickenleg","bacon","egg","omelet","cheese","pie","tart","waffle","pancake","cookie",
    "biscuit","brownie","chocolate_bar","candy","lollipop","cane","icecream","sundae","cone","popsicle",
    "smoothie","milkshake","apple","banana","orange_fruit","lemon","lime_fruit","strawberry","cherry",
    "grape","watermelon","melon","pineapple","mango","peach_fruit","pear","coconut","avocado","tomato",
    "pumpkin","jackolantern","carrot","corn","broccoli","eggplant","mushroom_food","potato","fries",
    "popcorn","pretzel","potion","elixir","flask","vial","bottle","soda","can","juice","milk","coffee",
    "tea","mug","cup","teacup","teapot","goblet","chalice","wineglass","jar","honey"],
 "instrument": ["instrument","guitar","electricguitar","acoustic","bassguitar","ukulele","banjo","mandolin",
    "lute","sitar","violin","fiddle","viola","cello","doublebass","harp","lyre","piano","grandpiano",
    "keyboard_inst","synthesizer","synth","organ","accordion","harmonica","drum","drums","drumkit",
    "snare","bongo","conga","timpani","gong","xylophone","marimba","tambourine","maraca","bell_inst",
    "triangle_inst","saxophone","sax","trumpet","trombone","tuba","frenchhorn","bugle","flute","piccolo",
    "clarinet","oboe","bassoon","recorder","bagpipes","didgeridoo","ocarina","panflute","microphone",
    "mic","boombox","speaker","amp","amplifier","turntable","djdeck","jukebox","gramophone","phonograph","metronome"],
 "appliance": ["computer","pc","desktop","mac","imac","laptop","notebook","monitor","screen","display",
    "keyboard_pc","mouse_pc","printer","scanner","router","server","mainframe","phone","smartphone",
    "iphone","cellphone","telephone","payphone","tablet","ipad","tv","television","hdtv","crt","radio",
    "walkietalkie","camera","dslr","camcorder","webcam","projector","console","playstation","xbox",
    "nintendo","switch_console","gameboy","arcade","arcadecabinet","pinball","vr","headset","headphones",
    "earbuds","smartwatch","clock","alarmclock","digitalclock","watch","calculator","typewriter","atm",
    "vending","vendingmachine","cashregister","fridge","refrigerator","freezer","microwave","oven",
    "stove","toaster","blender","mixer","coffeemaker","espresso","kettle","dishwasher","washer",
    "washingmachine","dryer","vacuum","roomba","iron","fan","heater","airconditioner","ac","radiator","battery","generator","solar_panel"],
 "collectible": ["trophy","cup_trophy","award","oscar","medal","medallion","badge","coin","token","doubloon",
    "gem","gemstone","diamond","ruby_gem","emerald_gem","sapphire_gem","amethyst_gem","topaz","crystal",
    "shard","orb","prism","cube","tesseract","heart","star","moon","crescent","sun_emblem","lightning",
    "bolt","snowflake","skull","bone","ribcage","fossil","key","skeletonkey","keycard","padlock","lock",
    "bomb","timebomb","dynamite","tnt","grenade","mine","firework","scroll","parchment","map","book",
    "spellbook","grimoire","diary","notebook_item","compass","pocketwatch","hourglass","feather","quill",
    "inkwell"," magnifyingglass","Spyglass","binoculars","megaphone","umbrella","parasol","cane_item",
    "pokeball","dice","d20","chesspiece","pawn","rook","knight_chess","king_chess","queen_chess","gift",
    "present","ribbon","balloon","kite","yo_yo","top_toy","teddybear","doll","actionfigure","rubikscube",
    "puzzle","backpack_item","briefcase","suitcase","luggage","purse","handbag","wallet","crown_item",
    "tiara","halo_item","ring_item","necklace","amulet","talisman","anker","anchor","lifebuoy","bell",
    "Horseshoe","magnet","gear","cog","wrench","screwdriver","pliers","saw","pickaxe","shovel","spade",
    "hoe","rake","pitchfork","wateringcan","bucket","pail","broom","mop"," plunger"," paintbrush","roller","scissors","syringe","pill","bandage","firstaid"]}

ARCHES = list(ROOTS)

# Multi-word phrase overrides mapped before token splitting
PHRASE_MAP = {
 "monster truck": ("car", {"carbody":"pickup","prop":{"wheels":1.65,"lift":1.45}}),
 "fire truck": ("car", {"carbody":"van","add":"lightbar","theme":"race"}),
 "police car": ("car", {"carbody":"sedan","add":"lightbar","theme":"navy"}),
 "sports car": ("car", {"carbody":"sport","add":"sp_spoiler"}),
 "race car": ("car", {"carbody":"formula","add":"sp_spoiler"}),
 "formula 1": ("car", {"carbody":"formula","add":"sp_spoiler"}),
 "f1 car": ("car", {"carbody":"formula","add":"sp_spoiler"}),
 "ice cream truck": ("car", {"carbody":"van","theme":"pastel"}),
 "school bus": ("car", {"carbody":"van","theme":"warn"}),
 "dump truck": ("car", {"carbody":"pickup","prop":{"wheels":1.35}}),
 "dune buggy": ("car", {"carbody":"buggy","prop":{"wheels":1.3,"lift":1.2}}),
 "steam train": ("train", {"keyword":"steamtrain"}),
 "bullet train": ("train", {"keyword":"bullettrain"}),
 "pirate ship": ("boat", {"keyword":"pirateship"}),
 "cruise ship": ("boat", {"keyword":"cruiseship"}),
 "aircraft carrier": ("boat", {"keyword":"carrier"}),
 "space shuttle": ("plane", {"keyword":"shuttle"}),
 "fighter jet": ("plane", {"keyword":"fighterjet"}),
 "flying saucer": ("space", {"keyword":"ufo","float":True}),
 "space station": ("space", {"keyword":"spacestation","float":True}),
 "lunar lander": ("space", {"keyword":"lander"}),
 "treasure chest": ("furniture", {"keyword":"treasurechest"}),
 "grandfather clock": ("furniture", {"keyword":"grandfatherclock"}),
 "rocking chair": ("furniture", {"keyword":"rockingchair"}),
 "dining table": ("furniture", {"keyword":"diningtable"}),
 "coffee table": ("furniture", {"keyword":"coffeetable"}),
 "bunk bed": ("furniture", {"keyword":"bunkbed"}),
 "arcade cabinet": ("appliance", {"keyword":"arcade"}),
 "arcade machine": ("appliance", {"keyword":"arcade"}),
 "vending machine": ("appliance", {"keyword":"vending"}),
 "washing machine": ("appliance", {"keyword":"washer"}),
 "gaming pc": ("appliance", {"keyword":"pc","theme":"neon"}),
 "smart phone": ("appliance", {"keyword":"phone"}),
 "cell phone": ("appliance", {"keyword":"phone"}),
 "electric guitar": ("instrument", {"keyword":"electricguitar"}),
 "acoustic guitar": ("instrument", {"keyword":"guitar"}),
 "grand piano": ("instrument", {"keyword":"grandpiano"}),
 "drum kit": ("instrument", {"keyword":"drumkit"}),
 "drum set": ("instrument", {"keyword":"drumkit"}),
 "ice cream": ("food", {"keyword":"icecream"}),
 "hot dog": ("food", {"keyword":"hotdog"}),
 "birthday cake": ("food", {"keyword":"birthdaycake"}),
 "coffee mug": ("food", {"keyword":"mug"}),
 "ray gun": ("gun", {"keyword":"raygun","theme":"neon"}),
 "laser gun": ("gun", {"keyword":"lasergun","theme":"neon"}),
 "machine gun": ("gun", {"keyword":"minigun"}),
 "rocket launcher": ("gun", {"keyword":"rpg"}),
 "sniper rifle": ("gun", {"keyword":"sniper"}),
 "assault rifle": ("gun", {"keyword":"rifle"}),
 "water gun": ("gun", {"keyword":"watergun","theme":"sky"}),
 "battle axe": ("weapon", {"keyword":"battleaxe"}),
 "war hammer": ("weapon", {"keyword":"warhammer"}),
 "great sword": ("weapon", {"keyword":"greatsword"}),
 "tower shield": ("weapon", {"keyword":"towershield"}),
 "grim reaper": ("monster", {"keyword":"reaper","float":True,"theme":"dark","add":"eq_scythe"}),
 "santa claus": ("humanoid", {"keyword":"santa","theme":"race","add":"hg_santa"}),
 "polar bear": ("quadruped", {"species":"polarbear"}),
 "red panda": ("quadruped", {"species":"raccoon"}),
 "sea turtle": ("turtle", {"keyword":"turtle"}),
 "praying mantis": ("spider", {"keyword":"mantis"}),
 "palm tree": ("tree", {"keyword":"palm"}),
 "pine tree": ("tree", {"keyword":"pine"}),
 "oak tree": ("tree", {"keyword":"oak"}),
 "christmas tree": ("tree", {"keyword":"pine","theme":"gold"}),
 "wind mill": ("structure", {"keyword":"windmill"}),
 "torii gate": ("structure", {"keyword":"torii"}),
 "wishing well": ("structure", {"keyword":"well"}),
 "fire hydrant": ("structure", {"keyword":"hydrant"}),
 "traffic light": ("structure", {"keyword":"trafficlight"}),
 "street lamp": ("structure", {"keyword":"streetlamp"}),
 "totem pole": ("structure", {"keyword":"totem"}),
 "eiffel tower": ("building", {"keyword":"tower","sharp":1.6}),
 "teddy bear": ("collectible", {"keyword":"teddybear"}),
 "spell book": ("collectible", {"keyword":"spellbook"}),
 "pocket watch": ("collectible", {"keyword":"pocketwatch"}),
 "time bomb": ("collectible", {"keyword":"bomb"}),
 "first aid": ("collectible", {"keyword":"firstaid"}),
}

MODS = {
 "bald":{"rm":["hair"]},"muscular":{"prop":{"chest":1.35,"limbs":1.25}},
 "buff":{"prop":{"chest":1.4,"limbs":1.3}},"jacked":{"prop":{"chest":1.45,"limbs":1.35}},
 "fat":{"prop":{"chest":1.38,"limbs":1.18}},"chubby":{"prop":{"chest":1.28,"limbs":1.12}},
 "skinny":{"prop":{"chest":.78,"limbs":.78}},"slender":{"prop":{"chest":.75,"limbs":1.2}},
 "cute":{"prop":{"head":1.32,"limbs":.8},"sharp":-0.6,"scale":0.85,"eyes":1.45},
 "chibi":{"prop":{"head":1.55,"limbs":.7},"sharp":-0.7,"scale":0.78,"eyes":1.6},
 "kawaii":{"prop":{"head":1.4,"limbs":.78},"sharp":-0.65,"scale":0.82,"eyes":1.5},
 "tall":{"prop":{"limbs":1.3},"scale":1.15},"short":{"prop":{"limbs":.75},"scale":.85},
 "tiny":{"scale":0.6},"mini":{"scale":0.65},"micro":{"scale":0.5},
 "huge":{"scale":1.5},"giant":{"scale":1.65},"colossal":{"scale":1.8},"mega":{"scale":1.6},
 "big":{"scale":1.25},"small":{"scale":.75},"little":{"scale":.8},
 "baby":{"scale":.7,"prop":{"head":1.25},"eyes":1.35},
 "evil":{"sharp":0.65,"theme":"dark","add":"brow_evil","pose":-8},
 "angry":{"add":"brow_evil"},"fierce":{"add":"brow_evil","sharp":0.4},
 "royal":{"theme":"gold","add":"hg_crown"},"crown":{"add":"hg_crown"},"crowned":{"add":"hg_crown"},
 "king":{"theme":"gold","add":"hg_crown"},"queen":{"theme":"gold","add":"hg_crown"},
 "icy":{"theme":"ice","mat":"ice","add":"hg_crystal"},"frozen":{"theme":"ice","mat":"ice","add":"hg_crystal"},
 "frost":{"theme":"ice","mat":"ice"},"crystal":{"theme":"crystal","mat":"ice","add":"hg_crystal"},
 "crystalline":{"theme":"crystal","mat":"ice","add":"hg_crystal"},
 "fire":{"theme":"lava","mat":"lava"},"fiery":{"theme":"lava","mat":"lava"},
 "flaming":{"theme":"lava","mat":"lava"},"magma":{"theme":"lava","mat":"lava"},
 "lava":{"theme":"lava","mat":"lava"},"infernal":{"theme":"lava","mat":"lava","add":"h_curved"},
 "golden":{"theme":"gold","mat":"gold"},"silver":{"theme":"steel","mat":"metal"},
 "bronze":{"theme":"bronze","mat":"metal"},"copper":{"theme":"copper","mat":"metal"},
 "metallic":{"mat":"metal"},"steel":{"theme":"steel","mat":"metal"},"iron":{"theme":"steel","mat":"metal"},
 "chrome":{"theme":"steel","mat":"metal"},"diamond":{"theme":"ice","mat":"ice"},
 "emerald":{"theme":"emerald"},"ruby":{"theme":"ruby"},"obsidian":{"theme":"obsidian"},
 "wooden":{"theme":"wood"},"stone":{"theme":"stone"},"rock":{"theme":"stone"},
 "dark":{"theme":"dark"},"shadow":{"theme":"obsidian"},"cursed":{"theme":"cursed","add":"brow_evil"},
 "holy":{"theme":"holy","add":"hg_halo"},"blessed":{"theme":"holy","add":"hg_halo"},
 "angelic":{"theme":"holy","add":"w_big"},"demonic":{"theme":"lava","add":"h_curved"},
 "toxic":{"theme":"toxic"},"radioactive":{"theme":"toxic"},"poison":{"theme":"toxic"},
 "cyberpunk":{"theme":"neon","add":"hg_glasses"},"cyber":{"theme":"neon","mat":"metal"},
 "futuristic":{"theme":"sky","mat":"metal"},"scifi":{"theme":"sky","mat":"metal"},
 "steampunk":{"theme":"bronze","add":"hg_glasses"},"medieval":{"theme":"steel"},
 "ancient":{"theme":"gold"},"ghostly":{"theme":"ghost","float":True},
 "neon":{"theme":"neon"},"glowing":{"theme":"neon"},"pastel":{"theme":"pastel"},
 "floating":{"float":True,"pose":-6},"flying":{"float":True,"pose":-8},"hovering":{"float":True,"pose":-5},
 "sport":{"carbody":"sport","add":"sp_spoiler","theme":"race"},
 "supercar":{"carbody":"sport","add":"sp_spoiler","theme":"neon"},
 "formula":{"carbody":"formula","add":"sp_spoiler","theme":"race"},
 "f1":{"carbody":"formula","add":"sp_spoiler","theme":"race"},
 "offroad":{"prop":{"wheels":1.5,"lift":1.3}},
 "taxi":{"carbody":"sedan","add":"taxi_sign","theme":"gold"},
 "police":{"carbody":"sedan","add":"lightbar","theme":"navy"},
 "ambulance":{"carbody":"van","add":"lightbar","theme":"holy"},
 "firetruck":{"carbody":"van","add":"lightbar","theme":"race"},
 "van":{"carbody":"van"},"bus":{"carbody":"van"},"limo":{"carbody":"limo"},"limousine":{"carbody":"limo"},
 "buggy":{"carbody":"buggy"},"beetle":{"carbody":"buggy"},
 "monster":{"carbody":"pickup","prop":{"wheels":1.6,"lift":1.4}},
 "pickup":{"carbody":"pickup"},"tractor":{"carbody":"tractor"},
 "anime":{"eyes":1.5,"add":"hair_spiky"},
 "karate":{"add":"hg_headband","pose":-12},"monk":{"add":"hg_headband","rm":["hair"]},
 "wizard":{"add":"hg_pointy","theme":"mystic","eq":"eq_staff"},
 "mage":{"add":"hg_pointy","theme":"mystic","eq":"eq_wand"},
 "witch":{"add":"hg_pointy","theme":"dark","eq":"eq_wand"},
 "knight":{"add":"hg_helmet","theme":"steel","eq":"eq_sword","eq2":"eq_shield"},
 "paladin":{"add":"hg_helmet","theme":"gold","eq":"eq_hammer","eq2":"eq_shield"},
 "samurai":{"add":"hg_samurai","theme":"race","eq":"eq_sword"},
 "viking":{"add":"hg_viking","theme":"bronze","eq":"eq_axe","eq2":"eq_shield"},
 "spartan":{"add":"hg_helmet","theme":"bronze","eq":"eq_sword","eq2":"eq_shield"},
 "ninja":{"add":"hg_mask","theme":"dark","eq":"eq_sword"},
 "assassin":{"add":"hg_hood","theme":"dark","eq":"eq_sword"},
 "pirate":{"add":"hg_tricorn","theme":"sea","eq":"eq_sword"},
 "cowboy":{"add":"hg_cowboy","theme":"wood","eq":"eq_gun"},
 "sheriff":{"add":"hg_cowboy","theme":"gold","eq":"eq_gun"},
 "soldier":{"add":"hg_helmet","theme":"camo","eq":"eq_gun"},
 "sniper":{"add":"hg_helmet","theme":"camo","eq":"eq_gun"},
 "chef":{"add":"hg_toque"},"baker":{"add":"hg_toque"},
 "driver":{"add":"hg_cap","theme":"race"},"engineer":{"add":"hg_hardhat","theme":"warn"},
 "miner":{"add":"hg_hardhat","theme":"warn","eq":"eq_axe"},
 "builder":{"add":"hg_hardhat","theme":"warn","eq":"eq_hammer"},
 "pilot":{"add":"hg_cap","theme":"sky"},"astronaut":{"add":"hg_dome","add2":"jetpack"},
 "doctor":{"add":"hg_cap"},"teacher":{"add":"hg_glasses"},"scientist":{"add":"hg_glasses"},
 "santa":{"add":"hg_santa","add2":"beard_long","theme":"race"},
 "glasses":{"add":"hg_glasses"},"sunglasses":{"add":"hg_glasses"},"visor":{"add":"hg_glasses"},
 "helmet":{"add":"hg_helmet"},"armored":{"add":"shoulder_pads","mat":"metal"},
 "hat":{"add":"hg_cap"},"cap":{"add":"hg_cap"},"mask":{"add":"hg_mask"},"masked":{"add":"hg_mask"},
 "hood":{"add":"hg_hood"},"hooded":{"add":"hg_hood"},
 "halo":{"add":"hg_halo"},"wings":{"add":"w_big"},"winged":{"add":"w_big"},
 "horns":{"add":"h_curved"},"horned":{"add":"h_curved"},
 "cape":{"add":"cape_long"},"caped":{"add":"cape_long"},"cloak":{"add":"cape_long"},
 "jetpack":{"add":"jetpack"},"backpack":{"add":"backpack"},
 "beard":{"add":"beard_long"},"bearded":{"add":"beard_long"},"mustache":{"add":"mustache"},
 "catgirl":{"add":"hg_ears_cat"},"neko":{"add":"hg_ears_cat"},"bunnygirl":{"add":"hg_ears_bunny"},
 "aura":{"add":"aura_ring"},"spiky":{"sharp":0.9},"smooth":{"sharp":-0.6}}

THEMES = {
 "gold":(45,.85,.78),"dark":(265,.28,.16),"neon":(310,1.0,.96),"ice":(195,.42,.93),
 "lava":(12,.95,.82),"mystic":(275,.75,.58),"steel":(215,.08,.65),"sea":(200,.75,.52),
 "warn":(48,.95,.84),"sky":(205,.72,.75),"navy":(225,.82,.32),"pastel":(330,.35,.88),
 "race":(0,.88,.65),"bronze":(30,.72,.58),"copper":(18,.78,.62),"emerald":(145,.82,.58),
 "ruby":(350,.88,.62),"obsidian":(260,.35,.12),"wood":(28,.65,.48),"stone":(210,.06,.52),
 "cursed":(285,.82,.32),"holy":(48,.45,.96),"toxic":(105,.95,.78),"crystal":(185,.55,.94),
 "ghost":(190,.28,.92),"camo":(100,.52,.38)}

SPECIFICS = {}

# natural palettes for archetypes that should not get random colours (A,B,C,S,D,L)
NATURAL = {
 "tree":("#3f9b4f","#7a5230","#e64a4a","#2f7a3c","#4a301b","#f4efe0"),
 "weapon":("#b8bcc4","#7a4f2a","#4a8fe0","#d4a640","#2b221a","#eef1f6"),
 "gun":("#4a4e57","#2c2f36","#ff5500","#7a808c","#1b1d22","#c8cdd6"),
 "furniture":("#8c5830","#633b1d","#d9a441","#b57c4a","#2e1c0e","#f2eadf"),
 "instrument":("#c47a32","#4a2e16","#e8c547","#d9d9d9","#1c1612","#f7f3eb"),
 "structure":("#9a9ea6","#6e727a","#4aa3df","#c49a45","#32353b","#eceef2")}

COLOR_WORDS = {
 "red":(0,.85,.62),"crimson":(348,.9,.55),"scarlet":(5,.9,.65),"maroon":(350,.8,.35),"burgundy":(345,.78,.32),
 "coral":(14,.75,.85),"salmon":(12,.65,.88),"orange":(24,.9,.65),"amber":(38,.92,.75),"peach":(26,.55,.92),
 "yellow":(52,.9,.72),"gold":(45,.85,.75),"lemon":(56,.88,.85),"cream":(45,.2,.95),"ivory":(48,.12,.96),
 "beige":(36,.28,.85),"tan":(32,.42,.72),"khaki":(42,.38,.68),"sand":(40,.35,.82),
 "green":(140,.72,.52),"lime":(95,.88,.75),"olive":(75,.65,.42),"emerald":(145,.82,.58),"jade":(158,.72,.55),
 "mint":(160,.45,.84),"forest":(135,.78,.35),"teal":(175,.78,.52),"turquoise":(178,.75,.72),
 "cyan":(188,.88,.72),"aqua":(185,.82,.78),"sky":(202,.72,.82),"azure":(210,.85,.75),
 "blue":(215,.82,.58),"cobalt":(220,.88,.55),"sapphire":(222,.88,.52),"navy":(225,.82,.32),"indigo":(255,.82,.48),
 "purple":(275,.72,.58),"violet":(282,.75,.68),"lavender":(270,.42,.88),"magenta":(305,.88,.72),
 "pink":(330,.7,.78),"rose":(340,.75,.72),"fuchsia":(315,.9,.75),
 "white":(0,0,.96),"snow":(200,.04,.98),"silver":(215,.06,.78),"platinum":(210,.05,.86),
 "grey":(220,.05,.55),"gray":(220,.05,.55),"slate":(215,.15,.45),"charcoal":(220,.1,.25),
 "black":(260,.2,.14),"obsidian":(260,.35,.12),"ebony":(250,.2,.15),
 "brown":(25,.65,.42),"chocolate":(22,.72,.35),"coffee":(24,.68,.32),"bronze":(30,.7,.55),"copper":(18,.78,.58)}

NEG = {"no","without","not","never","minus","wingless","hornless","hairless"}
STOP = set("""build make me a an the create generate give please pls i im want need can you of with and my some
for to model roblox lego brick bricks blocky block 3d one new cool nice awesome simple it its that this like
lets let draw design looking looks look who is are be as in on at from so very really just also something
thing object toy cartoon style versionHolding wearing carrying equipped""".lower().split())

ALL_KEYS = sorted({k for ks in ROOTS.values() for k in ks})
KNOWN = set(ALL_KEYS)|set(MODS)|set(COLOR_WORDS)|NEG|STOP
IRREG = {"mice":"mouse","men":"man","women":"woman","oxen":"ox","geese":"goose","wolves":"wolf",
         "calves":"calf","knives":"knife","swords":"sword","leaves":"leaf","teeth":"tooth","feet":"foot",
         "children":"child","people":"person","elves":"elf","dwarves":"dwarf","octopi":"octopus","cacti":"cactus"}
SKIN = ["#f2c9a0","#e0ac7e","#c68863","#8d5a3b","#6b4226","#ffdfc4"]
HAIR = ["#2b1d12","#4a2f1b","#6b4423","#141414","#d9a441","#c2652e","#8a8a8a","#f2e2c4"]
ANIME_HAIR = ["#ff7ab8","#7ad8ff","#ffd166","#b48cff","#5ce6a0","#ff5c77"]
NAME_PRE = ["Brick","Stud","Krag","Zor","Bloxx","Torv","Pixl","Grim","Lux","Vex","Snap","Mek",
 "Vor","Quil","Rune","Ember","Frost","Thorn","Gale","Umber","Nova","Aether","Chrono","Valk"]
NAME_SUF = {
 "octopus":"pus","serpent":"enth","fish":"fin","bird":"wing","crab":"claw","spider":"ling","bug_fly":"flutter",
 "golem":"mok","humanoid":"guard","mech":"prime","turtle":"shell","jelly":"meduse","monster":"fiend",
 "car":"runner","train":"express","bike":"cycle","boat":"wave","plane":"jet","heli":"rotor","tank":"tread",
 "space":"cosmos","quadruped":"hoof","building":"stead","structure":"arch","tree":"bark","weapon":"edge",
 "gun":"blast","furniture":"craft","food":"bite","instrument":"chord","appliance":"tek","collectible":"relic","prop":"bloxx"}

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
    # Join adjacent tokens to catch compound words like "polarbear", "icecream", "pirateship"
    for i in range(len(toks)-1):
        joined = toks[i] + toks[i+1]
        tset |= stems(joined)
    I = {"root":None,"mods":[],"traits":{},"neg":set(),"colors":[],"size":1.0,"sharp":1.0,
         "pose":0,"mat":None,"float":False,"prop":{},"eyes":1.0,"palette_force":None,"var":None,
         "carbody":None,"species":None,"keyword":None,"unknown":[],"ram":False,"tokens":set(tset)}
    for phrase,cfg in SPECIFICS.items():
        if phrase in raw:
            I.update({k:v for k,v in cfg.items() if k!="palette"})
            I["palette_force"]=cfg.get("palette"); I["root"]=cfg.get("root",I["root"]); return I
    # Check multi-word phrases
    phrase_root = None
    for phrase, (proot, pcfg) in PHRASE_MAP.items():
        if phrase in raw:
            phrase_root = proot
            if "carbody" in pcfg: I["carbody"] = pcfg["carbody"]
            if "keyword" in pcfg: I["keyword"] = pcfg["keyword"]
            if "species" in pcfg: I["species"] = pcfg["species"]
            if "prop" in pcfg: I["prop"].update(pcfg["prop"])
            if "theme" in pcfg: I["colors"].append(THEMES[pcfg["theme"]])
            if "add" in pcfg: I["traits"][pcfg["add"]] = 1
            if "float" in pcfg: I["float"] = pcfg["float"]
            if "sharp" in pcfg: I["sharp"] = pcfg["sharp"]
            break
    best, root = score_roots(tset)
    if phrase_root:
        root = phrase_root; best = max(best, 1)
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
    # If both humanoid and weapon/gun/shield are mentioned (e.g. "knight with a sword"), keep humanoid and equip weapon!
    if "humanoid" in [r for r,ks in ROOTS.items() if any(k in tset for k in ks)] and root in ("weapon","gun"):
        if any(k in tset for k in ROOTS["humanoid"]):
            w_kw = next((k for k in ROOTS[root] if k in tset), None)
            root = "humanoid"
            if w_kw in ("shield","buckler","towershield","aegis"): I["traits"]["eq_shield"] = 1
            elif w_kw in ("bow","longbow","crossbow"): I["traits"]["eq_bow"] = 1
            elif w_kw in ("staff","scepter"): I["traits"]["eq_staff"] = 1
            elif w_kw in ("wand","rod"): I["traits"]["eq_wand"] = 1
            elif w_kw in ("axe","battleaxe","hatchet","halberd"): I["traits"]["eq_axe"] = 1
            elif w_kw in ("hammer","warhammer","mace","maul"): I["traits"]["eq_hammer"] = 1
            elif w_kw in ("scythe",): I["traits"]["eq_scythe"] = 1
            elif w_kw in ROOTS["gun"]: I["traits"]["eq_gun"] = 1
            else: I["traits"]["eq_sword"] = 1
    I["root"] = root
    I["tokens"] = set(tset)
    if root == "quadruped":
        if not I["species"]:
            I["species"] = "beast"
            for sp, keys in SPECIES_KEYS.items():
                if any(k in tset for k in keys): I["species"] = sp; break
        I["ram"] = "ram" in tset; I["keyword"] = I["species"]
    elif root != "prop" and not I["keyword"]:
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
        if m.get("add2"): I["traits"][m["add2"]]=1
        if root == "humanoid":
            if m.get("eq"): I["traits"][m["eq"]]=1
            if m.get("eq2"): I["traits"][m["eq2"]]=1
    if "wingless" in tset: I["neg"].add("w_big")
    if "hornless" in tset: I["neg"].update(["h_curved","horns"])
    if "hairless" in tset: I["neg"].add("hair")
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
    if I["mat"]=="gold": h,s,v=45,.85,.82
    if I["mat"]=="ice": h,s,v=195,.4,.93
    if I["mat"]=="lava": h,s,v=12,.95,.8
    off=rng.choice([180,28,120,150])
    c2 = I["colors"][1] if len(I["colors"])>1 else (h+rng.choice([-25,25]),s*.7,min(1,v*1.2))
    c3 = I["colors"][2] if len(I["colors"])>2 else (h+off,max(.5,s),min(1,v*1.35))
    P={"A":hsv_hex(h,s*.85,v),"B":hsv_hex(c2[0],c2[1],c2[2]),
       "C":hsv_hex(c3[0],c3[1],c3[2]),"S":hsv_hex(h+off+rng.choice([-30,30]),max(.45,s*.9),min(1,v*1.1)),
       "D":hsv_hex(h,min(1,s*1.05),max(.1,v*.38)),"L":hsv_hex(h+15,max(.06,s*.32),min(1,v*1.55))}
    if I["root"]=="humanoid":
        if I["mat"]=="metal" or "robot" in I["mods"] or "cyborg" in I["tokens"] or "android" in I["tokens"]:
            P["K"]=hsv_hex(h,.15,.75)
        elif "alien" in I["mods"] or "orc" in I["tokens"] or "goblin" in I["tokens"] or "zombie_man" in I["tokens"]:
            P["K"]=hsv_hex(125,.55,.62)
        elif "skeleton" in I["tokens"] or "vampire" in I["tokens"] or "clown" in I["tokens"]:
            P["K"]="#f2efe9"
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
        sz=[round(max(.04,v*self.scale),2) for v in size]; po=[round(v*self.scale,2) for v in pos]
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
        self.counts[shape]+=1
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
def _hand(B,side="R"):
    target="Hand"+side
    for p in B.parts:
        if p["n"]==target: return target
    return B.root
def _chest(B):
    for p in B.parts:
        if p["n"]=="Chest": return "Chest"
    return B.root

# ------------------------------------------------------------------ 35+ Modular Addons
def add_brow_evil(B,I,r):
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Brow"+suf,_head(B),"box",(.42,.12,.15),None,(sx*.38,.42,-.62),(0,0,sx*-18),"D")
def add_hg_crown(B,I,r):
    c=B.add("Crown",_head(B),"box",(.95,.3,.95),"top",(0,0,0),(0,0,0),"S")
    for i in range(4): B.add("CrownPt%d"%i,c,"pyramid",(.22,.5,.22),"top",((i-1.5)*.26,0,-.3),(0,0,0),"C")
def add_hg_pointy(B,I,r):
    b=B.add("HatBrim",_head(B),"box",(1.6,.16,1.6),"top",(0,0,0),(0,0,0),"B")
    B.add("HatCone",b,"pyramid",(.85,1.55,.85),"top",(0,.05,0),(0,0,0),"C")
def add_hg_helmet(B,I,r):
    h=B.add("Helmet",_head(B),"box",(1.35,1.0,1.3),"top",(0,-.15,0),(0,0,0),"D")
    B.add("HelmetCrest",h,"wedge",(.22,.45,1.1),"top",(0,0,0),(0,0,0),"C")
def add_hg_samurai(B,I,r):
    h=B.add("Kabuto",_head(B),"box",(1.4,.55,1.35),"top",(0,-.05,0),(0,0,0),"D")
    B.add("KabutoCrest",h,"wedge",(.9,.65,.15),"front",(0,.25,-.05),(0,0,0),"S")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Shikoro"+suf,h,"box",(.18,.6,1.1),"right" if sx>0 else "left",(0,-.3,.1),(0,0,sx*15),"B")
def add_hg_viking(B,I,r):
    h=B.add("VikHelm",_head(B),"box",(1.35,.55,1.3),"top",(0,-.05,0),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        bh=B.add("VikHorn"+suf,h,"box",(.28,.55,.28),"right" if sx>0 else "left",(0,.1,0),(0,0,sx*-35),"L")
        B.add("VikTip"+suf,bh,"pyramid",(.22,.5,.22),"top",(0,0,0),(0,0,0),"L")
def add_hg_cowboy(B,I,r):
    b=B.add("CowboyBrim",_head(B),"box",(1.8,.14,1.55),"top",(0,0,0),(0,0,0),"B")
    B.add("CowboyCrown",b,"box",(1.05,.55,1.05),"top",(0,0,0),(0,0,0),"A")
def add_hg_santa(B,I,r):
    b=B.add("SantaTrim",_head(B),"box",(1.3,.24,1.3),"top",(0,0,0),(0,0,0),"L")
    c=B.add("SantaCone",b,"pyramid",(.95,1.1,.95),"top",(0,0,.1),(18,0,0),"C")
    B.add("SantaPom",c,"gem",(.35,.35,.35),"top",(0,0,0),(0,0,0),"L")
def add_hg_halo(B,I,r):
    B.add("Halo",_head(B),"cylinder",(1.15,.12,1.15),"top",(0,.45,0),(0,0,0),"S")
def add_hg_hood(B,I,r):
    B.add("Hood",_head(B),"box",(1.4,1.25,1.35),"top",(0,-.2,.08),(0,0,0),"D")
def add_hg_ears_cat(B,I,r):
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("CatEar"+suf,_head(B),"pyramid",(.32,.5,.26),"top",(sx*.38,0,-.05),(0,0,-sx*12),"C")
def add_hg_ears_bunny(B,I,r):
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("BunEar"+suf,_head(B),"box",(.26,1.1,.2),"top",(sx*.34,0,0),(0,0,-sx*8),"L")
def add_hg_mask(B,I,r): B.add("Mask",_head(B),"box",(1.05,.52,.22),"front",(0,-.05,-.02),(0,0,0),"D")
def add_hg_tricorn(B,I,r):
    b=B.add("TriBrim",_head(B),"box",(1.7,.15,1.25),"top",(0,0,0),(0,0,0),"D")
    B.add("TriTop",b,"wedge",(1.5,.42,1.0),"top",(0,.05,0),(0,0,0),"B")
def add_hg_toque(B,I,r): B.add("Toque",_head(B),"cylinder",(.95,.95,.95),"top",(0,.1,0),(0,0,0),"L")
def add_hg_cap(B,I,r):
    t=B.add("CapTop",_head(B),"box",(1.12,.25,1.12),"top",(0,0,-.05),(0,0,0),"C")
    B.add("CapBrim",t,"box",(1.0,.12,.6),"front",(0,-.1,-.2),(0,0,0),"C")
def add_hg_hardhat(B,I,r): B.add("HardHat",_head(B),"box",(1.32,.45,1.32),"top",(0,.05,0),(0,0,0),"C")
def add_hg_dome(B,I,r): B.add("Dome",_head(B),"gem",(1.55,1.55,1.55),None,(0,.1,0),(0,0,0),"L")
def add_hg_glasses(B,I,r): B.add("Glasses",_head(B),"box",(1.05,.24,.16),"front",(0,.12,-.05),(0,0,0),"D")
def add_hg_headband(B,I,r): B.add("Headband",_head(B),"box",(1.25,.22,1.25),"top",(0,-.25,0),(0,0,0),"C")
def add_hg_crystal(B,I,r):
    for i in range(3): B.add("Crys%d"%i,_head(B),"pyramid",(.25,.9-i*.2,.25),"top",((i-1)*.35,.05,.2),(0,0,0),"C")
def add_hair_spiky(B,I,r):
    for i in range(4): B.add("HairSpike%d"%i,_head(B),"pyramid",(.22,.6,.22),"top",((i-1.5)*.3,0,-.1),(0,0,0),"H")
def add_beard_long(B,I,r):
    B.add("BeardAdd",_head(B),"wedge",(.85,.9,.35),"front",(0,-.55,-.02),(0,0,0),"H")
def add_mustache(B,I,r):
    B.add("Mustache",_head(B),"box",(.68,.16,.18),"front",(0,-.22,-.04),(0,0,0),"H")
def add_shoulder_pads(B,I,r):
    ch=_chest(B)
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("PauldronAdd"+suf,ch,"box",(.75,.45,.85),"right" if sx>0 else "left",(0,.65,0),(0,0,sx*-10),"S",studs=True)
def add_jetpack(B,I,r):
    ch=_chest(B); jp=B.add("Jetpack",ch,"box",(1.1,1.2,.55),"back",(0,.1,0),(0,0,0),"D")
    for sx,suf in ((1,"R"),(-1,"L")):
        t=B.add("JetThruster"+suf,jp,"cylinder",(.38,1.1,.38),None,(sx*.38,0,.15),(0,0,0),"B")
        B.add("JetFlame"+suf,t,"pyramid",(.32,.55,.32),"bot",(0,0,0),(180,0,0),"C")
def add_backpack(B,I,r):
    B.add("Backpack",_chest(B),"box",(1.15,1.25,.6),"back",(0,.05,0),(0,0,0),"B",studs=True)
def add_aura_ring(B,I,r):
    B.ring("AuraOrb",B.root,6,1.8,1.2,(.28,.28,.28),"C")
def add_eq_sword(B,I,r):
    h=_hand(B,"R"); g=B.add("EqGuard",h,"box",(.7,.18,.28),"front",(0,0,-.15),(0,0,0),"S")
    b=B.add("EqBlade",g,"box",(.22,1.9,.12),"top",(0,0,0),(0,0,0),"L")
    B.add("EqTip",b,"pyramid",(.22,.45,.12),"top",(0,0,0),(0,0,0),"L")
def add_eq_shield(B,I,r):
    h=_hand(B,"L"); s=B.add("EqShield",h,"box",(.22,1.5,1.15),"left",(-.08,.1,-.1),(0,0,0),"B")
    B.add("EqShieldBoss",s,"gem",(.28,.45,.45),"left",(0,0,0),(0,0,0),"S")
def add_eq_staff(B,I,r):
    h=_hand(B,"R"); s=B.add("EqStaff",h,"box",(.18,3.2,.18),"front",(0,.6,-.12),(0,0,0),"B")
    B.add("EqStaffOrb",s,"gem",(.55,.55,.55),"top",(0,0,0),(0,0,0),"C")
def add_eq_wand(B,I,r):
    h=_hand(B,"R"); s=B.add("EqWand",h,"box",(.14,1.3,.14),"front",(0,.35,-.12),(0,0,0),"B")
    B.add("EqWandStar",s,"gem",(.36,.36,.36),"top",(0,0,0),(0,0,0),"C")
def add_eq_axe(B,I,r):
    h=_hand(B,"R"); s=B.add("EqAxeShaft",h,"box",(.2,2.2,.2),"front",(0,.45,-.12),(0,0,0),"B")
    B.add("EqAxeBlade",s,"wedge",(.22,.85,.85),"top",(0,-.2,-.3),(0,0,0),"L")
def add_eq_hammer(B,I,r):
    h=_hand(B,"R"); s=B.add("EqHamShaft",h,"box",(.22,2.1,.22),"front",(0,.45,-.12),(0,0,0),"B")
    B.add("EqHamHead",s,"box",(.75,.65,1.2),"top",(0,0,0),(0,0,0),"D")
def add_eq_scythe(B,I,r):
    h=_hand(B,"R"); s=B.add("EqScytheShaft",h,"box",(.18,3.1,.18),"front",(0,.6,-.12),(0,0,0),"B")
    B.add("EqScytheBlade",s,"wedge",(.16,.45,1.4),"top",(0,-.1,-.55),(0,0,0),"L")
def add_eq_bow(B,I,r):
    h=_hand(B,"L"); B.add("EqBow",h,"box",(.16,1.8,.45),"front",(0,.2,-.2),(0,0,0),"B")
def add_eq_gun(B,I,r):
    h=_hand(B,"R"); g=B.add("EqGunGrip",h,"box",(.22,.45,.28),"front",(0,.1,-.12),(0,0,0),"D")
    B.add("EqGunBarrel",g,"box",(.24,.28,.95),"top",(0,0,-.32),(0,0,0),"D")
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

ADDONS={
 "brow_evil":add_brow_evil,"hg_crown":add_hg_crown,"hg_pointy":add_hg_pointy,
 "hg_helmet":add_hg_helmet,"hg_samurai":add_hg_samurai,"hg_viking":add_hg_viking,
 "hg_cowboy":add_hg_cowboy,"hg_santa":add_hg_santa,"hg_halo":add_hg_halo,
 "hg_hood":add_hg_hood,"hg_ears_cat":add_hg_ears_cat,"hg_ears_bunny":add_hg_ears_bunny,
 "hg_mask":add_hg_mask,"hg_tricorn":add_hg_tricorn,"hg_toque":add_hg_toque,
 "hg_cap":add_hg_cap,"hg_hardhat":add_hg_hardhat,"hg_dome":add_hg_dome,
 "hg_glasses":add_hg_glasses,"hg_headband":add_hg_headband,"hg_crystal":add_hg_crystal,
 "hair_spiky":add_hair_spiky,"beard_long":add_beard_long,"mustache":add_mustache,
 "shoulder_pads":add_shoulder_pads,"jetpack":add_jetpack,"backpack":add_backpack,
 "aura_ring":add_aura_ring,"eq_sword":add_eq_sword,"eq_shield":add_eq_shield,
 "eq_staff":add_eq_staff,"eq_wand":add_eq_wand,"eq_axe":add_eq_axe,
 "eq_hammer":add_eq_hammer,"eq_scythe":add_eq_scythe,"eq_bow":add_eq_bow,"eq_gun":add_eq_gun,
 "taxi_sign":add_taxi_sign,"lightbar":add_lightbar,
 "w_big":add_w_big,"h_curved":add_h_curved,"cape_long":add_cape_long,"sp_spoiler":add_sp_spoiler}

# ------------------------------------------------------------------ 32 Archetype Builders
def b_humanoid(B,I,r):
    p=I["prop"];v=B.var;kw=I.get("keyword") or "human"
    cw=1.5*p.get("chest",1.0)*(1.12 if v==2 else .94 if v==1 else 1.0)
    lw=p.get("limbs",1.0); hw=1.12*p.get("head",1.0)*(1.1 if v==0 else 1.0)
    leg=1.35*lw*(1.1 if v==3 else 1.0)
    hips=B.add("HumanoidRootPart",None,"box",(cw*.9,.5,.9),None,(0,0,0),(0,0,0),"P")
    for sx,suf in ((1,"R"),(-1,"L")):
        th=B.add("Thigh"+suf,hips,"box",(.62*lw,leg,.7),"bot",(sx*.42,-.05,0),(0,0,0),"P")
        shn=B.add("Shin"+suf,th,"box",(.5*lw,leg,.58),"bot")
        B.add("Shoe"+suf,shn,"wedge",(.6,.35,1.05),"bot",(0,0,-.18),(0,0,0),"D")
    torso=B.add("Chest",hips,"box",(cw,1.7,.95),"top",(0,.05,0),(0,0,0),"A",studs=True)
    B.add("Collar",torso,"box",(cw*.55,.18,.98),"top",(0,-.08,0),(0,0,0),"B")
    B.add("Emblem",torso,"gem",(.45,.45,.18),"front",(0,.25,0),(0,0,0),"C")
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
    B.add("Buckle",hips,"box",(.32,.26,.16),"front",(0,.15,0),(0,0,0),"S")
    # Role-based automatic gear if not already added by MODS
    if kw in ("knight","paladin","crusader","templar") and "eq_sword" not in I["traits"]:
        add_hg_helmet(B,I,r); add_eq_sword(B,I,r); add_eq_shield(B,I,r); add_shoulder_pads(B,I,r)
    elif kw in ("samurai","shogun","ronin") and "hg_samurai" not in I["traits"]:
        add_hg_samurai(B,I,r); add_eq_sword(B,I,r); add_shoulder_pads(B,I,r)
    elif kw in ("viking","barbarian","berserker") and "hg_viking" not in I["traits"]:
        add_hg_viking(B,I,r); add_eq_axe(B,I,r); add_beard_long(B,I,r)
    elif kw in ("wizard","mage","sorcerer","warlock") and "hg_pointy" not in I["traits"]:
        add_hg_pointy(B,I,r); add_eq_staff(B,I,r); add_beard_long(B,I,r)
    elif kw in ("king","queen","prince","princess","emperor","pharaoh") and "hg_crown" not in I["traits"]:
        add_hg_crown(B,I,r); add_cape_long(B,I,r)
    elif kw in ("astronaut","cosmonaut") and "hg_dome" not in I["traits"]:
        add_hg_dome(B,I,r); add_jetpack(B,I,r)
    B.tag("humanoid")

def b_mech(B,I,r):
    v=B.var
    pel=B.add("HumanoidRootPart",None,"box",(2.2,.8,1.5),None,(0,3.2,0),(0,0,0),"D")
    ch=B.add("Chest",pel,"box",(3.0,2.2,2.0),"top",(0,.1,0),(0,0,0),"A",studs=True)
    B.add("CockpitGlass",ch,"wedge",(1.8,1.1,.55),"front",(0,.2,0),(0,0,0),"C")
    B.add("ReactorCore",ch,"gem",(.85,.85,.45),"front",(0,-.45,-.05),(0,0,0),"S")
    hd=B.add("Head",ch,"box",(1.3,.9,1.2),"top",(0,.05,0),(0,0,0),"B",studs=True)
    B.add("Visor",hd,"box",(1.1,.3,.2),"front",(0,.05,-.02),(0,0,0),"C")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Antenna"+suf,hd,"box",(.14,.75,.22),"top",(sx*.5,0,0),(0,0,sx*-12),"S")
        sh=B.add("Shoulder"+suf,ch,"box",(1.4,1.2,1.6),"right" if sx>0 else "left",(0,.65,0),(0,0,0),"B",studs=True)
        pod=B.add("MissilePod"+suf,sh,"box",(.9,.75,1.1),"top",(0,0,0),(0,0,0),"D")
        for mx in (-.22,.22): B.add("Missile%s%d"%(suf,1 if mx>0 else 0),pod,"cylinder",(.24,.25,.24),"front",(mx,0,0),(90,0,0),"C")
        ua=B.add("Arm"+suf,sh,"box",(.8,1.5,.85),"bot",(0,0,0),(0,0,sx*5),"A")
        fa=B.add("Fore"+suf,ua,"box",(.95,1.6,1.1),"bot",(0,0,-.15),(-12,0,0),"B")
        if sx>0 or v%2==0:
            B.add("Cannon"+suf,fa,"cylinder",(.45,1.8,.45),"front",(0,-.2,-.3),(90,0,0),"D")
        else:
            B.add("EnergyBlade"+suf,fa,"wedge",(.2,2.2,.65),"bot",(0,-.3,-.2),(0,0,0),"C")
        th=B.add("Thigh"+suf,pel,"box",(.95,1.6,1.1),"bot",(sx*.85,0,0),(0,0,0),"B")
        B.add("KneePad"+suf,th,"wedge",(.85,.6,.45),"front",(0,-.55,0),(0,0,0),"S")
        shn=B.add("Shin"+suf,th,"box",(1.1,1.8,1.3),"bot",(0,0,0),(0,0,0),"A")
        B.add("Foot"+suf,shn,"wedge",(1.3,.65,2.1),"bot",(0,0,-.3),(0,0,0),"D")
    add_jetpack(B,I,r)
    B.tag("mech","armor","glow")

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
    kw=I.get("keyword") or "serpent"
    n=10 if B.var!=2 else 12
    d=[10]+[r.choice([-13,13])*(1 if i%2 else -1) for i in range(n-1)]
    par=None;names=[]
    for i in range(n):
        sz=(1.5-i*.07,1.35-i*.06,1.6)
        nn=B.add("Seg%d"%i,par if par else None,"box",sz,None if par else None,
                 (0,1.5,4.2) if not par else (0,0,0),(0,d[i],0),"A" if i%2 else "B",studs=i%3==0)
        names.append(nn);par=nn
    hd=B.add("Head",par,"box",(1.9,1.5,2.3),"front",(0,.25,.2),(0,0,0),"A",studs=True)
    if kw=="cobra":
        B.add("HoodR",hd,"wedge",(1.2,1.8,.4),"right",(0,-.2,.3),(0,0,-15),"B")
        B.add("HoodL",hd,"wedge",(1.2,1.8,.4),"left",(0,-.2,.3),(0,0,15),"B")
    B.add("Snout",hd,"wedge",(1.3,.9,1.3),"front",(0,-.25,.2),(-90,0,0),"B")
    B.add("Tongue",hd,"box",(.25,.08,.9),"front",(0,-.45,-.4),(0,0,0),"C")
    B.eyes(hd,.45,-1.05,.5,.72)
    for i in range(0,n-2,2): B.add("Dorsal%d"%i,names[i],"wedge",(.28,.9,1.0),"top",(0,.05,0),(0,0,0),"C")
    B.add("TailFin",names[0],"wedge",(1.3,1.5,.28),"back",(0,.2,-.2),(90,0,0),"C")
    if kw in ("dragon","wyvern","wyrm"):
        add_w_big(B,I,r); add_h_curved(B,I,r)
    B.tag("tail")

def b_fish(B,I,r):
    kw=I.get("keyword") or "fish"
    B.add("CoreRoot",None,"box",(2.6,2.6,2.4),None,(0,2.0,0),(0,0,0),"A",studs=True)
    sn=B.add("SnoutSec","CoreRoot","box",(2.0,2.0,1.4),"front",(0,0,.1),(0,0,0),"A")
    if kw in ("swordfish","narwhal"):
        B.add("TuskBill",sn,"pyramid",(.3,2.2,.3),"front",(0,0,-.2),(-90,0,0),"L")
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

def b_bug_fly(B,I,r):
    kw=I.get("keyword") or "butterfly"
    th=B.add("CoreRoot",None,"box",(1.1,1.0,1.8),None,(0,2.2,0),(0,0,0),"D",studs=True)
    ab=B.add("Abdomen",th,"box",(1.2,1.1,2.2),"back",(0,0,.1),(0,0,0),"A",studs=True)
    for i in range(3):
        B.add("Stripe%d"%i,ab,"box",(1.24,1.14,.32),None,(0,0,(i-1)*.6),(0,0,0),"D")
    if kw in ("bee","wasp","hornet"):
        B.add("Stinger",ab,"pyramid",(.35,.7,.35),"back",(0,0,0),(90,0,0),"D")
    hd=B.add("Head",th,"box",(1.0,.95,.95),"front",(0,.05,0),(0,0,0),"D")
    B.eyes(hd,.15,-.48,.34,.35,sc="C")
    for sx,suf in ((1,"R"),(-1,"L")):
        B.add("Antenna"+suf,hd,"box",(.12,.8,.12),"top",(sx*.28,0,-.2),(-25,0,-sx*18),"D")
        w1=B.add("WingUp"+suf,th,"box",(2.6,.12,1.6),None,(sx*1.6,.4,-.2),(0,sx*10,sx*18),"C")
        B.add("WingDot"+suf,w1,"gem",(.7,.18,.7),"top",(sx*.4,0,0),(0,0,0),"S")
        B.add("WingLo"+suf,th,"box",(2.0,.1,1.3),None,(sx*1.3,.2,.9),(0,-sx*12,sx*8),"B")
        for li in range(3):
            B.add("Leg%d%s"%(li,suf),th,"box",(.16,.9,.16),"bot",(sx*.45,0,(li-1)*.5),(0,0,sx*22),"D")
    B.mirrored.append(("WingUpR","WingUpL"))
    B.tag("wings","insect")

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

def b_monster(B,I,r):
    kw=I.get("keyword") or "beholder"
    if kw in ("beholder","cyclops","eyeball"):
        core=B.add("CoreRoot",None,"gem",(2.8,2.8,2.8),None,(0,2.6,0),(0,0,0),"A")
        eye=B.add("MainEye",core,"cylinder",(1.35,.35,1.35),"front",(0,.2,0),(90,0,0),"L")
        B.add("MainPupil",eye,"gem",(.65,.3,.65),"top",(0,.05,0),(0,0,0),"C")
        B.add("Maw",core,"box",(1.8,.65,.55),"front",(0,-.75,.15),(0,0,0),"D")
        for i in range(5):
            B.add("Fang%d"%i,"Maw","pyramid",(.22,.42,.22),"top",((i-2)*.34,-.1,-.15),(180,0,0),"L")
        for i in range(6):
            az=i*60.0; a=math.radians(az)
            st=B.add("Stalk%d"%i,core,"box",(.3,1.2,.3),None,(1.1*math.sin(a),1.3,1.1*math.cos(a)),(22,az,0),"B")
            B.add("StalkEye%d"%i,st,"gem",(.5,.5,.5),"top",(0,0,0),(0,0,0),"C")
    elif kw in ("ghost","phantom","wraith","specter","spirit","reaper","grimreaper"):
        core=B.add("CoreRoot",None,"box",(2.0,2.4,1.8),None,(0,2.4,0),(0,0,0),"A",studs=True)
        hd=B.add("Head",core,"box",(1.5,1.4,1.5),"top",(0,0,0),(0,0,0),"B")
        B.add("Hood",hd,"wedge",(1.65,.65,1.65),"top",(0,0,0),(0,0,0),"A")
        B.eyes(hd,.1,-.78,.38,.42,sc="C")
        for i in range(6):
            az=i*60.0; a=math.radians(az)
            B.add("Tatter%d"%i,core,"pyramid",(.6,1.1,.6),None,(.8*math.sin(a),-1.4,.8*math.cos(a)),(180,az,0),"A")
        for sx,suf in ((1,"R"),(-1,"L")):
            ua=B.add("Arm"+suf,core,"box",(.45,1.3,.45),"right" if sx>0 else "left",(0,.4,0),(0,0,sx*18),"B")
            B.add("Hand"+suf,ua,"box",(.4,.4,.4),"bot",(0,0,0),(0,0,0),"L")
        if "reaper" in kw: add_eq_scythe(B,I,r)
    else:
        b_golem(B,I,r)
    B.tag("monster")

def b_car(B,I,r):
    p=I["prop"];body=I.get("carbody") or {0:"sedan",1:"sport",2:"buggy",3:"pickup"}[B.var]
    ws=.85*p.get("wheels",1.0);lift=.25*p.get("lift",1.0)
    low={"sport":.85,"formula":.72,"buggy":1.0,"pickup":1.15,"van":1.2,"limo":.95,"tractor":1.25,"sedan":1.0}.get(body,1.0)
    L={"sport":4.6,"formula":4.8,"sedan":4.5,"buggy":3.6,"pickup":4.8,"van":4.9,"limo":6.2,"tractor":3.8}.get(body,4.5); W=2.1
    ch=B.add("CoreRoot",None,"box",(W,.7*low,L),None,(0,.9*low+lift,0),(0,0,0),"A",studs=True)
    if body=="van":
        cab=B.add("Cabin",ch,"box",(W*.92,1.5,L*.72),"top",(0,0,.35),(0,0,0),"A",studs=True)
        B.add("WinF",cab,"box",(W*.8,.6,.12),"front",(0,.35,-.02),(0,0,0),"D")
    else:
        cl=2.0 if body not in ("buggy","formula") else 1.4
        cab=B.add("Cabin",ch,"box",(W*.82,.8*low,cl),"top",(0,0,.5 if body=="pickup" else .3),(0,0,0),"B")
        B.add("WinF",cab,"wedge",(W*.78,.7*low,.15),"front",(0,0,0),(0,0,0),"D")
        B.add("WinB",cab,"box",(W*.78,.6*low,.12),"back",(0,0,-.02),(0,0,0),"D")
        B.add("Hood",ch,"wedge",(W*.9,.3,L*.3),"top",(0,-.12,-L*.3),(0,0,0),"A")
    if body=="buggy":
        for sx in (1,-1): B.add("Roll%d"%sx,ch,"box",(.15,.9,.15),"top",(sx*.8,.1,.6),(0,0,0),"D")
        B.add("RollBar",ch,"box",(1.8,.15,.15),"top",(0,.95,.6),(0,0,0),"D")
    if body in ("sport","formula"):
        for sx in (1,-1): B.add("Stripe%d"%sx,ch,"box",(.28,.06,L*.75),"top",(sx*.45,.02,-.35),(0,0,0),"L")
    if body=="pickup": B.add("Bed",ch,"box",(W*.95,.6,1.4),"top",(0,.15,1.5),(0,0,0),"A")
    for sx,suf in ((1,"R"),(-1,"L")):
        for zz,tag in ((L*.32,"F"),(-L*.32,"B")):
            w=B.add("Wheel%s%s"%(tag,suf),ch,"cylinder",(ws,.45,ws),None,(sx*(W/2+.05),-.25,zz),(0,0,90),"D")
            B.add("Hub%s%s"%(tag,suf),w,"cylinder",(ws*.5,.55,ws*.5),None,(0,0,0),(0,0,90),"C")
        B.add("Light%s"%suf,ch,"box",(.45,.28,.12),"front",(sx*.7,.1,0),(0,0,0),"C")
        B.add("Tail%s"%suf,ch,"box",(.45,.28,.12),"back",(sx*.7,.1,0),(0,0,0),"S")
        B.add("Skirt%s"%suf,ch,"box",(.15,.35,L*.7),"right" if sx>0 else "left",(0,-.15,0),(0,0,0),"D")
    B.add("BumpF",ch,"box",(W,.35,.3),"front",(0,-.15,0),(0,0,0),"D")
    B.add("BumpB",ch,"box",(W,.35,.3),"back",(0,-.15,0),(0,0,0),"D")
    if body in ("sport","formula") or "sp_spoiler" in I["traits"]:
        B.add("Spoiler",ch,"box",(W*.9,.14,.55),"back",(0,.55,.15),(0,0,0),"D")
        for sx in (1,-1): B.add("SpoPost%d"%sx,ch,"box",(.14,.5,.14),"back",(sx*.7,.3,.15),(0,0,0),"D")
    B.tag("wheels")

def b_train(B,I,r):
    kw=I.get("keyword") or "train"
    ch=B.add("CoreRoot",None,"box",(2.2,.6,6.0),None,(0,1.1,0),(0,0,0),"D",studs=True)
    if kw in ("bullettrain","shinkansen","subway","metro","monorail"):
        bd=B.add("Coach",ch,"box",(2.15,1.6,5.2),"top",(0,0,.3),(0,0,0),"A",studs=True)
        B.add("BulletNose",bd,"wedge",(2.1,1.5,1.8),"front",(0,-.05,0),(-90,0,0),"A")
        B.add("CockpitWin",bd,"box",(1.7,.45,.2),"front",(0,.35,-.02),(0,0,0),"D")
        for i in range(4):
            for sx,suf in ((1,"R"),(-1,"L")):
                B.add("Win%d%s"%(i,suf),bd,"box",(.12,.55,.8),"right" if sx>0 else "left",(0,.2,(i-1.5)*1.1),(0,0,0),"L")
    else:
        cab=B.add("Cabin",ch,"box",(2.1,2.1,2.0),"top",(0,0,1.8),(0,0,0),"A",studs=True)
        B.add("CabRoof",cab,"box",(2.3,.25,2.2),"top",(0,0,0),(0,0,0),"D")
        bl=B.add("Boiler",ch,"cylinder",(1.7,3.6,1.7),"top",(0,.2,-.9),(90,0,0),"B")
        st=B.add("Smokestack",ch,"cylinder",(.55,1.3,.55),"top",(0,1.4,-2.1),(0,0,0),"D")
        B.add("SmokePuff",st,"gem",(.75,.55,.75),"top",(0,.1,0),(0,0,0),"L")
        B.add("Cowcatcher",ch,"wedge",(2.2,.7,1.1),"front",(0,-.1,0),(-90,0,0),"C")
        B.add("Headlamp",ch,"cylinder",(.55,.3,.55),"front",(0,1.1,.1),(90,0,0),"S")
    for i,zz in enumerate((-2.1,-.7,.7,2.1)):
        for sx,suf in ((1,"R"),(-1,"L")):
            B.add("TrainWheel%d%s"%(i,suf),ch,"cylinder",(.85,.3,.85),None,(sx*1.15,-.3,zz),(0,0,90),"C")
    B.tag("train","wheels")

def b_bike(B,I,r):
    fr=B.add("CoreRoot",None,"box",(.5,.7,2.2),None,(0,1.2,0),(0,0,0),"A")
    for zz,tag in ((-1.3,"F"),(1.3,"B")):
        B.add("Wheel%s"%tag,fr,"cylinder",(1.1,.35,1.1),None,(0,-.5,zz),(0,0,90),"D")
    B.add("Fork",fr,"box",(.2,1.0,.2),"front",(0,-.3,-.2),(20,0,0),"B")
    B.add("Bar",fr,"box",(1.4,.2,.2),"top",(0,.2,-.9),(0,0,0),"D")
    B.add("Seat",fr,"box",(.6,.25,.9),"top",(0,0,.7),(0,0,0),"B")
    B.tag("wheels")

def b_boat(B,I,r):
    kw=I.get("keyword") or "boat"
    hl=B.add("CoreRoot",None,"box",(2.4,1.1,5.0),None,(0,1.2,0),(0,0,0),"A",studs=True)
    B.add("Bow",hl,"pyramid",(2.4,1.0,1.6),"front",(0,-.1,0),(-90,0,0),"A")
    cab=B.add("Cabin",hl,"box",(1.8,1.0,1.8),"top",(0,0,.6),(0,0,0),"B",studs=True)
    B.add("Win",cab,"box",(1.4,.5,.12),"front",(0,0,-.02),(0,0,0),"D")
    if kw in ("pirateship","sailboat","galleon","yacht") or B.var!=1:
        m=B.add("Mast",cab,"box",(.22,2.8,.22),"top",(0,0,0),(0,0,0),"D")
        B.add("Sail",m,"box",(2.2,1.8,.15),"front",(0,.1,0),(0,0,0),"L")
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
    bd=B.add("CoreRoot",None,"box",(2.0,1.6,3.4),
