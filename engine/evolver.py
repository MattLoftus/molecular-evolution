"""
Genetic algorithm for molecular evolution.

Evolves populations of SELFIES molecules to maximize a multi-objective
fitness function: drug-likeness (QED), synthetic accessibility, novelty,
and optionally protein-ligand binding affinity (AutoDock Vina).
"""

import json
import random
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Callable

import numpy as np

from .molecule import (
    random_selfies, fragment_selfies, selfies_to_mol, selfies_to_3d,
    mutate_selfies, crossover_selfies, Molecule3D, is_organic,
)
from .properties import (
    compute_properties, sa_score_normalized,
    morgan_fingerprint, novelty_score, scaffold_novelty_score,
    MoleculeProperties, tanimoto_similarity,
)


@dataclass
class EvolutionConfig:
    """Configuration for a molecular evolution run."""
    target_pdb: str = ''
    target_name: str = 'none'

    # GA parameters
    population_size: int = 100
    num_generations: int = 200
    crossover_prob: float = 0.7
    mutation_rate: float = 0.3
    max_tokens: int = 30
    tournament_size: int = 3
    elite_count: int = 5
    random_immigrants: float = 0.10
    fragment_seed_ratio: float = 0.70

    # Docking
    dock_top_n: int = 0       # 0 = no docking; >0 = dock top N per generation
    dock_exhaustiveness: int = 8

    # Scaffold hopping
    scaffold_hop: bool = False  # if True, penalize similarity to known drugs for target

    # Fitness weights (should sum to ~1.0)
    weight_binding: float = 0.0
    weight_qed: float = 0.45
    weight_sa: float = 0.35
    weight_novelty: float = 0.20

    # Output
    output_dir: str = 'results'
    run_name: str = 'default'

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return EvolutionConfig(**{k: v for k, v in d.items()
                                   if k in EvolutionConfig.__dataclass_fields__})


@dataclass
class GenerationStats:
    generation: int
    best_fitness: float
    avg_fitness: float
    best_qed: float
    best_sa: float
    best_novelty: float
    best_binding: float
    population_diversity: float
    best_molecule: dict
    best_properties: dict
    elapsed_sec: float

    def to_dict(self):
        return asdict(self)


@dataclass
class Individual:
    selfies: str
    mol: object = None
    fitness: float = 0.0
    scores: dict = field(default_factory=dict)
    properties: Optional[MoleculeProperties] = None
    fingerprint: object = None


def _compute_fitness(scores: dict, config: EvolutionConfig,
                     mol=None, props: MoleculeProperties = None) -> float:
    """Compute full fitness including penalties."""
    base = (
        config.weight_qed * scores.get('qed', 0) +
        config.weight_sa * scores.get('sa', 0) +
        config.weight_novelty * scores.get('novelty', 0) +
        config.weight_binding * scores.get('binding', 0)
    )

    if mol is None or props is None:
        return round(base, 6)

    n_atoms = mol.GetNumHeavyAtoms()

    if n_atoms < 12:
        size_penalty = (n_atoms / 12.0) ** 2
    elif n_atoms < 18:
        size_penalty = 0.6 + 0.4 * (n_atoms - 12) / 6.0
    elif n_atoms <= 35:
        size_penalty = 1.0
    elif n_atoms > 45:
        size_penalty = max(0.3, 1.0 - (n_atoms - 45) / 25.0)
    else:
        size_penalty = 1.0 - (n_atoms - 35) * 0.02

    if not is_organic(mol):
        return round(base * 0.1, 6)

    carbon_count = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 6)
    carbon_fraction = carbon_count / max(1, n_atoms)
    if carbon_fraction < 0.3:
        organic_bonus = 0.4
    elif carbon_fraction < 0.5:
        organic_bonus = 0.4 + 0.6 * (carbon_fraction - 0.3) / 0.2
    else:
        organic_bonus = 1.0

    if props.num_rings == 0:
        ring_bonus = 0.4
    elif props.num_rings <= 4:
        ring_bonus = 1.0
    else:
        ring_bonus = max(0.5, 1.0 - (props.num_rings - 4) * 0.1)

    aromatic_bonus = 1.0 if props.num_aromatic_rings > 0 else 0.7

    # Formal charge penalty: real drugs are mostly neutral
    n_charged = sum(1 for a in mol.GetAtoms() if a.GetFormalCharge() != 0)
    if n_charged > 1:
        charge_penalty = max(0.3, 1.0 - n_charged * 0.25)
    elif n_charged == 1:
        charge_penalty = 0.85
    else:
        charge_penalty = 1.0

    # Scaffold hopping bonus: reward molecules UNLIKE known drugs
    scaffold_bonus = 1.0
    scaffold_nov = scores.get('scaffold_novelty', -1)
    if scaffold_nov >= 0:  # -1 means not computed
        # scaffold_novelty is 0-1 where 1 = completely different from known drugs
        # Molecules with Tanimoto > 0.5 to a known drug get penalized
        if scaffold_nov < 0.5:
            scaffold_bonus = 0.3 + 0.7 * (scaffold_nov / 0.5)
        else:
            scaffold_bonus = 1.0 + 0.3 * (scaffold_nov - 0.5) / 0.5  # up to 1.3x bonus

    return round(base * size_penalty * organic_bonus * ring_bonus * aromatic_bonus * charge_penalty * scaffold_bonus, 6)


