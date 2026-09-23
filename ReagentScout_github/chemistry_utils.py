import requests
from urllib.parse import quote

from rdkit import Chem
from rdkit.Chem import Draw


def is_valid_smiles(smiles):
    if not smiles:
        return False

    mol = Chem.MolFromSmiles(smiles)

    return mol is not None


def make_2d_molecule_image(smiles):
    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        return None

    return Draw.MolToImage(
        mol,
        size=(500, 500),
    )


def canonicalize_smiles(smiles):
    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        return None

    return Chem.MolToSmiles(
        mol,
        canonical=True,
        isomericSmiles=True,
    )


def get_pubchem_smiles_from_name(molecule_name):
    encoded_name = quote(molecule_name.strip())

    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        f"{encoded_name}/property/SMILES,ConnectivitySMILES,IUPACName/JSON"
    )

    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        return None

    data = response.json()

    properties = data.get("PropertyTable", {}).get("Properties", [])

    if not properties:
        return None

    record = properties[0]

    pubchem_smiles = (
        record.get("SMILES")
        or record.get("ConnectivitySMILES")
        or record.get("IsomericSMILES")
        or record.get("CanonicalSMILES")
        or ""
    )

    return {
        "pubchem_cid": record.get("CID"),
        "iupac_name": record.get("IUPACName", ""),
        "pubchem_smiles": pubchem_smiles,
        "raw_pubchem_record": record,
    }

def validate_smiles_with_pubchem(molecule_name, generated_smiles):
    pubchem_record = get_pubchem_smiles_from_name(molecule_name)

    if pubchem_record is None:
        return {
            "status": "not_found",
            "message": "No matching molecule was found in PubChem.",
        }

    generated_canonical = canonicalize_smiles(generated_smiles)
    pubchem_canonical = canonicalize_smiles(pubchem_record["pubchem_smiles"])

    if generated_canonical is None or pubchem_canonical is None:
        return {
            "status": "invalid",
            "message": "One of the SMILES strings could not be parsed by RDKit.",
            "pubchem_record": pubchem_record,
        }

    match = generated_canonical == pubchem_canonical

    return {
        "status": "match" if match else "mismatch",
        "message": (
            "The generated SMILES matches PubChem after RDKit canonicalization."
            if match
            else "The generated SMILES does not match PubChem after RDKit canonicalization."
        ),
        "pubchem_record": pubchem_record,
        "generated_canonical": generated_canonical,
        "pubchem_canonical": pubchem_canonical,
    }