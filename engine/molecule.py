"""
SELFIES-based molecular representation with GA operators.

Every SELFIES string decodes to a valid molecule, so mutations and
crossovers always produce valid chemistry — no repair step needed.

The alphabet is filtered to organic elements only (C, N, O, S, F, Cl, Br)
to prevent the GA from converging on inorganic junk.
"""

import random
from dataclasses import dataclass, field
from typing import Optional

import selfies as sf
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors


# --- Alphabet filtering ---
# Only allow organic chemistry elements + structural tokens
_ORGANIC_ELEMENTS = {'C', 'N', 'O', 'S', 'F', 'Cl', 'Br'}
_STRUCTURAL_PREFIXES = {'Branch', 'Ring', 'Expl'}
_ALPHABET = None
_FULL_ALPHABET = None


def _is_organic_token(token: str) -> bool:
    """Check if a SELFIES token uses only organic elements."""
    inner = token.strip('[]')
    for prefix in ['=', '#', '/', '\\']:
        inner = inner.lstrip(prefix)
    # Structural tokens (Branch, Ring) are always OK
    for sp in _STRUCTURAL_PREFIXES:
        if inner.startswith(sp):
            return True
    # Extract element symbol
    elem = ''
    for c in inner:
        if c.isupper():
            elem = c
        elif c.islower() and elem:
            elem += c
        else:
            break
    return elem in _ORGANIC_ELEMENTS


def get_alphabet():
    """Get the organic-filtered SELFIES alphabet (cached)."""
    global _ALPHABET
    if _ALPHABET is None:
        full = list(sf.get_semantic_robust_alphabet())
        _ALPHABET = [t for t in full if _is_organic_token(t)]
    return _ALPHABET


# --- Drug fragment seeds ---
# Common drug scaffolds as SMILES for population seeding.
# These represent the most frequent substructures in approved drugs.
DRUG_FRAGMENTS = [
    # Aromatic rings & heterocycles
    'c1ccccc1',                    # benzene
    'c1ccncc1',                    # pyridine
    'c1cc[nH]c1',                  # pyrrole
    'c1ccoc1',                     # furan
    'c1ccsc1',                     # thiophene
    'c1cnc2ccccc2n1',              # quinazoline
    'c1ccc2[nH]ccc2c1',           # indole
    'c1ccc2ncccc2c1',             # quinoline
    'C1CCNCC1',                    # piperidine
    'C1CCNC1',                     # pyrrolidine
    'C1CCOCC1',                    # tetrahydropyran
    'C1CNCCN1',                    # piperazine
    'c1cn[nH]c1',                  # pyrazole
    'c1cncnc1',                    # pyrimidine
    'c1c[nH]cn1',                  # imidazole

    # Simple drug-like building blocks
    'c1ccc(N)cc1',                 # aniline
    'c1ccc(O)cc1',                 # phenol
    'c1ccc(C(=O)O)cc1',           # benzoic acid
    'c1ccc(C(=O)N)cc1',           # benzamide
    'c1ccc(NC(=O)C)cc1',          # acetanilide
    'CC(=O)Oc1ccccc1C(=O)O',     # aspirin scaffold
    'c1ccc(-c2ccccc2)cc1',        # biphenyl
    'c1ccc(Oc2ccccc2)cc1',        # diphenyl ether
    'c1ccc(Nc2ncncn2)cc1',        # aminopyrimidine
    'CC(C)Cc1ccc(C(C)C(=O)O)cc1', # ibuprofen scaffold

    # Drug-like intermediates
    'c1ccc(C(=O)Nc2ccccc2)cc1',   # benzanilide
    'c1ccc(S(=O)(=O)N)cc1',       # sulfonamide
    'c1ccc(NC(=O)c2ccccn2)cc1',   # picolinamide
    'O=C(O)CCc1ccccc1',           # phenylpropionic acid
    'c1cc(F)ccc1NC(=O)C',         # fluoroacetanilide
    'c1ccc(Cl)cc1NC(=O)C',        # chloroacetanilide
    'c1ccc(OC)cc1CC=O',           # methoxyphenylacetaldehyde
]


# CPK element colors for 3D visualization
ELEMENT_COLORS = {
    'C': '#909090', 'N': '#3050F8', 'O': '#FF0D0D', 'S': '#FFFF30',
    'H': '#FFFFFF', 'F': '#90E050', 'Cl': '#1FF01F', 'Br': '#A62929',
    'I': '#940094', 'P': '#FF8000', 'B': '#FFB5B5',
}

VDW_RADII = {
    'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80, 'H': 1.20,
    'F': 1.47, 'Cl': 1.75, 'Br': 1.85, 'I': 1.98, 'P': 1.80, 'B': 1.65,
}


@dataclass
class Molecule3D:
    """A molecule with 3D coordinates for visualization."""
    selfies: str
    smiles: str
    atoms: list = field(default_factory=list)
    bonds: list = field(default_factory=list)

    def to_dict(self):
        return {
            'selfies': self.selfies,
            'smiles': self.smiles,
            'atoms': self.atoms,
            'bonds': self.bonds,
        }

    @staticmethod
    def from_dict(d):
        return Molecule3D(
            selfies=d['selfies'],
            smiles=d['smiles'],
            atoms=d.get('atoms', []),
            bonds=d.get('bonds', []),
        )


