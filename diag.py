import traceback, brain
prompts = [...]
for p in prompts:
    try:
        s, I = brain.build_one(p)
        warn = s["meta"].get("warn")
        ok_root = s["archetype"] == I["root"]
        checks = dict(brain.structural_checks(s, I))
        failed = [k for k, v in checks.items() if not v]
        status = "WARN" if warn or failed or not ok_root else "OK  "
        print("%s %-24s -> %-9s parts=%-3d warn=%s failed=%s" % (
            status, p, s["archetype"], len(s["parts"]), warn, failed))
    except Exception:
        print("FAIL", p); traceback.print_exc()
