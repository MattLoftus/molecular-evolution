"""
Drug property calculations using RDKit.

Computes QED, synthetic accessibility, Lipinski violations,
and other drug-relevant molecular descriptors.
"""

import math
import os
import sys
from dataclasses import dataclass, asdict

from rdkit import Chem
from rdkit.Chem import Descriptors, QED, RDConfig
from rdkit.Chem import DataStructs
from rdkit.Chem import AllChem

# Import the real Ertl SA scorer from RDKit Contrib
_sa_contrib_path = os.path.join(RDConfig.RDContribDir, 'SA_Score')
if os.path.exists(_sa_contrib_path):
    sys.path.insert(0, _sa_contrib_path)
    import sascorer as _ertl_sascorer
    HAS_ERTL_SA = True
else:
    HAS_ERTL_SA = False


@dataclass
class MoleculeProperties:
    """All computed drug-relevant properties."""
    qed: float = 0.0               # Quantitative Estimate of Drug-likeness (0-1)
    sa_score: float = 5.0           # Synthetic Accessibility (1=easy, 10=hard)
    mw: float = 0.0                 # Molecular weight
    logp: float = 0.0               # Lipophilicity (Wildman-Crippen)
    hbd: int = 0                    # H-bond donors
    hba: int = 0                    # H-bond acceptors
    tpsa: float = 0.0              # Topological polar surface area
    rotatable_bonds: int = 0
    num_rings: int = 0
    num_aromatic_rings: int = 0
    num_heavy_atoms: int = 0
    lipinski_violations: int = 0

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return MoleculeProperties(**{k: v for k, v in d.items()
                                      if k in MoleculeProperties.__dataclass_fields__})


# --- Synthetic Accessibility Score ---
# Simplified SA Score based on fragment contributions
# Full Ertl SA score requires a pre-computed fragment database;
# this approximation uses structural complexity heuristics.

def _sa_score_approx(mol) -> float:
    """Approximate synthetic accessibility score (1-10).

    Uses structural complexity heuristics:
    - Ring complexity (spiro, bridged, fused)
    - Stereocenters
    - Macrocycles
    - Fragment novelty (approximated by heavy atom count and ring info)
    """
    ri = mol.GetRingInfo()
    num_rings = ri.NumRings()
    num_atoms = mol.GetNumHeavyAtoms()

    if num_atoms == 0:
        return 10.0

    # Base score from molecular complexity
    score = 1.0

    # Penalize very large molecules
    if num_atoms > 35:
        score += (num_atoms - 35) * 0.1

    # Penalize many rings
    if num_rings > 4:
        score += (num_rings - 4) * 0.5

    # Penalize stereocenters
    chiral = Chem.FindMolChiralCenters(mol, includeUnassigned=True)
    score += len(chiral) * 0.3

    # Penalize macrocycles (ring size > 8)
    for ring in ri.AtomRings():
        if len(ring) > 8:
            score += 1.0

    # Penalize bridged/spiro systems
    if num_rings >= 2:
        ring_atoms = set()
        for ring in ri.AtomRings():
            shared = ring_atoms.intersection(set(ring))
            if len(shared) > 1:
                score += 0.5  # fused
            elif len(shared) == 1:
                score += 0.8  # spiro
            ring_atoms.update(ring)

    # Reward common fragments (aromatic rings, simple chains)
    num_aromatic = Descriptors.NumAromaticRings(mol)
    score -= num_aromatic * 0.2  # aromatic rings are easy

    return max(1.0, min(10.0, score))


