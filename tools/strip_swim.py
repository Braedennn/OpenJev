from pathlib import Path

p = Path(r"E:\OpenJev\harness\packages\client\ui-conversation\src\client\skeleton\EmptyHero.tsx")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
assert lines[73].startswith("/* Hover swim"), lines[73][:60]
up_i = next(i for i, l in enumerate(lines) if l.startswith("const HERO_SWIM_UP_PATH"))
down_i = next(i for i, l in enumerate(lines) if l.startswith("const HERO_SWIM_DOWN_PATH"))
end = next(i for i in range(down_i, len(lines)) if lines[i].strip() == "")
del lines[73 : end + 1]
p.write_text("".join(lines), encoding="utf-8")
print("removed lines", end + 1 - 73, "now", len(lines))
