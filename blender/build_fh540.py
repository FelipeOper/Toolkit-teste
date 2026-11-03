"""Volvo FH 540 6x4 Globetrotter (nova geracao) - modelo v2.

Eixos: x = lateral (DIREITA do caminhao = -x, ESQUERDA = +x), y = frente(-) -> traseira(+), z = altura.
Eixo dianteiro em y=0. Unidades em metros.
Medidas tiradas das fotos de referencia (largura da cabine 2,50 m e pneu 1,04 m como escala).

Uso: python blender/build_fh540.py [--render] [--views front,front34,sideL,rear34]
"""
import sys, math, os
import bpy, bmesh
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.environ.get("FH_TMP", "/tmp")
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
KEEP = []  # objetos que vao para o .glb

# Medidas de referencia (lateral Volvo FH 6x4: cota 4100 mm eixo dianteiro -> ultimo eixo; pneu 1,03 m)
# CONFIRMAR com trena no caminhao real (entre-eixos varia por configuracao).
D1, D2 = 2.74, 4.10          # eixos trativos (y); dianteiro em y=0
FW_Y = 3.25                  # centro da quinta roda
FRAME_END = D2 + 0.90        # fim do chassi
CAB_BOTTOM = 1.15            # piso da cabine (z)
ROOF = 3.70                  # teto Globetrotter (z)


def rear(z):
    """y da traseira da cabine na altura z (a traseira inclina para tras embaixo)."""
    return 1.48 - 0.34 * (z - CAB_BOTTOM) / (3.60 - CAB_BOTTOM)



# ---------------------------------------------------------------- materiais
def mat(name, color, metallic=0.0, rough=0.5, alpha=1.0, image=None, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    if image:
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = image
        m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    return m


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


def hex_texture(name, w_m, h_m, fg="#6f9bb5", bg="#08090b", ppm=500):
    """Grade hexagonal alongada (frente do FH) como imagem, com antialias (desenha 3x e reduz)."""
    from PIL import Image, ImageDraw, ImageFilter
    k = 3
    W, H = int(w_m * ppm), int(h_m * ppm)
    im = Image.new("RGB", (W * k, H * k), bg)
    d = ImageDraw.Draw(im)
    cw, ch = 60 * k, 22 * k
    col, x = 0, -cw
    while x < W * k + cw:
        y = -ch + (ch / 2 if col % 2 else 0)
        while y < H * k + ch:
            pts = [(x, y + ch / 2), (x + cw * .25, y), (x + cw * .75, y), (x + cw, y + ch / 2),
                   (x + cw * .75, y + ch), (x + cw * .25, y + ch)]
            d.polygon(pts, outline=fg, width=6 * k)
            y += ch
        x += cw * .75
        col += 1
    im = im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.3))
    path = os.path.join(TMP, f"{name}.png")
    im.save(path)
    img = bpy.data.images.load(path)
    img.pack()
    return img


M = {
    "paint": mat("paint", srgb("#35566a"), 0.55, 0.28),
    "face": mat("face", srgb("#3a3d41"), 0.1, 0.55),
    "glass": mat("glass", srgb("#3b5159"), 0.0, 0.03, 0.30),
    "rubber": mat("rubber", srgb("#161616"), 0, 0.9),
    "chrome": mat("chrome", srgb("#d5d8dc"), 1.0, 0.12),
    "plastic": mat("plastic", srgb("#141517"), 0, 0.6),
    "steel": mat("steel", srgb("#3a3d41"), 0.7, 0.5),
    "frame": mat("frame", srgb("#25282c"), 0.3, 0.6),
    "alu": mat("alu", srgb("#c9ccd0"), 0.95, 0.28),
    "rim": mat("rim", srgb("#b4b8bd"), 0.9, 0.35),
    "light": mat("light", srgb("#aeb8bf"), 0.4, 0.12, emit=0.0),
    "led": mat("led", srgb("#fff6dc"), 0.0, 0.1, emit=3.0),
    "red": mat("red", srgb("#9b1111"), 0, 0.2, emit=0.4),
    "amber": mat("amber", srgb("#e88a14"), 0, 0.2, emit=0.6),
    "battery": mat("battery", srgb("#aeb2b6"), 0.7, 0.45),
    "adblue": mat("adblue", srgb("#1c1d1f"), 0, 0.6),
    "bluecap": mat("bluecap", srgb("#2a63d6"), 0, 0.4),
}


