class_name Ship
extends Node3D
## Cross-section motion inside the corridor. The rail (LevelRunner) owns forward motion.
## Visual bank/pitch live on `model` only; collision logic uses x/y.

signal bumped

const BANK_MAX := deg_to_rad(22.0)
const PITCH_MAX := deg_to_rad(10.0)
const SOFT_ZONE := 4.0
const HOVER_H := 3.0
const HOP := 6.0

var mode := "air"
var x := 0.0
var y := 0.0
var vel := Vector2.ZERO
var inp := Vector2.ZERO
var max_speed := 12.0
var model: Node3D
var _bank := 0.0
var _pitch := 0.0
var _wobble := 0.0
var _happy := 0.0
var _bump_cd := 0.0


func setup(scene: PackedScene, m: String) -> void:
	mode = m
	max_speed = 12.0 if m == "air" else 10.0
	model = scene.instantiate()
	add_child(model)
	Game.paint(model)


## raw: steer input in [-1,1]^2. lo/hi: hard bounds (cross-section). floor_y: terrain under the ship (hover).
func step(dt: float, raw: Vector2, lo: Vector2, hi: Vector2, pull: Vector2, floor_y: float) -> void:
	_bump_cd -= dt
	for i in 2:  # keyboard -> stick-like ramps (0.15 s up, 0.10 s down)
		var r := 1.0 / 0.15 if absf(raw[i]) > absf(inp[i]) else 1.0 / 0.10
		inp[i] = move_toward(inp[i], raw[i], r * dt)
	var target := inp * max_speed + pull
	if mode == "hover":
		target.y = 0.0
	vel = vel.lerp(target, 1.0 - exp(-6.0 * dt))
	# soft push-back in the outer zone: drift home before touching anything
	for i in 2:
		var p := x if i == 0 else y
		if p > hi[i] - SOFT_ZONE:
			vel[i] -= (p - (hi[i] - SOFT_ZONE)) * 9.0 * dt
		elif p < lo[i] + SOFT_ZONE:
			vel[i] += ((lo[i] + SOFT_ZONE) - p) * 9.0 * dt
	if mode == "hover":
		# critically damped spring to hover height; steer_up = hop
		var goal := floor_y + HOVER_H + maxf(inp.y, 0.0) * HOP
		var k := 30.0
		vel.y += (k * (goal - y) - 2.0 * sqrt(k) * vel.y) * dt
		lo.y = floor_y + 1.2
	x += vel.x * dt
	y += vel.y * dt
	if x < lo.x or x > hi.x:
		x = clampf(x, lo.x, hi.x)
		bump(Vector2(-signf(vel.x), 0))
	if y < lo.y or y > hi.y:
		y = clampf(y, lo.y, hi.y)
		if mode == "air":
			bump(Vector2(0, -signf(vel.y)))
		else:
			vel.y = 0.0
	# visuals
	_bank = lerpf(_bank, -vel.x / max_speed * BANK_MAX, 1.0 - exp(-5.0 * dt))
	_pitch = lerpf(_pitch, vel.y / max_speed * PITCH_MAX, 1.0 - exp(-5.0 * dt))
	_wobble = maxf(_wobble - dt, 0.0)
	_happy = maxf(_happy - dt, 0.0)
	var wob := sin(_wobble * 30.0) * _wobble * 0.5
	var hap := sin(_happy * 12.0) * _happy * 0.25
	var bob := sin(Game.t * TAU / 2.0) * (0.25 if mode == "hover" else 0.12)
	model.rotation = Vector3(_pitch + wob * 0.5, hap, clampf(_bank + wob + hap, -BANK_MAX, BANK_MAX))
	model.position.y = bob


## Gentle bounce: never removes control, never costs anything.
func bump(dir: Vector2) -> void:
	if dir == Vector2.ZERO:
		dir = Vector2.UP
	vel = dir.normalized() * 5.0
	if _bump_cd > 0.0:
		return
	_bump_cd = 0.6
	_wobble = 0.4
	AudioBus.play("sfx_boop")
	bumped.emit()


func happy() -> void:
	_happy = 1.0


func pos2() -> Vector2:
	return Vector2(x, y)
