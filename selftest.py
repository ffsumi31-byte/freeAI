"""Self-Test Suite for Roblox Cloud 3D Modeler AI."""
import server, diag

TEST_PROMPTS = [
    "build me a giant serpent",
    "orange tabby cat",
    "modern two story cafe building",
    "charizard fire dragon",
    "trex dinosaur",
    "black widow spider",
    "red sports car"
]

def run_tests():
    for p in TEST_PROMPTS:
        spec, _ = server.build_one(p, seed=42)
        d = diag.diagnose(spec)
        assert d["ok"], f"Failed on {p}"
        print(f"[PASS] {p:32s} -> {spec['archetype']:12s} | {d['summary']}")
    print("ALL SELF-TESTS PASSED.")

if __name__ == "__main__":
    run_tests()
