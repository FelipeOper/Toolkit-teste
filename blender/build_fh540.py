"""Volvo FH 540 6x4 Globetrotter (nova geracao) - modelo v0.4.

Convencao de eixos: ver blender/truckkit.py (esquerda = +x, frente = -y, eixo dianteiro em y = 0).
Fontes das medidas:
  - fotos do caminhao no patio (frente reta, lateral, detalhes) -> face, grade, farois, espelhos
  - lateral de referencia com cota 4100 mm (eixo dianteiro -> ultimo eixo) -> entre-eixos, profundidade da cabine
CONFIRMAR o entre-eixos real com trena e ajustar D1/D2/FW_Y.

Uso: python blender/build_fh540.py [--render] [--views front,front34R,sideL,rear34]
"""
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import truckkit as tk  # noqa: E402
from truckkit import box, cyl, prism, region, boolean, trash, finish, patch, SIDES, KEEP, M  # noqa: E402

tk.reset()
tk.base_materials(paint="#35566a", face="#3a3d41")
tk.mat("gloss_black", tk.srgb("#0d0f11"), 0.0, 0.12, coat=0.8)

# ---------------------------------------------------------------- medidas principais
D1, D2 = 2.74, 4.10          # eixos trativos (y); dianteiro em y=0
FW_Y = 3.25                  # centro da quinta roda
FRAME_END = D2 + 0.90
CAB_BOTTOM = 1.15            # piso da cabine
ROOF = 3.70                  # teto Globetrotter
TR, TW = 0.52, 0.295         # pneu 295/80 R22.5


def rear(z):
    """y da traseira da cabine na altura z (a traseira inclina para tras embaixo)."""
    return 1.48 - 0.34 * (z - CAB_BOTTOM) / (3.60 - CAB_BOTTOM)


def rrect(x0, x1, z0, z1, r, n=4):
    """Retangulo de cantos arredondados (contorno 2D)."""
    pts = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


# ================================================================ CABINE: casco por 3 silhuetas
side = [(rear(CAB_BOTTOM), CAB_BOTTOM), (rear(3.60), 3.60), (1.05, 3.67), (0.75, ROOF), (0.0, ROOF), (-0.45, 3.66),
        (-0.80, 3.58), (-1.00, 3.50), (-1.08, 3.42), (-1.07, 3.14), (-1.04, 3.12), (-1.27, 2.30), (-1.32, 2.27),
        (-1.32, 1.75), (-0.57, 1.75), (-0.57, CAB_BOTTOM)]
frontsil = [(1.25, CAB_BOTTOM), (1.25, 2.95), (1.22, 3.20), (1.15, 3.42), (1.03, 3.57), (0.85, 3.65), (0.55, 3.69),
            (0.0, 3.71), (-0.55, 3.69), (-0.85, 3.65), (-1.03, 3.57), (-1.15, 3.42), (-1.22, 3.20), (-1.25, 2.95),
            (-1.25, CAB_BOTTOM)]
plan = tk.plan_round(1.25, -1.33, 1.50, rf=(0.24, 0.30), rr=(0.12, 0.12))
shell = tk.hull3("cab_shell", side, frontsil, plan)
tk.bevel(shell, 0.05, 4, 25)
sk_cab = tk.skin(shell, 0.008)

DOOR = [(0.04, CAB_BOTTOM - 0.1), (0.04, 3.13), (-0.92, 3.13), (-1.08, 2.40), (-1.12, 1.70), (-0.57, 1.70),
        (-0.57, CAB_BOTTOM - 0.1)]
APIL = [(-1.45, 2.31), (-1.45, 3.13), (-0.92, 3.13), (-1.08, 2.40), (-1.10, 2.31)]


def yz(outline, x0, x1):
    return prism("cut", outline, "x", x0, x1)


