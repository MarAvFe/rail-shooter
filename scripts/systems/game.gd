extends Node
## Scene flow, the one animation clock, shared materials, command-line test modes.

const TITLE := "res://scenes/title.tscn"
const LEVEL := "res://scenes/level_runner.tscn"
const BOOK := "res://scenes/sticker_book.tscn"
const ENDING := "res://scenes/ending.tscn"
const PARENT := "res://scenes/parent_menu.tscn"

var t := 0.0  ## one clock for every looping animation
var level_id := 1
var args: Dictionary = {}
var vc_mat: StandardMaterial3D
var glow_mat: StandardMaterial3D
var _parent_menu: Node = null
var _fade: ColorRect


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a: String in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=")
		args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	vc_mat = StandardMaterial3D.new()
	vc_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	vc_mat.vertex_color_use_as_albedo = true
	glow_mat = vc_mat.duplicate()
	glow_mat.disable_fog = true
	Bindings.parent_menu_requested.connect(open_parent_menu)
	var cl := CanvasLayer.new()
	cl.layer = 100
	add_child(cl)
	_fade = ColorRect.new()
	_fade.color = Color(1, 0.97, 0.93, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	cl.add_child(_fade)
	get_tree().root.focus_exited.connect(func() -> void: get_tree().call_group("pausable", "request_pause"))
	if args.has("test"):
		_self_test.call_deferred()
		return
	if args.has("check"):
		_check_scripts.call_deferred()
		return
	if args.has("snap"):  # --snap=<name> [--scene=book]: screenshot after 2 s, quit
		_snap.call_deferred()
	if args.has("level"):
		level_id = int(args["level"])
		go.call_deferred(LEVEL)


## One shared pulse for every glowing thing (integer cycles per 2 s).
func pulse(cycles := 1) -> float:
	return 0.5 + 0.5 * sin(TAU * t * cycles / 2.0)


func _process(delta: float) -> void:
	t += delta
	glow_mat.albedo_color = Color.WHITE.lerp(Color(0.82, 0.9, 0.9), pulse())


func go(scene: String) -> void:
	get_tree().paused = false
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, 0.4)
	tw.tween_callback(func() -> void: get_tree().change_scene_to_file(scene))
	tw.tween_property(_fade, "color:a", 0.0, 0.5)


func start_level(n: int) -> void:
	level_id = n
	go(LEVEL)


## Apply flat vertex-colour material to every mesh under `root`.
func paint(root: Node, glow := false) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		(n as MeshInstance3D).material_override = glow_mat if glow else vc_mat


func open_parent_menu() -> void:
	if _parent_menu != null and is_instance_valid(_parent_menu):
		return
	if not ResourceLoader.exists(PARENT):
		return
	var ps: PackedScene = load(PARENT)
	_parent_menu = ps.instantiate()
	get_tree().paused = true
	add_child(_parent_menu)


func quit_bot(result: Dictionary) -> void:
	print("BOT_RESULT ", JSON.stringify(result))
	var f := FileAccess.open("user://bot_result.json", FileAccess.WRITE)  # GUI builds have no stdout
	if f:
		f.store_string(JSON.stringify(result))
		f.close()
	get_tree().quit(0 if result.get("ok", false) else 1)


## --check: compile every script in project context (autoloads present); exit 1 on any failure.
func _check_scripts() -> void:
	var bad := 0
	var n := 0
	var stack: Array[String] = ["res://scripts", "res://tests"]
	while not stack.is_empty():
		var dir := stack.pop_back() as String
		for sub in DirAccess.get_directories_at(dir):
			stack.append(dir + "/" + sub)
		for f in DirAccess.get_files_at(dir):
			if f.ends_with(".gd"):
				n += 1
				var sc: GDScript = load(dir + "/" + f)
				if sc == null or not sc.can_instantiate():
					bad += 1
					print("CHECK_FAIL ", dir + "/" + f)
	print("CHECK scripts=%d failed=%d" % [n, bad])
	get_tree().quit(1 if bad > 0 else 0)


func _snap() -> void:
	match str(args.get("scene", "")):
		"book": get_tree().change_scene_to_file(BOOK)
		"ending": get_tree().change_scene_to_file(ENDING)
		"parent": open_parent_menu()
	await get_tree().create_timer(2.0).timeout
	get_viewport().get_texture().get_image().save_png("res://docs/shots/%s.png" % args["snap"])
	get_tree().quit()


## Highest level that has data (the ending plays after it).
func last_level() -> int:
	var n := 1
	for i in range(1, 7):
		if FileAccess.file_exists("res://levels/level_%d.json" % i):
			n = i
	return n


## --test: input layer + save robustness. Prints TEST lines, exits 1 on failure.
func _self_test() -> void:
	var fails: PackedStringArray = []
	var backup := {}  # never clobber the family's real save/bindings
	for p: String in [Save.PATH, Bindings.PATH]:
		backup[p] = FileAccess.get_file_as_string(p) if FileAccess.file_exists(p) else null
	var honks := [0]
	Bindings.honked.connect(func() -> void: honks[0] += 1)
	# 1. unbound pad button and unbound key -> honk, nothing else
	for ev: InputEvent in [Bindings.joy_btn(JOY_BUTTON_RIGHT_SHOULDER), Bindings.key(KEY_Q)]:
		ev.set("pressed", true)
		Input.parse_input_event(ev)
		await get_tree().process_frame
	if honks[0] != 2:
		fails.append("unbound->honk got %d" % honks[0])
	# 2. learn mode: a raw button becomes FIRE, keyboard default kept
	var learned := Bindings.joy_btn(JOY_BUTTON_MISC1)
	Bindings.learn("fire", learned)
	if not InputMap.event_is_action(learned, "fire") or not InputMap.event_is_action(Bindings.key(KEY_SPACE), "fire"):
		fails.append("learn fire")
	var ax := Bindings.joy_axis(JOY_AXIS_RIGHT_X, -1.0)
	Bindings.learn("steer_left", ax)
	if not InputMap.event_is_action(ax, "steer_left") or not InputMap.event_is_action(ax, "menu_left"):
		fails.append("learn axis")
	Bindings.reset_bindings()
	if InputMap.event_is_action(learned, "fire"):
		fails.append("reset bindings")
	# 3. corrupt and missing save -> defaults, no crash
	var f := FileAccess.open(Save.PATH, FileAccess.WRITE)
	f.store_string("{not json!!")
	f.close()
	Save.load_data()
	if Save.level(1)["cleared"] != false:
		fails.append("corrupt save")
	f = FileAccess.open(Save.PATH, FileAccess.WRITE)
	f.store_string('{"levels": {"1": {"cleared": "yes"}}, "settings": {"music": "loud"}}')
	f.close()
	Save.load_data()
	if typeof(Save.level(1)["cleared"]) != TYPE_BOOL or typeof(Save.setting("music")) != TYPE_FLOAT:
		fails.append("wrong-typed save")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(Save.PATH))
	Save.load_data()
	if Save.level(1)["cleared"] != false:
		fails.append("missing save")
	for p: String in backup:
		if backup[p] == null:
			DirAccess.remove_absolute(ProjectSettings.globalize_path(p))
		else:
			var w := FileAccess.open(p, FileAccess.WRITE)
			w.store_string(backup[p])
			w.close()
	print("TEST input+save: ", "PASS" if fails.is_empty() else "FAIL " + ", ".join(fails))
	get_tree().quit(0 if fails.is_empty() else 1)
