# Visualizador 3D de avarias (Volvo FH 540, modelo de teste)

React + Vite + Three.js (React Three Fiber). Carrega `public/fh540.glb` (gerado por `blender/build_fh540.py`).

```bash
cd web
npm install
npm run dev      # http://localhost:5173
```

- Clique numa peça para registrar a avaria (tipo, gravidade, serviço, peças, mão de obra).
- A cor da peça segue a gravidade: amarelo (leve), laranja (moderada), vermelho (grave).
- Avarias ficam salvas no `localStorage` do navegador (Supabase entra numa fase seguinte).
- Os valores sugeridos em `src/damage.ts` são de exemplo; trocar pela tabela real da oficina.
- Nomes das peças em português: `src/parts.ts` (mapeia o nome do objeto no .glb).

Atualizar o modelo: rodar o script do Blender e copiar `models/fh540_blockout.glb` para `web/public/fh540.glb`.
