// Mapeia o nome do objeto no .glb (definido no Blender) para rótulo e grupo.
export type Group =
  | 'cabine' | 'vidros' | 'iluminacao' | 'retrovisores' | 'para-choque'
  | 'chassi' | 'rodas' | 'combustivel' | 'escape' | 'eletrica' | 'quinta-roda' | 'outros'

export interface PartInfo { label: string; group: Group }

const SIDE: Record<string, string> = { L: 'esquerdo', R: 'direito' }
const SIDE_F: Record<string, string> = { L: 'esquerda', R: 'direita' }

const AXLE: Record<string, string> = { F: 'Dianteiro', D1: '1º eixo trativo', D2: '2º eixo trativo' }

interface Rule { re: RegExp; group: Group; label: (m: RegExpMatchArray) => string }

const rules: Rule[] = [
  { re: /^cab_body_lower/, group: 'cabine', label: () => 'Cabine – parte inferior' },
  { re: /^cab_body_upper/, group: 'cabine', label: () => 'Cabine – parte superior' },
  { re: /^cab_roof_spoiler/, group: 'cabine', label: () => 'Defletor de teto' },
  { re: /^cab_roof_visor/, group: 'cabine', label: () => 'Quebra-sol' },
  { re: /^cab_rear_panel/, group: 'cabine', label: () => 'Painel traseiro da cabine' },
  { re: /^cab_door_([LR])/, group: 'cabine', label: m => `Porta ${SIDE_F[m[1]]}` },
  { re: /^cab_fender_front_([LR])/, group: 'cabine', label: m => `Para-lama dianteiro ${SIDE[m[1]]}` },
  { re: /^cab_step2_([LR])/, group: 'cabine', label: m => `Degrau superior ${SIDE[m[1]]}` },
  { re: /^cab_step_([LR])/, group: 'cabine', label: m => `Degrau inferior ${SIDE[m[1]]}` },
  { re: /^cab_side_skirt_([LR])/, group: 'cabine', label: m => `Saia lateral ${SIDE_F[m[1]]}` },
  { re: /^grille/, group: 'cabine', label: () => 'Grade frontal' },
  { re: /^windshield/, group: 'vidros', label: () => 'Para-brisa' },
  { re: /^cab_window_([LR])/, group: 'vidros', label: m => `Vidro da porta ${SIDE_F[m[1]]}` },
  { re: /^mirror_arm_([LR])/, group: 'retrovisores', label: m => `Braço do retrovisor ${SIDE[m[1]]}` },
  { re: /^mirror_([LR])/, group: 'retrovisores', label: m => `Retrovisor ${SIDE[m[1]]}` },
  { re: /^headlight_([LR])/, group: 'iluminacao', label: m => `Farol ${SIDE[m[1]]}` },
  { re: /^drl_([LR])/, group: 'iluminacao', label: m => `Luz diurna (DRL) ${SIDE_F[m[1]]}` },
  { re: /^fog_light_([LR])/, group: 'iluminacao', label: m => `Farol de neblina ${SIDE[m[1]]}` },
  { re: /^rear_light_([LR])/, group: 'iluminacao', label: m => `Lanterna traseira ${SIDE_F[m[1]]}` },
  { re: /^bumper_front/, group: 'para-choque', label: () => 'Para-choque dianteiro' },
  { re: /^license_plate_front/, group: 'para-choque', label: () => 'Placa dianteira' },
  { re: /^rear_bumper_beam/, group: 'para-choque', label: () => 'Travessa traseira' },
  { re: /^chassis_rail_([LR])/, group: 'chassi', label: m => `Longarina ${SIDE_F[m[1]]}` },
  { re: /^chassis_crossmember_(\d+)/, group: 'chassi', label: m => `Travessa do chassi ${Number(m[1]) + 1}` },
  { re: /^air_tank/, group: 'chassi', label: () => 'Reservatório de ar' },
  { re: /^mudguard_rear_([LR])/, group: 'chassi', label: m => `Para-lama traseiro ${SIDE[m[1]]}` },
  { re: /^tire_(F|D1|D2)_([LR])(?:_(out|in))?/, group: 'rodas',
    label: m => `Pneu ${AXLE[m[1]].toLowerCase()} ${SIDE[m[2]]}${m[3] ? (m[3] === 'out' ? ' (externo)' : ' (interno)') : ''}` },
  { re: /^rim_(F|D1|D2)_([LR])(?:_(out|in))?/, group: 'rodas',
    label: m => `Roda ${AXLE[m[1]].toLowerCase()} ${SIDE[m[2]]}${m[3] ? (m[3] === 'out' ? ' (externa)' : ' (interna)') : ''}` },
  { re: /^axle_front/, group: 'chassi', label: () => 'Eixo dianteiro' },
  { re: /^axle_drive(\d)/, group: 'chassi', label: m => `Eixo trativo ${m[1]}` },
  { re: /^fuel_tank_([LR])/, group: 'combustivel', label: m => `Tanque de combustível ${SIDE[m[1]]}` },
  { re: /^exhaust_pipe/, group: 'escape', label: () => 'Escapamento' },
  { re: /^battery_box/, group: 'eletrica', label: () => 'Caixa de baterias (24 V)' },
  { re: /^fifth_wheel_plate/, group: 'quinta-roda', label: () => 'Quinta roda – placa' },
  { re: /^fifth_wheel_base/, group: 'quinta-roda', label: () => 'Quinta roda – base' },
]

export function partInfo(name: string): PartInfo {
  // remove sufixos que o exportador pode acrescentar (".001", "_1")
  const clean = name.replace(/\.\d+$/, '')
  for (const r of rules) {
    const m = clean.match(r.re)
    if (m) return { label: r.label(m), group: r.group }
  }
  return { label: clean, group: 'outros' }
}
