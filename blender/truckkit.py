"""Kit de modelagem de caminhoes por script (Blender / bpy).

Convencao de eixos (todos os modelos):
  x = lateral (ESQUERDA do caminhao = +x, DIREITA = -x)
  y = frente (-) -> traseira (+), eixo dianteiro em y = 0
  z = altura, chao em z = 0
Unidades em metros. Cada peca clicavel e um objeto com nome padronizado (ver web/src/parts.ts).

Uso tipico (ver build_fh540.py):
    import truckkit as tk
    tk.reset(); tk.base_materials("#35566a")
    shell = tk.hull3("cab_shell", side, front, plan)
    ...
    tk.export_glb("models/x.glb"); tk.render("x", views)
"""
import os
import math
import bpy
import bmesh
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.environ.get("FH_TMP", "/tmp")
KEEP = []   # objetos exportados para o .glb
M = {}      # materiais por nome
SIDES = {"L": 1, "R": -1}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    KEEP.clear()
    M.clear()


# ================================================================ materiais
def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


def mat(name, color, metallic=0.0, rough=0.5, alpha=1.0, image=None, emit=0.0, coat=0.0):
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
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    if image:
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = image
        m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    M[name] = m
    return m


def base_materials(paint="#35566a", face="#3a3d41"):
    mat("paint", srgb(paint), 0.55, 0.30, coat=0.6)
    mat("face", srgb(face), 0.1, 0.55)
    mat("glass", srgb("#2e4148"), 0.0, 0.03, 0.30)
    mat("rubber", srgb("#161616"), 0, 0.88)
    mat("chrome", srgb("#d5d8dc"), 1.0, 0.10)
    mat("plastic", srgb("#141517"), 0, 0.6)
    mat("steel", srgb("#3a3d41"), 0.7, 0.5)
    mat("frame", srgb("#25282c"), 0.3, 0.6)
    mat("alu", srgb("#c9ccd0"), 0.95, 0.28)
    mat("rim", srgb("#b4b8bd"), 0.9, 0.35)
    mat("light", srgb("#c5cdd2"), 0.2, 0.06, 0.85)
    mat("led", srgb("#fff6dc"), 0.0, 0.1, emit=3.0)
    mat("red", srgb("#9b1111"), 0, 0.2, emit=0.4)
    mat("amber", srgb("#e88a14"), 0, 0.2, emit=0.6)
    mat("battery", srgb("#aeb2b6"), 0.7, 0.45)
    mat("adblue", srgb("#1c1d1f"), 0, 0.6)
    mat("bluecap", srgb("#2a63d6"), 0, 0.4)


def hex_texture(name, w_m, h_m, fg="#6f9bb5", bg="#08090b", ppm=500, cell=(60, 22), line=6):
    """Grade hexagonal alongada como imagem (desenha 3x, reduz e suaviza)."""
    from PIL import Image, ImageDraw, ImageFilter
    k = 3
    W, H = int(w_m * ppm), int(h_m * ppm)
    im = Image.new("RGB", (W * k, H * k), bg)
    d = ImageDraw.Draw(im)
    cw, ch = cell[0] * k, cell[1] * k
    col, x = 0, -cw
    while x < W * k + cw:
        y = -ch + (ch / 2 if col % 2 else 0)
        while y < H * k + ch:
            pts = [(x, y + ch / 2), (x + cw * .25, y), (x + cw * .75, y), (x + cw, y + ch / 2),
                   (x + cw * .75, y + ch), (x + cw * .25, y + ch)]
            d.polygon(pts, outline=fg, width=line * k)
            y += ch
        x += cw * .75
        col += 1
    im = im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.3))
    path = os.path.join(TMP, f"{name}.png")
    im.save(path)
    img = bpy.data.images.load(path)
    img.pack()
    return img


# ================================================================ malha basica
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


