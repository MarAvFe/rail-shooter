# How this project was made

This whole game was created by an AI coding agent (Claude, in Claude Code) from the prompt below. The agent wrote the design docs, the Python geometry and audio generators and the Godot project, then tested and exported the build. It ran with very little hand-holding, reviewing its own screenshots and bot playthroughs and iterating.

The first section is the **bootstrap prompt**, unedited. The second lists the short **follow-up directions** that changed scope or direction. Small fixes and tweak requests are left out.

---

## 1. Bootstrap prompt

The prompt was sent together with one extra instruction:

> be wary of budget. sacrifice details in favor of budget and we can always iterate beautification as we go.

````markdown
# Soft-Sky Rail Shooter — Full Game Pipeline
### design → geometry (Python + Shapely) → glTF → Godot 4 → verify → complete, runnable PC build

You are building a **complete, finished, playable game** for a 4-year-old, from an empty repo: design it first, generate every ship, enemy and landscape piece from geometry (Python + Shapely + trimesh), import them into Godot 4, play-test them with automated bots and screenshots, review against the checklists below, and iterate until it passes. **Do not deliver the first build.** Do not stop at a demo: the definition of "complete" is in its own section and is the finish line.

The method comes from a pixel-art pipeline that worked well (design brief first, flat-colour geometry, palette-locked ramps, one clock for all motion, review sheets, a failure→fix table, 1–3 changes per round). The *method* carries over. The 2D pixel renderer does not, because this game is 3D. If the file `reference/pixel_pipeline.md` exists in the repo, it is that original prompt: **port the helpers named in section 3.2 from it verbatim** instead of rewriting them, and ignore `pixelize.py` and `lightpass.py` (the look is achieved in-engine, section 5.7).

---

## The request (filled in)

```
GAME:         A 3D "on-rails" flying shooter (think old console rail shooters). The ship moves forward by
              itself; the player steers inside a canyon and shoots. Two vehicle types: an AIR ship that
              flies between giant mountains and through gaps in walls that cross the sky, and a HOVER
              ship that skims just above terrain. Only the MECHANICS of those games are mimicked; every
              design, name, sound and word is original.
PLAYER:       A 4-year-old. Plays on the couch with a PS2-style controller (USB adapter) in the end;
              during development: keyboard, WASD + one fire key. Cannot read. Short sessions.
              A parent is nearby and may open a hidden parent menu.
USE:          Private play now. It may be posted on Steam LATER, so everything must be releasable
              (original or properly licensed assets, a licence manifest) — but Steam integration itself
              is NOT part of this job.
STYLE TARGET: Old-console 3D (late-90s/PS2 feel) but SOFT: pastel, hue-shifted palettes, slow pace,
              low-poly flat-shaded shapes, optional low-resolution pixelated render. Calm and friendly,
              never aggressive. No blood, no scary imagery, no loud sounds.
PLATFORM:     The developer's own PC (detect the OS yourself). Godot 4.x, GDScript.
SCOPE:        A complete product: title → 6 short levels → ending → credits, with pause, parent menu,
              settings, save data, audio, and an exported build. See "Definition of complete".
MUST HAVE:    No text needed to play. Cannot fail or lose. Restart/quit never reachable by accident, but
              one press away for the parent. Input only through named actions (section 5.2).
              Motion-comfortable. Runs at 60 fps on a modest PC.
AVOID:        Anything copied from a known game, film, character, ship or sound. Hard fail states.
              Screen shake, fast rolls, flashing. Loud or sudden audio. Text-dependent UI for the child.
```

If something important is ambiguous, make the most reasonable choice, **write which reading you took in `docs/DECISIONS.md`**, and keep going. Do not ask me about it (see section 12 for the only times to stop).

---

## Standing assumptions (already decided — change a line here to change the game)

1. **Engine:** Godot 4.x latest stable, pinned in `README.md` and `project.godot`. **GDScript only**, statically typed. Use Godot 4 syntax (`@export`, `await`, `signal.connect()`, `CharacterBody3D`); do not write Godot 3 syntax.
2. **Renderer:** Compatibility (OpenGL). Widest hardware support, and it can render under software GL for automated screenshots.
3. **Look:** flat-shaded low-poly, vertex-colour materials from one palette file, one directional light, fog for depth. **Optional "retro" mode** (default ON): render the 3D scene at 640×360 in a `SubViewport` and upscale with NEAREST by an integer factor. Toggle lives in the parent menu.
4. **Camera:** chase camera behind and above the ship, fixed FOV ~70°, gentle lag. **No shake, no FOV kicks, horizon never rolls more than ~12°.**
5. **Movement model:** the ship follows a 3D spline ("rail") at a constant slow speed. The left stick / WASD moves it **laterally and vertically inside the corridor cross-section**. No pitch/yaw/roll control; the ship banks and pitches **visually** only, with caps.
6. **Controls:** abstract named actions only (section 5.2). Keyboard now, controller later through the same actions.
7. **One gameplay button:** `fire` (hold). Auto-aim assist with a soft lock-on ring. One optional cosmetic button `honk`. Any other unbound button also triggers `honk`, so button-mashing is always harmless and fun.
8. **No fail state.** No health, no game over. Collisions bounce and gently stall; enemies pop into soft puffs. Progress is a counter of collected glow orbs shown as filling shapes, never numbers.
9. **Vehicle per level, no switching mid-level.** Levels alternate AIR / HOVER.
10. **Content:** 6 levels of ~2.5–3 minutes each (see section 1.5), 2 player ships × 3 colour variants, 3 enemy types + 1 gentle guardian at the end, 1 pickup (glow orb).
11. **Pace:** forward speed 14–16 m/s (air) and 10–12 m/s (hover) as *starting values*; tune by feel using the bot and screenshots, then by my playtests. A `game_speed` setting in the parent menu (0.6× / 0.8× / 1.0×).
12. **Difficulty is invisible and only goes easier:** a dynamic assist widens gaps and slows the rail slightly if the child keeps bumping. It never gets harder because the child is doing well, only because levels progress.
13. **Audio is generated, not downloaded:** sound effects and music are synthesised with Python (`audiokit.py`), so they are original and release-safe.
14. **No localisation of the child's UI** (there is no text). The parent menu uses a translation table (en + es) so adding a language is trivial.
15. **Save data:** `user://save.json` (levels cleared, orb count per level, unlocked colours, settings, input bindings). Never crash on a missing or corrupt save; fall back to defaults.
16. **Units:** 1 Godot unit = 1 metre. Ship length ≈ 6 m. Forward axis = −Z. Origin at the ship's centre of mass.
17. **All assets are original or have a recorded licence.** Mechanics may be inspired by existing games; **no names, designs, characters, ship shapes, level layouts, music or sound from any existing game, film or franchise appear in code, art, audio, filenames, comments shipped in the build, or the title.** Reference games may be named only in `docs/DECISIONS.md`.
18. **Working title:** "Sky Skimmers" (placeholder; do not claim it is unique — a name check is needed before any store page).
19. **The child can never quit by accident.** Quit/settings only through the parent menu (hold Start+Select, or F1, for 3 seconds). Window close (Alt+F4) is allowed because it is a deliberate OS action.
20. **Focus loss pauses the game.**

