"""
Known drug reference structures for scaffold hopping.

Pre-computed fingerprints for known inhibitors of each target,
used to penalize evolved molecules that are too structurally similar.
"""

from rdkit import Chem
from rdkit.Chem import AllChem

# Known inhibitors by target
KNOWN_INHIBITORS = {
    'EGFR': {
        'erlotinib': 'C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1',
        'gefitinib': 'COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1',
        'osimertinib': 'C=CC(=O)Nc1cc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c(OC)cc1N(C)CCN(C)C',
        'lapatinib': 'CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1',
        'afatinib': 'CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1',
        'dacomitinib': 'COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1NC/C=C/CN1CCOCC1',
        'icotinib': 'C#Cc1cccc(Nc2ncnc3cc(OCCOCCOC)ccc23)c1',
    },
    'COX-2': {
        'celecoxib': 'Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(S(N)(=O)=O)cc2)cc1',
        'rofecoxib': 'CS(=O)(=O)c1ccc(C2=C(c3ccccc3)C(=O)OC2)cc1',
    },
}

# Cache fingerprints
_FP_CACHE = {}


def get_reference_fps(target_name: str) -> list:
    """Get Morgan fingerprints for known inhibitors of a target."""
    if target_name in _FP_CACHE:
        return _FP_CACHE[target_name]

    if target_name not in KNOWN_INHIBITORS:
        return []

    fps = []
    for name, smiles in KNOWN_INHIBITORS[target_name].items():
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            fps.append(fp)

    _FP_CACHE[target_name] = fps
    return fps