cuts = []
for s, sx in SIDES.items():
    xa, xb = (0.9, 1.5) if sx > 0 else (-1.5, -0.9)
    cuts += [(f"cab_door_{s}", lambda a=xa, b=xb: yz(DOOR, a, b), "paint", 0.012),
             (f"cab_a_pillar_{s}", lambda a=xa, b=xb: yz(APIL, a, b), "face", 0.010),
             (f"cab_side_panel_{s}", lambda a=xa, b=xb: region(a, b, 0.04, 0.92, CAB_BOTTOM - 0.1, 3.13), "paint", 0.012)]
cuts += [("cab_rear_panel", lambda: region(-1.5, 1.5, 0.92, 1.9, CAB_BOTTOM - 0.1, 4.0), "paint", 0.025),
         ("cab_roof", lambda: region(-1.5, 1.5, -0.80, 0.92, 3.13, 4.0), "paint", 0.035),
         ("cab_roof_front", lambda: region(-1.5, 1.5, -1.45, -0.80, 3.50, 4.0), "paint", 0.03),
         ("cab_visor", lambda: region(-1.5, 1.5, -1.45, -0.80, 3.13, 3.50), "gloss_black", 0.012),
         ("cab_face_upper", lambda: region(-1.5, 1.5, -1.45, -1.12, 1.70, 2.31), "face", 0.012)]

core = tk.copy(shell, "cab_structure")
P = {}
for name, mk, material, bev in cuts:
    reg = mk()
    p = tk.copy(shell, name)
    boolean(p, reg, "INTERSECT")
    boolean(core, reg, "DIFFERENCE")
    trash(reg)
    if name == "cab_rear_panel":  # nicho do pos-tratamento
        rec = region(-0.62, 0.62, 1.15, 2.0, 1.0, 2.05)
        boolean(p, rec)
        trash(rec)
    P[name] = finish(p, material, bev, 2)
trash(shell)
finish(core, "paint")

# ---- vidros (recortados da pelicula: seguem a curvatura dos cantos)
patch("windshield", sk_cab, rrect(-1.13, 1.13, 2.31, 3.12, 0.07), "y", -1.5, -0.85, "glass")
DW = [(-0.08, 2.40), (-0.08, 2.98), (-0.15, 3.05), (-0.88, 3.05), (-1.02, 2.50), (-1.04, 2.27)]
SW = [(0.12, 2.45), (0.12, 3.03), (0.17, 3.07), (0.60, 3.07), (0.68, 3.00), (0.80, 2.62), (0.76, 2.50), (0.70, 2.46)]
for s, sx in SIDES.items():
    xa, xb = (1.0, 1.5) if sx > 0 else (-1.5, -1.0)
    patch(f"cab_window_{s}", sk_cab, DW, "x", xa, xb, "glass")
    patch(f"cab_window_rear_{s}", sk_cab, SW, "x", xa, xb, "glass")
trash(sk_cab)

# ================================================================ FRENTE INFERIOR (para-lamas, grade, farois)
fside = [(-0.55, 0.40), (-0.55, 1.75), (-1.32, 1.75), (-1.34, 1.62), (-1.35, 1.45), (-1.35, 0.55), (-1.36, 0.40)]
ffront = [(-1.25, 0.40), (-1.25, 1.70), (-1.22, 1.75), (1.22, 1.75), (1.25, 1.70), (1.25, 0.40)]
fplan = tk.plan_round(1.25, -1.37, -0.40, rf=(0.28, 0.38), rr=(0.02, 0.02))
front = tk.hull3("cab_front_body", fside, ffront, fplan)
arch = cyl("arch_cut", 0.68, 3.4, (0, 0, TR), "x", keep=False)
boolean(front, arch)
trash(arch)
for sx in (1, -1):
    well = region(0.90 if sx > 0 else -1.4, 1.4 if sx > 0 else -0.90, -0.98, -0.55, 0.30, 0.72)
    boolean(front, well)
    trash(well)
