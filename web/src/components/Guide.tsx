function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-6 mb-4">
      <h3 className="text-lg font-semibold text-[#e8edf5] mb-3">{title}</h3>
      <div className="text-sm text-gray-300 leading-relaxed space-y-3">{children}</div>
    </div>
  );
}

function Pill({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border border-[#1e2d3d]">
      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

export default function Guide() {
  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-[#e8edf5] mb-2">How It Works</h2>
        <p className="text-gray-400">
          Evolving drug-like molecules using genetic algorithms
        </p>
      </div>

      <Section title="Overview">
        <p>
          The Molecular Evolution Engine uses a <strong>genetic algorithm</strong> to design
          novel drug-like molecules from scratch. Instead of manually designing molecules,
          the system evolves populations of candidate molecules over many generations,
          selecting for drug-likeness, synthetic accessibility, and structural novelty.
        </p>
        <p>
          This mirrors how pharmaceutical companies explore chemical space — but automated,
          running thousands of evaluations per minute instead of months of manual design.
        </p>
      </Section>

      <Section title="SELFIES: Molecular Representation">
        <p>
          Molecules are encoded as <strong>SELFIES</strong> (Self-Referencing Embedded Strings),
          a string-based representation where <em>every possible string decodes to a valid molecule</em>.
          This is critical for genetic algorithms: unlike SMILES, random mutations and crossovers
          on SELFIES strings always produce valid chemistry.
        </p>
        <div className="bg-[#0f1923] rounded p-3 font-mono text-xs">
          <div className="text-gray-500 mb-1">Example SELFIES:</div>
          <div className="text-green-400">[C][=C][C][=C][C][=C][Ring1][=Branch1]</div>
          <div className="text-gray-500 mt-1">Decodes to: benzene (C6H6)</div>
        </div>
        <p>
          <strong>Mutation</strong> swaps, inserts, or deletes tokens.
          <strong> Crossover</strong> splices two parent SELFIES at random cut points.
          Both always produce valid molecules.
        </p>
      </Section>

      <Section title="Fitness Function">
        <p>Each molecule is scored on multiple objectives:</p>
        <div className="flex flex-wrap gap-2 my-3">
          <Pill color="#3b82f6" label="QED — Drug-likeness (45%)" />
          <Pill color="#f59e0b" label="SA — Synthesizability (35%)" />
          <Pill color="#8b5cf6" label="Novelty — Diversity (20%)" />
        </div>
        <p>
          <strong>QED</strong> (Quantitative Estimate of Drug-likeness) is a composite score
          from RDKit capturing molecular weight, lipophilicity, H-bond donors/acceptors,
          polar surface area, rotatable bonds, and aromatic rings. Scores range 0–1,
          with most approved drugs scoring 0.3–0.9.
        </p>
        <p>
          <strong>Synthetic Accessibility</strong> estimates how easy a molecule is to
          synthesize in a real lab. Molecules with common substructures and simple
          topologies score higher.
        </p>
        <p>
          <strong>Novelty</strong> measures Tanimoto distance from the rest of the population
          using Morgan fingerprints, rewarding structural diversity and preventing
          premature convergence.
        </p>
      </Section>

      <Section title="The Evolution Process">
        <div className="space-y-2">
          <div className="flex gap-3">
            <span className="text-[#10b981] font-bold w-6">1.</span>
            <div><strong>Initialize</strong> — Generate random SELFIES molecules (population of 100)</div>
          </div>
          <div className="flex gap-3">
            <span className="text-[#10b981] font-bold w-6">2.</span>
            <div><strong>Evaluate</strong> — Score each molecule on QED, SA, and novelty</div>
          </div>
          <div className="flex gap-3">
            <span className="text-[#10b981] font-bold w-6">3.</span>
            <div><strong>Select</strong> — Tournament selection picks parents (best of 3 random)</div>
          </div>
          <div className="flex gap-3">
            <span className="text-[#10b981] font-bold w-6">4.</span>
            <div><strong>Reproduce</strong> — Crossover (70%) + mutation (30%) create offspring</div>
          </div>
          <div className="flex gap-3">
            <span className="text-[#10b981] font-bold w-6">5.</span>
            <div><strong>Survive</strong> — Top 5 elites carry over + 10% random immigrants maintain diversity</div>
          </div>
          <div className="flex gap-3">
            <span className="text-[#10b981] font-bold w-6">6.</span>
            <div><strong>Repeat</strong> — 200 generations, converging toward optimal drug-like molecules</div>
          </div>
        </div>
      </Section>

      <Section title="Drug-Likeness: Lipinski's Rule of 5">
        <p>
          Most orally active drugs obey Lipinski's Rule of 5 — a set of simple
          property thresholds that predict oral bioavailability:
        </p>
        <div className="bg-[#0f1923] rounded p-3 text-xs space-y-1">
          <div>Molecular Weight <span className="text-blue-400">&lt; 500 Da</span></div>
          <div>LogP (lipophilicity) <span className="text-blue-400">&lt; 5</span></div>
          <div>H-bond donors <span className="text-blue-400">&le; 5</span></div>
          <div>H-bond acceptors <span className="text-blue-400">&le; 10</span></div>
        </div>
        <p>
          Molecules violating 2+ rules are unlikely to be orally active.
          The fitness function penalizes violations through the QED score.
        </p>
      </Section>

      <Section title="Protein-Ligand Docking">
        <p>
          <strong>AutoDock Vina</strong> predicts how strongly a molecule binds to a
          target protein's active site. Docking scores are reported in kcal/mol
          (more negative = stronger binding). Typical drug-like binding: -6 to -10 kcal/mol.
        </p>
        <div className="bg-[#0f1923] rounded p-3 text-xs space-y-1">
          <div className="text-gray-500 mb-1">EGFR kinase (PDB: 1M17) — evolved vs known drugs:</div>
          <div>Keto-benzanilide (evolved): <span className="text-green-400">-7.5 kcal/mol</span> | QED 0.910</div>
          <div>Pyrrole-picolinamide (evolved, docking-guided): <span className="text-green-400">-7.2 kcal/mol</span> | QED 0.864</div>
          <div>Gefitinib (known drug): <span className="text-blue-400">-7.3 kcal/mol</span> | QED 0.518</div>
          <div>Erlotinib (known drug): <span className="text-blue-400">-6.5 kcal/mol</span> | QED 0.418</div>
          <div>Aspirin (control): <span className="text-gray-400">-5.4 kcal/mol</span></div>
        </div>
        <p>
          Evolved molecules dock to EGFR at <strong>-7.0 to -7.5 kcal/mol</strong>,
          comparable to gefitinib and better than erlotinib, while maintaining
          dramatically higher drug-likeness scores (QED 0.86-0.91 vs 0.42-0.52).
          Docking-guided evolution uses binding affinity as 40% of the fitness function,
          producing molecules with heterocyclic diversity (pyrroles, pyrimidines) tuned
          for the EGFR binding pocket.
        </p>
      </Section>

      <Section title="Scaffold Hopping">
        <p>
          <strong>Scaffold hopping</strong> forces the GA to find structurally novel molecules
          by penalizing similarity to known drugs. Molecules that resemble existing EGFR
          inhibitors (erlotinib, gefitinib, osimertinib, etc.) receive a fitness penalty
          proportional to their Tanimoto similarity.
        </p>
        <div className="bg-[#0f1923] rounded p-3 text-xs space-y-1">
          <div className="text-gray-500 mb-1">Best scaffold hop result:</div>
          <div>Cyclohexenone-pyrrolidine: <span className="text-green-400">-8.0 kcal/mol</span> | QED 0.858</div>
          <div>Similarity to nearest known drug: <span className="text-purple-400">0.103</span> (essentially zero overlap)</div>
          <div className="text-gray-500 mt-1">For context: approved EGFR drugs share 0.4-0.5 similarity with each other</div>
        </div>
        <p>
          This is a completely novel scaffold — a cyclohexenone ring system with a
          pyrrolidine-bearing sidechain — that the GA discovered to fit the EGFR binding
          pocket better than erlotinib (-6.3) or gefitinib (-7.0), despite sharing almost
          no structural features with any known kinase inhibitor.
        </p>
      </Section>

      <Section title="Visualization">
        <p>
          Molecules are rendered in 3D using ball-and-stick representation:
        </p>
        <div className="flex flex-wrap gap-2 my-3">
          <Pill color="#909090" label="Carbon" />
          <Pill color="#3050F8" label="Nitrogen" />
          <Pill color="#FF0D0D" label="Oxygen" />
          <Pill color="#FFFF30" label="Sulfur" />
          <Pill color="#FF8000" label="Phosphorus" />
          <Pill color="#1FF01F" label="Chlorine" />
        </div>
        <p>
          3D coordinates are generated by RDKit's ETKDG algorithm with MMFF force field
          optimization. Bond order is shown by cylinder count (single, double, triple).
        </p>
      </Section>

      <Section title="Technology Stack">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div><strong>RDKit</strong> — Molecular manipulation & property calculation</div>
          <div><strong>SELFIES</strong> — Robust molecular string representation</div>
          <div><strong>Python GA</strong> — Tournament selection, crossover, mutation</div>
          <div><strong>React + Three.js</strong> — 3D molecule visualization</div>
          <div><strong>Plotly.js</strong> — Fitness curves & property plots</div>
          <div><strong>Zustand</strong> — Lightweight state management</div>
        </div>
      </Section>
    </div>
  );
}
