"""Blockout Volvo FH 540 (cavalo mecanico 6x4, cabine Globetrotter).

Eixos: x = lateral (esq negativo), y = frente(-) -> traseira(+), z = altura.
Unidades em metros. Dimensoes aproximadas (ver docs/CHECKLIST.md).
Uso: python blender/build_fh540.py [--render]
"""
import sys, math, os
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- materiais ----------
def mat(name, color, metallic=0.0, rough=0.5, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m

M = {
    "paint": mat("paint", (0.02, 0.07, 0.25), 0.6, 0.25),
    "glass": mat("glass", (0.02, 0.05, 0.07), 0.0, 0.05, 0.45),
    "rubber": mat("rubber", (0.02, 0.02, 0.02), 0, 0.9),
    "chrome": mat("chrome", (0.8, 0.8, 0.82), 1.0, 0.12),
    "plastic": mat("plastic", (0.03, 0.03, 0.035), 0, 0.6),
    "steel": mat("steel", (0.25, 0.26, 0.28), 0.8, 0.45),
    "light": mat("light", (1.0, 0.95, 0.8), 0, 0.1),
    "red": mat("red", (0.6, 0.02, 0.02), 0, 0.2),
}

# ---------- helpers ----------
def finish(o, material, bevel=0.0, smooth=True):
    o.data.materials.append(M[material])
    if bevel:
        bm = o.modifiers.new("bevel", "BEVEL")
        bm.width, bm.segments, bm.limit_method = bevel, 3, "ANGLE"
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="bevel")
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    return o

