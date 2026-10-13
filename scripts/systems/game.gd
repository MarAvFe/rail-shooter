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
	if args.get("scene", "") == "book":
		get_tree().change_scene_to_file(BOOK)
	await get_tree().create_timer(2.0).timeout
	get_viewport().get_texture().get_image().save_png("res://docs/shots/%s.png" % args["snap"])
	get_tree().quit()
