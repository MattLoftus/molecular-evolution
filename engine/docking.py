"""
AutoDock Vina docking wrapper.

Uses the Vina CLI binary (subprocess) + meeko for ligand preparation +
openbabel for receptor preparation.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rdkit import Chem
from rdkit.Chem import AllChem

VINA_BIN = str(Path(__file__).parent.parent / 'data' / 'vina')
TARGETS_DIR = Path(__file__).parent.parent / 'data' / 'targets'


@dataclass
class DockingResult:
    """Result of a docking calculation."""
    affinity_kcal: float  # Best binding affinity (kcal/mol, more negative = better)
    success: bool
    error: str = ''


@dataclass
class TargetConfig:
    """Configuration for a docking target."""
    name: str
    pdb_path: str
    pdbqt_path: str  # prepared receptor
    center_x: float
    center_y: float
    center_z: float
    size_x: float = 22.0
    size_y: float = 22.0
    size_z: float = 22.0


# Pre-defined targets with binding site coordinates
# Centers from co-crystallized ligand positions
TARGETS = {
    'EGFR': TargetConfig(
        name='EGFR wild-type (erlotinib site)',
        pdb_path=str(TARGETS_DIR / '1M17.pdb'),
        pdbqt_path=str(TARGETS_DIR / '1M17_receptor.pdbqt'),
        center_x=22.0, center_y=0.3, center_z=52.8,
        size_x=22, size_y=22, size_z=22,
    ),
    'EGFR_T790M': TargetConfig(
        name='EGFR T790M resistance mutant',
        pdb_path=str(TARGETS_DIR / '4I22.pdb'),
        pdbqt_path=str(TARGETS_DIR / '4I22_receptor.pdbqt'),
        center_x=10.2, center_y=-15.8, center_z=11.2,
        size_x=22, size_y=22, size_z=22,
    ),
    'EGFR_C797S': TargetConfig(
        name='EGFR C797S resistance mutant',
        pdb_path=str(TARGETS_DIR / '5Y9T.pdb'),
        pdbqt_path=str(TARGETS_DIR / '5Y9T_receptor.pdbqt'),
        center_x=-0.5, center_y=49.6, center_z=-17.7,
        size_x=22, size_y=22, size_z=22,
    ),
}

# Target groups for multi-target docking
TARGET_GROUPS = {
    'EGFR': ['EGFR'],
    'EGFR_resistant': ['EGFR', 'EGFR_T790M'],
    'EGFR_all': ['EGFR', 'EGFR_T790M', 'EGFR_C797S'],
}


def prepare_receptor(pdb_path: str, output_pdbqt: str) -> bool:
    """Convert PDB to PDBQT using Open Babel.

    Removes water, heteroatoms (ligands), adds polar hydrogens.
    """
    try:
        from openbabel import openbabel as ob

        conv = ob.OBConversion()
        conv.SetInAndOutFormats('pdb', 'pdbqt')

        # Options: remove waters, add hydrogens
        conv.AddOption('r', ob.OBConversion.OUTOPTIONS)  # rigid
        conv.AddOption('x', ob.OBConversion.OUTOPTIONS)  # no torsion tree
        conv.AddOption('h', ob.OBConversion.GENOPTIONS)  # add hydrogens

        mol = ob.OBMol()

        # Read PDB
        conv.ReadFile(mol, pdb_path)

        # Remove waters and non-protein atoms
        atoms_to_delete = []
        for atom in ob.OBMolAtomIter(mol):
            res = atom.GetResidue()
            if res:
                resname = res.GetName().strip()
                if resname in ('HOH', 'WAT', 'AHB', 'ERL'):  # water + erlotinib ligand
                    atoms_to_delete.append(atom.GetIdx())

        # Delete in reverse order
        for idx in sorted(atoms_to_delete, reverse=True):
            atom = mol.GetAtom(idx)
            if atom:
                mol.DeleteAtom(atom)

        # Add hydrogens
        mol.AddHydrogens()

        # Write PDBQT
        conv.WriteFile(mol, output_pdbqt)
        return os.path.exists(output_pdbqt) and os.path.getsize(output_pdbqt) > 0
    except Exception as e:
        print(f"Receptor preparation failed: {e}")
        return False


def prepare_ligand_pdbqt(mol) -> Optional[str]:
    """Convert RDKit Mol to PDBQT string for Vina.

    Uses meeko for proper torsion tree generation.
    """
    if mol is None:
        return None

    try:
        from meeko import MoleculePreparation, PDBQTWriterLegacy

        mol_h = Chem.AddHs(mol)
        result = AllChem.EmbedMolecule(mol_h, AllChem.ETKDGv3())
        if result == -1:
            return None
        AllChem.MMFFOptimizeMolecule(mol_h, maxIters=200)

        preparator = MoleculePreparation()
        mol_setups = preparator.prepare(mol_h)
        if not mol_setups:
            return None

        pdbqt_string, is_ok, error = PDBQTWriterLegacy.write_string(mol_setups[0])
        if is_ok:
            return pdbqt_string
        return None
    except Exception:
        return None


def dock(mol, target_name: str = 'EGFR', exhaustiveness: int = 4,
         timeout: int = 30) -> DockingResult:
    """Dock a molecule against a protein target using Vina CLI.

    Args:
        mol: RDKit Mol object
        target_name: Key into TARGETS dict
        exhaustiveness: Vina search exhaustiveness (4=fast, 8=default, 32=thorough)
        timeout: Max seconds for docking

    Returns:
        DockingResult with binding affinity
    """
    if target_name not in TARGETS:
        return DockingResult(affinity_kcal=0, success=False,
                             error=f'Unknown target: {target_name}')

    target = TARGETS[target_name]

    # Ensure receptor is prepared
    if not os.path.exists(target.pdbqt_path):
        ok = prepare_receptor(target.pdb_path, target.pdbqt_path)
        if not ok:
            return DockingResult(affinity_kcal=0, success=False,
                                 error='Receptor preparation failed')

    # Prepare ligand
    ligand_pdbqt = prepare_ligand_pdbqt(mol)
    if ligand_pdbqt is None:
        return DockingResult(affinity_kcal=0, success=False,
                             error='Ligand preparation failed')

    # Write to temp files and run Vina
    with tempfile.TemporaryDirectory() as tmpdir:
        lig_path = os.path.join(tmpdir, 'ligand.pdbqt')
        out_path = os.path.join(tmpdir, 'out.pdbqt')

        with open(lig_path, 'w') as f:
            f.write(ligand_pdbqt)

        cmd = [
            VINA_BIN,
            '--receptor', target.pdbqt_path,
            '--ligand', lig_path,
            '--out', out_path,
            '--center_x', str(target.center_x),
            '--center_y', str(target.center_y),
            '--center_z', str(target.center_z),
            '--size_x', str(target.size_x),
            '--size_y', str(target.size_y),
            '--size_z', str(target.size_z),
            '--exhaustiveness', str(exhaustiveness),
            '--num_modes', '1',
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            if result.returncode != 0:
                return DockingResult(affinity_kcal=0, success=False,
                                     error=result.stderr[:200])

            # Parse affinity from Vina output
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('1'):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            affinity = float(parts[1])
                            return DockingResult(affinity_kcal=affinity,
                                                 success=True)
                        except ValueError:
                            pass

            return DockingResult(affinity_kcal=0, success=False,
                                 error='Could not parse Vina output')

        except subprocess.TimeoutExpired:
            return DockingResult(affinity_kcal=0, success=False,
                                 error='Docking timed out')
        except Exception as e:
            return DockingResult(affinity_kcal=0, success=False,
                                 error=str(e)[:200])


def dock_multi(mol, target_group: str = 'EGFR', exhaustiveness: int = 4,
               timeout: int = 30) -> dict:
    """Dock against multiple targets in a group.

    Returns dict of {target_name: DockingResult}.
    For fitness, use the WORST (least negative) affinity — the molecule
    must bind ALL targets well to score high.
    """
    if target_group not in TARGET_GROUPS:
        return {}

    results = {}
    for target_name in TARGET_GROUPS[target_group]:
        results[target_name] = dock(mol, target_name, exhaustiveness, timeout)
    return results


def multi_target_score(results: dict) -> float:
    """Score from multi-target docking: worst-case binding across targets.

    A resistance-proof molecule must bind ALL variants well.
    Returns 0-1 score based on the weakest binding.
    """
    affinities = []
    for r in results.values():
        if r.success and r.affinity_kcal < 0:
            affinities.append(r.affinity_kcal)

    if not affinities:
        return 0.0

    # Use the worst (least negative) affinity
    worst = max(affinities)  # max because values are negative
    return min(1.0, -worst / 10.0)


def dock_smiles(smiles: str, target_name: str = 'EGFR', **kwargs) -> DockingResult:
    """Convenience: dock a SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return DockingResult(affinity_kcal=0, success=False, error='Invalid SMILES')
    return dock(mol, target_name, **kwargs)
