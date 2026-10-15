import traceback, brain
PROMPTS = ["build me a goat","goat","goats","gaot","human","car","police car","anime character","octopus",
  "spiky purple octopus","boat","heli","tank","bike","jelly","turtle","karate teacher human","sports car",
  "build me a dog","a cute fluffy sheep","wizard cat","evil purple wolf","royal lion","tiger","horse",
  "unicorn","cow","pig","giant elephant","giraffe","camel","panda","bear","rabbit","deer with antlers",
  "dinosaur","crocodile","castle","house","pine tree","cactus","mushroom","sword","axe","shield",
  "toaster","pizza","build me something"]
bad = 0
for p in PROMPTS:
    try:
        s, I = brain.build_one(p)
        checks = dict(brain.structural_checks(s, I))
        failed = [k for k, v in checks.items() if not v]
        warn = s["meta"].get("warn")
        status = "WARN" if (warn or failed) else "OK  "
        if status == "WARN": bad += 1
        print("%s %-24s -> %-9s %-9s parts=%-3d failed=%s warn=%s" % (
            status, p, s["archetype"], s["meta"].get("species") or "-", len(s["parts"]), failed, warn))
    except Exception:
        bad += 1; print("FAIL", p); traceback.print_exc()
print("\n%d prompts, %d with problems" % (len(PROMPTS), bad))
