# export_molecule_html.py

import sys
from visualization import draw_3d_molecule


def main():
    """
    Export an interactive 3D molecule viewer as an HTML file.

    Usage:
        python export_molecule_html.py "CCO" molecule_3d.html
    """

    if len(sys.argv) != 3:
        print("Usage: python export_molecule_html.py SMILES OUTPUT_HTML_PATH")
        sys.exit(1)

    smiles = sys.argv[1]
    output_path = sys.argv[2]

    plotter = draw_3d_molecule(smiles)

    if plotter is None:
        print("Error: invalid SMILES string or failed 3D molecule generation.")
        sys.exit(1)

    plotter.export_html(output_path)
    plotter.close()

    print(f"Interactive 3D molecule exported to: {output_path}")


if __name__ == "__main__":
    main()