def compute_properties(mol) -> MoleculeProperties:
    """Compute all drug-relevant properties for a molecule."""
    if mol is None:
        return MoleculeProperties()

    try:
        props = MoleculeProperties()

        # QED (0-1, higher is more drug-like)
        try:
            props.qed = QED.qed(mol)
        except Exception:
            props.qed = 0.0

        # Synthetic accessibility (Ertl score if available, else approximation)
        if HAS_ERTL_SA:
            try:
                props.sa_score = _ertl_sascorer.calculateScore(mol)
            except Exception:
                props.sa_score = _sa_score_approx(mol)
        else:
            props.sa_score = _sa_score_approx(mol)

        # Basic descriptors
        props.mw = Descriptors.MolWt(mol)
        props.logp = Descriptors.MolLogP(mol)
        props.hbd = Descriptors.NumHDonors(mol)
        props.hba = Descriptors.NumHAcceptors(mol)
        props.tpsa = Descriptors.TPSA(mol)
        props.rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        props.num_rings = Descriptors.RingCount(mol)
        props.num_aromatic_rings = Descriptors.NumAromaticRings(mol)
        props.num_heavy_atoms = mol.GetNumHeavyAtoms()

        # Lipinski Rule of 5
        violations = 0
        if props.mw > 500: violations += 1
        if props.logp > 5: violations += 1
        if props.hbd > 5: violations += 1
        if props.hba > 10: violations += 1
        props.lipinski_violations = violations

        return props
    except Exception:
        return MoleculeProperties()


def drug_likeness_score(mol) -> float:
    """Composite drug-likeness score (0-1).

    Primary: QED (0-1, captures the overall drug-likeness profile).
    Bonus: Lipinski compliance adds up to 0.1.
    """
    props = compute_properties(mol)
    score = props.qed * 0.9
    lipinski_bonus = (4 - props.lipinski_violations) / 4.0 * 0.1
    return max(0.0, min(1.0, score + lipinski_bonus))


def sa_score_normalized(mol) -> float:
    """Synthetic accessibility as a 0-1 score (1 = easy to synthesize)."""
    props = compute_properties(mol)
    return max(0.0, (10.0 - props.sa_score) / 9.0)


def morgan_fingerprint(mol, radius: int = 2, n_bits: int = 2048):
    """Compute Morgan fingerprint for similarity calculations."""
    if mol is None:
        return None
    try:
        return AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    except Exception:
        return None


def tanimoto_similarity(fp1, fp2) -> float:
    """Tanimoto similarity between two fingerprints (0-1)."""
    if fp1 is None or fp2 is None:
        return 0.0
    return DataStructs.TanimotoSimilarity(fp1, fp2)


def scaffold_novelty_score(mol, reference_fps: list) -> float:
    """How structurally DIFFERENT is this molecule from known drugs?

    Returns 1 - max_similarity. Higher = more novel scaffold.
    Used in scaffold hopping to penalize molecules that resemble known drugs.
    """
    if not reference_fps:
        return 1.0
    fp = morgan_fingerprint(mol)
    if fp is None:
        return 0.0
    max_sim = max(tanimoto_similarity(fp, rfp) for rfp in reference_fps if rfp is not None)
    return 1.0 - max_sim


def drug_similarity_score(mol, reference_fps: list) -> float:
    """How similar is this molecule to known drug structures?

    Returns max Tanimoto similarity to any reference drug.
    Higher = more drug-like scaffold.
    """
    if not reference_fps:
        return 0.0
    fp = morgan_fingerprint(mol)
    if fp is None:
        return 0.0
    sims = [tanimoto_similarity(fp, rfp) for rfp in reference_fps if rfp is not None]
    return max(sims) if sims else 0.0


def novelty_score(mol, population_fps: list) -> float:
    """How different is this molecule from the rest of the population?

    Returns average Tanimoto distance (1 - similarity) from population.
    Higher = more novel.
    """
    if not population_fps:
        return 1.0

    fp = morgan_fingerprint(mol)
    if fp is None:
        return 0.0

    similarities = [tanimoto_similarity(fp, pfp) for pfp in population_fps if pfp is not None]
    if not similarities:
        return 1.0

    avg_similarity = sum(similarities) / len(similarities)
    return 1.0 - avg_similarity