def evaluate(individual: Individual, config: EvolutionConfig,
             population_fps: list) -> float:
    """Evaluate fitness on properties (fast). Docking is done separately."""
    mol = selfies_to_mol(individual.selfies)
    individual.mol = mol

    if mol is None or mol.GetNumHeavyAtoms() < 3:
        individual.fitness = 0.0
        individual.scores = {'qed': 0, 'sa': 0, 'novelty': 0, 'binding': 0}
        individual.properties = MoleculeProperties()
        return 0.0

    props = compute_properties(mol)
    individual.properties = props

    fp = morgan_fingerprint(mol)
    individual.fingerprint = fp

    scores = {
        'qed': round(props.qed, 4),
        'sa': round(sa_score_normalized(mol), 4),
        'novelty': round(novelty_score(mol, population_fps), 4),
        'binding': individual.scores.get('binding', 0),  # preserve from previous docking
    }

    # Scaffold hopping: compute distance from known inhibitors
    if config.scaffold_hop and config.target_name != 'none':
        from .references import get_reference_fps
        ref_fps = get_reference_fps(config.target_name)
        if ref_fps:
            scores['scaffold_novelty'] = round(scaffold_novelty_score(mol, ref_fps), 4)

    individual.scores = scores
    individual.fitness = _compute_fitness(individual.scores, config, mol, props)
    return individual.fitness


def _dock_top_n(population: list, config: EvolutionConfig, verbose: bool = False):
    """Dock the top N individuals by property fitness.

    Only docks individuals that haven't been docked yet (binding == 0).
    Updates their binding scores and recomputes fitness.
    """
    if config.dock_top_n <= 0 or config.target_name == 'none':
        return

    from .docking import dock, dock_multi, multi_target_score, TARGETS, TARGET_GROUPS

    # Determine if we're doing multi-target or single-target docking
    is_multi = config.target_name in TARGET_GROUPS and len(TARGET_GROUPS.get(config.target_name, [])) > 1
    if not is_multi and config.target_name not in TARGETS:
        return

    # Sort by current fitness, pick top N that need docking
    ranked = sorted(population, key=lambda ind: ind.fitness, reverse=True)
    to_dock = []
    for ind in ranked:
        if ind.mol is not None and ind.scores.get('binding', 0) == 0:
            to_dock.append(ind)
        if len(to_dock) >= config.dock_top_n:
            break

    for ind in to_dock:
        if is_multi:
            results = dock_multi(ind.mol, config.target_name,
                                 exhaustiveness=config.dock_exhaustiveness, timeout=30)
            binding_score = multi_target_score(results)
            # Store per-target affinities for analysis
            ind.scores['dock_details'] = {
                name: round(r.affinity_kcal, 2) if r.success else None
                for name, r in results.items()
            }
        else:
            result = dock(ind.mol, config.target_name,
                          exhaustiveness=config.dock_exhaustiveness, timeout=30)
            if result.success and result.affinity_kcal < 0:
                binding_score = min(1.0, -result.affinity_kcal / 10.0)
            else:
                binding_score = 0.0

        ind.scores['binding'] = round(binding_score, 4)
        ind.fitness = _compute_fitness(ind.scores, config, ind.mol, ind.properties)

        if verbose:
            smiles = ''
            try:
                from rdkit import Chem
                smiles = Chem.MolToSmiles(ind.mol)[:30]
            except Exception:
                pass
            if is_multi:
                details = ind.scores.get('dock_details', {})
                detail_str = ' | '.join(f'{k}={v}' for k, v in details.items() if v)
                status = f"score={binding_score:.3f} ({detail_str})"
            else:
                status = f"{result.affinity_kcal:.1f} kcal/mol" if result.success else f"FAIL: {result.error[:30]}"
            print(f"    Dock: {smiles:30s} → {status} (score={binding_score:.3f})")


