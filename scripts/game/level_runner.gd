extends Node3D
## Generic level loader + rail/corridor/wall/combat logic. Everything level-specific comes from JSON.

signal orb_collected
signal enemy_popped
signal gap_passed

const UP := Vector3.UP
const FIRE_RATE := 0.25
const SHOT_SPEED := 60.0
const SHOT_LIFE := 2.0
const AIM_CONE := deg_to_rad(12.0)
const AIM_KEEP := deg_to_rad(20.0)
const ORB_R := 3.8
const SPAWN_AHEAD := 260.0

var L: Dictionary
var mode := "air"
var curve := Curve3D.new()
var length := 0.0
var rail: Array = []  # [x,y,z,w,f]
var s := 0.0
var speed := 0.0
var base_speed := 15.0
var finished := false
var ship: Ship
var cam: Camera3D
var walls: Array[Dictionary] = []
var enemies: Array[Enemy] = []
var orbs: Array[Dictionary] = []  # {node, pos, taken, free}
var shots: Array[Dictionary] = []
var bubbles: Array[Dictionary] = []
var target: Enemy = null
var lock_t := 0.0
var ring: MeshInstance3D
var fire_cd := 0.0
var fired_once := false
var checkpoint := 0.0
var collected := 0
var total_orbs := 0
var stall_t := 0.0
var bumps := 0
var stalls := 0
var restart_hold := 0.0
var frame_ms: PackedFloat32Array = []
var _last_us := 0
var assist := 0.0  # 0..1, only ever makes things easier
var _bump_times: Array[float] = []
var hud: Node
var pause_layer: CanvasLayer
var glint: MeshInstance3D
var puffs: Array[CPUParticles3D] = []
var sparkle: CPUParticles3D
var bot: Node = null
var _cam_look := Vector3.ZERO
var touring := false
var engine: AudioStreamPlayer
var _sky_mat: ProceduralSkyMaterial
var _world_root: Node
var guardian: Enemy = null
var gate_lit := false


func _ready() -> void:
	add_to_group("pausable")
	var path := "res://levels/level_%d.json" % Game.level_id
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("level missing: " + path)
		Game.go(Game.TITLE)
		return
	L = parsed
	mode = str(L["mode"])
	base_speed = float(L["speed"])
	rail = L["rail"]
	for p: Array in rail:
		curve.add_point(Vector3(p[0], p[1], p[2]))
	curve.bake_interval = 1.0
	length = minf(curve.get_baked_length(), float(L["length"]))
	_build_env()
	_build_world()
	_build_ship()
	_build_fx()
	hud = preload("res://scripts/ui/hud.gd").new()
	add_child(hud)
	total_orbs = orbs.size() + 2 * enemies.size()  # enemies drop 1-3
	AudioBus.music(str(L["music"]))
	ship.bumped.connect(_on_bump)
	Bindings.honked.connect(_on_honk)
	engine = AudioStreamPlayer.new()  # engine hum: follows rail speed, sits under the music
	engine.stream = AudioBus.stream("loop_engine", true)
	engine.bus = "SFX"
	engine.volume_db = -6.0
	add_child(engine)
	engine.play()
	speed = base_speed * 0.5
	_last_us = Time.get_ticks_usec()
	if Game.args.has("bot"):
		bot = load("res://tests/bot.gd").new()
		bot.set("runner", self)
		bot.set("bad", Game.args["bot"] == "bad")
		add_child(bot)
	if Game.args.has("shots"):
		_shot_tour.call_deferred()


# ---------------- build ----------------
func _build_env() -> void:
	var pal: Dictionary = L["palette"]
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(pal["sky"][0])
	sm.sky_horizon_color = Color(pal["sky"][1])
	sm.ground_horizon_color = Color(pal["sky"][1])
	sm.ground_bottom_color = Color(pal["fog"])
	sm.sun_angle_max = 1.0
	sky.sky_material = sm
	_sky_mat = sm
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.WHITE
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_light_color = Color(pal["fog"])
	env.fog_density = 1.0
	env.fog_depth_begin = float(L["fog"][0])
	env.fog_depth_end = float(L["fog"][1])
	env.fog_depth_curve = 1.4
	env.fog_sky_affect = 0.4
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color(pal["light"])
	sun.rotation_degrees = Vector3(-55, -35, 0)
	add_child(sun)


