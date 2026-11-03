// Gera public/<modelo>.glb.txt (base64) para cada public/*.glb.
// O visualizador lê o texto e decodifica no navegador (hospedagens que não servem .glb).
import { readFileSync, writeFileSync, readdirSync } from 'node:fs'
const dir = new URL('../public/', import.meta.url)
for (const f of readdirSync(dir).filter(n => n.endsWith('.glb'))) {
  const buf = readFileSync(new URL(f, dir))
  writeFileSync(new URL(f + '.txt', dir), buf.toString('base64'))
  console.log(f + '.txt', buf.length, 'bytes')
}
