"""DAF XF 530 6x4 (Space Cab, Euro 6) - modelo v0.1 a partir das fotos do patio.

Convencao de eixos: ver blender/truckkit.py (esquerda = +x, frente = -y, eixo dianteiro em y = 0).
Medidas (fotos IMG_6951 frente reta, IMG_6954 lateral direita, IMG_6960 lateral esquerda):
  escala pela largura da cabine (2,49 m) e pelo pneu 315/80 R22.5 (~1,07 m).
  Entre-eixos medido nas duas laterais (3,41 e 3,52 m) -> media; CONFIRMAR com trena.
Quando o CAD oficial (JT convertido) chegar, a cabine sera substituida pela malha real.

Uso: python blender/build_xf530.py [--render] [--views front,front34,sideL,sideR,rear34]
"""
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import truckkit as tk  # noqa: E402
from truckkit import box, cyl, prism, region, boolean, trash, finish, patch, SIDES  # noqa: E402

tk.reset()
tk.base_materials(paint="#e6e8e9", face="#1b1c1e")
tk.mat("gloss_black", tk.srgb("#0b0c0d"), 0.0, 0.12, coat=0.8)

D1, D2 = 3.50, 4.85          # eixos trativos (y)
FW_Y = 3.80                  # quinta roda
FRAME_END = D2 + 0.65
CB = 1.32                    # piso/soleira da cabine
ROOF = 3.58                  # teto Space Cab
TR, TW = 0.535, 0.315        # pneu 315/80 R22.5

# ================================================================ CABINE (3 silhuetas)
side = [(0.95, CB), (0.95, 3.46), (0.86, 3.56), (0.55, ROOF), (-0.85, ROOF), (-1.04, 3.53), (-1.13, 3.44),
        (-1.13, 3.21), (-1.25, 2.52), (-1.29, 2.30), (-1.30, 1.96), (-0.62, 1.96), (-0.62, CB)]
frontsil = [(1.245, CB), (1.245, 3.0), (1.23, 3.30), (1.17, 3.47), (1.04, 3.55), (0.80, ROOF), (-0.80, ROOF),
            (-1.04, 3.55), (-1.17, 3.47), (-1.23, 3.30), (-1.245, 3.0), (-1.245, CB)]
plan = tk.plan_round(1.245, -1.31, 0.96, rf=(0.17, 0.26), rr=(0.10, 0.10))
shell = tk.hull3("cab_shell", side, frontsil, plan)
tk.bevel(shell, 0.05, 4, 25)
sk_cab = tk.skin(shell, 0.008)

DOOR = [(-0.10, CB - 0.1), (-0.10, 3.18), (-1.04, 3.18), (-1.12, 2.55), (-1.14, 1.90), (-0.62, 1.90), (-0.62, CB - 0.1)]
APIL = [(-1.45, 2.30), (-1.45, 3.22), (-1.04, 3.18), (-1.12, 2.55), (-1.14, 2.30)]


def yz(outline, x0, x1):
    return prism("cut", outline, "x", x0, x1)


cuts = []
for s, sx in SIDES.items():
    xa, xb = (0.9, 1.5) if sx > 0 else (-1.5, -0.9)
    cuts += [(f"cab_door_{s}", lambda a=xa, b=xb: yz(DOOR, a, b), "paint", 0.012),
             (f"cab_a_pillar_{s}", lambda a=xa, b=xb: yz(APIL, a, b), "face", 0.010),
             (f"cab_side_panel_{s}", lambda a=xa, b=xb: region(a, b, -0.10, 0.80, 2.15, 3.18), "paint", 0.012),
             (f"cab_side_lower_{s}", lambda a=xa, b=xb: region(a, b, -0.10, 0.80, CB - 0.1, 2.15), "paint", 0.012)]
cuts += [("cab_rear_panel", lambda: region(-1.5, 1.5, 0.80, 1.2, CB - 0.1, 4.0), "paint", 0.025),
         ("cab_roof", lambda: region(-1.5, 1.5, -1.45, 0.80, 3.22, 4.0), "paint", 0.035),
         ("cab_cowl", lambda: region(-0.9, 0.9, -1.45, -1.16, 2.30, 2.52), "face", 0.010),
         ("cab_hood", lambda: region(-1.5, 1.5, -1.45, -1.16, 1.96, 2.30), "paint", 0.012)]
core = tk.copy(shell, "cab_structure")
P = {}
for name, mk, material, bev in cuts:
    reg = mk()
    p = tk.copy(shell, name)
    boolean(p, reg, "INTERSECT")
    boolean(core, reg, "DIFFERENCE")
    trash(reg)
    P[name] = finish(p, material, bev, 2)