tk.bevel(front, 0.04, 4, 30)
skf = [tk.skin(front, t) for t in (0.010, 0.020, 0.026)]
for s, sx in SIDES.items():
    reg = region(0.92 if sx > 0 else -1.4, 1.4 if sx > 0 else -0.92, -1.5, -0.5, 0.2, 1.8)
    fe = tk.copy(front, f"cab_fender_front_{s}")
    boolean(fe, reg, "INTERSECT")
    boolean(front, reg, "DIFFERENCE")
    trash(reg)
    P[fe.name] = finish(fe, "paint", 0.012, 2)
finish(front, "paint")
tk.rename(front, "cab_front_panel")

# farol em "L": carcaca cromada + lente + DRL, projetados no canto curvo
HL = [(1.245, 1.18), (1.15, 1.18), (0.97, 0.79), (0.89, 0.74), (0.88, 0.57), (0.93, 0.52), (1.21, 0.52), (1.245, 0.58)]
DRL = [(1.235, 1.165), (1.185, 1.165), (1.015, 0.80), (1.06, 0.80)]
for s, sx in SIDES.items():
    poly = [(sx * x, z) for x, z in HL]
    patch(f"headlight_{s}", skf[0], poly, "y", -1.5, -1.05, "chrome")
    patch(f"headlight_lens_{s}", skf[1], tk.scale_poly(poly, 0.90), "y", -1.5, -1.05, "light")
    patch(f"drl_{s}", skf[2], [(sx * x, z) for x, z in DRL], "y", -1.5, -1.05, "led")
    box(f"fog_light_{s}", (0.20, 0.04, 0.07), (sx * 1.04, -1.395, 0.455), "light", 0.012)
trash(*skf)

# vinco lateral (linha de estilo que sobe do farol ate o dormitorio)
for s, sx in SIDES.items():
    tk.groove([P[f"cab_fender_front_{s}"], P[f"cab_door_{s}"], P[f"cab_side_panel_{s}"]],
              (-1.25, 1.34), (0.92, 1.86), sx * 1.25)

# grade e para-choque
GY = -1.362
box("grille_backing", (1.90, 0.012, 1.12), (0, GY + 0.004, 0.99), "plastic", 0.01)
box("grille_housing", (1.95, 0.05, 0.14), (0, GY, 1.49), "plastic", 0.012)
for nm, w, h, z in (("grille_mesh_upper", 1.79, 0.27, 1.31), ("grille_mesh_mid", 1.75, 0.14, 1.09),
                    ("grille_mesh_lower", 1.60, 0.09, 0.705)):
    tk.mat(nm, (1, 1, 1), 0.5, 0.4, image=tk.hex_texture(nm, w, h))
    tk.front_uv(box(nm, (w, 0.022, h), (0, GY - 0.006, z), nm, 0.0))
box("grille_slats_upper", (1.55, 0.03, 0.30), (0, GY - 0.004, 0.875), "face", 0.01)
box("grille_slats_lower", (1.45, 0.03, 0.20), (0, GY - 0.004, 0.535), "face", 0.01)
for i, z in enumerate((0.965, 0.835, 0.60, 0.47)):
    box(f"grille_chrome_{i}", (1.5 if i < 2 else 1.4, 0.018, 0.022), (0, GY - 0.022, z), "chrome", 0.004)
box("grille_radar_plate", (0.30, 0.02, 0.12), (0, GY - 0.02, 0.56), "plastic", 0.01)
bump = tk.hull3("bumper_front", [(-0.75, 0.18), (-0.75, 0.42), (-1.38, 0.42), (-1.42, 0.32), (-1.40, 0.18)],
                [(-1.26, 0.18), (-1.26, 0.42), (1.26, 0.42), (1.26, 0.18)],
                tk.plan_round(1.26, -1.42, -0.70, rf=(0.30, 0.42), rr=(0.02, 0.02)))
