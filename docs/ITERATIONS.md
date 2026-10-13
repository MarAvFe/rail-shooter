# Iterations (one line per round)
- R1 actors: lathe axis was Z (engines/stalks sideways) -> fixed in meshkit.lathe; glow parts get facet steps so orbs read as gems.
- R2 actors: Guardian horns read devilish -> round ears.
- R3 level1: floor ribbon winding/order fixed (floor was folded/back-facing); rock -> warm stone, sky walls -> own lavender ramp so the gap reads.
- R4 UI: book icon read as a pause symbol -> redrawn as an open book with slanted pages.
- R5 audio: all sounds rebuilt smooth (sine voices, raised-cosine attacks, low-pass, small reverb, 32 kHz), quieter peaks; engine hum -> soft wind; AudioBus anti-stacking (70 ms, max 2 copies); hit tick replaces pitched boop.
- R6 levels 3-6: added as data; L6 Gate + Guardian + sunrise sky; fixed wall-front freeze found by bad bot.
- R7 audio: crispiness = Godot's default lossy QOA WAV import -> PCM (importer_defaults); engine -> audible 110 Hz hum following speed; shot -> soft zap. UI: pause-menu speed chevrons, finer parent speed steps, title gear (hold 1.5 s).