def box(name, size, loc, material="paint", bevel=0.03, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return finish(o, material, bevel)

def cyl(name, r, depth, loc, rot=(0, 0, 0), material="steel", verts=32, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts,
                                        location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return finish(o, material, bevel)

SIDE = {"L": 1, "R": -1}  # frente = -y => direita do caminhao = -x

# ---------- dimensoes ----------
W = 2.50            # largura da cabine
TR, TW = 0.52, 0.315  # raio e largura do pneu
AX_F, AX_D1, AX_D2 = 0.0, 3.70, 5.00   # posicoes dos eixos (y)
CAB_Y0, CAB_Y1 = -0.62, 1.85           # frente e fundo da cabine
CAB_Z0 = 1.12

# ---------- chassi ----------
for s, sx in SIDE.items():
    box(f"chassis_rail_{s}", (0.10, 7.0, 0.28), (sx * 0.43, 2.9, 0.88), "steel", 0.01)
for i, y in enumerate([0.4, 1.6, 2.8, 4.0, 5.2]):
    box(f"chassis_crossmember_{i}", (0.86, 0.08, 0.2), (0, y, 0.88), "steel", 0.01)

# ---------- cabine ----------
box("cab_body_lower", (W, CAB_Y1 - CAB_Y0, 1.25), (0, (CAB_Y0 + CAB_Y1) / 2, CAB_Z0 + 0.63), "paint", 0.08)
box("cab_body_upper", (W - 0.06, CAB_Y1 - CAB_Y0 - 0.08, 1.35), (0, (CAB_Y0 + CAB_Y1) / 2 + 0.02, CAB_Z0 + 1.85), "paint", 0.10)
box("cab_roof_spoiler", (W - 0.3, 0.9, 0.22), (0, 1.35, 3.80), "paint", 0.06, rot=(math.radians(-8), 0, 0))
box("cab_roof_visor", (W - 0.2, 0.30, 0.10), (0, CAB_Y0 - 0.02, 3.55), "paint", 0.03)
box("cab_rear_panel", (W - 0.1, 0.06, 2.2), (0, CAB_Y1 + 0.03, CAB_Z0 + 1.4), "paint", 0.03)
box("windshield", (W - 0.30, 0.04, 1.30), (0, CAB_Y0 + 0.02, CAB_Z0 + 1.80), "glass", 0.01, rot=(math.radians(-6), 0, 0))
for s, sx in SIDE.items():
    box(f"cab_door_{s}", (0.05, 1.20, 1.80), (sx * (W / 2 + 0.01), 0.30, CAB_Z0 + 1.30), "paint", 0.04)
    box(f"cab_window_{s}", (0.04, 0.95, 0.70), (sx * (W / 2 + 0.035), 0.25, CAB_Z0 + 1.85), "glass", 0.01)
    box(f"cab_fender_front_{s}", (0.22, 0.95, 0.30), (sx * (W / 2 - 0.05), -0.05, 0.98), "paint", 0.05)
    box(f"cab_step_{s}", (0.30, 0.55, 0.06), (sx * (W / 2 - 0.15), 0.30, 0.55), "plastic", 0.01)
    box(f"cab_step2_{s}", (0.30, 0.55, 0.06), (sx * (W / 2 - 0.15), 0.30, 0.82), "plastic", 0.01)
    box(f"cab_side_skirt_{s}", (0.06, 1.7, 0.45), (sx * (W / 2 + 0.02), 0.75, 0.88), "plastic", 0.02)
    box(f"mirror_arm_{s}", (0.45, 0.04, 0.04), (sx * (W / 2 + 0.22), CAB_Y0 + 0.30, 2.55), "plastic", 0.01)
    box(f"mirror_{s}", (0.10, 0.04, 0.60), (sx * (W / 2 + 0.45), CAB_Y0 + 0.30, 2.35), "plastic", 0.02)
    box(f"headlight_{s}", (0.62, 0.08, 0.20), (sx * 0.78, CAB_Y0 - 0.02, 1.38), "light", 0.04)
    box(f"drl_{s}", (0.50, 0.04, 0.04), (sx * 0.78, CAB_Y0 - 0.07, 1.54), "light", 0.01)
    box(f"fog_light_{s}", (0.20, 0.06, 0.14), (sx * 0.95, CAB_Y0 - 0.12, 0.72), "light", 0.03)

# ---------- frente ----------
box("grille", (1.05, 0.08, 0.80), (0, CAB_Y0 - 0.03, 1.55), "chrome", 0.04)
box("bumper_front", (W - 0.10, 0.30, 0.40), (0, CAB_Y0 - 0.15, 0.72), "plastic", 0.07)
box("license_plate_front", (0.52, 0.02, 0.13), (0, CAB_Y0 - 0.31, 0.72), "chrome", 0.005)

# ---------- tanques, baterias, escape ----------
for s, sx in SIDE.items():
    cyl(f"fuel_tank_{s}", 0.36, 1.35, (sx * 1.0, 2.4, 0.55), rot=(math.radians(90), 0, 0), material="chrome")
    box(f"mudguard_rear_{s}", (0.45, 0.9, 0.04), (sx * 1.05, AX_D1 + 0.65, 1.08), "plastic", 0.02)
box("battery_box", (0.55, 0.70, 0.45), (1.05, 1.1, 0.62), "plastic", 0.03)
cyl("exhaust_pipe", 0.07, 2.2, (-1.20, CAB_Y1 + 0.18, 2.20), material="chrome")
box("air_tank", (0.30, 0.95, 0.30), (1.0, 3.0, 0.45), "steel", 0.05)

# ---------- rodas ----------
def wheel(name, x, y):
    cyl(f"tire_{name}", TR, TW, (x, y, TR), rot=(0, math.radians(90), 0), material="rubber", verts=40, bevel=0.03)
    cyl(f"rim_{name}", TR * 0.62, TW + 0.02, (x, y, TR), rot=(0, math.radians(90), 0), material="chrome", verts=24)

for s, sx in SIDE.items():
    wheel(f"F_{s}", sx * 1.02, AX_F)
    for tag, ay in (("D1", AX_D1), ("D2", AX_D2)):
        wheel(f"{tag}_{s}_out", sx * 1.05, ay)
        wheel(f"{tag}_{s}_in", sx * 0.70, ay)
for n, y in (("front", AX_F), ("drive1", AX_D1), ("drive2", AX_D2)):
    cyl(f"axle_{n}", 0.07, 2.1, (0, y, TR), rot=(0, math.radians(90), 0), material="steel")

# ---------- quinta roda ----------
box("fifth_wheel_plate", (1.0, 0.95, 0.10), (0, 4.35, 1.10), "steel", 0.02)
box("fifth_wheel_base", (0.9, 0.7, 0.10), (0, 4.35, 1.00), "steel", 0.02)
for s, sx in SIDE.items():
    box(f"rear_light_{s}", (0.10, 0.06, 0.30), (sx * 0.95, 6.55, 0.85), "red", 0.02)
box("rear_bumper_beam", (2.2, 0.12, 0.16), (0, 6.5, 0.70), "steel", 0.02)

# ---------- cena ----------
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 3, 0))
ground = bpy.context.active_object
ground.name = "ground"
ground.data.materials.append(mat("floor", (0.35, 0.36, 0.38), 0, 0.8))
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.name != "ground":
        o.select_set(True)

out = os.path.join(ROOT, "models", "fh540_blockout.glb")
for o in bpy.data.objects:
    o.select_set(o.type == "MESH" and o.name != "ground")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True)
print("GLB:", out, "objetos:", sum(1 for o in bpy.data.objects if o.type == "MESH" and o.name != "ground"))

if "--render" in sys.argv:
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    w = bpy.data.worlds.new("w"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.7, 0.85, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
    scene.world = w
    bpy.ops.object.light_add(type="SUN", location=(5, -8, 10), rotation=(math.radians(50), 0, math.radians(30)))
    bpy.context.active_object.data.energy = 4
    views = {"front34": ((6.5, -7.5, 2.4), (0, 2.8, 1.6)),
             "side": ((12, 3, 1.8), (0, 3, 1.8)),
             "rear34": ((-6, 14, 3.0), (0, 3, 1.6))}
    for vn, (cl, tg) in views.items():
        bpy.ops.object.camera_add(location=cl)
        cam = bpy.context.active_object
        d = (cam.location.__class__(tg) - cam.location)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 40 if vn != "side" else 60
        scene.camera = cam
        scene.render.filepath = os.path.join(ROOT, "renders", f"fh540_blockout_{vn}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)
