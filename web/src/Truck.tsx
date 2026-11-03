import { useEffect, useMemo } from 'react'
import { useGLTF } from '@react-three/drei'
import * as THREE from 'three'
import type { ThreeEvent } from '@react-three/fiber'
import { SEVERITY_COLOR, type Damage } from './damage'

interface Props {
  url: string
  damages: Record<string, Damage>
  selected: string | null
  hovered: string | null
  onSelect: (name: string | null) => void
  onHover: (name: string | null, point?: THREE.Vector3) => void
}

type Std = THREE.MeshStandardMaterial & { userData: { orig?: THREE.Color } }

export function Truck({ url, damages, selected, hovered, onSelect, onHover }: Props) {
  const { scene } = useGLTF(url)
  // clone para não compartilhar materiais entre instâncias
  const root = useMemo(() => {
    const c = scene.clone(true)
    c.traverse(o => {
      if ((o as THREE.Mesh).isMesh) {
        const m = o as THREE.Mesh
        m.material = (m.material as THREE.Material).clone()
        const mat = m.material as Std
        mat.userData.orig = mat.color.clone()
        m.castShadow = true
        m.receiveShadow = true
      }
    })
    return c
  }, [scene])

  useEffect(() => {
    root.traverse(o => {
      if (!(o as THREE.Mesh).isMesh) return
      const m = o as THREE.Mesh
      const mat = m.material as Std
      const orig = mat.userData.orig!
      const dmg = damages[m.name]
      mat.color.copy(orig)
      mat.emissive.set('#000000')
      mat.emissiveIntensity = 1
      if (dmg) {
        mat.color.lerp(new THREE.Color(SEVERITY_COLOR[dmg.severity]), 0.85)
        mat.emissive.set(SEVERITY_COLOR[dmg.severity]).multiplyScalar(0.25)
      }
      if (m.name === hovered) mat.emissive.set('#38bdf8').multiplyScalar(0.5)
      if (m.name === selected) {
        // seleção: realça sem apagar a cor da gravidade
        if (dmg) mat.emissive.set(SEVERITY_COLOR[dmg.severity]).multiplyScalar(0.6)
        else mat.emissive.set('#3b82f6').multiplyScalar(0.7)
      }
    })
  }, [root, damages, selected, hovered])

  const meshOf = (e: ThreeEvent<PointerEvent | MouseEvent>) => e.object as THREE.Mesh

  return (
    <primitive
      object={root}
      onPointerOver={(e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); onHover(meshOf(e).name, e.point) }}
      onPointerMove={(e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); onHover(meshOf(e).name, e.point) }}
      onPointerOut={() => onHover(null)}
      onClick={(e: ThreeEvent<MouseEvent>) => { e.stopPropagation(); onSelect(meshOf(e).name) }}
    />
  )
}
