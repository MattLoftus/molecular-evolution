# Pharmaceutical Research Project Ideas

## 1. Molecular Evolution Engine — De Novo Drug Design via Genetic Algorithm (SELECTED)

**The core idea:** Evolve novel drug-like molecules from scratch to bind a specific protein target. Instead of evolving wire geometries to maximize gain (antenna-evolution), evolve molecular structures to maximize binding affinity while maintaining drug-likeness.

**Why this is compelling:**
- Direct evolutionary search parallel to antenna project
- Molecules are inherently 3D — ball-and-stick, surface, and binding pocket visualizations
- Multi-objective optimization (binding vs. drug-likeness vs. synthesizability) mirrors gain/VSWR/F:B tradeoffs
- Can benchmark against known drugs for well-studied targets
- Genuine discovery potential — novel scaffolds for validated targets are publishable

**Computational engine:**
- **Molecular representation:** SELFIES strings (robust self-referencing embedded strings — unlike SMILES, every SELFIES string is a valid molecule, so random mutations always produce valid chemistry)
- **Fitness function (multi-objective):**
  - **Binding affinity** (~40%): AutoDock Vina docking score against target protein (seconds per molecule)
  - **Drug-likeness** (~25%): Lipinski Rule of 5, Veber rules, QED (quantitative estimate of drug-likeness via RDKit)
  - **Synthetic accessibility** (~20%): SA Score (1-10, RDKit) — can this molecule actually be made?
  - **Novelty** (~15%): Tanimoto distance from known actives in ChEMBL — reward structural novelty
- **GA operators:** SELFIES crossover (swap molecular fragments at valid cut points), point mutation (swap SELFIES tokens), fragment insertion/deletion
- **Elitism + diversity:** Top-N elite preservation + fingerprint-based diversity filter (reject clones)

**Protein targets (starter set):**

| Target | Disease | PDB | Known drugs | Why interesting |
|--------|---------|-----|-------------|-----------------|
| EGFR kinase | Lung cancer | 1M17 | Erlotinib, Gefitinib | Deep binding pocket, rich SAR data |
| COX-2 | Inflammation | 1CX2 | Celecoxib, Rofecoxib | Classic selectivity problem |
| HIV protease | HIV/AIDS | 1HVR | Saquinavir, Ritonavir | Multiple resistance mutations |
| SARS-CoV-2 Mpro | COVID-19 | 7BQY | Nirmatrelvir (Paxlovid) | Timely, well-characterized |
| DPP-4 | Type 2 diabetes | 2ONC | Sitagliptin | Clean active site |

**3D visualization (react-three-fiber):**
- **Binding pocket view:** Protein surface mesh (computed from PDB coordinates) with evolved ligand docked inside. Hydrogen bonds as dashed cylinders, hydrophobic contacts as green surfaces.
- **Generation slider:** Scrub through evolution — watch the molecule morph from random fragment to optimized binder
- **Interaction diagram:** 2D Plotly schematic showing all protein-ligand contacts
- **Fitness landscape:** 3D scatter (binding affinity × drug-likeness × SA score) with Pareto front highlighted

**Web app tabs:**
- **Dashboard:** 3D binding pocket + best molecule + fitness curves over generations
- **Evolution:** Generation slider with molecular structure + docking pose at each step
- **Library:** All evolved molecules ranked by composite score, filterable by property
- **Compare:** Side-by-side evolved molecule vs. known drug for same target
- **Guide:** Drug discovery 101, SELFIES representation, docking mechanics, fitness function design

**Validation strategy:** Run the engine against EGFR, then check if evolved molecules share pharmacophoric features with known EGFR inhibitors (erlotinib scaffold). "Rediscovery rate" = fraction of runs that independently converge on known active chemotypes.

**Tech stack:**
- `rdkit` — molecular manipulation, fingerprints, property calculation, 2D/3D coordinate generation
- `autodock-vina` (Python bindings) — fast docking (~1-5s per molecule)
- `selfies` — robust molecular string representation
- `biopython` + `biotite` — PDB parsing, protein structure handling
- React 19 + react-three-fiber + Plotly.js + Zustand

**What makes this go beyond the antenna pattern:**
- Chemical validity constraints — discrete molecular graph space with valence rules
- Multi-scale visualization — atomic detail ↔ surface ↔ abstract property space
- Real-world database integration — PDB targets, ChEMBL actives, DrugBank

---

## 2. Pharmacokinetic Body Simulator — Drug Distribution Through a 3D Body Model

**The core idea:** Simulate how a drug moves through the human body over time — absorption from the gut, distribution through blood to organs, metabolism in the liver, excretion through kidneys. Optimize dosing regimens to maximize therapeutic effect while minimizing toxicity.

**Computational engine:**
- **PBPK model:** System of ODEs representing compartments (gut → portal vein → liver → systemic → organs)
- **Metabolism:** Michaelis-Menten kinetics (CYP450 enzymes in liver)
- **Optimization:** Evolutionary search over dosing regimen parameters

**3D visualization:**
- Translucent human body with organs glowing by drug concentration over time
- Time scrubber for 24-72 hour simulation
- Multi-drug interaction visualization

**Confidence: 78%** — visually spectacular but 3D body model adds complexity.

---

## 3. Antibiotic Resistance Evolution Simulator

**The core idea:** Simulate bacterial populations evolving resistance to antibiotics, optimize treatment protocols (cycling, combinations, adaptive dosing) to minimize resistance emergence.

**Computational engine:**
- Wright-Fisher population genetics model
- Hill equation pharmacodynamics
- GA optimization over treatment protocol parameters

**3D visualization:**
- Bacterial population "petri dish" with resistance genotype coloring
- Phylogenetic tree growing over time
- Fitness landscape sculpted by antibiotics

**Confidence: 85%** — scientifically important, most original, great 3D potential.

---

## 4. Protein Folding Landscape Explorer

**The core idea:** Map the energy landscape of protein conformations, transition pathways between metastable states, and how drug binding reshapes the landscape.

**Computational engine:**
- Coarse-grained MD (Gō model or elastic network model)
- Metadynamics for enhanced sampling
- Diffusion map dimensionality reduction

**3D visualization:**
- Energy landscape as 3D surface with conformational basins
- Protein ribbon diagrams morphing between states
- Drug-bound vs. apo landscape comparison

**Confidence: 65%** — highest scientific ceiling but highest technical risk. Phase 2 candidate.
