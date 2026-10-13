extends Control
## Sticker book: 6 page-tiles (level sky colours + landmark shape), filled orb shapes, a star sticker when
## cleared. Bottom row: ship colourways (unlocked after levels 2, 4, 6). Pick with stick + fire.

const SKY := ["#8ec9f0", "#f5b39a", "#7fb4ea", "#c9a3e8", "#a99ad6", "#f6a98f"]

var _tiles: IconMenu
var _colours: IconMenu
var _row := 0
var _bg: ColorRect


func _ready() -> void:
	_bg = ColorRect.new()
	_bg.color = Color("#fdf1e6")
	_bg.show_behind_parent = true
	add_child(_bg)
	_tiles = IconMenu.new()
	_tiles.icon_size = 80.0
	for i in range(1, 7):
		var built := ResourceLoader.exists("res://levels/level_%d.json" % i) or FileAccess.file_exists("res://levels/level_%d.json" % i)
		var open := built and (i == 1 or bool(Save.level(i - 1)["cleared"]))
		var lv := Save.level(i)
		var icon := "star" if lv["cleared"] else ("ship" if open else ("lock" if built else "cone"))
		_tiles.add_item(str(i), icon, Color(SKY[i - 1]).lightened(0.1 if lv["cleared"] else 0.0) if built else Color("#ffb38a"), open)
	add_child(_tiles)
	_colours = IconMenu.new()
	_colours.icon_size = 80.0
	var pal: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/palette.json"))
	for i in 3:
		var c := Color(pal["colourways"][i][2])
		_colours.add_item(str(i), "ship" if i < Save.unlocked_colours() else "lock", c, i < Save.unlocked_colours())
	_colours.add_item("home", "home", Color("#ffd59e"))
	add_child(_colours)
	_tiles.chosen.connect(func(id: String) -> void: Game.start_level(int(id)))
	_colours.chosen.connect(_on_colour)
	_colours.process_mode = Node.PROCESS_MODE_DISABLED
	_tiles.sel = 0
	for i in range(6, 0, -1):
		if _tiles.items[i - 1]["enabled"]:
			_tiles.sel = i - 1
			break
	AudioBus.music("music_title")


func _on_colour(id: String) -> void:
	if id == "home":
		Game.go(Game.TITLE)
		return
	Save.data["colour"] = int(id)
	Save.write()
	AudioBus.play("sfx_honk")


func _process(_dt: float) -> void:
	var vs := get_viewport().get_visible_rect().size
	_bg.size = vs
	_tiles.position = Vector2((vs.x - _tiles.size.x) / 2.0, vs.y * 0.25)
	_colours.position = Vector2((vs.x - _colours.size.x) / 2.0, vs.y * 0.62)
	var want := _row
	if Input.is_action_just_pressed("menu_down"):
		want = 1
	elif Input.is_action_just_pressed("menu_up"):
		want = 0
	if want != _row:
		_row = want
		_tiles.process_mode = Node.PROCESS_MODE_INHERIT if _row == 0 else Node.PROCESS_MODE_DISABLED
		_colours.process_mode = Node.PROCESS_MODE_INHERIT if _row == 1 else Node.PROCESS_MODE_DISABLED
		_tiles.modulate.a = 1.0 if _row == 0 else 0.6
		_colours.modulate.a = 1.0 if _row == 1 else 0.6
	queue_redraw()


func _draw() -> void:
	# orb progress under each tile: 5 small diamonds
	for i in range(6):
		var n: Control = _tiles.items[i]["node"]
		var lv := Save.level(i + 1)
		var frac := float(lv["orbs"]) / maxf(float(lv["total"]) * 0.8, 1.0)
		var base := n.global_position + Vector2(n.size.x / 2.0 - 40.0, n.size.y + 22.0)
		for k in 5:
			var c := Color("#5fd6c8") if frac * 5.0 > k + 0.5 else Color(0.6, 0.6, 0.7, 0.4)
			var p := base + Vector2(k * 20, 0)
			draw_colored_polygon(PackedVector2Array([p + Vector2(0, -7), p + Vector2(6, 0), p + Vector2(0, 7), p + Vector2(-6, 0)]), c)
