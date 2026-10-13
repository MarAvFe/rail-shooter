extends Node
## Music (crossfaded) + pooled effects. Missing files are logged and silently skipped.

const DIR := "res://assets/audio/"
const FADE := 1.2

var _sfx: Array[AudioStreamPlayer] = []
var _music: Array[AudioStreamPlayer] = []
var _cur := 0
var _cache: Dictionary = {}
var _chime := 0
var _chime_t := 0.0
var _last: Dictionary = {}  # sound -> last start time (anti-stacking)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for b: String in ["Music", "SFX"]:
		if AudioServer.get_bus_index(b) == -1:
			var i := AudioServer.bus_count
			AudioServer.add_bus(i)
			AudioServer.set_bus_name(i, b)
			AudioServer.set_bus_send(i, "Master")
	Save.apply_settings()
	var lim := AudioEffectHardLimiter.new()
	lim.ceiling_db = -3.0
	AudioServer.add_bus_effect(0, lim)
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_sfx.append(p)
	for i in 2:
		var p := AudioStreamPlayer.new()
		p.bus = "Music"
		add_child(p)
		_music.append(p)


func stream(name: String, loop := false) -> AudioStream:
	if _cache.has(name):
		return _cache[name]
	var path := DIR + name + ".wav"
	if not ResourceLoader.exists(path):
		push_warning("missing audio " + path)
		_cache[name] = null
		return null
	var s: AudioStreamWAV = load(path)
	if loop:
		s = s.duplicate()
		s.loop_mode = AudioStreamWAV.LOOP_FORWARD
		s.loop_begin = 0
		s.loop_end = s.data.size() / 2
	_cache[name] = s
	return s


func play(name: String, pitch := 1.0, vol_db := 0.0) -> void:
	var s := stream(name)
	if s == null:
		return
	# the same sound never restarts within 70 ms, and at most 2 copies overlap: no harsh stacking
	var now := Time.get_ticks_msec()
	if now - int(_last.get(name, -1000)) < 70:
		return
	var copies := 0
	for p in _sfx:
		if p.playing and p.stream == s:
			copies += 1
	if copies >= 2:
		return
	_last[name] = now
	for p in _sfx:
		if not p.playing:
			p.stream = s
			p.pitch_scale = pitch
			p.volume_db = vol_db
			p.play()
			return


## Rising pentatonic chime with consecutive orbs; resets after a pause.
func chime() -> void:
	var now := Time.get_ticks_msec() / 1000.0
	_chime = mini(_chime + 1, 7) if now - _chime_t < 2.0 else 0
	_chime_t = now
	play("sfx_chime_%d" % _chime)


func music(name: String) -> void:
	var s := stream(name, true)
	var old := _music[_cur]
	_cur = 1 - _cur
	var nw := _music[_cur]
	if old.playing:
		var tw := create_tween()
		tw.tween_property(old, "volume_db", -60.0, FADE)
		tw.tween_callback(old.stop)
	if s:
		nw.stream = s
		nw.volume_db = -60.0
		nw.play()
		create_tween().tween_property(nw, "volume_db", 0.0, FADE)


func stop_music() -> void:
	for p in _music:
		if p.playing:
			var tw := create_tween()
			tw.tween_property(p, "volume_db", -60.0, FADE)
			tw.tween_callback(p.stop)
