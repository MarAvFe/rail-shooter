extends CanvasLayer
## Wordless HUD: a row of 10 orb shapes that fill as orbs are collected. No numbers.

const SLOTS := 10

var _icons: Array[TextureRect] = []
var _row: HBoxContainer
var _celebrate := 0.0


func _ready() -> void:
	_row = HBoxContainer.new()
	_row.add_theme_constant_override("separation", 6)
	_row.set_anchors_preset(Control.PRESET_CENTER_TOP)
	add_child(_row)
	var tex: Texture2D = load("res://assets/ui/icon_orb.png")
	for i in SLOTS:
		var t := TextureRect.new()
		t.texture = tex
		t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		t.custom_minimum_size = Vector2(26, 26)
		t.pivot_offset = Vector2(13, 13)
		_row.add_child(t)
		_icons.append(t)


func _process(dt: float) -> void:
	var r := get_parent()
	var frac := float(r.get("collected")) / maxf(float(r.get("total_orbs")) * 0.8, 1.0)  # 80% fills the row
	var filled := frac * SLOTS
	var vs := get_viewport().get_visible_rect().size
	_row.position = Vector2((vs.x - _row.size.x) / 2.0, 10.0 + _celebrate * vs.y * 0.3)
	for i in SLOTS:
		var f := clampf(filled - i, 0.0, 1.0)
		var t := _icons[i]
		t.modulate = Color(0.55, 0.55, 0.7, 0.45).lerp(Color("#8ff0e0"), f)
		var k := 1.0 + 0.25 * f * Game.pulse() * float(_celebrate > 0.0) + (1.0 if _celebrate > 0.0 else 0.0)
		t.scale = t.scale.lerp(Vector2(k, k), 1.0 - exp(-6.0 * dt))


func celebrate() -> void:
	create_tween().tween_property(self, "_celebrate", 1.0, 1.0).set_trans(Tween.TRANS_SINE)
