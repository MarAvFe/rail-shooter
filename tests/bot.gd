extends Node
## Bot pilots drive the game ONLY through input actions, exercising the real code paths.
## good: follows walls' gaps and the orb path, fires when locked. bad: random holds and mashing.

var runner: Node
var bad := false
var _t := 0.0
var _rnd := Vector2.ZERO
var _fire := false
var _rng := RandomNumberGenerator.new()
var _timeout := 0.0


func _ready() -> void:
	_rng.seed = 7


func _process(dt: float) -> void:
	_timeout += dt
	if _timeout > 600.0:
		Game.quit_bot({"ok": false, "why": "timeout", "s": runner.get("s")})
		return
	var steer := Vector2.ZERO
	if bad:
		_t -= dt
		if _t <= 0.0:
			_t = _rng.randf_range(0.2, 1.5)
			_rnd = Vector2(_rng.randf_range(-1, 1), _rng.randf_range(-1, 1)).round()
			_fire = _rng.randf() < 0.5
			if _rng.randf() < 0.3:
				Input.action_press("honk")
				Input.action_release("honk")
		steer = _rnd
	else:
		var goal := Vector2.ZERO
		var s: float = runner.get("s")
		var found := false
		for wl: Dictionary in runner.get("walls"):
			if not wl["passed"] and float(wl["s"]) - s < 160.0:
				goal = wl["centre"]
				found = true
				break
		if not found:
			var best := INF
			for o: Dictionary in runner.get("orbs"):
				if o["taken"]:
					continue
				var local: Vector3 = (o["pos"] as Vector3) - (runner.call("_world", s, Vector2.ZERO) as Vector3)
				var bs: Basis = runner.call("basis_at", s)
				var ahead := -local.dot(bs.z)
				if ahead > 5.0 and ahead < best:
					best = ahead
					goal = Vector2(local.dot(bs.x), local.y)
		var ship: Ship = runner.get("ship")
		steer = ((goal - ship.pos2()) / 6.0).limit_length(1.0)
		_fire = runner.get("target") != null
	_press_axis("steer_right", "steer_left", steer.x)
	_press_axis("steer_up", "steer_down", steer.y)
	if _fire:
		Input.action_press("fire")
	else:
		Input.action_release("fire")


func _press_axis(pos: String, neg: String, v: float) -> void:
	if v > 0.05:
		Input.action_press(pos, v)
		Input.action_release(neg)
	elif v < -0.05:
		Input.action_press(neg, -v)
		Input.action_release(pos)
	else:
		Input.action_release(pos)
		Input.action_release(neg)
