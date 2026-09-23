# state.py

import uuid

from molecule_record import initialize_molecule_record


def initialize_session_state(st):
    """
    Initialize all Streamlit session-state variables used by ReagentScout.
    """

    # -------------------------------------------------------------------------
    # Session tracking
    # -------------------------------------------------------------------------
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    # -------------------------------------------------------------------------
    # AI model selection
    # -------------------------------------------------------------------------
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = None

    # -------------------------------------------------------------------------
    # Molecule identification
    # -------------------------------------------------------------------------
    if "molecule_name" not in st.session_state:
        st.session_state.molecule_name = ""

    if "molecule_confidence" not in st.session_state:
        st.session_state.molecule_confidence = None

    if "molecule_explanation" not in st.session_state:
        st.session_state.molecule_explanation = ""

    # -------------------------------------------------------------------------
    # SMILES generation
    # -------------------------------------------------------------------------
    if "smiles" not in st.session_state:
        st.session_state.smiles = ""

    if "smiles_confidence" not in st.session_state:
        st.session_state.smiles_confidence = None

    if "smiles_explanation" not in st.session_state:
        st.session_state.smiles_explanation = ""

    # Compatibility with older code that may still use generated_text
    if "generated_text" not in st.session_state:
        st.session_state.generated_text = ""

    # -------------------------------------------------------------------------
    # PubChem validation
    # -------------------------------------------------------------------------
    if "pubchem_validation" not in st.session_state:
        st.session_state.pubchem_validation = None

    if "pubchem_cid" not in st.session_state:
        st.session_state.pubchem_cid = None

    if "pubchem_name" not in st.session_state:
        st.session_state.pubchem_name = ""

    if "pubchem_iupac_name" not in st.session_state:
        st.session_state.pubchem_iupac_name = ""

    if "pubchem_smiles" not in st.session_state:
        st.session_state.pubchem_smiles = ""

    if "cas_number" not in st.session_state:
        st.session_state.cas_number = ""

    if "molecular_formula" not in st.session_state:
        st.session_state.molecular_formula = ""

    if "molecular_weight" not in st.session_state:
        st.session_state.molecular_weight = ""

    # -------------------------------------------------------------------------
    # Final validated molecule output
    # -------------------------------------------------------------------------
    if "final_smiles" not in st.session_state:
        st.session_state.final_smiles = ""

    if "smiles_source" not in st.session_state:
        st.session_state.smiles_source = ""

    # -------------------------------------------------------------------------
    # ReagentScout molecule record
    # -------------------------------------------------------------------------
    initialize_molecule_record(st)