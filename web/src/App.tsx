import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { ContactShadows, Environment, Html, Lightformer, OrbitControls } from '@react-three/drei'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import * as THREE from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { Truck } from './Truck'
import { partInfo } from './parts'
import {
  DAMAGE_TYPES, SERVICES, SEVERITIES, SEVERITY_COLOR, brl, suggest,
  type Damage, type DamageType, type Service, type Severity,
} from './damage'

const MODEL = `${import.meta.env.BASE_URL}fh540.glb.txt`  // GLB em base64
const STORE = 'fh540-damages-v1'

const VIEWS: Record<string, { pos: [number, number, number]; target: [number, number, number] }> = {
  'Frente': { pos: [0, 2.4, -13], target: [0, 1.6, 2] },
  '3/4': { pos: [-9.5, 4.4, -10], target: [0, 1.4, 2.8] },
  'Lateral E': { pos: [-15, 2.4, 3], target: [0, 1.5, 3] },
  'Lateral D': { pos: [15, 2.4, 3], target: [0, 1.5, 3] },
  'Traseira': { pos: [0, 2.6, 15], target: [0, 1.5, 3] },
  'Topo': { pos: [0, 15, 3.5], target: [0, 0, 3.4] },
}

function CameraRig({ view, controls }: { view: string; controls: React.RefObject<OrbitControlsImpl | null> }) {
  const { camera } = useThree()
  const goal = useRef<{ pos: THREE.Vector3; target: THREE.Vector3 } | null>(null)
  useEffect(() => {
    const v = VIEWS[view]
    goal.current = { pos: new THREE.Vector3(...v.pos), target: new THREE.Vector3(...v.target) }
  }, [view])
  useFrame((_, dt) => {
    const g = goal.current, c = controls.current
    if (!g || !c) return
    const k = 1 - Math.exp(-6 * dt)
    camera.position.lerp(g.pos, k)
    c.target.lerp(g.target, k)
    c.update()
    if (camera.position.distanceTo(g.pos) < 0.02) goal.current = null
  })
  return null
}

/** Baixa o texto base64, decodifica para bytes e interpreta como GLB. */
function useModel(url: string) {
  const [scene, setScene] = useState<THREE.Object3D | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let alive = true
    fetch(url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.text() })
      .then(b64 => {
        const bin = atob(b64.trim())
        const bytes = new Uint8Array(bin.length)
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
        new GLTFLoader().parse(bytes.buffer, '', g => { if (alive) setScene(g.scene) },
          e => { if (alive) setError(String(e.message ?? e)) })
      })
      .catch(e => { if (alive) setError(String(e.message ?? e)) })
    return () => { alive = false }
  }, [url])
  return { scene, error }
}

function loadDamages(): Record<string, Damage> {
  try { return JSON.parse(localStorage.getItem(STORE) || '{}') } catch { return {} }
}

export default function App() {
  const [damages, setDamages] = useState<Record<string, Damage>>(loadDamages)
  const [selected, setSelected] = useState<string | null>(null)
  const [hover, setHover] = useState<{ name: string; point: THREE.Vector3 } | null>(null)
  const [view, setView] = useState('3/4')
  const controls = useRef<OrbitControlsImpl | null>(null)
  const { scene: model, error: modelError } = useModel(MODEL)

  useEffect(() => {
    try { localStorage.setItem(STORE, JSON.stringify(damages)) } catch { /* sem storage */ }
  }, [damages])

  const total = useMemo(
    () => Object.values(damages).reduce((s, d) => s + d.parts + d.labor, 0), [damages])

  return (
    <div className="app">
      <div className="stage">
        <div className="toolbar">
          {Object.keys(VIEWS).map(v => (
            <button key={v} className={v === view ? 'on' : ''} onClick={() => setView(v)}>{v}</button>
          ))}
        </div>
        <Canvas
          shadows
          camera={{ position: VIEWS['3/4'].pos, fov: 38, near: 0.1, far: 200 }}
          onPointerMissed={() => setSelected(null)}
        >
          <color attach="background" args={['#0b1220']} />
          <fog attach="fog" args={['#0b1220', 25, 60]} />
          <ambientLight intensity={0.35} />
          <directionalLight position={[6, 12, -6]} intensity={2.2} castShadow shadow-mapSize={[2048, 2048]}
            shadow-camera-left={-12} shadow-camera-right={12} shadow-camera-top={12} shadow-camera-bottom={-12} />
          <Environment resolution={256}>
            <Lightformer form="rect" intensity={3} position={[0, 6, 0]} scale={[14, 14, 1]} rotation-x={Math.PI / 2} />
            <Lightformer form="rect" intensity={2} position={[-8, 3, 0]} scale={[10, 4, 1]} rotation-y={Math.PI / 2} />
            <Lightformer form="rect" intensity={2} position={[8, 3, 0]} scale={[10, 4, 1]} rotation-y={-Math.PI / 2} />
          </Environment>
          {!model && (
            <Html center className="loading">{modelError ? `Erro ao carregar o modelo: ${modelError}` : 'Carregando modelo…'}</Html>
          )}
          {model && (
            // o glTF exporta o comprimento no eixo -z; giramos 180° para a frente apontar para -z da cena
            <group rotation-y={Math.PI}>
              <Truck
                scene={model}
                damages={damages}
                selected={selected}
                hovered={hover?.name ?? null}
                onSelect={setSelected}
                onHover={(name, point) => setHover(name && point ? { name, point: point.clone() } : null)}
              />
            </group>
          )}
          {/* plataforma */}
          <mesh rotation-x={-Math.PI / 2} position={[0, -0.01, 3.2]} receiveShadow>
            <circleGeometry args={[11, 96]} />
            <meshStandardMaterial color="#111a2e" metalness={0.4} roughness={0.55} />
          </mesh>
          <mesh rotation-x={-Math.PI / 2} position={[0, 0.002, 3.2]}>
            <ringGeometry args={[10.6, 10.8, 96]} />
            <meshBasicMaterial color="#3b82f6" />
          </mesh>
          <ContactShadows position={[0, 0.01, 3.2]} opacity={0.5} scale={30} blur={2.5} far={4} />
          {hover && (
            <Html position={hover.point} style={{ pointerEvents: 'none' }}>
              <div className="tip">{partInfo(hover.name).label}</div>
            </Html>
          )}
          <OrbitControls ref={controls} makeDefault enableDamping maxPolarAngle={Math.PI / 2 - 0.02}
            minDistance={3} maxDistance={30} target={VIEWS['3/4'].target} />
          <CameraRig view={view} controls={controls} />
        </Canvas>
        <div className="hint">Arraste para girar · role para aproximar · clique em uma peça</div>
        <div className="legend">
          {SEVERITIES.map(s => (
            <span key={s}><i style={{ background: SEVERITY_COLOR[s] }} />{s}</span>
          ))}
        </div>
      </div>

      <aside className="panel">
        <header>
          <h1>Volvo FH 540</h1>
          <p>Cavalo mecânico 6x4 · modelo de teste (blockout)</p>
        </header>

        {selected
          ? <DamageForm key={selected} name={selected} existing={damages[selected]}
              onSave={d => setDamages(p => ({ ...p, [selected]: d }))}
              onRemove={() => setDamages(p => { const n = { ...p }; delete n[selected]; return n })} />
          : <div className="empty">Clique em uma peça do caminhão para registrar uma avaria.</div>}

        <section className="list">
          <h2>Avarias registradas <span>{Object.keys(damages).length}</span></h2>
          {Object.keys(damages).length === 0 && <p className="muted">Nenhuma avaria ainda.</p>}
          {Object.entries(damages).map(([name, d]) => (
            <button key={name} className={'row' + (name === selected ? ' sel' : '')} onClick={() => setSelected(name)}>
              <i style={{ background: SEVERITY_COLOR[d.severity] }} />
              <span className="n">{partInfo(name).label}<small>{d.type} · {d.service}</small></span>
              <b>{brl(d.parts + d.labor)}</b>
            </button>
          ))}
          <div className="total"><span>Total do orçamento</span><b>{brl(total)}</b></div>
          {Object.keys(damages).length > 0 && (
            <button className="ghost" onClick={() => { if (confirm('Limpar todas as avarias?')) { setDamages({}); setSelected(null) } }}>
              Limpar tudo
            </button>
          )}
        </section>
      </aside>
    </div>
  )
}

