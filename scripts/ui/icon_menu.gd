class_name IconMenu
extends HBoxContainer
## Wordless big-icon row: stick/arrows move, fire/enter picks, mouse works too. Selected icon breathes.

signal chosen(id: String)

var items: Array[Dictionary] = []
var sel := 0
var _cool := 0.0
var _arm := 0.25  # ignore the press that opened us
var icon_size := 128.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	alignment = BoxContainer.ALIGNMENT_CENTER
	add_theme_constant_override("separation", int(icon_size * 0.35))


func add_item(id: String, icon: String, tint := Color.WHITE, enabled := true) -> void:
	var b := TextureButton.new()
	b.texture_normal = load("res://assets/ui/icon_%s.png" % icon)
	b.ignore_texture_size = true
	b.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	b.custom_minimum_size = Vector2(icon_size, icon_size)
	b.pivot_offset = Vector2(icon_size, icon_size) / 2.0
	b.modulate = tint if enabled else Color(0.5, 0.5, 0.6, 0.6)
	b.focus_mode = Control.FOCUS_NONE
	var idx := items.size()
	b.pressed.connect(func() -> void: _pick(idx))
	b.mouse_entered.connect(func() -> void: sel = idx)
	add_child(b)
	items.append({"id": id, "node": b, "enabled": enabled})


func _pick(i: int) -> void:
	if _arm > 0.0 or not items[i]["enabled"]:
		return
	AudioBus.play("sfx_blip", 1.3)
	chosen.emit(str(items[i]["id"]))


func _process(dt: float) -> void:
	if not is_visible_in_tree() or items.is_empty():
		return
	_arm -= dt
	_cool -= dt
	var dir := 0
	if Input.is_action_pressed("menu_right"):
		dir = 1
	elif Input.is_action_pressed("menu_left"):
		dir = -1
	if dir != 0 and _cool <= 0.0:
		sel = posmod(sel + dir, items.size())
		_cool = 0.3
		AudioBus.play("sfx_blip")
	elif dir == 0:
		_cool = 0.0
	if Input.is_action_just_pressed("menu_accept") or Input.is_action_just_pressed("fire"):
		_pick(sel)
	for i in items.size():
		var n: Control = items[i]["node"]
		var k := 1.0 + (0.18 + 0.06 * sin(Game.t * PI * 2.0)) * float(i == sel)
		n.scale = n.scale.lerp(Vector2(k, k), 1.0 - exp(-12.0 * dt))
