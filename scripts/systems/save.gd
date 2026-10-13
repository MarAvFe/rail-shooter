extends Node
## Save data + settings in user://save.json. Atomic writes; missing/corrupt file -> defaults.

signal settings_changed

const PATH := "user://save.json"
const LEVEL_COUNT := 6

var data: Dictionary = {}


func _ready() -> void:
	load_data()
	apply_settings()


func defaults() -> Dictionary:
	var lv := {}
	for i in range(1, LEVEL_COUNT + 1):
		lv[str(i)] = {"cleared": false, "orbs": 0, "total": 0}
	return {
		"version": 1, "levels": lv, "colour": 0,
		"settings": {"music": 0.8, "sfx": 0.8, "speed": 1.0, "retro": true, "fullscreen": false,
			"invert_y": false, "deadzone": 0.2, "lang": "en"},
	}


func load_data() -> void:
	data = defaults()
	if not FileAccess.file_exists(PATH):
		return
	var txt := FileAccess.get_file_as_string(PATH)
	var parsed: Variant = JSON.parse_string(txt)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("save corrupt, using defaults")
		return
	_merge(data, parsed as Dictionary)


func _merge(into: Dictionary, src: Dictionary) -> void:
	# only accept keys we know, with the same type as the default
	for k: Variant in into.keys():
		if not src.has(k):
			continue
		if typeof(into[k]) == TYPE_DICTIONARY and typeof(src[k]) == TYPE_DICTIONARY:
			_merge(into[k], src[k])
		elif typeof(into[k]) == typeof(src[k]) or (typeof(into[k]) == TYPE_FLOAT and typeof(src[k]) == TYPE_INT):
			into[k] = src[k]


func write() -> void:
	var tmp := PATH + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		push_warning("cannot write save")
		return
	f.store_string(JSON.stringify(data, " "))
	f.close()
	DirAccess.rename_absolute(ProjectSettings.globalize_path(tmp), ProjectSettings.globalize_path(PATH))


func reset() -> void:
	var keep: Dictionary = data["settings"]
	data = defaults()
	data["settings"] = keep
	write()


func setting(key: String) -> Variant:
	return data["settings"][key]


func set_setting(key: String, value: Variant) -> void:
	data["settings"][key] = value
	write()
	apply_settings()
	settings_changed.emit()


func level(n: int) -> Dictionary:
	return data["levels"][str(n)]


func record_level(n: int, orbs: int, total: int) -> void:
	var l := level(n)
	l["cleared"] = true
	l["orbs"] = maxi(int(l["orbs"]), orbs)
	l["total"] = total
	write()


func unlocked_colours() -> int:
	var n := 1
	for i: int in [1, 2]:  # 2-level scope (was 2, 4, 6)
		if level(i)["cleared"]:
			n += 1
	return n


func apply_settings() -> void:
	var s: Dictionary = data["settings"]
	var win := get_tree().root
	if bool(s["retro"]):
		win.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
		win.content_scale_size = Vector2i(640, 360)
		win.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_INTEGER
	else:
		win.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		win.content_scale_size = Vector2i(1280, 720)
		win.content_scale_stretch = Window.CONTENT_SCALE_STRETCH_FRACTIONAL
	if not DisplayServer.get_name() == "headless":
		var mode := DisplayServer.WINDOW_MODE_FULLSCREEN if bool(s["fullscreen"]) else DisplayServer.WINDOW_MODE_WINDOWED
		if DisplayServer.window_get_mode() != mode:
			DisplayServer.window_set_mode(mode)
	for b: String in ["Music", "SFX"]:
		var i := AudioServer.get_bus_index(b)
		if i != -1:  # buses are created by AudioBus, which re-applies settings
			AudioServer.set_bus_volume_db(i, linear_to_db(maxf(float(s[b.to_lower()]), 0.001)))
	TranslationServer.set_locale(str(s["lang"]))