tk.bevel(bump, 0.03, 3, 30)
finish(bump, "paint")
box("bumper_center_plate", (0.78, 0.02, 0.17), (0, -1.425, 0.30), "plastic", 0.01)

# ================================================================ DETALHES DA CABINE
cyl("cab_logo", 0.125, 0.02, (0, -1.335, 1.90), "y", "chrome", 48)
cyl("cab_logo_disc", 0.105, 0.025, (0, -1.338, 1.90), "y", "plastic", 48)
box("cab_logo_line", (0.95, 0.012, 0.014), (0.0, -1.328, 1.90), "chrome", 0.002, rot=(0, math.radians(-18), 0))
box("cab_cowl_strip", (2.10, 0.012, 0.018), (0, -1.33, 2.275), "chrome", 0.003)
for i, x in enumerate((-0.65, 0.42)):
    box(f"wiper_blade_{i}", (0.95, 0.02, 0.03), (x, -1.29, 2.36), "plastic", 0.005)
    box(f"wiper_mount_{i}", (0.28, 0.07, 0.07), (x - 0.18 if i == 0 else x + 0.18, -1.32, 2.29), "plastic", 0.015)
box("windshield_camera", (0.12, 0.05, 0.06), (0, -1.03, 3.02), "plastic", 0.01)
for i, x in enumerate((-0.33, 0.0, 0.33)):
    box(f"cab_roof_light_{i}", (0.10, 0.04, 0.04), (x, -1.00, 3.51), "led", 0.01)
box("cab_roof_hatch", (0.70, 0.90, 0.04), (0, -0.15, ROOF + 0.005), "alu", 0.02)
cyl("antenna", 0.007, 0.28, (-0.76, -0.55, 3.86), "z", "plastic", 8)
# espelho frontal (de aproximacao), canto superior direito do para-brisa
tk.tube("mirror_front_arm", [(-0.92, -1.06, 3.30), (-0.92, -1.18, 3.10), (-0.90, -1.22, 2.95)], 0.02)
box("mirror_front", (0.20, 0.07, 0.13), (-0.88, -1.24, 2.88), "plastic", 0.03, seg=3)

