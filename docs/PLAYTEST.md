# Playtest guide (for the parent)

**Setup:** start `SkySkimmers.exe`. If you're using the PS2 pad, first hold F1 for 3 s → *Set up a controller…*. Then hand over the controller and say nothing. Watch the first two minutes without helping.

## Watch for
1. **First 10 seconds:** does he discover steering by himself? (The rail is empty for 5 s, then a line of orbs curves left to right.)
2. **Fire:** does he find the button? A white glint pulses on the ship's nose until he first fires. How long until he presses it?
3. **The first wall (~30 s in):** does he see the glowing gap early? Does he aim for it, or does the ship stall in front of the wall? A stall is fine; note how long before the assist pulls him through.
4. **Hover level:** does he figure out that Up makes the Sled hop? Does he steer around rocks or bump into them?
5. **Mood:** where does he laugh? Where does he look bored or frustrated? Does any sound startle him?
6. **Comfort:** any sign of motion discomfort?
7. **Mashing:** does mashing buttons ever do something confusing? It should only honk.
8. **Attention:** at what point does he want to stop? Each level is about 3 min.

## Note down (one line each)
- Where he got lost:
- Where he laughed:
- What he ignored:
- Anything he tried that didn't work:
- Speed: too fast or too slow? (parent menu → Game speed 60/80/100 %)
- Retro pixel look on or off: which did he like?

## Easy tuning knobs (tell me the note, or change them yourself)
- Speed: `"speed"` in `tools/levels.py` per level, or the parent menu.
- Gap sizes: `"gap"` tuples in `tools/levels.py`.
- Wall magnet strength: `level_runner.gd`, `magnet = 0.25` (levels 1–2).