func _build_world() -> void:
	var kit: PackedScene = load("res://assets/kits/level_%d.glb" % Game.level_id)
	var world := kit.instantiate()
	add_child(world)
	_world_root = world
	for n: Node in world.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		mi.material_override = Game.glow_mat if mi.name.begins_with("trim_") or mi.get_parent().name.begins_with("trim_") else Game.vc_mat
	for i in L["walls"].size():
		var w: Dictionary = L["walls"][i]
		var poly := PackedVector2Array()
		for p: Array in w["gap"]:
			poly.append(Vector2(p[0], p[1]))
		var mv: Array = w.get("move", [0, 1])
		var nodes: Array[Node3D] = []
		for nm: String in ["wall_%d" % i, "trim_%d" % i]:
			var nd := world.find_child(nm, true, false) as Node3D
			if nd:
				nodes.append(nd)
		walls.append({"s": float(w["s"]), "half": float(w["thickness"]) * 0.5, "gap": poly,
			"centre0": Vector2(w["centre"][0], w["centre"][1]), "centre": Vector2(w["centre"][0], w["centre"][1]),
			"passed": false, "ddx": 0.0, "amp": float(mv[0]), "period": maxf(float(mv[1]), 1.0), "dx": 0.0, "nodes": nodes,
			"base": nodes.map(func(n: Node3D) -> Vector3: return n.position)})
	var scenes := {}
	for e: Dictionary in L["enemies"]:
		var k := str(e["type"])
		if not scenes.has(k):
			scenes[k] = load("res://assets/enemies/enemy_%s.glb" % k)
		var en := Enemy.new()
		en.setup(e, scenes[k])
		if k == "pod":
			en.base.y = _floor_at(en.s, en.base.x) + 0.5
		add_child(en)
		en.popped.connect(_on_popped)
		enemies.append(en)
		if k == "guardian":
			guardian = en
	var orb_scene: PackedScene = load("res://assets/fx/pickup_orb.glb")
	for o: Dictionary in L["orbs"]:
		_add_orb(orb_scene, _world(float(o["s"]), Vector2(o["x"], o["y"])), false)


func _add_orb(sc: PackedScene, pos: Vector3, free: bool) -> void:
	var n: Node3D = sc.instantiate()
	Game.paint(n, true)
	n.position = pos
	add_child(n)
	orbs.append({"node": n, "pos": pos, "taken": false, "free": free})


func _build_ship() -> void:
	ship = Ship.new()
	var sc: PackedScene = load("res://assets/ships/ship_%s_c%d.glb" % ["air_kite" if mode == "air" else "hover_sled", int(Save.data["colour"])])
	add_child(ship)
	ship.setup(sc, mode)
	if mode == "hover":
		ship.y = _floor_at(0.0, 0.0) + Ship.HOVER_H
	cam = Camera3D.new()
	cam.fov = 70.0
	cam.far = 1200.0
	cam.near = 0.5
	add_child(cam)
	cam.make_current()
	_place_ship()
	_cam_follow(1.0, true)
	# nose glint: hints at the fire button until first used
	glint = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.35
	sm.height = 0.7
	sm.radial_segments = 8
	sm.rings = 4
	glint.mesh = sm
	glint.material_override = _flat(Color("#ffffff"))
	glint.position = Vector3(0, 0.5, -3.3)
	ship.model.add_child(glint)