trash(shell)
finish(core, "paint")

patch("windshield", sk_cab, tk.rrect(-1.15, 1.15, 2.52, 3.21, 0.06), "y", -1.5, -0.95, "glass")
DW = [(-0.15, 2.40), (-0.15, 3.10), (-0.95, 3.10), (-1.06, 2.62), (-1.07, 2.40)]
SW = tk.rrect(0.10, 0.55, 2.42, 3.06, 0.06)
for s, sx in SIDES.items():
    xa, xb = (1.0, 1.5) if sx > 0 else (-1.5, -1.0)
    patch(f"cab_window_{s}", sk_cab, DW, "x", xa, xb, "glass")
    patch(f"cab_window_rear_{s}", sk_cab, SW, "x", xa, xb, "glass")
trash(sk_cab)

# ================================================================ FRENTE INFERIOR (cantos, grade, farois)
fside = [(-0.60, 0.45), (-0.60, 1.96), (-1.30, 1.96), (-1.32, 1.85), (-1.32, 0.62), (-1.33, 0.45)]
ffront = [(-1.245, 0.45), (-1.245, 1.90), (-1.22, 1.96), (1.22, 1.96), (1.245, 1.90), (1.245, 0.45)]
fplan = tk.plan_round(1.245, -1.34, -0.40, rf=(0.20, 0.30), rr=(0.02, 0.02))
front = tk.hull3("cab_front_body", fside, ffront, fplan)
arch = cyl("arch_cut", 0.70, 3.4, (0, 0, TR), "x", keep=False)
boolean(front, arch)
trash(arch)
for sx in (1, -1):
    well = region(0.92 if sx > 0 else -1.4, 1.4 if sx > 0 else -0.92, -1.05, -0.58, 0.40, 0.92)
    boolean(front, well)
    trash(well)
tk.bevel(front, 0.04, 4, 30)
skf = [tk.skin(front, t) for t in (0.010, 0.020, 0.026)]
for s, sx in SIDES.items():
    reg = region(0.92 if sx > 0 else -1.4, 1.4 if sx > 0 else -0.92, -1.5, -0.5, 0.3, 2.0)
    fe = tk.copy(front, f"cab_corner_panel_{s}")
    boolean(fe, reg, "INTERSECT")
    boolean(front, reg, "DIFFERENCE")
    trash(reg)
    P[fe.name] = finish(fe, "paint", 0.012, 2)
finish(front, "paint")
tk.rename(front, "cab_front_panel")

HL = [(1.21, 1.14), (0.95, 1.12), (0.82, 0.90), (0.84, 0.74), (1.20, 0.74)]
DRL = [(1.20, 1.13), (0.96, 1.11), (0.935, 1.075), (1.20, 1.09)]
for s, sx in SIDES.items():
    poly = [(sx * x, z) for x, z in HL]
    patch(f"headlight_{s}", skf[0], poly, "y", -1.5, -1.05, "chrome")
    patch(f"headlight_lens_{s}", skf[1], tk.scale_poly(poly, 0.88), "y", -1.5, -1.05, "light")
    patch(f"drl_{s}", skf[2], [(sx * x, z) for x, z in DRL], "y", -1.5, -1.05, "led")
    box(f"cab_corner_vent_{s}", (0.05, 0.03, 0.42), (sx * 1.15, -1.318, 1.68), "plastic", 0.01)
    box(f"fog_light_{s}", (0.24, 0.04, 0.10), (sx * 1.00, -1.375, 0.60), "light", 0.015)
trash(*skf)

# grade: moldura preta trapezoidal, barra cromada superior, 5 frisos cromados com tela
GY = -1.335
fr = prism("grille_frame", [(-0.92, 1.96), (0.92, 1.96), (0.72, 0.63), (-0.72, 0.63)], "y", GY, GY + 0.04)
finish(fr, "plastic", 0.012, 2)
bar = prism("grille_bar_top", [(-0.83, 1.87), (0.83, 1.87), (0.80, 1.58), (-0.80, 1.58)], "y", GY - 0.035, GY + 0.005)
finish(bar, "chrome", 0.012, 3)
tk.mat("grille_mesh", (1, 1, 1), 0.6, 0.4,
       image=tk.hex_texture("daf_mesh", 1.2, 0.09, fg="#a7adb3", bg="#060606", cell=(26, 12), line=4))