def lathe(name, profile, steps=48, closed=True):
    """Superficie de revolucao em torno do eixo x. profile = [(a, r), ...] (a = posicao axial)."""
    bm = bmesh.new()
    rings = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        rings.append([bm.verts.new((a, r * math.cos(t), r * math.sin(t))) for a, r in profile])
    n = len(profile)
    for i in range(steps):
        A, B = rings[i], rings[(i + 1) % steps]
        for j in range(n if closed else n - 1):
            k = (j + 1) % n
            bm.faces.new((A[j], A[k], B[k], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
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


def smooth(o, angle=35):
    active(o)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    except Exception:
        for p in o.data.polygons:
            p.use_smooth = True


def set_mat(o, material):
    o.data.materials.clear()
    o.data.materials.append(M[material] if isinstance(material, str) else material)


def finish(o, material, bev=0.0, seg=3, keep=True, angle=35):
    if bev:
        bevel(o, bev, seg)
    if material is not None:
        set_mat(o, material)
    smooth(o, angle)
    if keep and o not in KEEP:
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
        if o in KEEP:
            KEEP.remove(o)
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
    bpy.ops.object.transform_apply(rotation=True)
    return finish(o, material, bev, keep=keep)


def join(name, objs, material=None):
    active(objs[0])
    for o in objs:
        o.select_set(True)
        if o in KEEP:
            KEEP.remove(o)
    bpy.ops.object.join()
    j = bpy.context.active_object
    j.name = name
    if material:
        set_mat(j, material)
    KEEP.append(j)
    return j


def rename(o, name):
    o.name = name
    return o


def copy(o, name):
    c = bpy.data.objects.new(name, o.data.copy())
    return link(c)


def tube(name, pts, r, material="plastic", keep=True):
    """Tubo ao longo de uma poligonal 3D (bracos de espelho, mangueiras)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
    o = link(bpy.data.objects.new(name, cu))
    active(o)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object
    o.name = name
    return finish(o, material, keep=keep)


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


# ================================================================ formas de carroceria
def plan_round(hw, y0, y1, rf=(0.2, 0.25), rr=(0.1, 0.1), n=10):
    """Silhueta em planta (x, y) simetrica: retangulo de meia-largura hw de y0 (frente) a y1 (tras),
    cantos dianteiros elipticos rf=(rx, ry) e traseiros rr."""
    pts = []
    rx, ry = rf
    for i in range(n + 1):  # canto dianteiro direito (-x) -> esquerdo (+x)
        t = math.pi + (math.pi / 2) * i / n
        pts.append((-(hw - rx) + rx * math.cos(t), y0 + ry + ry * math.sin(t)))
    for i in range(n + 1):
        t = 1.5 * math.pi + (math.pi / 2) * i / n
        pts.append(((hw - rx) + rx * math.cos(t), y0 + ry + ry * math.sin(t)))
    rx, ry = rr
    for i in range(n + 1):
        t = (math.pi / 2) * i / n
        pts.append(((hw - rx) + rx * math.cos(t), y1 - ry + ry * math.sin(t)))
    for i in range(n + 1):
        t = math.pi / 2 + (math.pi / 2) * i / n
        pts.append((-(hw - rx) + rx * math.cos(t), y1 - ry + ry * math.sin(t)))
    return pts


def hull3(name, side, front, plan, ext=(-1.6, 1.6, -1.8, 2.2, -0.1, 4.6)):
    """Casco pela intersecao de 3 silhuetas: lateral (y,z), frontal (x,z) e planta (x,y)."""
    a = prism(name, side, "x", ext[0], ext[1])
    b = prism("hb", front, "y", ext[2], ext[3])
    c = prism("hc", plan, "z", ext[4], ext[5])
    boolean(a, b, "INTERSECT")
    boolean(a, c, "INTERSECT")
    trash(b, c)
    return a


def skin(o, t):
    """Pelicula externa de espessura t sobre a superficie de o (para recortar vidros/farois)."""
    s = copy(o, o.name + "_skin")
    m = s.modifiers.new("solid", "SOLIDIFY")
    m.thickness, m.offset = t, 1.0
    apply_mod(s, m)
    return s


def patch(name, sk, outline, axis, a0, a1, material, keep=True):
    """Peca recortada da pelicula sk pela projecao de um contorno 2D (segue a curvatura)."""
    p = prism(name, outline, axis, a0, a1)
    boolean(p, sk, "INTERSECT")
    return finish(p, material, keep=keep, angle=60)


def scale_poly(poly, k):
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in poly]


def groove(targets, p0, p1, x, width=0.012, depth=0.008):
    """Vinco (linha de estilo) na lateral: corta um sulco de p0=(y,z) a p1=(y,z) na superficie x."""
    (y0, z0), (y1, z1) = p0, p1
    L = math.hypot(y1 - y0, z1 - z0)
    ang = math.atan2(z1 - z0, y1 - y0)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, (y0 + y1) / 2, (z0 + z1) / 2), rotation=(ang, 0, 0))
    g = bpy.context.active_object
    g.scale = (depth * 2, L, width)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    for t in targets:
        boolean(t, g)
    trash(g)


# ================================================================ rodas
def wheel_templates(tr=0.52, tw=0.295, holes=10, nuts=10):
    """Cria (sem exportar) malhas-modelo de pneu e roda; a face externa aponta para +x."""
    h = tw / 2
    g = 0.010  # sulcos
    prof = [(-h + 0.012, 0.292), (-h - 0.004, 0.36), (-h - 0.006, 0.43), (-h + 0.008, 0.49), (-h + 0.035, tr - 0.004),
            (-h + 0.05, tr)]
    for c in (-0.075, 0.0, 0.075):
        prof += [(c - 0.012, tr), (c - 0.008, tr - g), (c + 0.008, tr - g), (c + 0.012, tr)]
    prof += [(h - 0.05, tr), (h - 0.035, tr - 0.004), (h - 0.008, 0.49), (h + 0.006, 0.43), (h + 0.004, 0.36),
             (h - 0.012, 0.292), (0, 0.286)]
    tire = lathe("tmpl_tire", prof, 64)
    finish(tire, "rubber", keep=False, angle=40)

    barrel = lathe("tmpl_barrel", [(-0.13, 0.302), (-0.125, 0.272), (0.125, 0.272), (0.13, 0.302), (0.12, 0.307),
                                   (0.10, 0.288), (-0.10, 0.288), (-0.12, 0.307)], 48)
    disc = lathe("tmpl_disc", [(0.055, 0.274), (0.075, 0.21), (0.092, 0.13), (0.095, 0.06), (0.080, 0.06), (0.077, 0.13),
                               (0.060, 0.21), (0.040, 0.274)], 48)
    for i in range(holes):
        a = 2 * math.pi * (i + 0.5) / holes
        c = cyl("hole", 0.033, 0.2, (0.07, 0.205 * math.cos(a), 0.205 * math.sin(a)), "x", keep=False)
        boolean(disc, c)
        trash(c)
    hub = cyl("tmpl_hub", 0.105, 0.09, (0.12, 0, 0), "x", "rim", 32, bev=0.01, keep=False)
    cap = cyl("tmpl_cap", 0.065, 0.05, (0.18, 0, 0), "x", "chrome", 24, bev=0.012, keep=False)
    parts = [barrel, disc, hub, cap]
    for o in (barrel, disc):
        finish(o, "rim", keep=False)
    for i in range(nuts):
        a = 2 * math.pi * i / nuts
        parts.append(cyl("nut", 0.018, 0.035, (0.11, 0.155 * math.cos(a), 0.155 * math.sin(a)), "x", "chrome", 6, keep=False))
    rim = join("tmpl_rim", parts)
    KEEP.remove(rim)
    return tire, rim


def place_wheel(name, x, y, z, out, tire_t, rim_t):
    for pre, t in (("tire_", tire_t), ("rim_", rim_t)):
        o = link(bpy.data.objects.new(pre + name, t.data))
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, 0 if out > 0 else math.pi)
        KEEP.append(o)


def fender(name, x, y, z, w=0.95, r=0.66, cut=0.70, th=0.065):
    o = cyl(name, r, w, (x, y, z), "x", "plastic", 48)
    inner = cyl("fi", r - th, w + 0.1, (x, y, z), "x", keep=False)
    boolean(o, inner)
    low = region(x - 1, x + 1, y - 1.5, y + 1.5, -1, cut)
    boolean(o, low)
    trash(inner, low)
    bevel(o, 0.012, 2)
    return o


# ================================================================ saida
def export_glb(path, parts_txt=None):
    for o in bpy.data.objects:
        o.select_set(o in KEEP)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)
    names = sorted(o.name for o in KEEP)
    print("GLB:", path, "objetos:", len(names))
    if parts_txt:
        open(parts_txt, "w").write("\n".join(names))
    return names


def render(prefix, views, select=None, out_dir=None, samples=40, size=(1280, 960)):
    scene = bpy.context.scene
    out_dir = out_dir or os.path.join(ROOT, "renders")
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = size
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
    for vn, (cl, tg, lens) in views.items():
        if select and vn not in select:
            continue
        bpy.ops.object.camera_add(location=cl)
        cam = bpy.context.active_object
        cam.rotation_euler = (Vector(tg) - Vector(cl)).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        scene.camera = cam
        scene.render.filepath = os.path.join(out_dir, f"{prefix}_{vn}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)


STD_VIEWS = {
    "front": ((0, -16, 1.9), (0, 0, 1.9), 85),
    "front34": ((7.5, -9.5, 2.3), (0, 0.5, 1.8), 45),
    "front34R": ((-7.5, -9.5, 2.3), (0, 0.5, 1.8), 45),
    "sideL": ((17, 1.8, 1.9), (0, 1.8, 1.9), 50),
    "sideR": ((-17, 1.8, 1.9), (0, 1.8, 1.9), 50),
    "rear34": ((-7, 11.5, 3.2), (0, 2.0, 1.5), 40),
    "top": ((0, 1.8, 18), (0, 1.8, 0), 50),
}
