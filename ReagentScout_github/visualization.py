# visualization.py

import numpy as np
import pyvista as pv

from rdkit import Chem
from rdkit.Chem import AllChem

pv.OFF_SCREEN = True


ATOM_COLORS = {
    "C": "black",
    "N": "blue",
    "O": "red",
    "H": "yellow",
    "S": "orange",
    "F": "green",
    "Cl": "green",
    "Br": "brown",
    "I": "purple",
    "P": "orange",
}

SCALING_FACTOR_ATOMIC_RADII = 1 / 2

ATOM_RADII = {
    "H": 0.31 * SCALING_FACTOR_ATOMIC_RADII,
    "C": 0.76 * SCALING_FACTOR_ATOMIC_RADII,
    "N": 0.71 * SCALING_FACTOR_ATOMIC_RADII,
    "O": 0.66 * SCALING_FACTOR_ATOMIC_RADII,
    "S": 1.05 * SCALING_FACTOR_ATOMIC_RADII,
    "F": 0.57 * SCALING_FACTOR_ATOMIC_RADII,
    "Cl": 1.02 * SCALING_FACTOR_ATOMIC_RADII,
    "Br": 1.20 * SCALING_FACTOR_ATOMIC_RADII,
    "I": 1.39 * SCALING_FACTOR_ATOMIC_RADII,
    "P": 1.07 * SCALING_FACTOR_ATOMIC_RADII,
}


def draw_3d_molecule(smiles):
    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        return None

    mol = Chem.AddHs(mol)

    embed_status = AllChem.EmbedMolecule(mol, randomSeed=42)

    if embed_status != 0:
        return None

    AllChem.MMFFOptimizeMolecule(mol)

    conf = mol.GetConformer()

    plotter = pv.Plotter(window_size=[700, 500])

    for atom in mol.GetAtoms():
        pos = conf.GetAtomPosition(atom.GetIdx())
        symbol = atom.GetSymbol()

        sphere = pv.Sphere(
            radius=ATOM_RADII.get(symbol, 0.3),
            center=(pos.x, pos.y, pos.z),
        )

        plotter.add_mesh(
            sphere,
            color=ATOM_COLORS.get(symbol, "gray"),
            smooth_shading=True,
        )

    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()

        p1 = conf.GetAtomPosition(i)
        p2 = conf.GetAtomPosition(j)

        start = np.array([p1.x, p1.y, p1.z])
        end = np.array([p2.x, p2.y, p2.z])

        cylinder = pv.Cylinder(
            center=(start + end) / 2,
            direction=end - start,
            radius=0.08,
            height=np.linalg.norm(end - start),
        )

        plotter.add_mesh(cylinder, color="gray")

    plotter.background_color = "white"
    plotter.camera_position = "iso"

    return plotter