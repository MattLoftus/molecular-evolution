"""
Reference drug structures for benchmarking and comparison.

Known drugs for each protein target, stored as SMILES strings
with their properties and target information.
"""

KNOWN_DRUGS = {
    # EGFR kinase inhibitors (lung cancer)
    'erlotinib': {
        'smiles': 'C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1',
        'name': 'Erlotinib (Tarceva)',
        'target': 'EGFR',
        'indication': 'Non-small cell lung cancer',
        'approval_year': 2004,
        'mw': 393.44,
        'ic50_nM': 2.0,
    },
    'gefitinib': {
        'smiles': 'COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1',
        'name': 'Gefitinib (Iressa)',
        'target': 'EGFR',
        'indication': 'Non-small cell lung cancer',
        'approval_year': 2003,
        'mw': 446.90,
        'ic50_nM': 33.0,
    },
    'osimertinib': {
        'smiles': 'C=CC(=O)Nc1cc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c(OC)cc1N(C)CCN(C)C',
        'name': 'Osimertinib (Tagrisso)',
        'target': 'EGFR',
        'indication': 'NSCLC with T790M mutation',
        'approval_year': 2015,
        'mw': 499.62,
        'ic50_nM': 12.9,
    },

    # COX-2 inhibitors (inflammation)
    'celecoxib': {
        'smiles': 'Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(S(N)(=O)=O)cc2)cc1',
        'name': 'Celecoxib (Celebrex)',
        'target': 'COX-2',
        'indication': 'Arthritis, pain',
        'approval_year': 1998,
        'mw': 381.37,
        'ic50_nM': 40.0,
    },

    # HIV protease inhibitors
    'saquinavir': {
        'smiles': 'CC(C)(C)NC(=O)[C@@H]1C[C@@H]2CCCC[C@@H]2CN1C[C@@H](O)[C@H](Cc1ccccc1)NC(=O)[C@H](CC(N)=O)NC(=O)c1ccc2ccccc2n1',
        'name': 'Saquinavir (Invirase)',
        'target': 'HIV-protease',
        'indication': 'HIV/AIDS',
        'approval_year': 1995,
        'mw': 670.84,
        'ic50_nM': 0.4,
    },

    # SARS-CoV-2 Mpro inhibitors
    'nirmatrelvir': {
        'smiles': 'CC1(C)C2CCC1(C)C(NC(=O)C(F)(F)F)C2NC(=O)[C@@H]1C[C@H](C#N)CN1C(=O)C(C)(C)C',
        'name': 'Nirmatrelvir (Paxlovid)',
        'target': 'SARS-CoV-2-Mpro',
        'indication': 'COVID-19',
        'approval_year': 2021,
        'mw': 499.53,
        'ic50_nM': 3.1,
    },

    # DPP-4 inhibitors (diabetes)
    'sitagliptin': {
        'smiles': 'N[C@@H](CC(=O)N1CCn2c(nnc2C(F)(F)F)C1)Cc1cc(F)c(F)cc1F',
        'name': 'Sitagliptin (Januvia)',
        'target': 'DPP-4',
        'indication': 'Type 2 diabetes',
        'approval_year': 2006,
        'mw': 407.31,
        'ic50_nM': 18.0,
    },

    # Common reference drugs (well-known, simple structures)
    'aspirin': {
        'smiles': 'CC(=O)Oc1ccccc1C(O)=O',
        'name': 'Aspirin',
        'target': 'COX-1/COX-2',
        'indication': 'Pain, inflammation',
        'approval_year': 1899,
        'mw': 180.16,
        'ic50_nM': None,
    },
    'ibuprofen': {
        'smiles': 'CC(C)Cc1ccc(C(C)C(O)=O)cc1',
        'name': 'Ibuprofen',
        'target': 'COX-1/COX-2',
        'indication': 'Pain, inflammation',
        'approval_year': 1969,
        'mw': 206.28,
        'ic50_nM': None,
    },
    'caffeine': {
        'smiles': 'Cn1c(=O)c2c(ncn2C)n(C)c1=O',
        'name': 'Caffeine',
        'target': 'Adenosine receptor',
        'indication': 'Stimulant',
        'approval_year': None,
        'mw': 194.19,
        'ic50_nM': None,
    },
}


# Target-specific drug groupings
DRUGS_BY_TARGET = {}
for drug_id, drug in KNOWN_DRUGS.items():
    target = drug['target']
    if target not in DRUGS_BY_TARGET:
        DRUGS_BY_TARGET[target] = []
    DRUGS_BY_TARGET[target].append(drug_id)


def get_drugs_for_target(target: str) -> list:
    """Get all known drugs for a specific target."""
    return [KNOWN_DRUGS[d] for d in DRUGS_BY_TARGET.get(target, [])]