# ---------------------------------------------------------------- utilitarios
def link(o):
    bpy.context.collection.objects.link(o)
    return o


def obj_from_bm(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def prism(name, pts, axis, a0, a1):
    """Poligono 2D extrudado. axis x: pts=(y,z); y: pts=(x,z); z: pts=(x,y)."""
    bm = bmesh.new()
    P = {"x": lambda p, a: (a, p[0], p[1]), "y": lambda p, a: (p[0], a, p[1]), "z": lambda p, a: (p[0], p[1], a)}[axis]
    f = bm.faces.new([bm.verts.new(P(p, a0)) for p in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    vv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    d = a1 - a0
    bmesh.ops.translate(bm, verts=vv, vec={"x": (d, 0, 0), "y": (0, d, 0), "z": (0, 0, d)}[axis])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return obj_from_bm(name, bm)


def active(o):
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    o.select_set(True)


def apply_mod(o, m):
    active(o)
    bpy.ops.object.modifier_apply(modifier=m.name)


def boolean(o, other, op="DIFFERENCE"):
    m = o.modifiers.new("bool", "BOOLEAN")
    m.operation, m.object, m.solver = op, other, "EXACT"
    apply_mod(o, m)


def bevel(o, width, seg=3, angle=30):
    m = o.modifiers.new("bevel", "BEVEL")
    m.width, m.segments, m.limit_method = width, seg, "ANGLE"
    m.angle_limit = math.radians(angle)
    apply_mod(o, m)


def smooth(o):
    active(o)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception:
        for p in o.data.polygons:
            p.use_smooth = True


def finish(o, material, bev=0.0, seg=3, keep=True):
    if bev:
        bevel(o, bev, seg)
    o.data.materials.clear()
    o.data.materials.append(M[material] if isinstance(material, str) else material)
    smooth(o)
    if keep:
        KEEP.append(o)
    return o


def region(x0, x1, y0, y1, z0, z1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.active_object
    o.scale = (x1 - x0, y1 - y0, z1 - z0)
    bpy.ops.object.transform_apply(scale=True)
    return o


def trash(*objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def box(name, size, loc, material="paint", bev=0.02, rot=(0, 0, 0), keep=True, seg=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return finish(o, material, bev, seg, keep)


def cyl(name, r, depth, loc, axis="z", material="steel", verts=32, bev=0.0, keep=True):
    rot = {"x": (0, math.pi / 2, 0), "y": (math.pi / 2, 0, 0), "z": (0, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return finish(o, material, bev, keep=keep)


def join(name, objs, material=None):
    active(objs[0])
    for o in objs:
        o.select_set(True)
    for o in objs:
        if o in KEEP:
            KEEP.remove(o)
    bpy.ops.object.join()
    j = bpy.context.active_object
    j.name = name
    if material:
        j.data.materials.clear()
        j.data.materials.append(M[material])
    KEEP.append(j)
    return j


def rename(o, name):
    o.name = name
    return o


SIDES = {"L": 1, "R": -1}  # L = esquerda (lado do motorista) = +x


# ================================================================ CABINE
# ---- casca principal (visual hull: silhueta lateral x silhueta frontal)
side = [(rear(CAB_BOTTOM), CAB_BOTTOM), (rear(3.60), 3.60), (1.05, 3.67), (0.75, ROOF), (0.0, ROOF), (-0.40, 3.66), (-0.75, 3.61),
        (-1.00, 3.45), (-0.93, 3.12), (-1.02, 2.30), (-1.08, 2.28), (-1.08, 1.75), (-0.57, 1.75), (-0.57, CAB_BOTTOM)]
frontsil = [(1.25, CAB_BOTTOM), (1.25, 2.95), (1.22, 3.20), (1.15, 3.42), (1.03, 3.57), (0.85, 3.65), (0.55, 3.69), (0.0, 3.71),
            (-0.55, 3.69), (-0.85, 3.65), (-1.03, 3.57), (-1.15, 3.42), (-1.22, 3.20), (-1.25, 2.95), (-1.25, CAB_BOTTOM)]
A = prism("hullA", side, "x", -1.4, 1.4)
B = prism("hullB", frontsil, "y", -1.2, 1.7)
boolean(A, B, "INTERSECT")
trash(B)
shell = rename(A, "cab_shell")
# frente mais estreita (face superior 2,34 m)
for sx in (1, -1):
    c = region(1.17 if sx > 0 else -1.5, 1.5 if sx > 0 else -1.17, -1.3, -0.88, 1.6, 3.5)
    boolean(shell, c)
    trash(c)
bevel(shell, 0.07, 3, 35)

# ---- partes (cortes na casca)
parts_def = {
    "cab_door_L": (0.95, 1.4, -0.97, 0.04, CAB_BOTTOM, 3.12),
    "cab_door_R": (-1.4, -0.95, -0.97, 0.04, CAB_BOTTOM, 3.12),
    "cab_side_panel_L": (0.95, 1.4, 0.04, 0.92, CAB_BOTTOM, 3.12),
    "cab_side_panel_R": (-1.4, -0.95, 0.04, 0.92, CAB_BOTTOM, 3.12),
    "cab_rear_panel": (-1.4, 1.4, 0.92, 1.8, CAB_BOTTOM, 3.9),
    "cab_roof": (-1.4, 1.4, -0.80, 0.92, 3.12, 3.9),
    "cab_roof_front": (-1.4, 1.4, -1.2, -0.80, 3.50, 3.9),
    "cab_visor": (-1.4, 1.4, -1.2, -0.80, 3.12, 3.50),
    "cab_face_upper": (-1.4, 1.4, -1.2, -0.97, 1.75, 2.31),
}
core = bpy.data.objects.new("cab_structure", shell.data.copy())
link(core)
mats = {"cab_visor": "face", "cab_face_upper": "face"}
bev = {"cab_roof": 0.04, "cab_roof_front": 0.03, "cab_rear_panel": 0.025}
for name, r in parts_def.items():
    reg = region(*r)
    p = bpy.data.objects.new(name, shell.data.copy())
    link(p)
    boolean(p, reg, "INTERSECT")
    boolean(core, reg, "DIFFERENCE")
    trash(reg)
    if name == "cab_rear_panel":  # nicho do pos-tratamento na traseira da cabine
        rec = region(-0.62, 0.62, 1.15, 2.0, 1.0, 2.05)
        boolean(p, rec)
        trash(rec)
    finish(p, mats.get(name, "paint"), bev.get(name, 0.012), 2)
trash(shell)
finish(core, "paint", 0.0)

# ---- corpo frontal inferior (para-lamas + frente)
fside = [(-0.55, 0.40), (-0.55, 1.75), (-1.12, 1.75), (-1.24, 1.56), (-1.30, 1.40), (-1.30, 0.55), (-1.31, 0.40)]
ffront = [(-1.25, 0.40), (-1.25, 1.70), (-1.22, 1.75), (1.22, 1.75), (1.25, 1.70), (1.25, 0.40)]
F1 = prism("fa", fside, "x", -1.4, 1.4)
F2 = prism("fb", ffront, "y", -1.5, -0.5)
boolean(F1, F2, "INTERSECT")
trash(F2)
front = rename(F1, "cab_front_body")
arch = cyl("arch_cut", 0.68, 3.4, (0, 0, 0.52), "x", keep=False)
boolean(front, arch)
trash(arch)
for sx in (1, -1):
    well = region(0.90 if sx > 0 else -1.4, 1.4 if sx > 0 else -0.90, -0.98, -0.55, 0.30, 0.72)
    boolean(front, well)
    trash(well)
bevel(front, 0.05, 3, 35)
for s, sx in SIDES.items():
    reg = region(0.92 if sx > 0 else -1.4, 1.4 if sx > 0 else -0.92, -1.5, -0.5, 0.2, 1.8)
    fe = bpy.data.objects.new(f"cab_fender_front_{s}", front.data.copy())
    link(fe)
    boolean(fe, reg, "INTERSECT")
    boolean(front, reg, "DIFFERENCE")
    trash(reg)
    finish(fe, "paint", 0.012, 2)
finish(front, "paint", 0.0)
rename(front, "cab_front_panel")

# ---- vidros
quad = [(-0.93 - 0.012, 3.12), (-1.02 - 0.012, 2.30), (-1.04 - 0.012, 2.30), (-0.95 - 0.012, 3.12)]
ws = prism("windshield", quad, "x", -1.13, 1.13)
finish(ws, "glass", 0.0)
for s, sx in SIDES.items():
    box(f"cab_window_{s}", (0.014, 0.83, 0.80), (sx * 1.256, -0.505, 2.72), "glass", 0.004)
    box(f"cab_window_rear_{s}", (0.014, 0.70, 0.64), (sx * 1.256, 0.43, 2.75), "glass", 0.004)
    box(f"cab_door_handle_{s}", (0.03, 0.28, 0.05), (sx * 1.265, -0.17, 1.68), "chrome", 0.01)
    # espelhos
    for z, n in ((2.85, "up"), (2.05, "low")):
        box(f"mirror_arm_{n}_{s}", (0.30, 0.05, 0.05), (sx * 1.31, -0.93, z), "plastic", 0.01)
    box(f"mirror_{s}", (0.20, 0.27, 0.85), (sx * 1.40, -0.62, 2.48), "paint", 0.05, seg=3)
    box(f"mirror_glass_{s}", (0.17, 0.012, 0.78), (sx * 1.40, -0.485, 2.48), "plastic", 0.004)
    box(f"mirror_wide_{s}", (0.16, 0.20, 0.28), (sx * 1.40, -0.66, 2.12), "plastic", 0.04)
    box(f"mirror_conn_{s}", (0.05, 0.30, 0.05), (sx * 1.43, -0.80, 2.85), "plastic", 0.01)
    # defletores traseiros e entrada de ar (seguem a inclinacao da traseira da cabine)
    d = prism("defl", [(rear(1.25), 1.25), (rear(1.25) + 0.30, 1.25), (rear(3.40) + 0.30, 3.40), (rear(3.40), 3.40)], "x",
              sx * 1.18, sx * 1.25)
    finish(d, "plastic", 0.012, 2, keep=False)
    rename(d, f"cab_side_deflector_{s}")
    KEEP.append(d)
    ang = math.atan(0.34 / (3.60 - CAB_BOTTOM))
    ribs = [box(f"rib{i}", (0.34, 0.30, 0.018), (sx * 0.98, rear(1.45 + i * 0.09) + 0.17, 1.45 + i * 0.09), "adblue", 0.004,
                rot=(ang, 0, 0), keep=False) for i in range(20)]
    body = prism("intake_body", [(rear(1.35) + 0.02, 1.35), (rear(1.35) + 0.32, 1.35), (rear(3.25) + 0.32, 3.25), (rear(3.25) + 0.02, 3.25)],
                 "x", sx * 0.82, sx * 1.14)
    finish(body, "plastic", 0.02, 2, keep=False)
    join(f"cab_air_intake_{s}", [body] + ribs, "plastic")
    box(f"cab_step_lower_{s}", (0.34, 0.45, 0.05), (sx * 1.10, -0.78, 0.45), "steel", 0.01)
    box(f"cab_step_upper_{s}", (0.30, 0.40, 0.05), (sx * 1.10, -0.70, 0.84), "steel", 0.01)
    box(f"cab_skirt_{s}", (0.06, 2.40, 0.10), (sx * 1.225, 0.25, CAB_BOTTOM - 0.05), "plastic", 0.015)
    box(f"mudguard_front_{s}", (0.36, 1.30, 0.06), (sx * 1.02, 0.0, 1.17), "plastic", 0.02)

# ---- face superior (rosto escuro), faixa Globetrotter, luzes de teto
cyl("cab_logo", 0.125, 0.02, (0, -1.10, 1.90), "y", "chrome", 40)
cyl("cab_logo_disc", 0.105, 0.025, (0, -1.103, 1.90), "y", "plastic", 40)
box("cab_logo_line", (0.95, 0.012, 0.014), (0.0, -1.093, 1.90), "chrome", 0.002, rot=(0, math.radians(-18), 0))
box("cab_cowl_strip", (2.18, 0.012, 0.018), (0, -1.095, 2.275), "chrome", 0.003)
for i, x in enumerate((-0.65, 0.42)):
    box(f"wiper_blade_{i}", (0.95, 0.02, 0.03), (x, -1.07, 2.33), "plastic", 0.005)
    box(f"wiper_mount_{i}", (0.28, 0.07, 0.07), (x - 0.18 if i == 0 else x + 0.18, -1.06, 2.28), "plastic", 0.015)
box("windshield_camera", (0.12, 0.05, 0.06), (0, -0.93, 3.02), "plastic", 0.01)
for i, x in enumerate((-0.33, 0.0, 0.33)):
    box(f"cab_roof_light_{i}", (0.10, 0.03, 0.04), (x, -0.90, 3.66), "led", 0.01)
for s, sx in SIDES.items():
    box(f"cab_corner_light_{s}", (0.15, 0.04, 0.10), (sx * 0.95, -1.012, 3.30), "led", 0.01)
cyl("antenna", 0.007, 0.28, (-0.76, -0.55, 3.88), "z", "plastic", 8)

# ---- frente: grade hexagonal, aletas, para-choque, faróis
def front_uv(o):
    """Projeta a imagem inteira na face frontal (UV planar em x/z)."""
    me = o.data
    xs = [v.co.x for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    uv = me.uv_layers.active or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x - x0) / (x1 - x0), (co.z - z0) / (z1 - z0))


def gimg(n, w, h):
    return hex_texture(n, w, h)

GY = -1.312
box("grille_backing", (1.90, 0.012, 1.12), (0, GY + 0.004, 0.99), "plastic", 0.01)
box("grille_housing", (1.95, 0.05, 0.14), (0, GY, 1.49), "plastic", 0.012)
for nm, w, h, z in (("grille_mesh_upper", 1.79, 0.27, 1.31), ("grille_mesh_mid", 1.75, 0.14, 1.09), ("grille_mesh_lower", 1.60, 0.09, 0.705)):
    m = mat(nm, (1, 1, 1), 0.5, 0.4, image=gimg(nm, w, h))
    M[nm] = m
    pn = box(nm, (w, 0.022, h), (0, GY - 0.006, z), nm, 0.0)
    front_uv(pn)
box("grille_slats_upper", (1.55, 0.03, 0.30), (0, GY - 0.004, 0.875), "face", 0.01)
box("grille_slats_lower", (1.45, 0.03, 0.20), (0, GY - 0.004, 0.535), "face", 0.01)
for i, z in enumerate((0.965, 0.835, 0.60, 0.47)):
    box(f"grille_chrome_{i}", (1.5 if i < 2 else 1.4, 0.018, 0.022), (0, GY - 0.022, z), "chrome", 0.004)
box("grille_radar_plate", (0.30, 0.02, 0.12), (0, GY - 0.02, 0.56), "plastic", 0.01)
box("bumper_front", (2.50, 0.12, 0.24), (0, -1.30, 0.30), "paint", 0.04)
box("bumper_center_plate", (0.78, 0.02, 0.17), (0, -1.365, 0.30), "plastic", 0.01)

for s, sx in SIDES.items():
    HY0, HY1 = GY - 0.016, GY + 0.015
    strip = prism("hs", [(sx * 1.22, 1.18), (sx * 1.12, 1.18), (sx * 0.93, 0.74), (sx * 1.04, 0.70)], "y", HY0, HY1)
    low = prism("hl", [(sx * 0.88, 0.72), (sx * 1.24, 0.72), (sx * 1.20, 0.52), (sx * 0.90, 0.52)], "y", HY0, HY1)
    for p in (strip, low):
        finish(p, "light", 0.004, 2, keep=False)
    h = join(f"headlight_{s}", [strip, low], "light")
    box(f"drl_{s}", (0.04, 0.02, 0.40), (sx * 1.07, GY - 0.03, 0.97), "led", 0.005, rot=(0, math.radians(sx * 13), 0))
    box(f"fog_light_{s}", (0.20, 0.04, 0.07), (sx * 1.06, -1.345, 0.455), "light", 0.012)
    box(f"cab_turn_signal_{s}", (0.012, 0.18, 0.05), (sx * 1.253, -0.35, 1.42), "amber", 0.006)

# ================================================================ CHASSI
for s, sx in SIDES.items():
    box(f"chassis_rail_{s}", (0.10, FRAME_END + 0.55, 0.30), (sx * 0.43, (FRAME_END - 0.55) / 2, 0.85), "frame", 0.012)
for i, y in enumerate((0.6, 1.7, 2.6, 3.7, 4.6)):
    box(f"chassis_crossmember_{i}", (0.76, 0.09, 0.22), (0, y, 0.84), "frame", 0.01)
box("deck_plate", (1.0, 0.70, 0.04), (0, 2.00, 1.02), "chrome", 0.005)
cyl("driveshaft", 0.07, D1 - 0.2, (0, (D1 + 0.2) / 2 + 0.1, 0.62), "y", "steel", 20)
box("cab_rear_recess", (1.22, 0.04, 0.98), (0, 1.22, 1.52), "plastic", 0.01)
cyl("dpf_scr", 0.27, 0.76, (0.10, 1.42, 1.50), "x", "steel", 36, bev=0.0)
cyl("air_tank", 0.15, 0.95, (0, 2.20, 0.48), "x", "adblue", 24)
cyl("air_dryer", 0.07, 0.22, (-0.2, 2.05, 0.80), "z", "chrome", 16)
box("ecu_chassis", (0.26, 0.32, 0.14), (0.15, 1.75, 0.70), "plastic", 0.015)
box("ebs_module", (0.18, 0.22, 0.12), (-0.18, 2.55, 0.62), "plastic", 0.012)

# tanques (esquerda = +x ; direita = -x)
TANK_Y0, TANK_Y1 = 0.72, D1 - 0.69         # do eixo dianteiro ate o para-lama traseiro
xs = 1.0 - 0.14
box("fuel_tank_L", (0.64, TANK_Y1 - TANK_Y0, 0.64), (xs, (TANK_Y0 + TANK_Y1) / 2, 0.78), "alu", 0.07, seg=3)
BAT_L, ADB_L = 0.55, 0.33
box("battery_box", (0.66, BAT_L, 0.64), (-(1.0 - 0.1), TANK_Y0 + BAT_L / 2, 0.76), "battery", 0.03)
box("adblue_tank", (0.62, ADB_L, 0.55), (-xs, TANK_Y0 + BAT_L + ADB_L / 2, 0.775), "adblue", 0.05, seg=3)
cyl("adblue_cap", 0.05, 0.05, (-xs, TANK_Y0 + BAT_L + ADB_L / 2, 1.075), "z", "bluecap", 16)
fy0 = TANK_Y0 + BAT_L + ADB_L
box("fuel_tank_R", (0.64, TANK_Y1 - fy0, 0.64), (-xs, (fy0 + TANK_Y1) / 2, 0.78), "alu", 0.07, seg=3)

# ================================================================ RODAS
TR, TW = 0.52, 0.295


def wheel(name, x, y, out):
    cyl(f"tire_{name}", TR, TW, (x, y, TR), "x", "rubber", 48, bev=0.035)
    rim = cyl(f"rimtmp_{name}", 0.30, TW + 0.01, (x, y, TR), "x", "rim", 32, keep=False)
    parts = [rim, cyl(f"hubtmp_{name}", 0.105, 0.05, (x + out * (TW / 2 + 0.005), y, TR), "x", "rim", 24, keep=False)]
    for i in range(10):
        a = i * 2 * math.pi / 10
        parts.append(cyl(f"nut{i}", 0.017, 0.03, (x + out * (TW / 2 + 0.02), y + 0.165 * math.cos(a), TR + 0.165 * math.sin(a)),
                         "x", "chrome", 8, keep=False))
    join(f"rim_{name}", parts, "rim")


for s, sx in SIDES.items():
    wheel(f"F_{s}", sx * 1.02, 0.0, sx)
    for tag, ay in (("D1", D1), ("D2", D2)):
        wheel(f"{tag}_{s}_out", sx * 1.06, ay, sx)
        wheel(f"{tag}_{s}_in", sx * 0.68, ay, sx)
for n, y in (("front", 0.0), ("drive1", D1), ("drive2", D2)):
    cyl(f"axle_{n}", 0.075, 2.05, (0, y, TR), "x", "steel", 20)
    if n != "front":
        cyl(f"diff_{n}", 0.21, 0.5, (0, y, TR), "x", "steel", 28)


def fender(name, x, y, w=0.95):
    o = cyl(name, 0.66, w, (x, y, TR), "x", "plastic", 40)
    inner = cyl("fi", 0.595, w + 0.1, (x, y, TR), "x", keep=False)
    boolean(o, inner)
    low = region(x - 1, x + 1, y - 1, y + 1, -1, 0.70)
    boolean(o, low)
    trash(inner, low)
    bevel(o, 0.012, 2)
    return o


for s, sx in SIDES.items():
    fender(f"mudguard_rear_{s}_1", sx * 0.88, D1)
    fender(f"mudguard_rear_{s}_2", sx * 0.88, D2)
    box(f"mudguard_rear_{s}_link", (0.95, 0.60, 0.07), (sx * 0.88, (D1 + D2) / 2, 1.17), "plastic", 0.02)
    box(f"mudflap_{s}", (0.90, 0.025, 0.42), (sx * 0.88, D2 + 0.72, 0.48), "rubber", 0.006)
    box(f"rear_light_{s}", (0.20, 0.05, 0.12), (sx * 0.95, FRAME_END + 0.02, 0.78), "red", 0.01)
    box(f"side_marker_{s}", (0.012, 0.12, 0.04), (sx * 1.34, D2 + 0.65, 0.95), "amber", 0.004)
box("rear_bumper_beam", (2.1, 0.12, 0.16), (0, FRAME_END + 0.05, 0.68), "steel", 0.015)

# ---- quinta roda (JOST)
box("fifth_wheel_plate", (1.0, 1.0, 0.06), (0, FW_Y, 1.03), "frame", 0.012)
box("fifth_wheel_base", (0.72, 0.60, 0.18), (0, FW_Y, 1.15), "steel", 0.02)
cyl("fifth_wheel_top", 0.48, 0.08, (0, FW_Y, 1.27), "z", "steel", 48, bev=0.012)

# ================================================================ SAIDA / RENDER
glb = os.path.join(ROOT, "models", "fh540.glb")
for o in bpy.data.objects:
    o.select_set(o in KEEP)
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True)
names = sorted(o.name for o in KEEP)
print("GLB:", glb, "objetos:", len(names))
open(os.path.join(TMP, "fh540_parts.txt"), "w").write("\n".join(names))

if "--render" in sys.argv:
    vsel = None
    if "--views" in sys.argv:
        vsel = sys.argv[sys.argv.index("--views") + 1].split(",")
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 40
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1280, 960
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 2, 0))
    g = bpy.context.active_object
    g.data.materials.append(mat("floor", srgb("#8a7a68"), 0, 0.9))
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.68, 0.9, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.1
    scene.world = w
    bpy.ops.object.light_add(type="SUN", location=(5, -8, 10), rotation=(math.radians(55), 0, math.radians(35)))
    bpy.context.active_object.data.energy = 3.5
    views = {
        "front": ((0, -16, 1.9), (0, 0, 1.9), 85),
        "front34": ((7.5, -9.5, 2.3), (0, 0.5, 1.8), 45),
        "front34R": ((-7.5, -9.5, 2.3), (0, 0.5, 1.8), 45),
        "sideL": ((17, 1.8, 1.9), (0, 1.8, 1.9), 50),
        "sideR": ((-17, 1.8, 1.9), (0, 1.8, 1.9), 50),
        "sideL_cab": ((9, -2.5, 2.2), (0, -0.2, 2.0), 50),
        "rear34": ((-7, 11.5, 3.2), (0, 2.0, 1.5), 40),
        "top": ((0, 1.8, 18), (0, 1.8, 0), 50),
    }
    for vn, (cl, tg, lens) in views.items():
        if vsel and vn not in vsel:
            continue
        bpy.ops.object.camera_add(location=cl)
        cam = bpy.context.active_object
        cam.rotation_euler = (Vector(tg) - Vector(cl)).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        scene.camera = cam
        scene.render.filepath = os.path.join(ROOT, "renders", f"fh540_{vn}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)