for i, (z, hw) in enumerate([(1.39, 0.64), (1.23, 0.61), (1.06, 0.58), (0.89, 0.53), (0.72, 0.47)]):
    box(f"grille_slat_{i}", (2 * hw, 0.03, 0.03), (0, GY - 0.022, z), "chrome", 0.01)
    tk.front_uv(box(f"grille_mesh_{i}", (2 * hw * 0.96, 0.02, 0.09), (0, GY - 0.006, z - 0.065), "grille_mesh", 0.0))

bump = tk.hull3("bumper_front", [(-0.9, 0.40), (-0.9, 0.72), (-1.35, 0.72), (-1.38, 0.60), (-1.36, 0.40)],
                [(-1.25, 0.40), (-1.25, 0.72), (1.25, 0.72), (1.25, 0.40)],
                tk.plan_round(1.25, -1.38, -0.80, rf=(0.25, 0.35), rr=(0.02, 0.02)))
tk.bevel(bump, 0.03, 3, 30)
finish(bump, "paint")
box("bumper_chrome", (1.20, 0.02, 0.03), (0, -1.378, 0.45), "chrome", 0.008)

# ================================================================ DETALHES DA CABINE
vis = prism("cab_sun_visor", [(-1.12, 3.20), (-1.28, 3.22), (-1.34, 3.30), (-1.28, 3.47), (-1.08, 3.50)], "x", -1.15, 1.15)
finish(vis, "gloss_black", 0.02, 3)
for i, x in enumerate((-0.52, 0.42)):
    box(f"wiper_blade_{i}", (0.85, 0.02, 0.03), (x, -1.27, 2.58), "plastic", 0.005)
    box(f"wiper_mount_{i}", (0.24, 0.06, 0.06), (x - 0.15 if i == 0 else x + 0.15, -1.31, 2.40), "plastic", 0.012)
tk.tube("mirror_front_arm", [(-0.70, -1.14, 3.22), (-0.75, -1.24, 3.12), (-0.80, -1.26, 3.03)], 0.02)
box("mirror_front", (0.24, 0.08, 0.15), (-0.80, -1.28, 2.97), "plastic", 0.03, seg=3)
for s, sx in SIDES.items():
    box(f"cab_roof_light_{s}", (0.10, 0.04, 0.035), (sx * 0.83, -1.20, 3.51), "amber", 0.01)
    box(f"cab_door_handle_{s}", (0.03, 0.26, 0.05), (sx * 1.257, -0.26, 1.62), "plastic", 0.012)
    box(f"mirror_{s}", (0.18, 0.25, 0.40), (sx * 1.40, -0.98, 2.88), "paint", 0.06, seg=4)
    box(f"mirror_glass_{s}", (0.14, 0.012, 0.34), (sx * 1.40, -0.85, 2.88), "chrome", 0.004)
    box(f"mirror_wide_{s}", (0.17, 0.22, 0.24), (sx * 1.40, -0.98, 2.53), "paint", 0.05, seg=3)
    tk.tube(f"mirror_arm_up_{s}", [(sx * 1.12, -1.13, 3.15), (sx * 1.28, -1.10, 3.14), (sx * 1.38, -1.00, 3.08)], 0.022)
    tk.tube(f"mirror_arm_low_{s}", [(sx * 1.15, -1.20, 2.45), (sx * 1.28, -1.12, 2.42), (sx * 1.38, -1.00, 2.42)], 0.022)
    d = prism(f"cab_side_deflector_{s}", [(0.90, 1.40), (1.22, 1.40), (1.22, 3.30), (0.90, 3.30)], "x", sx * 1.19, sx * 1.25)
    finish(d, "plastic", 0.015, 2)
    box(f"cab_step_lower_{s}", (0.34, 0.40, 0.05), (sx * 1.08, -0.84, 0.48), "steel", 0.01)
    box(f"cab_step_upper_{s}", (0.30, 0.36, 0.05), (sx * 1.08, -0.80, 0.86), "steel", 0.01)
    box(f"cab_skirt_{s}", (0.06, 1.55, 0.10), (sx * 1.225, 0.17, CB - 0.05), "plastic", 0.015)
    tk.fender(f"cab_arch_flare_{s}", sx * 1.19, 0.0, TR, w=0.12, r=0.745, cut=0.62, th=0.04)

# ================================================================ CHASSI
for s, sx in SIDES.items():
    box(f"chassis_rail_{s}", (0.10, FRAME_END + 0.55, 0.30), (sx * 0.43, (FRAME_END - 0.55) / 2, 0.98), "frame", 0.012)
