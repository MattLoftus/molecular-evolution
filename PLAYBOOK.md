# Molecular Evolution Engine — Playbook

## Quick Start

### Run an evolution campaign
```bash
cd ~/workspace/molecular-evolution
source venv/bin/activate
python -m engine evolve --name my_run --pop 100 --gens 200
```

### Start the web dashboard
```bash
# Terminal 1: API server (port 8790)
source venv/bin/activate && python -m engine serve

# Terminal 2: Web dev server
cd web && export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && nvm use 22 && npm run dev
```

### Live evolution (WebSocket streaming)
```bash
source venv/bin/activate && pip install websockets
python -m engine live
# Then open the web dashboard — it connects via WebSocket on port 8791
```

## Architecture

```
molecular-evolution/
├── engine/               # Python computational engine
│   ├── molecule.py       # SELFIES representation, GA operators
│   ├── properties.py     # RDKit drug property calculations
│   ├── evolver.py        # Genetic algorithm loop
│   ├── known_drugs.py    # Reference drug structures
│   ├── serve.py          # HTTP API server (port 8790)
│   ├── ws_server.py      # WebSocket server (port 8791)
│   └── __main__.py       # CLI entry point
├── web/                  # React + TypeScript web dashboard
│   └── src/
│       ├── App.tsx       # Main layout with 5 tabs
│       ├── store.ts      # Zustand state management
│       ├── api.ts        # API client
│       └── components/   # MoleculeViewer, FitnessCurves, etc.
├── results/              # Campaign outputs (JSON)
└── data/targets/         # PDB files for docking (Phase 2)
```

## CLI Commands

```bash
python -m engine evolve [options]   # Run evolution campaign
python -m engine serve              # Start HTTP API server
python -m engine live               # Start WS + HTTP for live evolution
```

### Evolve options
- `--name NAME` — Campaign name (default: "default")
- `--pop N` — Population size (default: 100)
- `--gens N` — Number of generations (default: 200)
- `--crossover F` — Crossover probability (default: 0.7)
- `--mutation F` — Mutation rate (default: 0.3)
- `--max-tokens N` — Max SELFIES tokens (default: 30)
- `--w-qed F` — QED weight (default: 0.45)
- `--w-sa F` — SA weight (default: 0.35)
- `--w-novelty F` — Novelty weight (default: 0.20)

## Ports
- 8790: HTTP API
- 8791: WebSocket (live evolution)
- 5173+: Vite dev server (auto-assigned)

## Dependencies

### Docking (standalone test)
```bash
source venv/bin/activate
python3 -c "from engine.docking import dock_smiles; r = dock_smiles('COc1ccc(C(=O)Nc2ccccc2)cc1', 'EGFR'); print(r)"
```

### Python
```bash
/usr/bin/python3 -m venv venv
source venv/bin/activate
pip install selfies rdkit-pypi "numpy<2" scipy pandas gemmi
pip install meeko==0.5.0 openbabel-wheel  # for docking ligand/receptor prep
pip install websockets  # for live mode
```

### Node
```bash
cd web
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && nvm use 22
npm install
```

## Fitness Function

Weighted sum of:
- **QED** (45%): RDKit's Quantitative Estimate of Drug-likeness (0-1)
- **SA** (35%): Synthetic Accessibility (inverted, 0-1 where 1 = easy)
- **Novelty** (20%): Tanimoto distance from population (Morgan FP)

Multiplied by penalties:
- **Size**: Penalizes molecules < 10 or > 40 heavy atoms
- **Organic**: Penalizes low carbon fraction (< 20%)
- **Ring**: Bonus for ring-containing molecules

## Docking

Vina 1.2.5 binary at `data/vina` (x86_64, runs via Rosetta on ARM Mac).
Receptor PDBQT at `data/targets/1M17_receptor.pdbqt`.
Docking module: `engine/docking.py`.

### Validated results (exhaustiveness=8)
- Erlotinib (known EGFR drug): -6.4 kcal/mol
- Best evolved molecule: -7.4 kcal/mol (acetylamino-naphthalene)
- Aspirin (negative control): -5.4 kcal/mol

## Roadmap

### Phase 2: Docking-guided evolution (DONE)
- Docking wired into GA fitness: top-N docked per generation, binding = 40% weight
- Charge penalty added to prevent charged-species exploitation
- Best result: pyrrole-picolinamide at -7.2 kcal/mol (neutral, QED 0.864)
- Run with: `python -m engine evolve --target EGFR --dock-top-n 10 --w-binding 0.40 --w-qed 0.25 --w-sa 0.20 --w-novelty 0.15`

### Phase 2b: Scaffold hopping (DONE)
- Scaffold novelty penalty penalizes Tanimoto similarity to known EGFR drugs
- Best result: cyclohexenone-pyrrolidine at -8.0 kcal/mol, Tanimoto 0.103 to known drugs
- Run with: `python -m engine evolve --target EGFR --dock-top-n 10 --scaffold-hop --w-binding 0.50 --w-qed 0.20 --w-sa 0.15 --w-novelty 0.15`

### Phase 3: Resistance-proof evolution (DONE)
- Multi-target docking: WT + T790M + C797S, worst-case binding as fitness
- Best result: terphenyl hydroxamic acid, worst-case -7.2 kcal/mol (beats erlotinib's best of -6.5)
- Run with: `python -m engine evolve --target EGFR_all --dock-top-n 8 --scaffold-hop --w-binding 0.60 --w-qed 0.15 --w-sa 0.15 --w-novelty 0.10 --gens 40`

### Phase 3b: Longer campaigns + validation (NEXT)
- Run 100+ gen scaffold hopping campaigns (binding still climbing at gen 30)
- Validate top molecules with exhaustiveness=32
- Add targets: COX-2 (1CX2), HIV protease (1HVR)

### Phase 3: Advanced GA
- Fragment-based initialization (start from drug fragments, not random)
- Adaptive mutation rate based on diversity
- Island model with migration

### Phase 4: Deployment
- Vercel deployment for web dashboard
- Nightly automated campaigns
- Larger population experiments (500+ pop, 1000+ gens)
