# Decisions

Format: reading taken — reason — how to change.

## Setup (step 0, 2026-10-13)
- **Dev OS:** WSL2 Ubuntu 24.04 on Windows. The player's machine is the Windows host, so the shipped export target is **Windows x86_64**; Linux is used for development and tests. — Change via `export_presets.cfg`.
- **Godot 4.7.2-stable** (latest stable at the time), installed to `~/.local/bin/godot`. — Pinned in README + `project.godot` features.
- **Screenshots work** through WSLg (`DISPLAY=:0`) on Mesa llvmpipe (software GL), so no xvfb is needed. Frame times measured under llvmpipe are **not** representative; the 60 fps check has to happen on the Windows build.
- **Python 3.12** with shapely, trimesh, numpy, pillow, scipy, mapbox_earcut, manifold3d. **cairosvg was skipped**: UI icons are drawn with Pillow polygons directly, so no system cairo is needed.
- **Audio format: WAV** (16-bit mono, 22.05 kHz). No OGG encoder is available, and the spec allows WAV. Loops use Godot's import loop flags.
- `reference/pixel_pipeline.md` is **absent**, so the helpers are written fresh (minimal `ease`, `pulse`, `wave`).
- References: there was no web research pass (budget). Design follows general known principles; this is flagged.

## Budget mode (user instruction)
- "Sacrifice details in favour of budget; beautify later." So: fewer kit pieces, simpler generators, procedural primitives where a generator adds little; polish is deferred to iteration rounds.
- Outlines: skipped for now (flat shading + fog carry readability).
- Retro mode: implemented as a viewport `scaling_3d` / stretch setting rather than a separate SubViewport tree (cheaper, same look).

## Gameplay readings
- "Hop" for hover = `steer_up` raises the target height (up to +6 m) and it springs back when released.
- Walls: the ship cannot pass through solid. Instead of physics, the runner checks the ship's cross-section position against the wall's gap polygon as the rail reaches the wall; if outside, the rail eases to a stop and the assist drifts the ship toward the gap after 3 s (levels 1–2: magnet always on).
- Collisions with terrain are handled analytically (corridor bounds per rail distance), not with physics bodies: cheaper and they can never trap the ship.
