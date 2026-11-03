# Checklist: Volvo FH 540 (modelo 3D de teste)

Objetivo: gerar em Blender (por script Python) um cavalo mecânico Volvo FH 540 com peças separadas e nomeadas, exportar `.glb` e usar num visualizador 3D de avarias.

## Dados já levantados (não oficiais, a confirmar na ficha da Volvo Brasil)

**Mecânica**
- Motor D13K540: 13 L, 6 cilindros, turbo, common rail, 540 cv (397-405 kW), ~2.600 Nm, Euro 6, freio-motor VEB+
- Câmbio I-Shift 12 marchas (ex.: AT2612F); retarder hidráulico opcional
- Configurações 4x2, 6x2, 6x4, 8x4; eixo de tração simples ou com redução no cubo

**Dimensões (variam entre anúncios)**
- Largura 2.550 mm; entre-eixos 3.200-4.600 mm; altura ~3,86 m (um anúncio)
- Cabines Globetrotter e Globetrotter XL (sem medidas ainda)

**Elétrica**
- Rede CAN com unidades independentes (TEA2+), módulo central CCIOM
- Sistema 24 V, conversor DC/DC para 12 V (rádio, tomadas)
- Volvo proíbe ligar equipamento de terceiros nas redes internas

## 0. Dados necessários
- [ ] Ficha técnica Volvo Brasil do FH 540 (PDF com cotas)
- [ ] Fotos de referência: frente, traseira, laterais, três quartos
- [ ] Configuração-base (sugestão: cavalo mecânico 6x2 ou 6x4, Globetrotter)
- [ ] Definir se inclui carreta agora ou só o cavalo mecânico

## 1. Ambiente
- [x] Instalar `bpy` (Blender headless) e testar render simples (`pip install bpy==5.1.2` em venv)
- [x] Estrutura: `/blender`, `/models`, `/renders`, `/docs`

## 2. Documento técnico
- [ ] Dimensões reais (comprimento, largura, altura, entre-eixos, balanços, bitola, pneus)
- [ ] Componentes mecânicos: motor, câmbio, retarder, eixos, suspensão, freios, tanques, escapamento, quinta roda
- [ ] Componentes elétricos: baterias, alternador, CCIOM, chicotes, iluminação, sensores, painel
- [ ] Mapa componente -> avarias possíveis (alimenta o orçamento)

## 3. Modelagem 3D (Blender, por código)
- [ ] Cabine: teto, para-brisa, portas, laterais, traseira, defletor, spoiler, viseira
- [ ] Frente: grade, para-choque, faróis, LEDs, placa, estribos
- [ ] Vidros e retrovisores (principal e grande-angular)
- [ ] Chassi: longarinas, travessas, tanques, caixa de baterias, escapamento, para-lamas, defletores laterais
- [ ] Rodas e eixos: pneus, rodas, cubos, suspensão a ar
- [ ] Quinta roda e engates
- [ ] Nomes padronizados por peça (`cab_door_L`, `bumper_front`, `tank_L`...)
- [ ] Opcional: camada "raio-X" com componentes mecânicos e elétricos

## 4. Materiais
- [ ] Tinta metálica, vidro, borracha, cromado, plástico
- [ ] Logo: usar genérico ou sem logo, salvo confirmação de direito de uso da marca

## 5. Renders de conferência
- [ ] Frente, traseira, laterais, três quartos
- [ ] Render com cada peça colorida (checar nomes)
- [ ] Comparação com as fotos de referência e ajustes

## 6. Exportação
- [ ] `.glb` otimizado
- [ ] Validar no Three.js e clique por peça

## 7. Visualizador web (protótipo)
- [ ] React + React Three Fiber: girar, zoom, clicar na peça
- [ ] Destaque por peça e cor por gravidade (leve, moderada, grave)
- [ ] Painel lateral da avaria (tipo, gravidade, serviço, valor)

## 8. Depois do protótipo
- [ ] Supabase (clientes, veículos, avarias, orçamentos)
- [ ] Orçamento e PDF com imagens do 3D
- [ ] Dashboard e pátio

## Status
- **v0.2 (atual)**: `blender/build_fh540.py` gera `models/fh540.glb` com 141 peças nomeadas (cabine do FH novo/Globetrotter por silhueta lateral x frontal, face escura, grade hexagonal, faróis em L, espelhos, degraus, defletores, tanques, bateria, Arla, pós-tratamento, quinta roda, rodas de 10 parafusos, para-lamas). Proporções tiradas das fotos de referência (cabine 2,50 m e pneu 1,04 m como escala). Renders em `renders/`.
- Visualizador web em `web/` (ver `web/README.md`): girar, zoom, clicar na peça, avaria por gravidade, orçamento (localStorage). Todas as peças têm nome em português (`web/src/parts.ts`).
- **v0.3**: corrigido com a lateral de referência (cota 4100 mm): eixo dianteiro → 1º eixo trativo **2,74 m**, → último eixo **4,10 m**; traseira da cabine a **+1,48 m** (inclinada para trás embaixo); quinta roda em 3,25 m; teto Globetrotter 3,70 m. Tanques, bateria e Arla redimensionados para caber entre a cabine e o para-lama. **Confirmar o entre-eixos real do caminhão com trena** (varia por configuração) e ajustar `D1`, `D2` e `FW_Y` no topo de `blender/build_fh540.py`.
- Referências usadas só como consulta de proporção (fotos do cliente, imagem de lateral com cota, prévias de modelos 3D de terceiros); nada delas é copiado nem versionado.
- Fotos de referência ficam só localmente (`reference/fh540/`, não versionadas).

### Ainda falta no modelo
- Curvatura dos painéis laterais e do teto (hoje a cabine é um sólido de facetas suaves).
- Faróis mais fiéis (hoje: tira inclinada + unidade inferior), seta lateral, emblemas.
- Chassi: suspensão a ar, feixes, mangueiras, cardã com cruzetas, escapamento.
- Lateral pura E/D, topo e medidas com trena para calibrar.

Rodar: `python3 -m venv /tmp/venv-bpy && /tmp/venv-bpy/bin/pip install bpy==5.1.2 pillow && /tmp/venv-bpy/bin/python blender/build_fh540.py --render --views front,front34`