function DamageForm({ name, existing, onSave, onRemove }: {
  name: string; existing?: Damage; onSave: (d: Damage) => void; onRemove: () => void
}) {
  const info = partInfo(name)
  const [type, setType] = useState<DamageType>(existing?.type ?? 'Amassado')
  const [severity, setSeverity] = useState<Severity>(existing?.severity ?? 'moderada')
  const [service, setService] = useState<Service>(existing?.service ?? 'Reparo de lataria')
  const [parts, setParts] = useState(existing?.parts ?? suggest(info.group, 'Reparo de lataria', 'moderada').parts)
  const [labor, setLabor] = useState(existing?.labor ?? suggest(info.group, 'Reparo de lataria', 'moderada').labor)
  const [note, setNote] = useState(existing?.note ?? '')

  const resuggest = (sv: Service, sev: Severity) => {
    const s = suggest(info.group, sv, sev)
    setParts(s.parts); setLabor(s.labor)
  }

  return (
    <section className="form">
      <div className="partname">
        <small>Peça selecionada</small>
        <h2>{info.label}</h2>
        <code>{name} · {info.group}</code>
      </div>

      <label>Tipo de dano
        <select value={type} onChange={e => setType(e.target.value as DamageType)}>
          {DAMAGE_TYPES.map(t => <option key={t}>{t}</option>)}
        </select>
      </label>

      <div className="lbl">Gravidade</div>
      <div className="seg">
        {SEVERITIES.map(s => (
          <button key={s} className={s === severity ? 'on' : ''}
            style={s === severity ? { background: SEVERITY_COLOR[s], color: '#111' } : undefined}
            onClick={() => { setSeverity(s); if (!existing) resuggest(service, s) }}>{s}</button>
        ))}
      </div>

      <label>Serviço
        <select value={service} onChange={e => { const v = e.target.value as Service; setService(v); resuggest(v, severity) }}>
          {SERVICES.map(t => <option key={t}>{t}</option>)}
        </select>
      </label>

      <div className="two">
        <label>Peças e insumos (R$)
          <input type="number" min={0} value={parts} onChange={e => setParts(Number(e.target.value))} />
        </label>
        <label>Mão de obra (R$)
          <input type="number" min={0} value={labor} onChange={e => setLabor(Number(e.target.value))} />
        </label>
      </div>
      <p className="muted">Valores sugeridos são provisórios (tabela de exemplo). Edite à vontade.</p>

      <label>Observação
        <textarea rows={2} value={note} onChange={e => setNote(e.target.value)} placeholder="Ex.: dano na lateral, sem trinca na pintura" />
      </label>

      <div className="sub"><span>Subtotal</span><b>{brl(parts + labor)}</b></div>
      <div className="actions">
        <button className="primary" onClick={() => onSave({ part: name, type, severity, service, parts, labor, note })}>
          {existing ? 'Atualizar avaria' : 'Registrar avaria'}
        </button>
        {existing && <button className="danger" onClick={onRemove}>Remover</button>}
      </div>
    </section>
  )
}