def tournament_select(population: list, tournament_size: int) -> Individual:
    contestants = random.sample(population, min(tournament_size, len(population)))
    return max(contestants, key=lambda ind: ind.fitness)


def _evaluate_population(population: list, config: EvolutionConfig,
                         verbose_docking: bool = False):
    """Evaluate entire population: properties first, then dock top N."""
    # Phase 1: fast property evaluation
    fps = []
    for ind in population:
        evaluate(ind, config, fps)
        if ind.fingerprint is not None:
            fps.append(ind.fingerprint)

    # Re-evaluate novelty with full fingerprints
    for ind in population:
        if ind.mol is not None:
            ind.scores['novelty'] = round(novelty_score(ind.mol, fps), 4)
            ind.fitness = _compute_fitness(ind.scores, config, ind.mol, ind.properties)

    # Phase 2: dock top N (slow)
    _dock_top_n(population, config, verbose=verbose_docking)


def run_evolution(config: EvolutionConfig,
                  callback: Optional[Callable] = None) -> list:
    """Run the genetic algorithm."""
    start_time = time.time()
    history = []
    docking_enabled = config.dock_top_n > 0 and config.target_name != 'none'

    # Initialize population
    population = []
    n_fragment = int(config.population_size * config.fragment_seed_ratio)
    for _ in range(n_fragment):
        population.append(Individual(selfies=fragment_selfies()))
    for _ in range(config.population_size - n_fragment):
        population.append(Individual(selfies=random_selfies(config.max_tokens)))

    _evaluate_population(population, config, verbose_docking=docking_enabled)

    for gen in range(config.num_generations):
        population.sort(key=lambda ind: ind.fitness, reverse=True)

        best = population[0]
        avg_fitness = sum(ind.fitness for ind in population) / len(population)

        # Diversity
        valid_fps = [ind.fingerprint for ind in population if ind.fingerprint is not None]
        if len(valid_fps) > 1:
            sample_fps = random.sample(valid_fps, min(20, len(valid_fps)))
            dists = []
            for i in range(len(sample_fps)):
                for j in range(i + 1, len(sample_fps)):
                    dists.append(1.0 - tanimoto_similarity(sample_fps[i], sample_fps[j]))
            diversity = sum(dists) / len(dists) if dists else 0.0
        else:
            diversity = 0.0

        best_3d = selfies_to_3d(best.selfies)
        if best_3d is None:
            best_3d = Molecule3D(selfies=best.selfies, smiles='', atoms=[], bonds=[])

        stats = GenerationStats(
            generation=gen,
            best_fitness=best.fitness,
            avg_fitness=round(avg_fitness, 6),
            best_qed=best.scores.get('qed', 0),
            best_sa=best.scores.get('sa', 0),
            best_novelty=best.scores.get('novelty', 0),
            best_binding=best.scores.get('binding', 0),
            population_diversity=round(diversity, 4),
            best_molecule=best_3d.to_dict(),
            best_properties=best.properties.to_dict() if best.properties else {},
            elapsed_sec=round(time.time() - start_time, 2),
        )
        history.append(stats)

        if callback:
            callback(gen, stats.to_dict())

        # --- Next generation ---
        next_pop = []

        # Elitism: carry over top individuals WITH their docking scores
        for i in range(config.elite_count):
            elite = Individual(selfies=population[i].selfies)
            elite.scores = dict(population[i].scores)  # preserve binding score
            next_pop.append(elite)

        # Random immigrants
        n_immigrants = int(config.population_size * config.random_immigrants)
        for _ in range(n_immigrants):
            if random.random() < 0.5:
                next_pop.append(Individual(selfies=fragment_selfies()))
            else:
                next_pop.append(Individual(selfies=random_selfies(config.max_tokens)))

        # Offspring
        while len(next_pop) < config.population_size:
            parent1 = tournament_select(population, config.tournament_size)
            parent2 = tournament_select(population, config.tournament_size)

            if random.random() < config.crossover_prob:
                child1_sf, child2_sf = crossover_selfies(parent1.selfies, parent2.selfies)
            else:
                child1_sf, child2_sf = parent1.selfies, parent2.selfies

            child1_sf = mutate_selfies(child1_sf, config.mutation_rate)
            child2_sf = mutate_selfies(child2_sf, config.mutation_rate)

            next_pop.append(Individual(selfies=child1_sf))
            if len(next_pop) < config.population_size:
                next_pop.append(Individual(selfies=child2_sf))

        population = next_pop
        _evaluate_population(population, config, verbose_docking=False)

    population.sort(key=lambda ind: ind.fitness, reverse=True)
    return history


