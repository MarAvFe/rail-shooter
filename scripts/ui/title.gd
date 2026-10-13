extends Node3D
## Title: both ships idling over soft clouds. One press starts. Icons only.

var _ships: Array[Node3D] = []
var _menu: IconMenu


func _ready() -> void:
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color("#9fcff2")
	sm.sky_horizon_color = Color("#fde9d6")
	sm.ground_horizon_color = Color("#fde9d6")
	sm.ground_bottom_color = Color("#f6d3c0")
	sky.sky_material = sm
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var cam := Camera3D.new()
	cam.position = Vector3(0, 3.5, 24)
	cam.rotation.x = -0.08
	cam.fov = 50
	add_child(cam)
	for i in 2:
		var sc: PackedScene = load("res://assets/ships/ship_%s_c%d.glb" % [["air_kite", "hover_sled"][i], int(Save.data["colour"])])
		var n: Node3D = sc.instantiate()
		Game.paint(n)
		n.position = Vector3(-4.5 + i * 9.0, 0.5, 0)
		n.rotation.y = PI + (0.5 if i == 0 else -0.5)
		add_child(n)
		_ships.append(n)
	var cl := CanvasLayer.new()
	add_child(cl)
	_menu = IconMenu.new()
	_menu.add_item("play", "play", Color("#8ff0e0"))
	_menu.add_item("book", "book", Color("#f3b6d8"))
	cl.add_child(_menu)
	_menu.chosen.connect(_on_choice)
	AudioBus.music("music_title")
	Bindings.honked.connect(_on_honk)


func _on_honk() -> void:
	AudioBus.play("sfx_honk")
	for n in _ships:
		create_tween().tween_property(n, "position:y", n.position.y + 0.8, 0.15).set_trans(Tween.TRANS_SINE)


func _on_choice(id: String) -> void:
	if id == "play":
		var next := 1
		for i in range(1, 7):
			if not Save.level(i)["cleared"]:
				next = i
				break
		Game.start_level(next)
	else:
		Game.go(Game.BOOK)


func _process(dt: float) -> void:
	var vs := get_viewport().get_visible_rect().size
	_menu.position = Vector2((vs.x - _menu.size.x) / 2.0, vs.y * 0.68)
	for i in _ships.size():
		var n := _ships[i]
		n.position.y = lerpf(n.position.y, 0.5 + sin(Game.t * PI + i * 1.3) * 0.35, 1.0 - exp(-4.0 * dt))
		n.rotation.z = sin(Game.t * PI * 0.5 + i) * 0.08
