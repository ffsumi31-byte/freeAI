#!/usr/bin/env python3
"""BrickForge local QA harness: thousands of prompts, hard invariants, diversity checks.
Usage:  python selftest.py          (~6.3k prompts)
        python selftest.py --full   (~7.1k prompts, adds mod-pair combos)"""
import sys, time, json, zlib
import brain
def kw_root():
    for root, keys in brain.ROOTS.items():
        for k in keys: yield k, root
def matrix(full):
    P = [(k, rt) for k, rt in kw_root()]
    for k, rt in kw_root():
        for m in brain.MODS: P.append(("%s %s" % (m, k), rt))
    for k, rt in kw_root():
        for c in brain.COLOR_WORDS: P.append(("%s %s" % (c, k), rt))
    for k, rt in kw_root():
        for s in ["tiny","huge","cute","evil","spiky","no wings","big"]: P.append(("%s %s" % (s, k), rt))
    if full:
        ms = list(brain.MODS)
        for i in range(len(ms)):
            for j in range(i+1, len(ms)): P.append(("%s %s octopus" % (ms[i], ms[j]), "octopus"))
    P += [("build me a human","humanoid"),("anime character","humanoid"),
      ("karate teacher human","humanoid"),("sports car","car"),("police car","car"),("taxi","car"),
      ("monster truck","car"),("school bus","car"),("black floating serpent","serpent"),
      ("cute jelly","jelly"),("golden koi fish","fish"),("ice dragon","serpent"),
      ("build me a car","car"),("make a boat","boat"),("helicopter","heli"),("tank","tank"),
      ("bike","bike"),("spiky purple octopus","octopus"),("bald knight","humanoid"),
      ("wizard with cape","humanoid"),("pickup truck","car"),("van","car")]
    return P
def sig(spec): return (len(spec["parts"]), round(sum(sum(p["sz"]) for p in spec["parts"]), 1))
def main():
    full = "--full" in sys.argv
    prompts = matrix(full)
    print("prompt matrix: %d prompts" % len(prompts))
    fails = {}; t0 = time.time(); div_bad = 0; div_tot = 0
    for i, (pr, rt) in enumerate(prompts):
        seed = zlib.crc32(pr.encode()) % 100000
        try: spec, I = brain.build_one(pr, seed=seed, var=i % 4)
        except Exception as e:
            fails.setdefault("crash", []).append((pr, repr(e))); continue
        if spec["archetype"] != rt: fails.setdefault("root", []).append((pr, spec["archetype"]))
        for name, ok in brain.structural_checks(spec, I):
            if not ok: fails.setdefault(name, []).append((pr, ""))
        if i % 97 == 0:
            ss = {sig(brain.build_one(pr, seed=seed, var=v)[0]) for v in range(4)}
            div_tot += 1
            if len(ss) < 3:
                div_bad += 1; fails.setdefault("diversity", []).append((pr, str(len(ss))))
    dt = time.time() - t0
    print("ran %d prompts in %.1fs (%.0f prompts/s)" % (len(prompts), dt, len(prompts)/dt))
    if not fails: print("ALL CHECKS PASSED ✔")
    for k, v in sorted(fails.items(), key=lambda x: -len(x[1])):
        print("FAIL %-15s %5d   e.g. %s" % (k, len(v), v[:3]))
    print("diversity: %d/%d sampled prompts had <3 distinct variants" % (div_bad, div_tot))
    json.dump({k: v[:50] for k, v in fails.items()}, open("tests_report.json", "w"), indent=1)
    sys.exit(1 if fails else 0)
if __name__ == "__main__": main()
