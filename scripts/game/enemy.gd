class_name Enemy
extends Node3D
## Friendly-grumpy critters. They grow in from the fog, wobble when hit, puff when popped.

signal popped(enemy: Enemy)

const HP := {"drifter": 1, "pod": 2, "buzzer": 2, "guardian": 25}
const RADIUS := {"drifter": 3.6, "pod": 3.4, "buzzer": 3.4, "guardian": 14.0}  # +50% generous

var kind := "drifter"
var s := 0.0
var base := Vector2.ZERO
var offset := Vector2.ZERO  # current cross-section position
var phase := 0.0
var hp := 1
var state := "wait"  # wait -> live -> dying -> dead
var age := 0.0
var fire_t := 0.0
var model: Node3D
var _hit := 0.0
var _die := 0.0


func setup(d: Dictionary, scene: PackedScene) -> void:
	kind = str(d["type"])
	s = float(d["s"])
	base = Vector2(float(d["x"]), float(d["y"]))
	phase = float(d.get("phase", 0.0))
	hp = HP[kind]
	fire_t = 1.5 + phase * 0.3
	model = scene.instantiate()
	add_child(model)
	Game.paint(model)
	visible = false
	scale = Vector3.ONE * 0.01


func radius() -> float:
	return RADIUS[kind]


func activate() -> void:
	state = "live"
	visible = true
	age = 0.0


## Cross-section offset for this frame (behaviour lives here).
func update(dt: float) -> void:
	age += dt
	var t := Game.t + phase
	match kind:
		"drifter":
			offset = base + Vector2(sin(t * 0.35) * 7.0, sin(t * 0.8) * 1.2)
		"buzzer":
			offset = base + Vector2(sin(t * 0.5) * 7.0, sin(t * 1.0) * 3.0)
		"guardian":
			offset = base + Vector2(sin(t * 0.2) * 6.0, sin(t * 0.33) * 3.0)
		_:
			offset = base
	_hit = maxf(_hit - dt, 0.0)
	var grow := clampf(age / 1.2, 0.0, 1.0)
	var sc := ease(grow, 0.4) * (1.0 + sin(_hit * 40.0) * _hit * 0.6)
	if state == "dying":
		_die += dt
		sc = (1.0 - _die / 0.35) * (1.0 + sin(_die * 50.0) * 0.15)
		if _die >= 0.35:
			state = "dead"
			visible = false
			popped.emit(self)
			return
	scale = Vector3.ONE * maxf(sc, 0.01)
	model.rotation.y = sin(t * 0.7) * 0.4
	if kind == "guardian":
		var lit := 1.0 - float(hp) / float(HP[kind])
		model.scale = Vector3.ONE  # glow grows with hits via modulate on material copy (cheap: vertex tint later)
		model.position.y = lit * 2.0


func hit() -> void:
	if state != "live":
		return
	hp -= 1
	_hit = 0.3
	if hp <= 0:
		state = "dying"
		_die = 0.0


func alive() -> bool:
	return state == "live"
