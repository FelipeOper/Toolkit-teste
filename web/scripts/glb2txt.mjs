// Gera public/fh540.glb.txt (base64) a partir de public/fh540.glb.
// O visualizador lê o texto e decodifica no navegador (hospedagens que não servem .glb).
import { readFileSync, writeFileSync } from 'node:fs'
const buf = readFileSync(new URL('../public/fh540.glb', import.meta.url))
writeFileSync(new URL('../public/fh540.glb.txt', import.meta.url), buf.toString('base64'))
console.log('fh540.glb.txt', buf.length, 'bytes ->', Math.ceil(buf.length * 4 / 3))
