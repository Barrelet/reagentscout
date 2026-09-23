# molecule_record.py


def initialize_molecule_record(st):
    """
    Creates a single structured molecule record in Streamlit session state.

    This record becomes the central source of truth for ReagentScout.
    """

    if "molecule_record" not in st.session_state:
        st.session_state.molecule_record = {
            "input_name": None,
            "llm_name": None,
            "llm_smiles": None,
            "pubchem_cid": None,
            "pubchem_name": None,
            "pubchem_iupac_name": None,
            "pubchem_smiles": None,
            "cas_number": None,
            "molecular_formula": None,
            "molecular_weight": None,
            "final_smiles": None,
            "source_of_truth": None,
        }


def _get_from_dict(data, possible_keys):
    """
    Safely extracts a value from a dictionary using several possible key names.
    """

    if not isinstance(data, dict):
        return None

    for key in possible_keys:
        value = data.get(key)
        if value not in [None, ""]:
            return value

    return None


def sync_molecule_record_from_session(st):
    """
    Syncs existing Streamlit session-state variables into molecule_record.

    This version is aligned with your current app, which uses:
    - st.session_state.molecule_name
    - st.session_state.smiles
    - st.session_state.final_smiles
    - st.session_state.smiles_source
    - st.session_state.pubchem_validation
    """

    initialize_molecule_record(st)

    record = st.session_state.molecule_record

    # -------------------------------------------------------------------------
    # Existing molecule-name fields
    # -------------------------------------------------------------------------
    molecule_name = st.session_state.get("molecule_name", "")

    record["input_name"] = molecule_name
    record["llm_name"] = molecule_name

    # -------------------------------------------------------------------------
    # Existing SMILES fields from your app
    # -------------------------------------------------------------------------
    llm_smiles = st.session_state.get("smiles", "")
    final_smiles = st.session_state.get("final_smiles", "")
    smiles_source = st.session_state.get("smiles_source", "")

    record["llm_smiles"] = llm_smiles
    record["final_smiles"] = final_smiles

    # -------------------------------------------------------------------------
    # PubChem validation object
    # -------------------------------------------------------------------------
    pubchem_validation = st.session_state.get("pubchem_validation")

    if isinstance(pubchem_validation, dict):
        record["pubchem_cid"] = _get_from_dict(
            pubchem_validation,
            [
                "cid",
                "CID",
                "pubchem_cid",
                "PubChem CID",
            ],
        )

        record["pubchem_name"] = _get_from_dict(
            pubchem_validation,
            [
                "name",
                "compound_name",
                "pubchem_name",
                "title",
                "Title",
                "PubChem Name",
            ],
        )

        record["pubchem_iupac_name"] = _get_from_dict(
            pubchem_validation,
            [
                "iupac_name",
                "IUPACName",
                "iupac",
                "pubchem_iupac_name",
                "PubChem IUPAC Name",
            ],
        )

        record["pubchem_smiles"] = _get_from_dict(
            pubchem_validation,
            [
                "canonical_smiles",
                "CanonicalSMILES",
                "pubchem_smiles",
                "smiles",
                "SMILES",
                "PubChem SMILES",
            ],
        )

        record["molecular_formula"] = _get_from_dict(
            pubchem_validation,
            [
                "molecular_formula",
                "MolecularFormula",
                "formula",
                "Molecular Formula",
            ],
        )

        record["molecular_weight"] = _get_from_dict(
            pubchem_validation,
            [
                "molecular_weight",
                "MolecularWeight",
                "weight",
                "Molecular Weight",
            ],
        )

        record["cas_number"] = _get_from_dict(
            pubchem_validation,
            [
                "cas_number",
                "CAS",
                "CAS Number",
                "cas",
            ],
        )

    # -------------------------------------------------------------------------
    # Also support direct PubChem session-state fields if your app adds them later
    # -------------------------------------------------------------------------
    record["pubchem_cid"] = record.get("pubchem_cid") or st.session_state.get("pubchem_cid")
    record["pubchem_name"] = record.get("pubchem_name") or st.session_state.get("pubchem_name")
    record["pubchem_iupac_name"] = record.get("pubchem_iupac_name") or st.session_state.get("pubchem_iupac_name")
    record["pubchem_smiles"] = record.get("pubchem_smiles") or st.session_state.get("pubchem_smiles")
    record["cas_number"] = record.get("cas_number") or st.session_state.get("cas_number")
    record["molecular_formula"] = record.get("molecular_formula") or st.session_state.get("molecular_formula")
    record["molecular_weight"] = record.get("molecular_weight") or st.session_state.get("molecular_weight")

    # -------------------------------------------------------------------------
    # Source-of-truth logic
    # -------------------------------------------------------------------------
    if final_smiles:
        record["source_of_truth"] = smiles_source or "Final validated SMILES"
    elif record.get("pubchem_smiles"):
        record["source_of_truth"] = "PubChem"
    elif llm_smiles:
        record["source_of_truth"] = "LLM"
    else:
        record["source_of_truth"] = None

    st.session_state.molecule_record = record


def get_canonical_name(st):
    """
    Returns the best available molecule name.
    """

    sync_molecule_record_from_session(st)
    record = st.session_state.molecule_record

    return (
        record.get("pubchem_name")
        or record.get("pubchem_iupac_name")
        or record.get("llm_name")
        or record.get("input_name")
    )


def get_canonical_smiles(st):
    """
    Returns the best available SMILES string.

    Priority:
    1. final_smiles from your app
    2. PubChem SMILES
    3. LLM-generated SMILES
    """

    sync_molecule_record_from_session(st)
    record = st.session_state.molecule_record

    return (
        record.get("final_smiles")
        or record.get("pubchem_smiles")
        or record.get("llm_smiles")
    )


def display_molecule_record(st):
    """
    Displays a compact summary of the current ReagentScout molecule record.
    """

    sync_molecule_record_from_session(st)
    record = st.session_state.molecule_record

    st.subheader("ReagentScout Molecule Record")

    st.write("**Canonical name:**", get_canonical_name(st) or "Not available")
    st.write("**Canonical SMILES:**", get_canonical_smiles(st) or "Not available")
    st.write("**Source of truth:**", record.get("source_of_truth") or "Not available")

    if record.get("pubchem_cid"):
        st.write("**PubChem CID:**", record["pubchem_cid"])

    if record.get("cas_number"):
        st.write("**CAS number:**", record["cas_number"])

    if record.get("molecular_formula"):
        st.write("**Molecular formula:**", record["molecular_formula"])

    if record.get("molecular_weight"):
        st.write("**Molecular weight:**", record["molecular_weight"])