# rail-shooter — Design

## 1. Principles (from general knowledge; no web pass yet)
- Chase cam ~12 m behind / 4 m above, steady horizon; the ship banks, the camera never rolls.
- Children ~4: huge targets, forgiving windows, feedback on every press, no punishment, calm rests.
- Telegraph walls ≥ 3 s ahead (at 15 m/s that is ≥ 45 m; fog starts beyond 120 m).
- Motion comfort: low angular velocity, no shake, eased speed changes.

## 2. Brief
1. **Concept:** two little glowing skimmers carry light through pastel canyons, pop grumpy puff-critters, gather glow orbs, and light the Sky Gate so the sun rises.
2. **Feel:** gliding slowly and safely through a gap in something enormous.
3. **Silhouettes:** Kite = wide swept delta (a "V" from behind). Sled = low rounded slab with a skirt. Drifter = ball with two fins. Pod = mushroom on a stalk. Buzzer = crescent. Guardian = huge round dome.
4. **Materials:** painted hull (h), soft trim (t), glass (g), glow (e), rock (r), moss/ground (m).
5. **Light:** key light high, upper-left-behind the camera, for every level.
6. **Palette:** 5-step hue-shifted ramps (shadow cooler/purpler, highlight warmer), pastel. One `assets/palette.json`, with per-level overrides.
7. **Scale:** canyon walls 60–150 m tall, ship 6 m.

## 3. Levels
| # | Name | Mode | Look | New | Landmark (hints at next) |
|---|---|---|---|---|---|
| 1 | Meadow Canyon | AIR | green canyon, morning | steer, fire, orbs, 1 huge gap, Drifters | distant dune-coloured mesa |
| 2 | Sunrise Dunes | HOVER | peach dunes, low sun | terrain follow, hop, rocks | blue peak above clouds |
| 3 | Cloud Ridge | AIR | blue peaks | 3 walls, uneven gaps, Pods | pink crystal spire |
| 4 | Crystal River | HOVER | pink/violet gorge | narrower, Buzzers, arches | lavender floating island |
| 5 | Mist Peaks | AIR | lavender fog, islands | mixed enemies, sliding gaps | the Gate ring |
| 6 | Sky Gate | AIR | level-1 canyon, giant, dawn | Guardian, Gate lights, sunrise | — |

Gap widths (m): L1 44, L2 36, L3 34/30/28, L4 30, L5 26/24, L6 22+. Never < 20.

## 4. Vertical slice (Gate A)
Level 1 only: rail, Kite, steering, firing with lock-on, a Drifter cluster, orbs, one wall with a big gap, music + effects, and a bot run.