func _flat(c: Color, alpha := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = Color(c, alpha)
	if alpha < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return m


func _build_fx() -> void:
	var bm := SphereMesh.new()
	bm.radius = 0.7
	bm.height = 1.4
	bm.radial_segments = 10
	bm.rings = 5
	var bmat := _flat(Color("#c8fff3"), 0.85)
	for i in 14:
		var n := MeshInstance3D.new()
		n.mesh = bm
		n.material_override = bmat
		n.visible = false
		add_child(n)
		shots.append({"node": n, "live": false, "vel": Vector3.ZERO, "life": 0.0})
	var pm := SphereMesh.new()
	pm.radius = 1.6
	pm.height = 3.2
	pm.radial_segments = 10
	pm.rings = 5
	var pmat := _flat(Color("#e6d4ff"), 0.75)
	for i in 6:
		var n := MeshInstance3D.new()
		n.mesh = pm
		n.material_override = pmat
		n.visible = false
		add_child(n)
		bubbles.append({"node": n, "live": false, "pos2": Vector2.ZERO, "s": 0.0, "vel2": Vector2.ZERO})
	ring = MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 3.6
	tm.outer_radius = 4.2
	tm.rings = 16
	tm.ring_segments = 4
	ring.mesh = tm
	ring.material_override = _flat(Color("#8ff0e0"))
	ring.visible = false
	add_child(ring)
	for i in 4:
		puffs.append(_particles(Color("#fff3fb"), 18, 6.0, 0.9))
	sparkle = _particles(Color("#ffffff"), 24, 9.0, 0.8)


func _particles(c: Color, n: int, v: float, life: float) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	var m := SphereMesh.new()
	m.radius = 0.5
	m.height = 1.0
	m.radial_segments = 6
	m.rings = 3
	p.mesh = m
	p.material_override = _flat(c)
	p.amount = n
	p.one_shot = true
	p.emitting = false
	p.explosiveness = 0.9
	p.lifetime = life
	p.direction = Vector3.UP
	p.spread = 180.0
	p.gravity = Vector3.ZERO
	p.initial_velocity_min = v * 0.5
	p.initial_velocity_max = v
	p.damping_min = 3.0
	p.damping_max = 5.0
	var curve_s := Curve.new()
	curve_s.add_point(Vector2(0, 1))
	curve_s.add_point(Vector2(1, 0))
	p.scale_amount_curve = curve_s
	add_child(p)
	return p


# ---------------- rail math ----------------
func _sample(arr_idx: int, at: float) -> float:
	var f := clampf(at / 5.0, 0.0, rail.size() - 1.001)
	var i := int(f)
	return lerpf(float(rail[i][arr_idx]), float(rail[i + 1][arr_idx]), f - i)


func width_at(at: float) -> float:
	return _sample(3, at)


func floor_rel(at: float) -> float:
	return -_sample(4, at)


func _floor_at(at: float, x: float) -> float:
	# hover terrain: per-sample lateral floor heights (5 columns) if present, else flat floor
	if rail[0].size() > 5:
		var w := width_at(at)
		var u := clampf((x / w + 1.0) * 2.0, 0.0, 3.999)
		var j := int(u)
		return lerpf(_sample(5 + j, at), _sample(6 + j, at), u - j)
	return floor_rel(at)


func basis_at(at: float) -> Basis:
	var a := curve.sample_baked(clampf(at - 2.0, 0.0, length))
	var b := curve.sample_baked(clampf(at + 2.0, 0.0, length))
	var t := Vector3(b.x - a.x, 0.0, b.z - a.z).normalized()
	var r := t.cross(UP).normalized()
	return Basis(r, UP, -t)


func _world(at: float, p: Vector2) -> Vector3:
	var bs := basis_at(at)
	return curve.sample_baked(clampf(at, 0.0, length)) + bs.x * p.x + UP * p.y


# ---------------- frame ----------------
func _process(dt: float) -> void:
	var now := Time.get_ticks_usec()
	frame_ms.append((now - _last_us) / 1000.0)
	_last_us = now
	if touring:
		_update_enemies(dt)
		return
	if finished:
		_cam_follow(dt)
		return
	_update_assist(dt)
	var raw := Input.get_vector("steer_left", "steer_right", "steer_down", "steer_up")
	if bool(Save.setting("invert_y")):
		raw.y = -raw.y
	var w := width_at(s)
	var f := floor_rel(s)
	var lo := Vector2(-w + 5.0, f + 4.0)
	var hi := Vector2(w - 5.0, float(L["ceiling"]))
	var pull := Vector2.ZERO
	var target_speed := base_speed * float(Save.setting("speed")) * (1.0 - 0.25 * assist)
	var front_cap := INF
	_update_walls()
	if L.get("guardian_hold") != null and guardian and guardian.state in ["wait", "live"]:
		front_cap = sqrt(2.0 * 3.0 * maxf(float(L["guardian_hold"]) - s, 0.0))  # wait for the Guardian to doze off
	if _sky_mat and L["palette"].has("sky_end"):
		var k := clampf(s / length, 0.0, 1.0) if not gate_lit else 1.0
		_sky_mat.sky_top_color = Color(L["palette"]["sky"][0]).lerp(Color(L["palette"]["sky_end"][0]), k)
		_sky_mat.sky_horizon_color = Color(L["palette"]["sky"][1]).lerp(Color(L["palette"]["sky_end"][1]), k)
		_sky_mat.ground_horizon_color = _sky_mat.sky_horizon_color
	var prev := ship.pos2()
	var in_wall := false
	for wl: Dictionary in walls:
		if wl["passed"]:
			continue
		var front: float = wl["s"] - wl["half"] - 3.5
		var d := front - s
		if d > 160.0:
			break
		var inside := _in_gap(wl, ship.pos2())
		var to_gap: Vector2 = wl["centre"] - ship.pos2()
		var magnet := 0.0
		if Game.level_id <= 2:
			magnet = 0.25
		magnet += assist * 0.4
		if stall_t > 3.0:
			magnet += 0.9
		if d < 120.0:
			pull += to_gap.limit_length(1.0) * ship.max_speed * magnet * clampf(to_gap.length() / 6.0, 0.0, 1.0)
		if d > 0.0 and not inside:
			front_cap = minf(front_cap, sqrt(2.0 * 3.0 * d))
		if d <= 0.0:
			if not inside and s < wl["s"]:
				in_wall = true  # cannot enter solid: hold position, assist drifts to the gap
				front_cap = 0.0
			if s > wl["s"] + wl["half"] + 3.5:
				wl["passed"] = true
				AudioBus.play("sfx_gap")
				sparkle.global_position = ship.global_position
				sparkle.restart()
				ship.happy()
				gap_passed.emit()
		break
	# stall: rail eases to a stop in front of solid wall
	var stalled := front_cap < 1.0
	stall_t = stall_t + dt if stalled else 0.0
	if stalled and stall_t < dt * 1.5:
		stalls += 1
	speed = lerpf(speed, target_speed, 1.0 - exp(-1.2 * dt))
	speed = minf(speed, front_cap)
	ship.step(dt, raw, lo, hi, pull, _floor_at(s, ship.x))
	# rocks (hover): steer around or hop over
	for rk: Dictionary in L.get("rocks", []):
		var rs: float = rk["s"]
		if absf(rs - s) < float(rk["r"]) + 3.0:
			var dx := ship.x - float(rk["x"])
			var reach := float(rk["r"]) + 2.5
			if absf(dx) < reach and ship.y < float(rk["top"]) + 1.0:
				ship.x = lerpf(ship.x, float(rk["x"]) + signf(dx if dx != 0.0 else 1.0) * reach, 0.5)
				ship.bump(Vector2(signf(dx if dx != 0.0 else 1.0), 0.0))
	# can't move into the solid part of a wall while inside its thickness
	for wl: Dictionary in walls:
		# strictly inside the thickness: a ship parked at the front face must stay free to steer to the gap
		if not wl["passed"] and s > wl["s"] - wl["half"] - 3.5 + 0.05 and s <= wl["s"] + wl["half"] + 3.5:
			ship.x += float(wl["ddx"])  # ride along with a sliding gap
			if not _in_gap(wl, ship.pos2()):
				ship.x = prev.x
				ship.y = prev.y
				ship.bump((Vector2(wl["centre"]) - prev).normalized())
	if not in_wall:
		s = minf(s + speed * dt, length)
	for c: float in L["checkpoints"]:
		if s >= c:
			checkpoint = maxf(checkpoint, c)
	_place_ship()
	_cam_follow(dt)
	if engine:
		var k := clampf(speed / maxf(base_speed, 1.0), 0.0, 1.3)
		engine.pitch_scale = (1.25 if mode == "hover" else 1.0) * (0.8 + 0.25 * k) + ship.inp.length() * 0.05
		engine.volume_db = lerpf(-14.0, -3.0, clampf(k, 0.0, 1.0))
	_update_enemies(dt)
	_update_combat(dt)
	_update_orbs(dt)
	_restart_input(dt)
	if Input.is_action_just_pressed("pause"):
		request_pause()
	if s >= length - 0.5:
		_finish()


## Sliding gaps (level 5+): the wall + trim slide sideways slowly; the gap polygon follows.
func _update_walls() -> void:
	for wl: Dictionary in walls:
		var dx := 0.0
		if float(wl["amp"]) > 0.0:
			dx = float(wl["amp"]) * sin(TAU * Game.t / float(wl["period"]))
		wl["ddx"] = dx - float(wl["dx"])
		wl["dx"] = dx
		wl["centre"] = Vector2(wl["centre0"]) + Vector2(dx, 0.0)
		if dx != 0.0:
			var off := basis_at(float(wl["s"])).x * dx
			for i in (wl["nodes"] as Array).size():
				(wl["nodes"][i] as Node3D).position = (wl["base"][i] as Vector3) + off


func _in_gap(wl: Dictionary, p: Vector2) -> bool:
	return Geometry2D.is_point_in_polygon(p - Vector2(float(wl["dx"]), 0.0), wl["gap"])


func _place_ship() -> void:
	ship.global_transform = Transform3D(basis_at(s), _world(s, ship.pos2()))


func _cam_follow(dt: float, snap := false) -> void:
	var p := ship.pos2()
	var bs := basis_at(s)
	var want := curve.sample_baked(clampf(s - 12.0, 0.0, length)) + bs.x * (p.x * 0.75) + UP * (p.y * 0.75 + 4.5)
	if s < 12.0:
		want += bs.z * (12.0 - s)
	var look := _world(s + 25.0, p * 0.6) + UP * 1.0
	var kp := 1.0 if snap else 1.0 - exp(-dt / 0.25)
	var kr := 1.0 if snap else 1.0 - exp(-dt / 0.35)
	cam.global_position = cam.global_position.lerp(want, kp)
	_cam_look = _cam_look.lerp(look, kr)
	cam.look_at(_cam_look, UP)


func _update_enemies(dt: float) -> void:
	for e in enemies:
		if e.state == "wait" and s > e.s - SPAWN_AHEAD:
			e.activate()
		if e.kind == "guardian" and e.state == "live":
			e.s = maxf(e.s, s + 70.0)  # drifts ahead, waiting in front of the Gate
		if e.state == "live" or e.state == "dying" or e.state == "asleep":
			e.update(dt)
			if e.state == "dead":
				continue
			e.global_transform = Transform3D(basis_at(e.s), _world(e.s, e.offset)).scaled_local(e.scale)
			if e.state == "live" and absf(e.s - s) < e.radius() + 3.0:
				var rel := ship.pos2() - e.offset
				if rel.length() < e.radius() + 2.0:
					ship.bump(rel)
			if e.kind == "pod" and e.state == "live" and e.s - s < 140.0 and e.s > s + 20.0:
				e.fire_t -= dt
				if e.fire_t <= 0.0:
					e.fire_t = 3.0
					_pod_fire(e)
			if e.s < s - 30.0 and e.state == "live":
				e.state = "dead"  # left behind; not defeated, simply gone (stays gone after checkpoints)
				e.visible = false
	for b in bubbles:
		if not b["live"]:
			continue
		b["s"] -= 10.0 * dt  # drifts slowly toward the ship
		b["pos2"] += b["vel2"] * dt
		var n: MeshInstance3D = b["node"]
		n.global_position = _world(b["s"], b["pos2"])
		if absf(b["s"] - s) < 2.5 and (b["pos2"] - ship.pos2()).length() < 3.2:
			ship.bump(ship.pos2() - b["pos2"])
			b["live"] = false
			n.visible = false
		elif b["s"] < s - 10.0:
			b["live"] = false
			n.visible = false


func _pod_fire(e: Enemy) -> void:
	for b in bubbles:
		if not b["live"]:
			b["live"] = true
			b["s"] = e.s
			b["pos2"] = e.offset + Vector2(0, 3.5)
			b["vel2"] = (ship.pos2() - b["pos2"]) / maxf((e.s - s) / (speed + 10.0), 1.0) * 0.6
			(b["node"] as Node3D).visible = true
			return


func _update_combat(dt: float) -> void:
	var fwd := -basis_at(s).z
	var origin := ship.global_position
	# lock-on with hysteresis: keep target until it leaves the larger cone
	var keep := target != null and target.alive() and _angle_to(origin, fwd, target) < AIM_KEEP and target.s > s
	if not keep:
		var best: Enemy = null
		var best_a := AIM_CONE
		for e in enemies:
			if e.alive() and e.s > s + 8.0 and e.s < s + 130.0:
				var a := _angle_to(origin, fwd, e)
				if a < best_a:
					best_a = a
					best = e
		if best != target:
			target = best
			lock_t = 0.0
	lock_t += dt
	ring.visible = target != null
	if target:
		ring.global_position = target.global_position
		ring.look_at(cam.global_position, UP)
		ring.rotate_object_local(Vector3.RIGHT, PI / 2)
		ring.scale = Vector3.ONE * (target.radius() / 3.6) * (1.0 + 0.08 * Game.pulse(2)) * clampf(lock_t / 0.3, 0.3, 1.0)
	fire_cd -= dt
	if Input.is_action_pressed("fire") and fire_cd <= 0.0:
		fire_cd = FIRE_RATE
		fired_once = true
		for sh in shots:
			if not sh["live"]:
				sh["live"] = true
				sh["life"] = SHOT_LIFE
				sh["vel"] = fwd * (SHOT_SPEED + speed)
				(sh["node"] as Node3D).global_position = origin + fwd * 3.5
				(sh["node"] as Node3D).visible = true
				AudioBus.play("sfx_shot", randf_range(0.95, 1.05))
				break
	glint.visible = not fired_once and enemies.any(func(e: Enemy) -> bool: return e.alive())
	if glint.visible:
		glint.scale = Vector3.ONE * (0.6 + 0.8 * Game.pulse(2))
	for sh in shots:
		if not sh["live"]:
			continue
		var n: Node3D = sh["node"]
		if target and lock_t > 0.3:
			var want: Vector3 = (target.global_position - n.global_position).normalized() * sh["vel"].length()
			sh["vel"] = (sh["vel"] as Vector3).lerp(want, 1.0 - exp(-6.0 * dt))
		n.global_position += sh["vel"] * dt
		sh["life"] -= dt
		for e in enemies:
			if e.alive() and n.global_position.distance_to(e.global_position) < e.radius():
				e.hit()
				sh["life"] = 0.0
				AudioBus.play("sfx_hit")
				break
		if sh["life"] <= 0.0:
			sh["live"] = false
			n.visible = false


func _angle_to(origin: Vector3, fwd: Vector3, e: Enemy) -> float:
	return fwd.angle_to(e.global_position - origin)


func _on_popped(e: Enemy) -> void:
	if e.kind == "guardian":
		_light_gate(e)
		return
	AudioBus.play("sfx_puff")
	for p in puffs:
		if not p.emitting:
			p.global_position = e.global_position
			p.restart()
			break
	var sc: PackedScene = load("res://assets/fx/pickup_orb.glb")
	var n := 1 + int(e.phase * 10.0) % 3 if e.kind != "guardian" else 0
	for i in n:
		_add_orb(sc, e.global_position + Vector3(randf_range(-2, 2), randf_range(-1, 2), randf_range(-2, 2)), true)
	enemy_popped.emit()


func _light_gate(e: Enemy) -> void:
	gate_lit = true
	AudioBus.play("sfx_jingle")
	sparkle.global_position = e.global_position
	sparkle.restart()
	Game.paint(e.model, true)
	var gn := _world_root.find_child("gate_0", true, false)
	if gn:
		Game.paint(gn, true)
	enemy_popped.emit()


func _update_orbs(dt: float) -> void:
	var sp := ship.global_position
	for o in orbs:
		if o["taken"]:
			continue
		var n: Node3D = o["node"]
		var p: Vector3 = o["pos"]
		if o["free"]:  # orbs from popped critters float to the ship
			var d := sp - p
			if d.length() < 30.0:
				p += d.normalized() * minf(d.length(), (speed + 14.0) * dt)
				o["pos"] = p
		n.position = p + UP * sin(Game.t * PI + p.x) * 0.3
		n.rotation.y = Game.t * 1.5
		n.scale = Vector3.ONE * (1.0 + 0.12 * Game.pulse())
		if p.distance_to(sp) < ORB_R:
			o["taken"] = true
			n.visible = false
			collected += 1
			AudioBus.chime()
			sparkle.global_position = sp
			sparkle.restart()
			orb_collected.emit()


func _restart_input(dt: float) -> void:
	if Input.is_action_pressed("restart"):
		restart_hold += dt
		if restart_hold >= 1.0:
			restart_hold = -INF
			Game.start_level(Game.level_id)
	else:
		if restart_hold > 0.0:
			to_checkpoint()
		restart_hold = 0.0


func to_checkpoint() -> void:
	s = checkpoint
	speed = base_speed * 0.4
	ship.x = 0.0
	ship.y = _floor_at(s, 0.0) + Ship.HOVER_H if mode == "hover" else 0.0
	ship.vel = Vector2.ZERO
	stall_t = 0.0
	for e in enemies:  # critters ahead that were "left behind" come back; defeated ones stay defeated
		if e.state == "dead" and e.hp > 0 and e.s > s:
			e.state = "wait"
			e.scale = Vector3.ONE * 0.01
	_place_ship()
	_cam_follow(1.0, true)


func _on_honk() -> void:
	if get_tree().paused or finished:
		return
	AudioBus.play("sfx_honk", randf_range(0.95, 1.08))
	ship.happy()


func _on_bump() -> void:
	bumps += 1
	_bump_times.append(Game.t)


## Invisible assist: more bumps/stalls recently -> easier. Decays slowly; never harder.
func _update_assist(dt: float) -> void:
	while not _bump_times.is_empty() and Game.t - _bump_times[0] > 20.0:
		_bump_times.pop_front()
	var want := clampf(_bump_times.size() / 6.0 + (0.5 if stall_t > 2.0 else 0.0), 0.0, 1.0)
	assist = move_toward(assist, want, (0.5 if want > assist else 0.03) * dt)


func request_pause() -> void:
	if finished or get_tree().paused or bot != null:
		return
	get_tree().paused = true
	pause_layer = CanvasLayer.new()
	pause_layer.process_mode = Node.PROCESS_MODE_ALWAYS
	var dim := ColorRect.new()
	dim.color = Color(0.2, 0.18, 0.3, 0.45)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	pause_layer.add_child(dim)
	var m := IconMenu.new()
	m.icon_size = 100.0
	m.set_anchors_preset(Control.PRESET_CENTER)
	m.add_item("resume", "play", Color("#8ff0e0"))
	m.add_item("restart", "restart", Color("#ffd59e"))
	m.add_item("home", "book", Color("#f3b6d8"))
	m.add_item("speed", "speed_%d" % (_speed_idx() + 1), Color("#b9e3a0"))
	pause_layer.add_child(m)
	m.position -= Vector2(m.get_combined_minimum_size().x / 2, 64)
	m.chosen.connect(_on_pause_choice)
	add_child(pause_layer)


const SPEEDS := [0.6, 0.8, 1.0]


func _speed_idx() -> int:
	var cur := float(Save.setting("speed"))
	var best := 0
	for i in SPEEDS.size():
		if absf(SPEEDS[i] - cur) < absf(SPEEDS[best] - cur):
			best = i
	return best


func _on_pause_choice(id: String) -> void:
	if id == "speed":  # wordless speed: 1, 2 or 3 chevrons; stays in the pause menu
		var i := (_speed_idx() + 1) % SPEEDS.size()
		Save.set_setting("speed", SPEEDS[i])
		(pause_layer.get_child(1) as IconMenu).set_icon("speed", "speed_%d" % (i + 1))
		AudioBus.play("sfx_honk", 0.9 + 0.1 * i)
		return
	pause_layer.queue_free()
	get_tree().paused = false
	match id:
		"restart":
			to_checkpoint()
		"home":
			Game.go(Game.BOOK)


func _unhandled_input(ev: InputEvent) -> void:
	if get_tree().paused and pause_layer and is_instance_valid(pause_layer) and ev.is_action_pressed("pause"):
		_on_pause_choice("resume")


func _finish() -> void:
	finished = true
	AudioBus.play("sfx_jingle")
	ship.happy()
	hud.call("celebrate")
	if bot:  # tests never touch the family's progress
		Game.quit_bot(result())
		return
	Save.record_level(Game.level_id, collected, total_orbs)
	await get_tree().create_timer(4.5).timeout
	Game.go(Game.ENDING if Game.level_id == Game.last_level() else Game.BOOK)


func result() -> Dictionary:
	var sorted := frame_ms.duplicate()
	sorted.sort()
	var avg := 0.0
	for v in frame_ms:
		avg += v
	avg /= maxf(frame_ms.size(), 1)
	return {"ok": finished, "level": Game.level_id, "time_s": snappedf(Game.t, 0.1), "bumps": bumps, "stalls": stalls,
		"orbs": collected, "orb_total": total_orbs, "popped": enemies.filter(func(e: Enemy) -> bool: return e.hp <= 0).size(),
		"enemies": enemies.size(), "frame_ms_avg": snappedf(avg, 0.01),
		"frame_ms_p99": snappedf(sorted[int(sorted.size() * 0.99)] if sorted.size() > 0 else 0.0, 0.01)}


# ---------------- screenshot tour ----------------
func _shot_tour() -> void:
	var stops: Array[float] = [20.0]
	for wl in walls:
		stops.append(wl["s"] - 90.0)
		stops.append(wl["s"] - 30.0)
	for r: Array in L["rest_areas"]:
		stops.append((float(r[0]) + float(r[1])) * 0.5)
	for e in enemies:
		stops.append(e.s - 60.0)
		break
	if L.get("gate") != null:
		stops.append(float(L["gate"]["s"]) - 140.0)
	stops.append(length - 40.0)
	stops.sort()
	touring = true
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://docs/shots"))
	for i in stops.size():
		s = stops[i]
		ship.x = 0.0
		_place_ship()
		_cam_follow(1.0, true)
		for k in 20:
			await get_tree().process_frame
		var img := get_viewport().get_texture().get_image()
		img.save_png("res://docs/shots/level_%d_%02d.png" % [Game.level_id, i])
	print("SHOTS ", stops.size())
	get_tree().quit()
