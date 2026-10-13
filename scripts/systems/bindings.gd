extends Node
## The only place that knows about devices. Game code uses named actions only.
## Unknown/unbound buttons become a harmless honk. Parent-menu hold gesture lives here.

signal honked
signal parent_menu_requested

const PATH := "user://bindings.json"
const STEER := ["steer_left", "steer_right", "steer_up", "steer_down"]
const ACTIONS := ["steer_left", "steer_right", "steer_up", "steer_down", "fire", "honk", "pause", "restart",
	"menu_accept", "menu_back", "menu_left", "menu_right", "menu_up", "menu_down", "parent_menu_hold"]
const HOLD_TIME := 3.0

var _hold := 0.0
var _custom: Dictionary = {}  # action -> Array of serialized events (overrides defaults)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_load()
	rebuild()


static func key(k: Key) -> InputEventKey:
	var e := InputEventKey.new()
	e.physical_keycode = k
	return e


static func joy_btn(b: JoyButton) -> InputEventJoypadButton:
	var e := InputEventJoypadButton.new()
	e.button_index = b
	return e


static func joy_axis(a: JoyAxis, v: float) -> InputEventJoypadMotion:
	var e := InputEventJoypadMotion.new()
	e.axis = a
	e.axis_value = v
	return e


func default_events() -> Dictionary:
	return {
		"steer_left": [key(KEY_A), key(KEY_LEFT), joy_axis(JOY_AXIS_LEFT_X, -1.0), joy_btn(JOY_BUTTON_DPAD_LEFT)],
		"steer_right": [key(KEY_D), key(KEY_RIGHT), joy_axis(JOY_AXIS_LEFT_X, 1.0), joy_btn(JOY_BUTTON_DPAD_RIGHT)],
		"steer_up": [key(KEY_W), key(KEY_UP), joy_axis(JOY_AXIS_LEFT_Y, -1.0), joy_btn(JOY_BUTTON_DPAD_UP)],
		"steer_down": [key(KEY_S), key(KEY_DOWN), joy_axis(JOY_AXIS_LEFT_Y, 1.0), joy_btn(JOY_BUTTON_DPAD_DOWN)],
		"fire": [key(KEY_SPACE), joy_btn(JOY_BUTTON_A)],
		"honk": [key(KEY_H), joy_btn(JOY_BUTTON_B), joy_btn(JOY_BUTTON_X), joy_btn(JOY_BUTTON_Y)],
		"pause": [key(KEY_ESCAPE), joy_btn(JOY_BUTTON_START)],
		"restart": [key(KEY_R)],
		"menu_accept": [key(KEY_ENTER), key(KEY_SPACE), joy_btn(JOY_BUTTON_A)],
		"menu_back": [key(KEY_BACKSPACE), key(KEY_ESCAPE)],
		"menu_left": [key(KEY_A), key(KEY_LEFT), joy_axis(JOY_AXIS_LEFT_X, -1.0), joy_btn(JOY_BUTTON_DPAD_LEFT)],
		"menu_right": [key(KEY_D), key(KEY_RIGHT), joy_axis(JOY_AXIS_LEFT_X, 1.0), joy_btn(JOY_BUTTON_DPAD_RIGHT)],
		"menu_up": [key(KEY_W), key(KEY_UP), joy_axis(JOY_AXIS_LEFT_Y, -1.0), joy_btn(JOY_BUTTON_DPAD_UP)],
		"menu_down": [key(KEY_S), key(KEY_DOWN), joy_axis(JOY_AXIS_LEFT_Y, 1.0), joy_btn(JOY_BUTTON_DPAD_DOWN)],
		"parent_menu_hold": [key(KEY_F1)],
	}


func rebuild() -> void:
	var dz := float(Save.setting("deadzone"))
	var defs := default_events()
	for a: String in ACTIONS:
		if InputMap.has_action(a):
			InputMap.erase_action(a)
		InputMap.add_action(a, dz if a in STEER or a.begins_with("menu_") else 0.5)
		var evs: Array = defs[a]
		if _custom.has(a):
			evs = []
			for d: Dictionary in _custom[a]:
				var e := deserialize(d)
				if e != null:
					evs.append(e)
		for e: InputEvent in evs:
			InputMap.action_add_event(a, e)


## Bind one learned event to an action (learn mode). Keyboard defaults stay usable.
func learn(action: String, ev: InputEvent) -> void:
	var list: Array = _custom.get(action, [])
	if list.is_empty():
		for e: InputEvent in default_events()[action]:
			if e is InputEventKey:
				list.append(serialize(e))
	list.append(serialize(ev))
	_custom[action] = list
	# a learned steer axis drives the matching menu direction too
	if action in STEER:
		var m := action.replace("steer_", "menu_")
		_custom[m] = list.duplicate()
	_save()
	rebuild()


func reset_bindings() -> void:
	_custom.clear()
	_save()
	rebuild()


func serialize(e: InputEvent) -> Dictionary:
	if e is InputEventKey:
		return {"t": "key", "k": (e as InputEventKey).physical_keycode}
	if e is InputEventJoypadButton:
		return {"t": "btn", "b": (e as InputEventJoypadButton).button_index}
	if e is InputEventJoypadMotion:
		var m := e as InputEventJoypadMotion
		return {"t": "axis", "a": m.axis, "v": signf(m.axis_value)}
	return {}


func deserialize(d: Dictionary) -> InputEvent:
	match str(d.get("t", "")):
		"key": return key(int(d["k"]) as Key)
		"btn": return joy_btn(int(d["b"]) as JoyButton)
		"axis": return joy_axis(int(d["a"]) as JoyAxis, float(d["v"]))
	return null


func _load() -> void:
	if not FileAccess.file_exists(PATH):
		return
	var p: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if typeof(p) == TYPE_DICTIONARY:
		_custom = p


func _save() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_custom))


func is_known(ev: InputEvent) -> bool:
	for a: String in ACTIONS:
		if InputMap.event_is_action(ev, a):
			return true
	return false


func _input(ev: InputEvent) -> void:
	if ev.is_echo():
		return
	if ev.is_action_pressed("honk"):
		honked.emit()
		return
	var is_press := (ev is InputEventKey and ev.is_pressed()) or (ev is InputEventJoypadButton and ev.is_pressed())
	if is_press and not is_known(ev):
		honked.emit()  # any unbound button: harmless and fun


func _process(delta: float) -> void:
	var held := Input.is_action_pressed("parent_menu_hold")
	if not held:
		for j: int in Input.get_connected_joypads():
			if Input.is_joy_button_pressed(j, JOY_BUTTON_START) and Input.is_joy_button_pressed(j, JOY_BUTTON_BACK):
				held = true
	_hold = _hold + delta if held else 0.0
	if _hold >= HOLD_TIME:
		_hold = -INF  # fire once per hold
		parent_menu_requested.emit()


func hold_progress() -> float:
	return clampf(_hold / HOLD_TIME, 0.0, 1.0)