for s, sx in SIDES.items():
    box(f"cab_corner_light_{s}", (0.15, 0.04, 0.10), (sx * 0.90, -1.08, 3.30), "led", 0.01)
    box(f"cab_door_handle_{s}", (0.03, 0.28, 0.05), (sx * 1.262, -0.17, 1.80), "chrome", 0.012)
    box(f"cab_turn_signal_{s}", (0.012, 0.16, 0.05), (sx * 1.253, -0.75, 1.40), "amber", 0.006)
    # espelhos: carcaca arredondada, bracos curvos, grande-angular
    box(f"mirror_{s}", (0.17, 0.30, 0.82), (sx * 1.42, -0.98, 2.50), "paint", 0.06, seg=4)
    box(f"mirror_glass_{s}", (0.13, 0.012, 0.74), (sx * 1.42, -0.824, 2.50), "chrome", 0.004)
    box(f"mirror_wide_{s}", (0.14, 0.20, 0.26), (sx * 1.42, -1.00, 1.98), "paint", 0.04, seg=3)
    tk.tube(f"mirror_arm_up_{s}", [(sx * 1.13, -1.08, 2.95), (sx * 1.30, -1.12, 2.97), (sx * 1.41, -1.08, 2.92)], 0.022)
    tk.tube(f"mirror_arm_low_{s}", [(sx * 1.15, -1.22, 2.12), (sx * 1.32, -1.18, 2.08), (sx * 1.41, -1.08, 2.08)], 0.022)
    # defletores traseiros e colunas de entrada de ar (seguem a inclinacao da traseira)
    d = prism(f"cab_side_deflector_{s}", [(rear(1.30) - 0.05, 1.30), (rear(1.30) + 0.30, 1.30), (rear(3.55) + 0.30, 3.55),
                                          (rear(3.55) - 0.05, 3.55)], "x", sx * 1.195, sx * 1.255)
    finish(d, "paint", 0.015, 3)
    e = prism(f"cab_side_deflector_edge_{s}", [(rear(1.30) + 0.30, 1.30), (rear(1.30) + 0.35, 1.30), (rear(3.55) + 0.35, 3.55),
                                               (rear(3.55) + 0.30, 3.55)], "x", sx * 1.19, sx * 1.25)
    finish(e, "plastic", 0.01, 2)
    ang = math.atan(0.34 / (3.60 - CAB_BOTTOM))
    ribs = [box(f"rib{i}", (0.34, 0.30, 0.018), (sx * 0.98, rear(1.45 + i * 0.09) + 0.17, 1.45 + i * 0.09), "adblue",
                0.004, rot=(ang, 0, 0), keep=False) for i in range(20)]
    body = prism("intake", [(rear(1.35) + 0.02, 1.35), (rear(1.35) + 0.32, 1.35), (rear(3.25) + 0.32, 3.25),
                            (rear(3.25) + 0.02, 3.25)], "x", sx * 0.82, sx * 1.14)
    finish(body, "plastic", 0.02, 2, keep=False)
    tk.join(f"cab_air_intake_{s}", [body] + ribs, "plastic")
    # degraus, saia e moldura do para-lama dianteiro
    box(f"cab_step_lower_{s}", (0.34, 0.45, 0.05), (sx * 1.10, -0.78, 0.45), "steel", 0.01)
    box(f"cab_step_upper_{s}", (0.30, 0.40, 0.05), (sx * 1.10, -0.70, 0.84), "steel", 0.01)
    box(f"cab_skirt_{s}", (0.06, 2.40, 0.10), (sx * 1.225, 0.25, CAB_BOTTOM - 0.05), "plastic", 0.015)
    tk.fender(f"cab_arch_flare_{s}", sx * 1.19, 0.0, TR, w=0.12, r=0.705, cut=0.62, th=0.035)

# ================================================================ CHASSI
for s, sx in SIDES.items():
    box(f"chassis_rail_{s}", (0.10, FRAME_END + 0.55, 0.30), (sx * 0.43, (FRAME_END - 0.55) / 2, 0.85), "frame", 0.012)
for i, y in enumerate((0.6, 1.7, 2.6, 3.7, 4.6)):
    box(f"chassis_crossmember_{i}", (0.76, 0.09, 0.22), (0, y, 0.84), "frame", 0.01)
box("deck_plate", (1.0, 0.70, 0.04), (0, 2.00, 1.02), "chrome", 0.005)
cyl("driveshaft", 0.07, D1 - 0.2, (0, (D1 + 0.2) / 2 + 0.1, 0.62), "y", "steel", 20)
box("cab_rear_recess", (1.22, 0.04, 0.98), (0, 1.22, 1.52), "plastic", 0.01)
cyl("dpf_scr", 0.27, 0.76, (0.10, 1.42, 1.50), "x", "steel", 40, bev=0.02)
cyl("air_tank", 0.15, 0.95, (0, 2.20, 0.48), "x", "adblue", 24, bev=0.02)
cyl("air_dryer", 0.07, 0.22, (-0.2, 2.05, 0.80), "z", "chrome", 16)
box("ecu_chassis", (0.26, 0.32, 0.14), (0.15, 1.75, 0.70), "plastic", 0.015)
box("ebs_module", (0.18, 0.22, 0.12), (-0.18, 2.55, 0.62), "plastic", 0.012)


def tank(name, size, loc, material):
    t = box(name, size, loc, material, 0.07, seg=4, keep=False)
    straps = [box("strap", (size[0] + 0.02, 0.06, size[2] + 0.02), (loc[0], loc[1] + dy * size[1], loc[2]), "plastic",
                  0.03, seg=3, keep=False) for dy in (-0.28, 0.28)] if size[1] > 0.5 else []
    return tk.join(name, [t] + straps)


