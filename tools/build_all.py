"""One command: regenerate every asset, level, sound; enforce budgets. `python3 tools/build_all.py`"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import palette, actors, levels, audiokit, icons, review3d
from meshkit import ROOT

LEVEL_TRIS = 80_000


def main() -> int:
    t0 = time.time()
    palette.build()
    fails = []
    a = actors.build()
    for r in a:
        if r["tris"] > r["budget"]:
            fails.append(f"{r['name']}: {r['tris']} tris > {r['budget']}")
    lv = levels.build()
    for r in lv:
        if r["tris"] > LEVEL_TRIS:
            fails.append(f"level {r['level']}: {r['tris']} tris")
    au = audiokit.build()
    ic = icons.build()
    if "--review" in sys.argv:
        review3d.main()
    report = {"actors": a, "levels": lv, "audio": au, "icons": ic, "fails": fails}
    (ROOT / "docs/build_report.json").write_text(json.dumps(report, indent=1, default=float))
    for r in a:
        print(f"  {r['name']:<20} {r['tris']:>5} / {r['budget']}")
    for r in lv:
        print(f"  level {r['level']}: {r}")
    print(f"audio files: {len(au)}  icons: {len(ic)}  time: {time.time() - t0:.1f}s")
    print("FAIL:\n  " + "\n  ".join(fails) if fails else "BUILD OK")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