for i, y in enumerate((0.6, 1.7, 2.7, 3.9, 5.0)):
    box(f"chassis_crossmember_{i}", (0.76, 0.09, 0.22), (0, y, 0.97), "frame", 0.01)
box("deck_plate", (1.0, 0.60, 0.04), (0, 1.30, 1.15), "chrome", 0.005)
cyl("driveshaft", 0.07, D1 - 0.4, (0, (D1 + 0.4) / 2, 0.70), "y", "steel", 20)
box("dpf_scr", (0.66, 0.78, 0.66), (-0.90, 1.21, 0.75), "battery", 0.05, seg=3)
box("battery_box", (0.55, 0.38, 0.50), (0.85, 0.96, 0.80), "plastic", 0.03)
tk.ctank("fuel_tank_L", 0.88, 1.17, 2.77, 0.72, 0.33)
tk.ctank("fuel_tank_R", -0.88, 1.62, 2.48, 0.72, 0.33)
cyl("adblue_tank", 0.26, 0.30, (-0.88, 2.65, 0.70), "y", "adblue", 40, bev=0.03)
cyl("adblue_cap", 0.05, 0.05, (-0.88, 2.65, 0.98), "z", "bluecap", 16)
cyl("air_tank", 0.15, 0.80, (0, 2.95, 0.65), "x", "adblue", 24, bev=0.02)
cyl("air_dryer", 0.07, 0.22, (0.2, 2.10, 0.90), "z", "chrome", 16)
box("ecu_chassis", (0.26, 0.32, 0.14), (-0.15, 1.85, 0.85), "plastic", 0.015)
box("ebs_module", (0.18, 0.22, 0.12), (0.18, 3.30, 0.75), "plastic", 0.012)

# ================================================================ RODAS
tire_t, rim_t = tk.wheel_templates(TR, TW)
for s, sx in SIDES.items():
    tk.place_wheel(f"F_{s}", sx * 1.03, 0.0, TR, sx, tire_t, rim_t)
    for tag, ay in (("D1", D1), ("D2", D2)):
        tk.place_wheel(f"{tag}_{s}_out", sx * 1.07, ay, TR, sx, tire_t, rim_t)
        tk.place_wheel(f"{tag}_{s}_in", sx * 0.71, ay, TR, -sx, tire_t, rim_t)
for n, y in (("front", 0.0), ("drive1", D1), ("drive2", D2)):
    cyl(f"axle_{n}", 0.075, 2.05, (0, y, TR), "x", "steel", 20)
    if n != "front":
        cyl(f"diff_{n}", 0.21, 0.5, (0, y, TR), "x", "steel", 32, bev=0.03)
for s, sx in SIDES.items():
    tk.fender(f"mudguard_rear_{s}_1", sx * 0.89, D1, TR, r=0.68)
    tk.fender(f"mudguard_rear_{s}_2", sx * 0.89, D2, TR, r=0.68)
    box(f"mudguard_rear_{s}_link", (0.95, 0.55, 0.07), (sx * 0.89, (D1 + D2) / 2, 1.19), "plastic", 0.02)
    box(f"mudflap_{s}", (0.90, 0.025, 0.42), (sx * 0.89, D2 + 0.72, 0.48), "rubber", 0.006)
    box(f"rear_light_{s}", (0.30, 0.05, 0.14), (sx * 0.92, FRAME_END + 0.02, 0.80), "red", 0.01)
    box(f"side_marker_{s}", (0.012, 0.12, 0.04), (sx * 1.34, D2 + 0.65, 0.95), "amber", 0.004)
box("rear_bumper_beam", (2.1, 0.12, 0.16), (0, FRAME_END + 0.05, 0.70), "steel", 0.015)

box("fifth_wheel_plate", (1.0, 1.0, 0.06), (0, FW_Y, 1.16), "frame", 0.012)
box("fifth_wheel_base", (0.72, 0.60, 0.14), (0, FW_Y, 1.26), "steel", 0.02)
cyl("fifth_wheel_top", 0.48, 0.07, (0, FW_Y, 1.34), "z", "steel", 48, bev=0.012)

# ================================================================ SAIDA
tk.export_glb(os.path.join(tk.ROOT, "models", "xf530.glb"), os.path.join(tk.TMP, "xf530_parts.txt"))
if "--render" in sys.argv:
    sel = sys.argv[sys.argv.index("--views") + 1].split(",") if "--views" in sys.argv else None
    tk.render("xf530", tk.STD_VIEWS, sel)