TANK_Y0, TANK_Y1 = 0.72, D1 - 0.69
xs = 0.86
tank("fuel_tank_L", (0.64, TANK_Y1 - TANK_Y0, 0.64), (xs, (TANK_Y0 + TANK_Y1) / 2, 0.78), "alu")
BAT_L, ADB_L = 0.55, 0.33
box("battery_box", (0.66, BAT_L, 0.64), (-0.90, TANK_Y0 + BAT_L / 2, 0.76), "battery", 0.03)
box("adblue_tank", (0.62, ADB_L, 0.55), (-xs, TANK_Y0 + BAT_L + ADB_L / 2, 0.775), "adblue", 0.05, seg=3)
cyl("adblue_cap", 0.05, 0.05, (-xs, TANK_Y0 + BAT_L + ADB_L / 2, 1.075), "z", "bluecap", 16)
fy0 = TANK_Y0 + BAT_L + ADB_L
tank("fuel_tank_R", (0.64, TANK_Y1 - fy0, 0.64), (-xs, (fy0 + TANK_Y1) / 2, 0.78), "alu")

# ================================================================ RODAS (pneu e roda torneados)
tire_t, rim_t = tk.wheel_templates(TR, TW)
for s, sx in SIDES.items():
    tk.place_wheel(f"F_{s}", sx * 1.02, 0.0, TR, sx, tire_t, rim_t)
    for tag, ay in (("D1", D1), ("D2", D2)):
        tk.place_wheel(f"{tag}_{s}_out", sx * 1.06, ay, TR, sx, tire_t, rim_t)
        tk.place_wheel(f"{tag}_{s}_in", sx * 0.68, ay, TR, -sx, tire_t, rim_t)
for n, y in (("front", 0.0), ("drive1", D1), ("drive2", D2)):
    cyl(f"axle_{n}", 0.075, 2.05, (0, y, TR), "x", "steel", 20)
    if n != "front":
        cyl(f"diff_{n}", 0.21, 0.5, (0, y, TR), "x", "steel", 32, bev=0.03)

for s, sx in SIDES.items():
    tk.fender(f"mudguard_rear_{s}_1", sx * 0.88, D1, TR)
    tk.fender(f"mudguard_rear_{s}_2", sx * 0.88, D2, TR)
    box(f"mudguard_rear_{s}_link", (0.95, 0.60, 0.07), (sx * 0.88, (D1 + D2) / 2, 1.17), "plastic", 0.02)
    box(f"mudflap_{s}", (0.90, 0.025, 0.42), (sx * 0.88, D2 + 0.72, 0.48), "rubber", 0.006)
    box(f"rear_light_{s}", (0.20, 0.05, 0.12), (sx * 0.95, FRAME_END + 0.02, 0.78), "red", 0.01)
    box(f"side_marker_{s}", (0.012, 0.12, 0.04), (sx * 1.34, D2 + 0.65, 0.95), "amber", 0.004)
box("rear_bumper_beam", (2.1, 0.12, 0.16), (0, FRAME_END + 0.05, 0.68), "steel", 0.015)

# quinta roda (JOST)
box("fifth_wheel_plate", (1.0, 1.0, 0.06), (0, FW_Y, 1.03), "frame", 0.012)
box("fifth_wheel_base", (0.72, 0.60, 0.18), (0, FW_Y, 1.15), "steel", 0.02)
cyl("fifth_wheel_top", 0.48, 0.08, (0, FW_Y, 1.27), "z", "steel", 48, bev=0.012)

# ================================================================ SAIDA
tk.export_glb(os.path.join(tk.ROOT, "models", "fh540.glb"), os.path.join(tk.TMP, "fh540_parts.txt"))
if "--render" in sys.argv:
    sel = sys.argv[sys.argv.index("--views") + 1].split(",") if "--views" in sys.argv else None
    tk.render("fh540", tk.STD_VIEWS, sel)