---

## Definition of complete (the finish line)

The game is done only when **all** of this is true, verified, and written in `docs/DONE.md` with evidence:

- [ ] Boots to a title screen with sound; one press starts play (no text required).
- [ ] 6 levels playable start to finish, with checkpoints, and a gentle ending sequence that closes the loop (section 1.5).
- [ ] A "sticker book" progress screen (icons only) showing cleared levels and collected orbs; unlocks 3 ship colours.
- [ ] Pause works from every gameplay screen; restart and return-to-title work from the pause menu (and `R` on keyboard).
- [ ] Parent menu: volume (music/effects), game speed, retro look on/off, fullscreen/windowed, invert vertical, **input rebinding**, deadzone, reset save, quit. English + Spanish strings.
- [ ] Input rebinding works for keyboard **and** an unknown gamepad (learn mode: "press the button you want for FIRE").
- [ ] Saves and loads; survives a deleted or corrupt save file.
- [ ] Audio: music loop per biome, all effects, mix rules respected (section 7).
- [ ] Automated bot completes every level with no script errors; a "bad pilot" bot (random inputs) also completes every level.
- [ ] 60 fps average on the developer's machine; frame-time log attached; no stutter spikes on level load.
- [ ] Exported build runs by double-click on the developer's OS (export templates installed or instructions given).
- [ ] `LICENSES.md` lists every asset and its origin; everything is original-generated or CC0/permissive.
- [ ] `README.md`: how to run, controls, how to rebuild assets with **one command**, how to add a level.
- [ ] Git history with a commit per working milestone.

## Not building (cut line — do not add these)

Multiplayer or co-op, Steam/online integration, achievements, mobile or web builds, voiced dialogue or cutscene movies, a level editor, procedurally infinite levels, weapons/upgrades shop, health/lives, scores or leaderboards, complex physics, text-dependent tutorials, localisation beyond the parent menu.

---

## 0. Setup and the verification loop

Do this first, before any design work, and report the outcome in `docs/DECISIONS.md`.

1. **Detect:** OS, Godot (`godot --version`, install the pinned stable release if missing and network allows; otherwise stop and tell me exactly what to install), Python ≥ 3.10, git.
2. **Python deps:** `pip install shapely trimesh numpy pillow cairosvg mapbox_earcut scipy` (add `--break-system-packages` if pip refuses). Optional: `pyglet`/`pyrender` (not required).
3. **Prove you can see the game.** A game cannot be reviewed from one image. Test, in this order:
   - `godot --headless --import`, then `godot --headless --check-only --script <file>` looped over every `.gd` file (script errors). Note `--headless` uses a dummy renderer, so it cannot take screenshots.
   - A screenshot under a virtual display: `xvfb-run -a godot --rendering-method gl_compatibility --rendering-driver opengl3 --path . res://tests/screenshot_scene.tscn` (Linux; software GL via Mesa is fine) that saves a PNG from `get_viewport().get_texture().get_image()`. (On Windows/macOS render normally; no virtual display is needed.)
   - A scripted bot playthrough (section 10).
   Record what works. **If you cannot capture screenshots, say so at the top of your first report: it means I am the visual tester and you must make every check you can through logs, geometry assertions and bot results instead.**
4. `git init`, create the folder structure of section 5.1, commit.

---

## 1. Design before code

Generated-looking games come from **defaults**: symmetric levels, evenly spaced enemies, one template scaled, identical gaps, power shown as glow and particles. Every choice needs a reason you could say out loud.

### 1.1 References