def random_selfies(max_tokens: int = 20) -> str:
    """Generate a random valid SELFIES string from organic alphabet."""
    alphabet = get_alphabet()
    length = random.randint(8, max_tokens)
    tokens = [random.choice(alphabet) for _ in range(length)]
    return ''.join(tokens)


def fragment_selfies() -> str:
    """Generate a SELFIES string seeded from a drug fragment.

    Takes a known drug scaffold, converts to SELFIES, then applies
    light mutation to create variation.
    """
    smiles = random.choice(DRUG_FRAGMENTS)
    try:
        selfies_str = sf.encoder(smiles)
        if selfies_str:
            # Apply light mutation to create variation
            return mutate_selfies(selfies_str, mutation_rate=0.15)
    except Exception:
        pass
    return random_selfies()


def selfies_to_mol(selfies_str: str) -> Optional[Chem.Mol]:
    """Convert SELFIES to RDKit Mol. Returns None if conversion fails."""
    try:
        smiles = sf.decoder(selfies_str)
        if smiles is None:
            return None
        mol = Chem.MolFromSmiles(smiles)
        return mol
    except Exception:
        return None


def mol_to_selfies(mol: Chem.Mol) -> Optional[str]:
    """Convert RDKit Mol to SELFIES string."""
    try:
        smiles = Chem.MolToSmiles(mol)
        return sf.encoder(smiles)
    except Exception:
        return None


def is_organic(mol) -> bool:
    """Check if a molecule contains only organic elements."""
    allowed = {6, 7, 8, 9, 16, 17, 35}  # C, N, O, F, S, Cl, Br
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() not in allowed:
            return False
    return True


def mutate_selfies(selfies_str: str, mutation_rate: float = 0.3) -> str:
    """Token-level mutation on a SELFIES string using organic alphabet."""
    tokens = list(sf.split_selfies(selfies_str))
    if not tokens:
        return random_selfies()

    alphabet = get_alphabet()

    for i in range(len(tokens)):
        if random.random() < mutation_rate:
            op = random.choice(['swap', 'insert', 'delete'])
            if op == 'swap':
                tokens[i] = random.choice(alphabet)
            elif op == 'insert' and len(tokens) < 40:
                tokens.insert(i, random.choice(alphabet))
            elif op == 'delete' and len(tokens) > 3:
                tokens.pop(i)
                break

    return ''.join(tokens)


def crossover_selfies(parent1: str, parent2: str) -> tuple:
    """Single-point crossover on SELFIES token lists."""
    tokens1 = list(sf.split_selfies(parent1))
    tokens2 = list(sf.split_selfies(parent2))

    if len(tokens1) < 2 or len(tokens2) < 2:
        return parent1, parent2

    cut1 = random.randint(1, len(tokens1) - 1)
    cut2 = random.randint(1, len(tokens2) - 1)

    child1 = ''.join(tokens1[:cut1] + tokens2[cut2:])
    child2 = ''.join(tokens2[:cut2] + tokens1[cut1:])

    child1_tokens = list(sf.split_selfies(child1))
    child2_tokens = list(sf.split_selfies(child2))
    if len(child1_tokens) > 40:
        child1 = ''.join(child1_tokens[:40])
    if len(child2_tokens) > 40:
        child2 = ''.join(child2_tokens[:40])

    return child1, child2


def selfies_to_3d(selfies_str: str) -> Optional[Molecule3D]:
    """Convert SELFIES to 3D molecule with coordinates."""
    mol = selfies_to_mol(selfies_str)
    if mol is None:
        return None

    smiles = Chem.MolToSmiles(mol)
    mol_h = Chem.AddHs(mol)

    result = AllChem.EmbedMolecule(mol_h, AllChem.ETKDGv3())
    if result == -1:
        result = AllChem.EmbedMolecule(mol_h, AllChem.ETKDGv3())
        if result == -1:
            AllChem.Compute2DCoords(mol_h)

    try:
        AllChem.MMFFOptimizeMolecule(mol_h, maxIters=200)
    except Exception:
        pass

    conf = mol_h.GetConformer()

    atoms = []
    heavy_atom_map = {}
    idx = 0
    for i, atom in enumerate(mol_h.GetAtoms()):
        element = atom.GetSymbol()
        if element == 'H':
            continue
        pos = conf.GetAtomPosition(i)
        atoms.append({
            'element': element,
            'x': round(pos.x, 3),
            'y': round(pos.y, 3),
            'z': round(pos.z, 3),
        })
        heavy_atom_map[i] = idx
        idx += 1

    bonds = []
    for bond in mol_h.GetBonds():
        a1 = bond.GetBeginAtomIdx()
        a2 = bond.GetEndAtomIdx()
        if a1 in heavy_atom_map and a2 in heavy_atom_map:
            order = bond.GetBondTypeAsDouble()
            bonds.append({
                'atom1': heavy_atom_map[a1],
                'atom2': heavy_atom_map[a2],
                'order': int(order) if order == int(order) else order,
            })

    return Molecule3D(selfies=selfies_str, smiles=smiles, atoms=atoms, bonds=bonds)


def smiles_to_3d(smiles: str) -> Optional[Molecule3D]:
    """Convert SMILES to 3D molecule. Convenience wrapper."""
    try:
        selfies_str = sf.encoder(smiles)
        result = selfies_to_3d(selfies_str)
        if result:
            result.smiles = smiles
        return result
    except Exception:
        return None
