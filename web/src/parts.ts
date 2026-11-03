// Mapeia o nome do objeto no .glb (definido no Blender) para rótulo e grupo.
export type Group =
  | 'cabine' | 'grade' | 'vidros' | 'iluminacao' | 'retrovisores' | 'para-choque'
  | 'chassi' | 'mecanica' | 'rodas' | 'combustivel' | 'escape' | 'eletrica' | 'quinta-roda' | 'outros'

export interface PartInfo { label: string; group: Group }

const SIDE: Record<string, string> = { L: 'esquerdo', R: 'direito' }
const SIDE_F: Record<string, string> = { L: 'esquerda', R: 'direita' }
const AXLE: Record<string, string> = { F: 'dianteiro', D1: 'do 1º eixo trativo', D2: 'do 2º eixo trativo' }

interface Rule { re: RegExp; group: Group; label: (m: RegExpMatchArray) => string }
const fixed = (re: RegExp, group: Group, label: string): Rule => ({ re, group, label: () => label })
const sided = (re: RegExp, group: Group, label: string, fem = false): Rule => ({
  re, group, label: m => `${label} ${(fem ? SIDE_F : SIDE)[m[1]]}`,
})

const rules: Rule[] = [
  // ---- cabine (lataria)
  fixed(/^cab_structure/, 'cabine', 'Cabine – estrutura'),
  sided(/^cab_side_lower_([LR])/, 'cabine', 'Painel lateral inferior', false),
  fixed(/^cab_hood/, 'cabine', 'Painel frontal (capô)'),
  fixed(/^cab_cowl/, 'cabine', 'Grade de ventilação do para-brisa'),
  sided(/^cab_corner_panel_([LR])/, 'cabine', 'Painel de canto dianteiro', false),
  sided(/^cab_corner_vent_([LR])/, 'cabine', 'Entrada de ar do canto', true),
  fixed(/^cab_sun_visor/, 'cabine', 'Quebra-sol'),
  sided(/^cab_roof_light_([LR])/, 'iluminacao', 'Luz de teto', true),
  sided(/^cab_door_([LR])$/, 'cabine', 'Porta', true),
  sided(/^cab_door_handle_([LR])/, 'cabine', 'Maçaneta', true),
  sided(/^cab_side_panel_([LR])/, 'cabine', 'Painel lateral do dormitório', false),
  fixed(/^cab_rear_panel/, 'cabine', 'Painel traseiro da cabine'),
  fixed(/^cab_roof_front/, 'cabine', 'Teto – frente'),
  fixed(/^cab_roof$/, 'cabine', 'Teto'),
  fixed(/^cab_visor/, 'cabine', 'Faixa Globetrotter (viseira)'),
  fixed(/^cab_face_upper/, 'cabine', 'Face superior (rosto)'),
  fixed(/^cab_front_panel/, 'cabine', 'Frente inferior da cabine'),
  sided(/^cab_fender_front_([LR])/, 'cabine', 'Para-lama dianteiro', false),
  sided(/^cab_side_deflector_edge_([LR])/, 'cabine', 'Borda do defletor lateral', true),
  sided(/^cab_side_deflector_([LR])/, 'cabine', 'Defletor lateral traseiro', false),
  sided(/^cab_a_pillar_([LR])/, 'cabine', 'Coluna A', true),
  sided(/^cab_arch_flare_([LR])/, 'cabine', 'Moldura do para-lama dianteiro', true),
  fixed(/^cab_roof_hatch/, 'cabine', 'Escotilha do teto'),
  sided(/^cab_air_intake_([LR])/, 'cabine', 'Coluna de entrada de ar', true),
  sided(/^cab_step_lower_([LR])/, 'cabine', 'Degrau inferior', false),
  sided(/^cab_step_upper_([LR])/, 'cabine', 'Degrau superior', false),
  sided(/^cab_skirt_([LR])/, 'cabine', 'Saia lateral', true),
  sided(/^mudguard_front_([LR])/, 'cabine', 'Paralama (aro) dianteiro', false),
  fixed(/^cab_logo_line/, 'cabine', 'Friso cromado do emblema'),
  fixed(/^cab_logo/, 'cabine', 'Emblema (logo)'),
  fixed(/^cab_cowl_strip/, 'cabine', 'Friso cromado do capô'),
  fixed(/^cab_rear_recess/, 'cabine', 'Nicho traseiro do pós-tratamento'),
  fixed(/^antenna/, 'eletrica', 'Antena'),
  // ---- grade e frente
  fixed(/^grille_frame/, 'grade', 'Moldura da grade'),
  fixed(/^grille_bar_top/, 'grade', 'Barra cromada superior da grade'),
  { re: /^grille_slat_(\d)/, group: 'grade', label: m => `Friso cromado da grade ${Number(m[1]) + 1}` },
  { re: /^grille_mesh_(\d)/, group: 'grade', label: m => `Tela da grade ${Number(m[1]) + 1}` },
  fixed(/^grille_mesh_upper/, 'grade', 'Grade hexagonal superior'),
  fixed(/^grille_mesh_mid/, 'grade', 'Grade hexagonal intermediária'),
  fixed(/^grille_mesh_lower/, 'grade', 'Grade hexagonal inferior'),
  fixed(/^grille_slats_upper/, 'grade', 'Aletas da grade – superior'),
  fixed(/^grille_slats_lower/, 'grade', 'Aletas da grade – inferior'),
  fixed(/^grille_chrome_(\d)/, 'grade', 'Barra cromada da grade'),
  fixed(/^grille_(housing|backing)/, 'grade', 'Moldura da grade'),
  fixed(/^grille_radar_plate/, 'eletrica', 'Placa do radar / sensor frontal'),
  fixed(/^bumper_front/, 'para-choque', 'Para-choque dianteiro'),
  fixed(/^bumper_center_plate/, 'para-choque', 'Placa central do para-choque'),
  fixed(/^bumper_chrome/, 'para-choque', 'Friso cromado do para-choque'),
  fixed(/^rear_bumper_beam/, 'para-choque', 'Travessa traseira'),
  // ---- vidros e espelhos
  fixed(/^windshield_camera/, 'eletrica', 'Câmera do para-brisa'),
  fixed(/^windshield/, 'vidros', 'Para-brisa'),
  sided(/^cab_window_rear_([LR])/, 'vidros', 'Vidro do dormitório', false),
  sided(/^cab_window_([LR])/, 'vidros', 'Vidro da porta', false),
  { re: /^wiper_blade_(\d)/, group: 'cabine', label: m => `Palheta do limpador ${m[1] === '0' ? 'direito' : 'esquerdo'}` },
  { re: /^wiper_mount_(\d)/, group: 'cabine', label: m => `Base do limpador ${m[1] === '0' ? 'direito' : 'esquerdo'}` },
  sided(/^mirror_wide_([LR])/, 'retrovisores', 'Espelho grande-angular', false),
  sided(/^mirror_glass_([LR])/, 'retrovisores', 'Vidro do retrovisor', false),
  { re: /^mirror_arm_(up|low)_([LR])/, group: 'retrovisores', label: m => `Braço ${m[1] === 'up' ? 'superior' : 'inferior'} do retrovisor ${SIDE[m[2]]}` },
  sided(/^mirror_conn_([LR])/, 'retrovisores', 'Fixação do retrovisor', true),
  sided(/^mirror_([LR])$/, 'retrovisores', 'Retrovisor', false),
  fixed(/^mirror_front_arm/, 'retrovisores', 'Braço do espelho frontal'),
  fixed(/^mirror_front$/, 'retrovisores', 'Espelho frontal (de aproximação)'),
  // ---- iluminação
  sided(/^headlight_lens_([LR])/, 'iluminacao', 'Lente do farol', true),
  sided(/^headlight_([LR])/, 'iluminacao', 'Farol (carcaça)', false),
  sided(/^drl_([LR])/, 'iluminacao', 'Luz diurna (DRL)', true),
  sided(/^fog_light_([LR])/, 'iluminacao', 'Farol de neblina', false),
  sided(/^cab_turn_signal_([LR])/, 'iluminacao', 'Seta lateral', true),
  sided(/^cab_corner_light_([LR])/, 'iluminacao', 'Luz de canto do teto', true),
  { re: /^cab_roof_light_(\d)/, group: 'iluminacao', label: m => `Luz de teto ${['direita', 'central', 'esquerda'][Number(m[1])]}` },
  sided(/^rear_light_([LR])/, 'iluminacao', 'Lanterna traseira', true),
  sided(/^side_marker_([LR])/, 'iluminacao', 'Luz de posição lateral', true),
  // ---- chassi, mecânica, elétrica
  sided(/^chassis_rail_([LR])/, 'chassi', 'Longarina', true),
  { re: /^chassis_crossmember_(\d+)/, group: 'chassi', label: m => `Travessa do chassi ${Number(m[1]) + 1}` },
  fixed(/^deck_plate/, 'chassi', 'Plataforma atrás da cabine'),
  fixed(/^driveshaft/, 'mecanica', 'Cardã'),
  fixed(/^axle_front/, 'mecanica', 'Eixo dianteiro'),
  { re: /^axle_drive(\d)/, group: 'mecanica', label: m => `Eixo trativo ${m[1]}` },
  { re: /^diff_drive(\d)/, group: 'mecanica', label: m => `Diferencial do eixo ${m[1]}` },
  fixed(/^air_tank/, 'mecanica', 'Reservatório de ar'),
  fixed(/^air_dryer/, 'mecanica', 'Filtro secador de ar'),
  fixed(/^ebs_module/, 'eletrica', 'Módulo de freio EBS'),
  fixed(/^ecu_chassis/, 'eletrica', 'Módulo eletrônico do chassi (ECU)'),
  fixed(/^battery_box/, 'eletrica', 'Caixa de baterias (24 V)'),
  fixed(/^dpf_scr/, 'escape', 'Pós-tratamento (DPF/SCR)'),
  fixed(/^adblue_tank/, 'combustivel', 'Tanque de Arla 32'),
  fixed(/^adblue_cap/, 'combustivel', 'Tampa do Arla 32'),
  sided(/^fuel_tank_([LR])/, 'combustivel', 'Tanque de combustível', false),
  // ---- rodas e para-lamas traseiros
  { re: /^tire_(F|D1|D2)_([LR])(?:_(out|in))?/, group: 'rodas',
    label: m => `Pneu ${AXLE[m[1]]} ${SIDE[m[2]]}${m[3] ? (m[3] === 'out' ? ' (externo)' : ' (interno)') : ''}` },
  { re: /^rim_(F|D1|D2)_([LR])(?:_(out|in))?/, group: 'rodas',
    label: m => `Roda ${AXLE[m[1]]} ${SIDE_F[m[2]]}${m[3] ? (m[3] === 'out' ? ' (externa)' : ' (interna)') : ''}` },
  { re: /^mudguard_rear_([LR])_(1|2|link)/, group: 'chassi',
    label: m => `Paralama traseiro ${SIDE[m[1]]} ${m[2] === 'link' ? '(união)' : `(eixo ${m[2]})`}` },
  sided(/^mudflap_([LR])/, 'chassi', 'Barreiro', false),
  // ---- quinta roda
  fixed(/^fifth_wheel_plate/, 'quinta-roda', 'Quinta roda – placa de montagem'),
  fixed(/^fifth_wheel_base/, 'quinta-roda', 'Quinta roda – base'),
  fixed(/^fifth_wheel_top/, 'quinta-roda', 'Quinta roda – mesa'),
]

export function partInfo(name: string): PartInfo {
  // remove sufixos que o exportador pode acrescentar (".001")
  const clean = name.replace(/\.\d+$/, '')
  for (const r of rules) {
    const m = clean.match(r.re)
    if (m) return { label: r.label(m), group: r.group }
  }
  return { label: clean, group: 'outros' }
}