Look up (if you can search; otherwise say so and flag what you're unsure of) *principles*, never designs:
- **Rail-shooter feel:** camera distance and height, how the ship banks into lateral movement, lock-on behaviour, how walls are telegraphed, pacing of enemy clusters vs rest areas.
- **Hover/air behaviour:** how hovercraft and gliders bob, lean, and follow terrain.
- **Early-childhood game design:** big targets, forgiving timing, immediate feedback for every input, audio-visual rewards, no punishment, short sessions.
- **Motion comfort:** stable horizon, low angular velocity, no camera shake.
Never copy a specific ship, character, level, logo or composition. Write what you learned in `docs/DESIGN.md` §1.

### 1.2 Design brief (write before any code; keep it to one page)

1. **Concept** — one or two sentences, the story, readable without words. *(Default: two little glowing skimmer ships carry a lantern of light through soft pastel canyons of giant floating mountains, popping grumpy drifting critters, collecting glow orbs, and finally lighting the Sky Gate so the sun rises.)*
2. **The one thing it must feel like at 1×:** gliding through a gap in something enormous, slowly and safely.
3. **Silhouette** — every ship and enemy recognisable as a solid black shape at game distance, and distinct from each other.
4. **Materials** — painted hull, soft metal trim, glass canopy, glowing engine/orb. How each reacts to light.
5. **Light** — one key direction for the whole game (default: high, from upper-left-behind). Emissive things (engine glow, bubbles, orbs, lock-on ring) are *additional local lights*; see 1.6.
6. **Palette** — 4–6 colours per material family, **hue-shifted** (shadows cooler/purpler, highlights warmer), softened/pastel. Outlines are the *darkest colour of that material's ramp*, never pure black. One palette file drives everything.
7. **Scale and context** — what surrounds a ship decides how big it feels. Giant mountains and wide sky walls make a small ship feel fast and brave.

### 1.3 Design rules (translated to a game)

- **Focal hierarchy.** Star: the lit path through the gap. Secondary: the glow orbs along that path. Everything else is quiet. Leave rest areas.
- **Cluster, don't sprinkle.** Enemies and orbs in groups of 1/3/5, varied, at places that make physical sense. Evenly spaced enemies read as a shooting gallery.
- **Asymmetry with a reason.** Canyons curve, walls have uneven gaps, mountains differ. Never mirror a level about its centreline.
- **Imperfection tells the story.** Chipped wall edges, a crashed old ship in the canyon, moss on a ledge, a patched hull.
- **Exaggerate for readability.** Oversized bubbles, generous hit radii (+50% on enemies), bright telegraphed gaps and enemies.
- **Nothing floats unless it is meant to.** Floating islands are a deliberate motif; every other prop sits on, or is attached to, something. Compute attachments from parent geometry.
- **Faces: intentional only.** Enemies may have simple, friendly-grumpy faces (cute, never scary). Player ships and environment must not accidentally read as faces (two dark windows over a line, paired knotholes, symmetrical arches with two lights).

### 1.4 The player (design constraints that override taste)

- Age 4: one thumb on the stick, one finger on a button. Reaction time is slow: telegraph everything ≥ 3 s ahead at the starting speed.
- Cannot read: all meaning by shape, colour, motion and sound. The only text lives in the parent menu.
- Frustration limit is low, attention is short: levels ≤ 3 min, a calm rest area every ~40 s, rewards (orb chimes, sparkle, happy ship wobble) every ~8 s.
- Motion comfort: stable horizon, banking ≤ 22° visual, pitch ≤ 12° visual, no sudden accelerations, rail speed changes eased over ≥ 1 s.
- Peace and warmth come from light and stillness, not from strong effects. Calm beats chaotic.

### 1.5 Levels and progression (transformation story first)

The loop: the first canyon is small and green; the last level returns to that canyon, huge and at sunrise.

| # | Name (internal) | Mode | Biome / look | What's new | Why |
|---|---|---|---|---|---|
| 1 | Meadow Canyon | AIR | wide green canyon, soft morning, gentle hills | steer + fire, orbs, one wide wall with one huge gap, Drifters only | teach everything without words: orbs and a glowing arrow-shaped gap lead the eye |
| 2 | Sunrise Dunes | HOVER | warm peach dunes, low sun | terrain-following, hop (W lifts), ramps, rocks | introduce the second vehicle |
| 3 | Cloud Ridge | AIR | cool blue peaks above clouds | 3 walls with uneven gaps, first Pods | gap-threading is the star |
| 4 | Crystal River | HOVER | pink/violet crystal gorge, glowing water | narrower corridor, Buzzers, arches to pass under | rhythm and clusters |
| 5 | Mist Peaks | AIR | lavender mountains, fog, floating islands | mixed enemies, moving (slow) wall gaps | confidence test; still gentle |
| 6 | Sky Gate | AIR | level 1's canyon seen again, giant-scale, dawn → sunrise | the gentle Guardian, all orbs light the Gate | closes the loop; ending |

Each level gets: its own palette (same ramp structure, different hues), its own mountain/rock *shapes* (not rotated copies), its own music, and its own landmark (a distant silhouette that hints at the next level). Write this table, with a silhouette sketch idea per row, into `docs/DESIGN.md` before building.

**Ending:** the Gate lights up, the camera rises, the sun comes up over the level-1 canyon in miniature, the sticker book fills, fade to title. No text.

### 1.6 Light from glowing things

- Glow is **light on the things around it**: the hull near the engine, the canyon walls near a bubble, the ground under a hovering ship, orb light on the rock beside it. Use point lights sparingly (Compatibility renderer limits): prefer **baked-in vertex-colour ramp shifts** near emissive objects (computed in the generator) and a few real lights with short range.
- **No "halo bubbles."** No large translucent spheres around ships. A small additive sprite bloom on the brightest pixels is fine.
- **One shared glow ramp** for every glowing thing (e.g. teal → cyan → white) so engines, bubbles, orbs and the lock-on ring read as one family and can **pulse together** from one clock.
- Small glowing things (orbs, bubbles) are drawn 2–3× "real" size or they vanish in a big scene.

### 1.7 "Looks generated" checklist — fix any that apply

- [ ] Every enemy uses the same body template, only scaled
- [ ] Levels are symmetric about the path
- [ ] Enemies/orbs evenly spaced like buttons
- [ ] Every mountain is the same shape rotated
- [ ] Every wall gap is the same width and height
- [ ] Power shown as glow blobs, sparkles and halos instead of design
- [ ] Ramps are single-hue; outlines pure black
- [ ] Same shading formula on every material
- [ ] No wear, damage or story anywhere
- [ ] Floating things with no attachment or reason

### 1.8 Environments

- **Scale contrast:** the ship is small; the world is giant. Put huge shapes at the frame edges and distant ones in fog; show scale with a tiny bird-like critter near a gigantic arch.
- **Frame with dark masses, light in the middle:** near rock is the darkest value, the lit path through it the lightest. The eye path: gap → orbs → enemies → distant landmark.
- **Walls across the sky:** big, thick, readable slabs with irregular gaps, bright edge trim around the gap (the "safe" shape glows softly), height varies, never a ruler-straight top edge.
- **Mountains:** single peaks, ridgelines and canyon walls with different profiles per biome; noise-displaced, then masked outside the corridor.
- **Sky/fog:** per-level gradient sky + fog colour matched to the far silhouettes; fog is the depth cue and hides pop-in.
- **Contrast:** darkest value near-black-blue, lightest near-white tinted by the key light; rim light only near light sources.

---

## 2. Mechanics specification (starting values — tune by feel)

### 2.1 Rail and camera
- `Path3D` per level from the level JSON centreline. The ship's anchor is a `PathFollow3D`; the ship is offset inside it by (x, y).
- Rail speed: eased to a stop in front of walls when blocked (see 2.4), eased back up. Speed changes always eased ≥ 1 s.
- Camera: child of an anchor trailing ~12 m behind and ~4 m above, looking slightly ahead; position lag ~0.25 s; rotation lag ~0.35 s; no roll.

### 2.2 Steering
- Input: `Input.get_vector("steer_left","steer_right","steer_down","steer_up")` → a 2D value in [-1, 1]. **Keyboard input is smoothed** (ramp 0.12–0.18 s up, 0.10 s down) so WASD behaves like a stick; a real stick passes through its deadzone and curve.
- Ship cross-section velocity: target = input × max (12 m/s air, 10 hover); approach with exponential smoothing (~6/s). No inertia surprises.
- Visual banking: roll = −lateral_velocity_fraction × 22° (smoothed), pitch = vertical fraction × 10° (smoothed). Body only; the camera does not roll.
- **Boundaries:** soft push-back over the outer 4 m of the corridor cross-section (the ship drifts back before it ever touches a wall).

### 2.3 Hover vs air
- **Air:** cross-section box inside the corridor (e.g. ±26 m wide, 4–30 m above floor, per level). Mountains and walls are solid.
- **Hover:** the ship is held at `hover_height` (default 3 m) above the terrain by a critically-damped spring on a downward ray; `steer_up` adds a **hop** (up to +6 m, floats back down); the ship tilts to the terrain normal (capped). Hazards are bumps, arches and narrow gaps, never pits.

### 2.4 Collisions (never damaging)
- Static geometry (mountains, walls, rocks): contact → gentle push away along the surface normal, 0.4 s wobble animation, soft "boop" sound. Control is **never** removed.
- **Wall faces:** the rail eases to a stop in front of a wall (the ship cannot overlap solid); the safe gap glows brighter and pulses; after 3 s of no progress, a soft assist drifts the ship toward the gap. In levels 1–2 the gap also has a mild "magnet" toward it.
- Enemy contact or enemy bubbles: the same soft bounce and boop. **Nothing is ever lost** (no orbs, no progress).
- Collision shapes are **simplified** (boxes/convex hulls generated alongside the render mesh), never the render mesh.

### 2.5 Combat
- `fire` held: soft bubble shots, ~4/s, 60 m/s, range 120 m, oversized and slow-reading. Auto-aim cone ~12°: shots curve to the nearest target in the cone. A soft lock-on ring (glow ramp) hovers on the target; it appears 0.3 s before shots curve, never flickers.
- **Enemy types** (each a different silhouette and behaviour; all burst into soft puffs and release 1–3 orbs):

| Name | Silhouette | Behaviour | Hits | Threat |
|---|---|---|---|---|
| Drifter | round body, two little fins | floats slowly across the corridor in groups of 3–5 | 1 | none (only bounces if touched) |
| Pod | tall mushroom/stalk on ground or wall | stationary, fires one slow, large, visible bubble every ~3 s | 2 | a dodgeable bubble that only bounces |
| Buzzer | thin crescent | slow figure-8 around a point in rest-free zones | 2 | none |
| Guardian (finale) | huge, rounded, ancient | drifts in the Sky Gate; each hit makes it glow lighter; after ~25 hits it falls asleep and becomes the gate's lamp | 25 | none |

- **Orbs:** collect by flying through (generous 2.5 m radius); chime + sparkle; each level has ~40 orbs in clusters along safe paths and slightly off them.
- Enemy bursts are real animations: shrink-wobble → puff → orbs float out. Nothing blinks out of existence.

### 2.6 Progress, checkpoints, restart
- Level ends at the end of the rail: a short, calm celebration, orb count shown as filling shapes, then the sticker book.
- Checkpoints every ~45 s of rail. Restart is **never reachable by accident**: on keyboard `R` (tap = last checkpoint, hold 1 s = whole level) is for the parent; on a pad, restart exists only inside the pause menu as a big icon. A stray button press can pause or honk, but never restart, quit or lose progress.
- No game over exists. If the child stops steering, the ship keeps flying and is nudged away from obstacles.

### 2.7 First 60 seconds of level 1 (teach with no words)
Open sky, empty rail 5 s (the child discovers steering because the ship visibly responds); a line of 5 orbs curving gently left→right (follow them to learn steering, with chimes); 3 slow Drifters directly ahead in line of sight (the lock-on ring appears on the nearest; a glint on the ship's nose pulses to hint at the fire button until it is first pressed); the first wall with one very large glowing gap. After a successful pass, a happy ship animation + sparkle.

---

## 3. Build assets from geometry

### 3.1 Conventions
- Colours are named `FAMILY+DIGIT`, dark → light, first letter = material family (e.g. `h0..h4` hull, `t0..t3` trim, `g0..g3` glass, `e0..e3` emissive, `r0..r4` rock, `m0..m3` moss). One `assets/palette.json` drives everything, with a separate per-level palette block.
- **Vertex-colour, flat-shaded** meshes: export non-indexed faces with per-face normals; colour per face from the ramp (shadow = ramp step down on faces turned away from the key light, highlight = step up on faces toward it). **Verify in Godot** that vertex colours import and display; if the importer does not set albedo-from-vertex-colour, assign one shared `ShaderMaterial` that multiplies `COLOR`.
- Outlines (optional, recommended): inverted-hull or screen-space edge in the **darkest ramp colour of the surface's family**, thin.
- Build order within a ship: hull, wings, engines, canopy, details. Seeds for any jitter are fixed non-negative integers and **per element**, so regenerating never changes an unrelated part.
- Minimum feature size: a detail that must read at game distance is ≥ 0.35 m on a 6 m ship; a window or fin thinner than that merges into the hull at the retro resolution. Small parts need contrast with their surroundings.
- Pivots: ship at centre of mass; enemies at their centre; terrain pieces at their base centre.

### 3.2 Toolkit (write these in `tools/`)

**Port verbatim from `reference/pixel_pipeline.md` if present** (they are geometry/time helpers, dimension-agnostic):
- `shapekit.py`: `spline`, `tapered`, `stroke`, `facing`, `lit`, `dark`, `shade` logic (adapt the *idea* to meshes). Do not port `snap`/`pixel` (they are pixel-grid specific).
- `anim_kit.py`: `ease`, `sched`, `pulse`, `wave`, `Persistent`, `resample`, `lens`.
- Palette convention, hue-shifted ramps, the "never write per-asset hacks — fix the design in the generator" rule.

**New, write yourself:**
- `meshkit.py`
  - `extrude(poly, width, cap=True)` and `extrude_profile_x(poly)` (a Shapely side profile extruded across the ship's width via `trimesh.creation.extrude_polygon`, centred).
  - `visual_hull(side_poly, top_poly)` = intersection of the two extrusions (hull from two silhouettes).
  - `loft(stations, closed=True)` for fuselage cross-sections along a spline (tapered tubes: noses, tails, tentacles).
  - `lathe(profile)` for rotationally-symmetric parts (engine pods, mushroom stalks).
  - `boolean_diff/union` through `trimesh` (use `manifold3d` if installed; otherwise do cuts in 2D before extruding).
  - `attach(parent_mesh, local_point, normal)` returns a transform so parts sit on surfaces.
  - `mirror_x(mesh)` for ships (mirrored is *correct* for a ship; asymmetry comes from damage/trim details) — **but never mirror environment pieces.**
  - `bake_palette(mesh, ramps, light_dir, glow_sources)` → per-face colours (ramp step by facing, plus glow-light shifts near emissive sources).
  - `export_glb(meshes, path)` including a separate simplified collision mesh named `<name>_col`.
- `terrain.py` — corridor generation (below).
- `audiokit.py` — procedural audio (section 7).
- `review3d.py` — review sheets (section 9.1).
- `example_ship.py` — **write this first**, as the worked example the rest copy: a tiny ship from a side profile + top profile → `visual_hull` → one tapered wing pair → canopy cut → palette bake → `.glb` + `_col` mesh → review sheet. Every other generator follows its structure (palette in, geometry built back-to-front, one `build()` entry point, fixed per-element seeds).
- `build_all.py` — **one command** that regenerates every ship, enemy, prop, biome kit, level JSON, sound and music file, then runs the checks.

### 3.3 Which operation does what (3D edition)

| Want | Move |
|---|---|
| Hull from a side silhouette | Shapely polygon → `extrude` across width |
| Hull from side + top silhouettes | `visual_hull` |
| Wings, fins | `stroke`/`tapered` 2D shape → thin `extrude`, placed with `attach` at hand-chosen points |
| Canopy | scaled sphere/lens, difference-cut into the hull, glass ramp |
| Engine pods and glow | `lathe` + emissive-ramp faces on the nozzle |
| Tears, notches, bites (wear) | 2D `difference` with a wedge cutter *before* extruding |
| Tentacles, tails, stalks | `loft` along a hand-placed spline with a width profile that reaches ~0 |
| Canyon corridor | spline centreline, `buffer` for width (varying), terrain carved inside it |
| Mountains | heightmap noise (fixed seeds, different per biome) masked outside the corridor, plus a few hand-shaped hero peaks |
| Walls across the sky | footprint polygon extruded tall, gaps cut with `difference`, bright trim on the gap rim |
| Arches | 2D arch polygon (outer minus inner) extruded thick |
| Floating islands | lathe/loft cone-ish underside + flat top, moss patch on top |
| Merge parts | `unary_union` in 2D; mesh union only when needed |

### 3.4 Asset list (build all)

| Asset | Count | Silhouette idea | Notes |
|---|---|---|---|
| Air ship "Kite" | 1 (+2 colourways via palette swap) | wide swept-delta wing, short nose, twin small engines | readable from behind (camera sees its back) |
| Hover ship "Sled" | 1 (+2 colourways) | low, rounded, wide skirt, single rear engine, canopy forward | the skirt shows the hover |
| Enemies | Drifter, Pod, Buzzer, Guardian | see 2.5 table | each with burst animation data |
| Biome kits | 6 | per biome: 3 mountain/ridge variants, 2 rock/crystal clusters, 1 arch, 1 wall style, 3 props, 1 distant landmark | not rotated copies of each other |
| Pickups | orb | small sphere-ish gem, emissive ramp | drawn 2–3× real size |
| FX | bubble shot, puff burst, engine trail, dust trail (hover), sparkle, gap glow, lock-on ring | | share the glow ramp |
| UI icons | play, sticker book, gear, restart, speaker, ... | simple bold shapes | author as Shapely → SVG → PNG via `cairosvg` (the original 2D toolchain still applies to UI) |

### 3.5 Technical limits
```
TRIS PER SHIP:         ≤ 1500          TRIS PER ENEMY:   ≤ 700 (Guardian ≤ 4000)
TRIS VISIBLE / LEVEL:  ≤ 80,000        DRAW CALLS:       ≤ 250 (use MultiMesh for repeated props)
TEXTURES:              none (vertex colour)    EXPORT: glTF binary (.glb)
NAMING:                snake_case; ships ship_air_kite.glb, enemies enemy_drifter.glb, kits biome_<n>_<piece>.glb
```
Add automatic assertions in `build_all.py` that fail the build if a limit is exceeded.

---

## 4. Levels as data

Levels are **generated from geometry into JSON**, then built at runtime by one generic loader. Never write per-level script hacks.

`levels/level_N.json` contains: `mode` (air/hover), `rail` (3D control points, smooth), `corridor` (width and height profile along the rail), `terrain_seed`, `biome`, `palette` (sky, fog, key light colour/energy, ramp overrides), `walls` [ {s: distance along rail, gap: polygon in cross-section, thickness, trim colour, motion: optional slow slide of the gap panels, used from level 5} ], `props` (kit pieces with transforms, placed deliberately in clusters), `enemies` [ {type, s, offset, group_pattern} ], `orbs` [ clusters along safe paths ], `checkpoints`, `rest_areas`, `music`, `landmark`.

`terrain.py` builds, for each level: the rail from hand-placed control points, the carved terrain mesh, the walls with gaps (never the same gap size twice; gap sizes and positions follow a table that starts wide and narrows slowly across levels), props, and a **top-down + side-view debug PNG** of the whole level so you can review the layout without running the game.

Gap sizes (starting values): ship collision radius ≈ 2 m. Level 1 gap width ≥ 40 m, level 6 ≥ 22 m. Gaps are never narrower than 10× the ship radius.

---

## 5. Godot implementation

### 5.1 Project structure
```
project.godot            # pinned version noted in README
assets/                  # generated: ships/, enemies/, kits/, fx/, ui/, audio/, palette.json
levels/                  # generated JSON
scenes/                  # title, level_runner, sticker_book, parent_menu, ending, credits
scripts/                 # game/ (rail, ship, combat, orbs, walls), systems/ (input_map, save, audio, settings, assist), ui/
tools/                   # python generators + build_all.py + run_tests.sh
tests/                   # bot playthroughs, screenshot scenes
docs/                    # DESIGN.md, DECISIONS.md, ITERATIONS.md, DONE.md
reference/               # pixel_pipeline.md (original prompt, read-only)
LICENSES.md  README.md  CREDITS (in-game, no-text/icon credits plus text in parent menu)
```

### 5.2 Input abstraction (MANDATORY)

Game code **must not** reference keys, mouse or joypad buttons. It uses only these named actions, defined in `project.godot` (and again in code, so rebinding can rebuild them):

`steer_left`, `steer_right`, `steer_up`, `steer_down`, `fire`, `honk`, `pause`, `restart`, `menu_accept`, `menu_back`, `menu_left/right/up/down`, `parent_menu_hold`.

- **Default keyboard bindings:** `W/A/S/D` (also arrows) steer, `Space` fire, `H` honk, `Esc` pause, `R` restart, `Enter` accept, `Backspace` back, `F1` (held 3 s) parent menu.
- **Default pad bindings (applied for any pad that Godot reports a standard mapping for):** left stick steer (deadzone 0.2), `A`/`Cross` fire, any other face button honk, Start pause, Select unbound (honk), hold Start+Select 3 s parent menu. Restart is a pause-menu icon only.
- **Unknown pads (a PS2-to-USB adapter often lacks a standard mapping):** a *learn mode* in the parent menu: "press FIRE… press LEFT…" capturing raw axis/button events into the action map; stored in `user://bindings.json`; deadzone adjustable; shows live input values for diagnosing.
- All gameplay reads `Input.get_vector` / `Input.is_action_pressed`. Menu navigation also uses actions so the child can navigate icon menus with the stick + fire.
- **Any unbound button fires `honk`.** Never let a stray press do something destructive.
- **Bots drive the game through these same actions** (`Input.action_press/release`, `parse_input_event`), which is how the automated tests exercise real code paths.
- This is the same idea as a PC port's input layer: the game knows *actions*, the binding layer knows *devices*.

### 5.3 Ship controller
`CharacterBody3D` (or kinematic-style node) child of the rail follower; 2D cross-section motion per 2.2/2.3; model node separate from collision node so visual bank/pitch never affects collision. Typed GDScript, signals for `orb_collected`, `enemy_popped`, `bumped`, `gap_passed`.

### 5.4 Level runner
One `LevelRunner` scene loads a level JSON, builds Path3D, terrain, walls, props (MultiMesh), enemies, orbs, checkpoints, music, sky/fog/light, then starts the rail. Pooling for bullets and puffs. Streaming not required: levels are linear, but **load all required assets before the first frame** (no hitches mid-level).

### 5.5 Assist system
`AssistDirector` tracks bumps and stalls (rolling window). More bumps → widen effective gap magnetism, reduce rail speed up to −25%, soften boundary push. It decays back slowly. It never makes the game harder, and it is invisible.

### 5.6 Settings, save, parent menu
Autoload singletons: `Settings`, `Save`, `AudioBus`, `Bindings`. Parent menu is a plain, readable UI (text ok), openable from any screen by the hold gesture. Saves on every change; atomically (write temp, rename).

### 5.7 Rendering look
- Compatibility renderer, one `DirectionalLight3D` with soft shadows **off** (or a single simple blob shadow under each ship, which is cheaper and reads as "ground contact" in hover mode), `WorldEnvironment` with per-level sky gradient, fog (depth fade tinted like the far silhouettes), mild tonemapping, optional glow bloom on emissive.
- Retro mode: `SubViewportContainer` at 640×360, `stretch` on, texture filter NEAREST, integer upscale to the window; UI renders at native resolution above it.
- Vertex-colour shader (if needed): unshaded or simple lambert with the palette's own light logic baked, plus a rim term only near emissive sources.

---

## 6. Feel and animation

- **One clock drives everything** that animates (engine glow, orb pulse, lock-on ring, gap trim glow, hover bob, music-sync sparkles): write animation as functions of time `t`. Loops use **integer cycles** (`wave(t, cycles)`).
- **Shared pulse:** all emissive things breathe together from one `pulse(t)`.
- **Every input has an immediate response** within one frame: ship banks, sound, particle. A 4-year-old reads cause and effect from feedback.
- **Easing, not snapping:** rail speed, camera lag, bounce recovery, bursts. Use `sched`/`ease` for authored curves.
- **Identity, birth, death:** enemies spawn by fading/growing in from fog; they never pop in at full size inside the camera frustum. Deaths are shrink-wobble → puff → orbs float out.
- **Persistent features stay:** orbs already collected stay collected after a checkpoint reload, passed walls stay lit, defeated enemies stay defeated.
- **Hard limits on juice:** no screen shake; FOV constant; camera roll 0; max ship bank 22°; hit pause 0; particle counts capped; no flashing faster than 2 Hz.
- Frame rate target 60 fps; all gameplay timing based on delta time.

---

## 7. Audio (generated — `audiokit.py`)

- **Effects:** soft bubble shot, puff burst, orb chime (pentatonic, rising with consecutive orbs, resets after a pause), bump "boop", honk, gap-pass sparkle, UI blip, level-complete jingle, engine loops (air hum, hover whirr).
- **Music:** one calm loop per biome + title + ending. Synthesise from sine/triangle/soft-noise voices with ADSR envelopes, built on a major pentatonic or lydian scale, slow tempo (70–90 bpm), simple bass + arpeggio + pad, a different key/mode per biome. Loops must be an **integer number of bars** so they wrap seamlessly; render to `.ogg` (or `.wav` if OGG encoding is unavailable). Fixed seeds so rebuilds are identical.
- **Mix rules:** master peak ≤ −6 dBFS; engine ≤ −20 dB relative to music; no transient louder than the music bed; no sudden loud sounds; fade in/out on every scene change; separate music/effects buses with volume sliders; a master limiter.
- Check each file with a script (peak, RMS, loop-seam continuity) and put the results in the review log.

---

## 8. Product shell (what makes it a *complete* game)

- **Title:** the Kite and Sled idling in a calm scene; one press starts. Icons only: Play, Sticker Book, (hidden) Parent.
- **Level select = sticker book:** six page-tiles showing each level's landmark silhouette and the orbs collected as filled shapes; completed levels show a sticker; choose with stick + fire.
- **Level complete:** short calm celebration → return to book.
- **Pause:** big icon menu (resume, restart, book). Opens on focus loss.
- **Ship choice:** Kite/Sled are tied to levels; colourway chosen in the book (unlocked after levels 2, 4, 6).
- **Ending + credits:** wordless ending sequence; credits screen with icons and text, reachable from the parent menu and shown after the ending.
- **Errors never reach the child:** missing audio/asset → log + silent fallback, never a crash dialog. Unhandled script error at runtime → return to title, not to desktop.
- **Parent menu items:** per the Definition of complete. Reset-save requires a confirmation hold.

---

## 9. Review and iterate

### 9.1 Asset review sheets (`review3d.py`)
For every ship/enemy/kit piece, render a sheet and **look at it** before moving on: front, side, top, 3/4, rear (the camera sees ships from behind), a **solid-black silhouette**, and a **game-distance render** at the actual in-game pixel size (e.g. 64 px tall at retro resolution) on light, mid, dark and foggy backgrounds. If Godot can render under your verification loop, use it for the 3/4 and in-level views; otherwise rasterise with a simple orthographic painter's-algorithm in Pillow (adequate for flat low-poly).

Questions, in order:
1. Silhouette: readable as a solid shape? In a set, every member distinct?
2. Game-distance read: does it register in one glance at its actual size?
3. Focal hierarchy: one star, rest quiet?
4. Values: squint — grouped light/mid/dark, or noise?
5. Light: one key direction? Does glow light its surroundings with falloff?
6. Materials: does each read as itself?
7. Survival: did any detail vanish, merge, or become a blob at retro resolution?
8. Accidental shapes: faces, eyes, letters, weapons that look too aggressive?
9. Backgrounds: survives light, dark, fog, and its real level?
10. Brief: does it say what the brief says?

### 9.2 Game review (per build, via screenshots + bot logs + my playtest)
- First 30 seconds make sense with no explanation?
- Can the player always tell where to go? Is every wall visible and its gap obvious ≥ 3 s ahead?
- Can anything happen that the child won't understand (a surprise, an unexplained stop)?
- Motion comfort: any camera acceleration, roll, shake, or speed pop?
- Do all inputs respond visibly within one frame? Does mashing every button stay harmless?
- Frame-time stable? Memory stable across all levels?
- Do orbs and rewards arrive often enough? Are there calm rest areas?

### 9.3 Failure → fix (fix in the generator/level data, never with a per-asset hack)

| What you see | Fix |
|---|---|
| Ship is a featureless blob | change the silhouette (wing sweep, engine pods), not the size; add one asymmetric detail |
| Detail vanishes at retro resolution | ≥ 0.35 m, more contrast, fewer bigger parts with own colour |
| Parts look stuck on / floating | compute attachment from the parent surface (`attach`) |
| Ships/enemies look alike | change silhouette and motion, not scale |
| Mountains look like rotated copies | different profile curves and noise seeds per kit piece, hero peaks hand-placed |
| Level feels like a flat tube | vary corridor width/height along the rail, add rest basins and pinch points |
| Walls unreadable until too late | brighter gap trim, fog starts later, telegraph glow pulses from far away, add orbs through the gap |
| Child can't tell where to go | orbs lead through the gap; gap rim glows; fewer simultaneous things |
| Gap size is always the same | follow the gap table; vary shape (tall, wide, offset, low) |
| Ship collides with walls and gets stuck | soft boundary push, rail stall + gap assist, simplified collision hull |
| Hover ship jitters over terrain | critically-damped spring, smooth the terrain normal, lower tilt cap |
| Camera feels nauseating | reduce lag/rotation, lock roll, lower banking cap, ease speed changes |
| Glow looks like a blob/halo | light on neighbours with falloff and a small sprite bloom; no halo spheres |
| Enemies feel like targets in a gallery | cluster in odd groups with varied heights and timing; add rests |
| Enemies look scary | rounder, softer colours, simple friendly-grumpy face, bigger eyes, slower motion |
| Lock-on flickers | hysteresis (keep target until it leaves a larger cone) |
| Audio too harsh/loud | lower highs, softer attack, limiter, check peaks |
| Music loop pops | integer bars, matching tail/head, zero-crossing fades |
| Level load hitches | preload, pool, MultiMesh for props, simplify collision |
| Palette looks muddy | hue-shift ramps (cooler shadows, warmer highlights), raise lightest value, lower fog density |
| Scene feels small | zoom out props, bigger distant silhouettes, hero scale reference, more fog layers |
| Button mashing breaks something | route unknown buttons to `honk`; audit every action for state conflicts |

### 9.4 Iteration discipline
- Change 1–3 things per round, at the design level; regenerate; keep a **one-line log per round** in `docs/ITERATIONS.md`.
- A typical asset needs 3–6 rounds; a level needs bot + screenshots + my playtest.
- **Vertical slice first:** one level section with one Kite, one wall with a gap, one Drifter cluster, orbs, flying and shooting, complete with sound — before any second ship or level.
- Last mile: geometry gets ~90%; list in the README what a 3D artist or sound designer should hand-touch.

---

## 10. Automated checks (`tests/`, `tools/run_tests.sh`)

- `godot --headless --import`, `--check-only` on all scripts: zero errors.
- **Bot pilot:** follows the orb path using only input actions; must finish every level. **Bad-pilot bot:** random holds and mashes; must also finish (the assist system and soft bounds guarantee it). Record time-to-complete, bumps, stalls, orbs, frame times.
- **Geometry assertions:** every gap ≥ minimum; every level's rail has no sharp curvature spike; no prop intersects the rail corridor; all assets within poly budget; all `.glb` have `_col` meshes.
- **Screenshot tour:** capture frames at fixed rail positions of every level (start, each wall, mid-rest, end) and store them in `docs/shots/`; build a contact sheet. If I'm the visual tester, this is what I look at.
- **Audio checks:** peak, RMS, loop seam.
- **Save fuzz:** delete / corrupt `save.json`, boot, expect clean defaults.
- **Input fuzz:** unplug/replug pad (if possible), unknown-pad learn mode logic, all-buttons mash.
- Tests run in one command and print a pass/fail table.

---

## 11. Deliver

- The Godot project (git-tracked), the generators, the palette, **one rebuild command** (`python tools/build_all.py`), and `tools/run_tests.sh`.
- An **exported build** for the developer's OS in `build/` (install export templates if needed, or say exactly what to install), plus a `run` script.
- `docs/DONE.md` ticking the Definition of complete with evidence (test output, screenshots, frame-time log).
- `LICENSES.md` with every asset origin (all generated by this repo's scripts, plus any tool/library licences: Godot MIT, Python libs), `CREDITS`.
- `README.md`: design brief summary, level/enemy tables, controls and rebinding, timing, iteration log highlights, known issues, what a human should touch up, and how to add a level.
- A short **playtest guide** for me: what to watch my son do, what to note (where he got lost, where he laughed, what he ignored).

---

## 12. Process, gates, and how to talk to me

- **Order:** 0 setup → 1 design docs → toolkit → vertical slice → **GATE A** → remaining levels/enemies → product shell → polish/QA → **GATE B** → export → **GATE C**.
- **Stop only at three gates and report concisely:**
  - **Gate A (vertical slice):** screenshots, a built executable, bot result, and the three things you are least sure about (default candidates: feel of steering, readability of the gap, audio mood). Wait for my playtest.
  - **Gate B (feature-complete):** all Definition-of-complete boxes ticked except final polish; list of known issues.
  - **Gate C (final):** exported build and `DONE.md`.
- **Everywhere else, decide and keep going.** Log decisions in `docs/DECISIONS.md` (reading taken, reason, how to change it). Ask me only if a decision is expensive to reverse **and** could reasonably go either way, or you are blocked by something I must install/do.
- **Report format:** what changed, evidence (screenshot paths, test table), what you'll do next. No narration of effort. If something does not work, say so first.
- **Commits:** one per working milestone, imperative message, tests passing at each.
- **Never** deliver the first build, hide a failing test, or mark a box in `DONE.md` without evidence.
````

---

## 2. Follow-up directions

These are the prompts that changed scope or direction, in order. Small fixes are left out.

1. *"You can close at 2 levels, not 6. the other 4 can be 'under dev'."* The first build had 2 complete levels.
2. *"make the sound smooth, add all levels"*: levels 3–6 were added, along with the first audio smoothing pass.
3. *"sound is not smooth yet, very crispy… I can't even hear the engine… add the menu settings for speed. also change the bullet sound to something like a zap… a good readme to share this to github"*
4. *"sound is still too crispy, there is a squared digital hum… add some more props and outlines. and extend speed up to 150x in selector"*, plus a pause-menu stacking bug report.
5. *"also add mit license. and add a prompt.md with the original prompt used to create this whole project"*: that request created this file.

The full decision trail is in [`docs/DECISIONS.md`](docs/DECISIONS.md) and [`docs/ITERATIONS.md`](docs/ITERATIONS.md).
