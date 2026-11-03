import type { Group } from './parts'

export type Severity = 'leve' | 'moderada' | 'grave'
export const SEVERITIES: Severity[] = ['leve', 'moderada', 'grave']
export const SEVERITY_COLOR: Record<Severity, string> = {
  leve: '#facc15',
  moderada: '#fb923c',
  grave: '#ef4444',
}

export const DAMAGE_TYPES = ['Amassado', 'Risco / arranhão', 'Trinca', 'Quebrado', 'Pintura danificada', 'Desgaste', 'Falha elétrica'] as const
export type DamageType = (typeof DAMAGE_TYPES)[number]

export const SERVICES = ['Reparo de lataria', 'Pintura', 'Troca da peça', 'Polimento', 'Revisão elétrica'] as const
export type Service = (typeof SERVICES)[number]

export interface Damage {
  part: string       // nome do objeto no .glb
  type: DamageType
  severity: Severity
  service: Service
  parts: number      // R$ peças e insumos
  labor: number      // R$ mão de obra
  note: string
}

// Valores-base PLACEHOLDER (R$) por grupo e serviço. Trocar pela tabela real da oficina.
const BASE: Record<Group, Record<Service, number>> = {
  grade:          { 'Reparo de lataria': 500, 'Pintura': 600, 'Troca da peça': 2400, 'Polimento': 150, 'Revisão elétrica': 250 },
  mecanica:       { 'Reparo de lataria': 300, 'Pintura': 150, 'Troca da peça': 3500, 'Polimento': 0, 'Revisão elétrica': 400 },
  cabine:         { 'Reparo de lataria': 900, 'Pintura': 1200, 'Troca da peça': 4500, 'Polimento': 350, 'Revisão elétrica': 400 },
  vidros:         { 'Reparo de lataria': 0, 'Pintura': 0, 'Troca da peça': 2800, 'Polimento': 150, 'Revisão elétrica': 300 },
  iluminacao:     { 'Reparo de lataria': 0, 'Pintura': 0, 'Troca da peça': 1600, 'Polimento': 120, 'Revisão elétrica': 350 },
  retrovisores:   { 'Reparo de lataria': 200, 'Pintura': 250, 'Troca da peça': 900, 'Polimento': 80, 'Revisão elétrica': 300 },
  'para-choque':  { 'Reparo de lataria': 600, 'Pintura': 800, 'Troca da peça': 2200, 'Polimento': 250, 'Revisão elétrica': 250 },
  chassi:         { 'Reparo de lataria': 1500, 'Pintura': 600, 'Troca da peça': 6000, 'Polimento': 0, 'Revisão elétrica': 0 },
  rodas:          { 'Reparo de lataria': 300, 'Pintura': 300, 'Troca da peça': 2500, 'Polimento': 150, 'Revisão elétrica': 0 },
  combustivel:    { 'Reparo de lataria': 700, 'Pintura': 400, 'Troca da peça': 3800, 'Polimento': 200, 'Revisão elétrica': 250 },
  escape:         { 'Reparo de lataria': 400, 'Pintura': 300, 'Troca da peça': 2600, 'Polimento': 200, 'Revisão elétrica': 0 },
  eletrica:       { 'Reparo de lataria': 200, 'Pintura': 150, 'Troca da peça': 1800, 'Polimento': 0, 'Revisão elétrica': 500 },
  'quinta-roda':  { 'Reparo de lataria': 500, 'Pintura': 300, 'Troca da peça': 5200, 'Polimento': 0, 'Revisão elétrica': 0 },
  outros:         { 'Reparo de lataria': 500, 'Pintura': 500, 'Troca da peça': 2000, 'Polimento': 200, 'Revisão elétrica': 300 },
}
const SEV_FACTOR: Record<Severity, number> = { leve: 0.6, moderada: 1, grave: 1.7 }

/** Serviço mais comum por tipo de peça (vidro e farol normalmente são trocados, não reparados). */
export function defaultService(group: Group): Service {
  switch (group) {
    case 'vidros': case 'iluminacao': case 'rodas': case 'combustivel': case 'escape': case 'quinta-roda': case 'mecanica':
      return 'Troca da peça'
    case 'eletrica': return 'Revisão elétrica'
    default: return 'Reparo de lataria'
  }
}

/** Sugestão de valores; o usuário pode editar. Mão de obra = ~45% do total, peças = ~55%. */
export function suggest(group: Group, service: Service, severity: Severity) {
  const total = BASE[group][service] * SEV_FACTOR[severity]
  const parts = service === 'Troca da peça' ? total * 0.8 : total * 0.3
  return { parts: Math.round(parts), labor: Math.round(total - parts) }
}

export const brl = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
