export interface Atom {
  element: string;
  x: number;
  y: number;
  z: number;
}

export interface Bond {
  atom1: number;
  atom2: number;
  order: number;
}

export interface Molecule3D {
  selfies: string;
  smiles: string;
  atoms: Atom[];
  bonds: Bond[];
}

export interface MoleculeProperties {
  qed: number;
  sa_score: number;
  mw: number;
  logp: number;
  hbd: number;
  hba: number;
  tpsa: number;
  rotatable_bonds: number;
  num_rings: number;
  num_aromatic_rings: number;
  num_heavy_atoms: number;
  lipinski_violations: number;
}

export interface GenerationData {
  generation: number;
  best_fitness: number;
  avg_fitness: number;
  best_qed: number;
  best_sa: number;
  best_novelty: number;
  best_binding: number;
  population_diversity: number;
  best_molecule: Molecule3D;
  best_properties: MoleculeProperties;
  elapsed_sec: number;
}

export interface BestMolecule {
  molecule: Molecule3D;
  properties: MoleculeProperties;
  fitness: number;
  scores: {
    qed: number;
    sa: number;
    novelty: number;
    binding: number;
  };
  campaign?: string;
}

export interface CampaignConfig {
  target_pdb: string;
  target_name: string;
  population_size: number;
  num_generations: number;
  crossover_prob: number;
  mutation_rate: number;
  max_tokens: number;
  tournament_size: number;
  elite_count: number;
  random_immigrants: number;
  weight_binding: number;
  weight_qed: number;
  weight_sa: number;
  weight_novelty: number;
  run_name: string;
}

export interface Campaign {
  name: string;
  config: CampaignConfig;
  history: GenerationData[];
  best_molecule: BestMolecule | null;
}

export interface CampaignSummary {
  name: string;
  config?: CampaignConfig;
  generations?: number;
  best_fitness?: number;
  best_qed?: number;
}

export interface KnownDrug {
  smiles: string;
  name: string;
  target: string;
  indication: string;
  approval_year: number | null;
  mw: number;
  ic50_nM: number | null;
  structure?: Molecule3D;
}

export type TabId = 'dashboard' | 'evolution' | 'library' | 'compare' | 'guide';

// Element visualization constants
export const ELEMENT_COLORS: Record<string, string> = {
  C: '#909090',
  N: '#3050F8',
  O: '#FF0D0D',
  S: '#FFFF30',
  H: '#FFFFFF',
  F: '#90E050',
  Cl: '#1FF01F',
  Br: '#A62929',
  I: '#940094',
  P: '#FF8000',
  B: '#FFB5B5',
};

export const ELEMENT_RADII: Record<string, number> = {
  C: 0.35,
  N: 0.32,
  O: 0.30,
  S: 0.38,
  H: 0.25,
  F: 0.30,
  Cl: 0.36,
  Br: 0.38,
  I: 0.40,
  P: 0.38,
  B: 0.34,
};