def save_results(config: EvolutionConfig, history: list):
    out_dir = Path(config.output_dir) / config.run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / 'config.json', 'w') as f:
        json.dump(config.to_dict(), f, indent=2)

    history_data = [s.to_dict() if isinstance(s, GenerationStats) else s
                    for s in history]
    with open(out_dir / 'history.json', 'w') as f:
        json.dump(history_data, f, indent=2)

    if history:
        last = history[-1]
        best = last.to_dict() if isinstance(last, GenerationStats) else last
        with open(out_dir / 'best_molecule.json', 'w') as f:
            json.dump({
                'molecule': best['best_molecule'],
                'properties': best['best_properties'],
                'fitness': best['best_fitness'],
                'scores': {
                    'qed': best['best_qed'],
                    'sa': best['best_sa'],
                    'novelty': best['best_novelty'],
                    'binding': best['best_binding'],
                },
            }, f, indent=2)

    print(f"Results saved to {out_dir}")


def run_campaign(config: EvolutionConfig, verbose: bool = True):
    def progress(gen, stats):
        if verbose and gen % 5 == 0:
            binding_str = f"  bind={stats['best_binding']:.3f}" if stats['best_binding'] > 0 else ""
            print(f"  Gen {gen:3d}: fitness={stats['best_fitness']:.4f}  "
                  f"QED={stats['best_qed']:.3f}  SA={stats['best_sa']:.3f}  "
                  f"novelty={stats['best_novelty']:.3f}{binding_str}  "
                  f"div={stats['population_diversity']:.3f}  "
                  f"SMILES={stats['best_molecule']['smiles'][:50]}")

    docking_str = f", Docking top-{config.dock_top_n} against {config.target_name}" if config.dock_top_n > 0 else ""
    print(f"Starting evolution: {config.run_name}")
    print(f"  Population: {config.population_size}, Generations: {config.num_generations}{docking_str}")
    print(f"  Weights: QED={config.weight_qed}, SA={config.weight_sa}, "
          f"Novelty={config.weight_novelty}, Binding={config.weight_binding}")

    history = run_evolution(config, callback=progress)

    if history:
        last = history[-1]
        print(f"\nBest molecule (gen {last.generation}):")
        print(f"  SMILES: {last.best_molecule['smiles']}")
        print(f"  Fitness: {last.best_fitness:.4f}")
        print(f"  QED: {last.best_qed:.3f}, SA: {last.best_sa:.3f}, Binding: {last.best_binding:.3f}")

    save_results(config, history)
    return history
