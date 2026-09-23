OPENAI_API_KEY = "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"


import streamlit as st
from openai import OpenAI

import subprocess
import webbrowser
import os
import sys
import json
import requests
from urllib.parse import quote, quote_plus

from config import (
    APP_TITLE,
    APP_ICON,
    PAGE_HEADER,
    BETA_NOTICE,
    DEFAULT_MODEL,
    AVAILABLE_MODELS,
    DEV_MODE,
)

from prompts import MOLECULE_NAME_SYSTEM_PROMPT, SMILES_SYSTEM_PROMPT
from state import initialize_session_state
from llm_service import call_llm_json
from chemistry_utils import (
    make_2d_molecule_image,
    is_valid_smiles,
    validate_smiles_with_pubchem,
)
from visualization import draw_3d_molecule
from supplier_directory import SUPPLIERS
from safety_classifier import classify_sourcing_risk, display_sourcing_risk
from pubchem_utils import fetch_cas_number_from_pubchem_cid

from molecule_record import (
    sync_molecule_record_from_session,
    get_canonical_name,
    get_canonical_smiles,
    display_molecule_record,
)

from analytics import (
    track_app_event,
    track_supplier_click,
    track_sourcing_request,
    get_supplier_events_file_path,
    get_app_events_file_path,
    get_sourcing_requests_file_path,
    get_beta_analytics_summary,
)


client = OpenAI(api_key=OPENAI_API_KEY)



def render_model_selection_tab():
    st.header("Select LLM")

    st.session_state.selected_model = st.selectbox(
        "Choose a model",
        options=AVAILABLE_MODELS,
        index=(
            AVAILABLE_MODELS.index(st.session_state.selected_model)
            if st.session_state.selected_model in AVAILABLE_MODELS
            else 0
        ),
    )

    st.write("Selected model:")
    st.code(st.session_state.selected_model)
 


def render_2d_structure_tab():
    st.header("2D Structural Diagram")

    # Sync the central ReagentScout molecule record first
    sync_molecule_record_from_session(st)

    smiles = get_canonical_smiles(st)

    if not smiles:
        st.info(
            "Generate and validate a SMILES string in the earlier tabs first."
        )
        return

    smiles = smiles.strip()

    st.subheader("Molecule Name")
    st.code(get_canonical_name(st) or st.session_state.molecule_name)

    st.subheader("Canonical SMILES")
    st.code(smiles)

    if st.session_state.get("smiles_source"):
        st.caption(f"SMILES source: {st.session_state.smiles_source}")

    try:
        img = make_2d_molecule_image(smiles)

        if img is None:
            st.error(
                "The selected SMILES string could not be interpreted as a valid molecule."
            )
        else:
            st.image(
                img,
                caption=get_canonical_name(st) or st.session_state.molecule_name,
                use_container_width=False,
            )

    except Exception as e:
        st.exception(e)


def render_3d_visualization_tab():
    st.header("3D Molecule Visualization")
    st.subheader("Ball-and-Stick Model")

    # Sync the central ReagentScout molecule record first
    sync_molecule_record_from_session(st)

    smiles = get_canonical_smiles(st)

    if not smiles:
        st.info(
            "Generate and validate a SMILES string in the earlier tabs first."
        )
        return

    smiles = smiles.strip()
    molecule_name = get_canonical_name(st) or st.session_state.molecule_name

    st.subheader("Molecule Name")
    st.code(molecule_name)

    st.subheader("Selected SMILES")
    st.code(smiles)

    if st.session_state.get("smiles_source"):
        st.caption(f"SMILES source: {st.session_state.smiles_source}")

    try:
        plotter = draw_3d_molecule(smiles)

        if plotter is None:
            st.error(
                "The selected SMILES string could not be interpreted as a valid molecule."
            )
            return

        st.info(
            "Open an interactive version to rotate, pan, and zoom the molecule."
        )

        if st.button("Open Interactive 3D Viewer", key="open_3d_viewer"):
            html_path = os.path.abspath("molecule_3d.html")

            result = subprocess.run(
                [
                    sys.executable,
                    "export_molecule_html.py",
                    smiles,
                    html_path,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                webbrowser.open(f"file://{html_path}")
                st.success(
                    "The interactive 3D molecule has been opened in your browser."
                )
            else:
                st.error("Failed to generate the interactive HTML viewer.")
                st.code(result.stderr)

        st.image(
            plotter.screenshot(return_img=True),
            caption=f"3D Structure of {molecule_name}",
            use_container_width=True,
        )

        plotter.close()

    except Exception as e:
        st.exception(e)


        

def reset_after_new_molecule_name():
    st.session_state.smiles = ""
    st.session_state.smiles_confidence = None
    st.session_state.smiles_explanation = ""

    st.session_state.pubchem_validation = None
    st.session_state.final_smiles = ""
    st.session_state.smiles_source = ""


def render_molecule_name_tab(client):
    st.header("Molecule Name Identification")

    user_prompt = st.text_area(
        "Describe the molecule",
        height=150,
        placeholder="Example: The molecule that gives coffee's stimulant effect..."
    )

    if st.button("Generate Molecule Name"):

        if not user_prompt.strip():
            st.warning("Please enter a molecule description.")

        else:
            raw_output = ""

            try:
                with st.spinner("Identifying molecule..."):

                    result, raw_output = call_llm_json(
                        client=client,
                        model=st.session_state.selected_model,
                        system_prompt=MOLECULE_NAME_SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                    )

                st.session_state.molecule_name = result.get(
                    "molecule_name",
                    "",
                )

                st.session_state.molecule_confidence = result.get(
                    "confidence",
                    None,
                )

                st.session_state.molecule_explanation = result.get(
                    "confidence_explanation",
                    "",
                )

                # Important:
                # A new molecule name means the old SMILES, PubChem validation,
                # and 3D visualization SMILES may no longer be valid.
                reset_after_new_molecule_name()

            except json.JSONDecodeError:
                st.error("The model did not return valid JSON.")

                with st.expander("Raw model output"):
                    st.code(raw_output)

            except Exception as e:
                st.exception(e)

    if st.session_state.get("molecule_name"):

        st.divider()

        st.subheader("Molecule Name")
        st.code(st.session_state.molecule_name)

        st.subheader("Confidence")

        if st.session_state.molecule_confidence is not None:
            st.metric(
                label="Confidence",
                value=f"{st.session_state.molecule_confidence}/100",
            )

        st.subheader("Explanation")
        st.write(st.session_state.molecule_explanation)



def render_smiles_generation_tab(client):
    st.header("SMILES Generation")

    if not st.session_state.get("molecule_name"):
        st.info(
            "No molecule has been identified yet. Please complete the Molecule Name Identification tab first."
        )

    molecule_name = st.text_input(
        "Molecule Name",
        value=st.session_state.get("molecule_name", ""),
        help="Automatically populated from the previous tab. You may edit it before generating the SMILES string.",
    )

    if st.button("Generate SMILES"):

        if not molecule_name.strip():
            st.warning("Please enter a molecule name.")

        else:
            raw_output = ""

            try:
                with st.spinner("Generating canonical SMILES..."):

                    result, raw_output = call_llm_json(
                        client=client,
                        model=st.session_state.selected_model,
                        system_prompt=SMILES_SYSTEM_PROMPT,
                        user_prompt=molecule_name.strip(),
                    )

                st.session_state.molecule_name = result.get(
                    "molecule_name",
                    molecule_name.strip(),
                )

                candidate_smiles = result.get(
                    "smiles",
                    "",
                )

                if not is_valid_smiles(candidate_smiles):
                    st.error(
                        "The generated SMILES string could not be validated by RDKit. Please try again or edit the molecule name."
                    )
                    st.session_state.smiles = ""
                else:
                    st.session_state.smiles = candidate_smiles
                    st.session_state.smiles_source = "LLM"
                    st.session_state.pubchem_validation = None

                st.session_state.smiles_confidence = result.get(
                    "confidence",
                    None,
                )

                st.session_state.smiles_explanation = result.get(
                    "confidence_explanation",
                    "",
                )

            except json.JSONDecodeError:
                st.error("The model did not return valid JSON.")

                with st.expander("Raw model output"):
                    st.code(raw_output)

            except Exception as e:
                st.exception(e)

    st.divider()

    st.caption(
        "SMILES (Simplified Molecular Input Line Entry System) is a compact textual representation of a chemical structure."
    )

    if st.session_state.get("smiles"):

        st.subheader("Molecule Name")
        st.code(st.session_state.molecule_name)

        st.subheader("Canonical SMILES")
        st.code(st.session_state.smiles)

        if st.session_state.smiles_confidence is not None:
            st.subheader("Confidence")

            st.metric(
                label="LLM Confidence",
                value=f"{st.session_state.smiles_confidence}/100",
            )

        st.subheader("Confidence Explanation")
        st.write(st.session_state.smiles_explanation)

def render_pubchem_validation_tab():

    st.header("PubChem Validation")

    molecule_name = st.session_state.molecule_name.strip()
    generated_smiles = st.session_state.smiles.strip()

    if not molecule_name:
        st.warning("Generate a molecule name first.")
        return

    if not generated_smiles:
        st.warning("Generate a SMILES string first.")
        return

    st.subheader("Generated Molecule Name")
    st.code(molecule_name)

    st.subheader("Generated SMILES")
    st.code(generated_smiles)

    if st.button("Validate with PubChem"):

        encoded_molecule_name = quote(molecule_name)

        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            + encoded_molecule_name
            + "/property/"
            + "SMILES,ConnectivitySMILES,IUPACName,MolecularFormula,MolecularWeight"
            + "/JSON"
        )

        try:
            response = requests.get(url, timeout=15)
            data = response.json()

            if "PropertyTable" not in data:
                st.session_state.final_smiles = generated_smiles
                st.session_state.smiles_source = "LLM"
                st.session_state.pubchem_validation = None
                st.session_state.pubchem_smiles = ""

                st.warning("PubChem did not return a valid molecule record.")
                st.warning("The app will use the generated SMILES instead.")

            else:
                pubchem_data = data["PropertyTable"]["Properties"][0]

                pubchem_smiles = (
                    pubchem_data.get("SMILES")
                    or pubchem_data.get("ConnectivitySMILES")
                    or pubchem_data.get("IsomericSMILES")
                    or pubchem_data.get("CanonicalSMILES")
                    or ""
                )

                pubchem_cid = pubchem_data.get("CID")
                pubchem_iupac_name = pubchem_data.get("IUPACName", "")
                molecular_formula = pubchem_data.get("MolecularFormula", "")
                molecular_weight = pubchem_data.get("MolecularWeight", "")
                cas_number = fetch_cas_number_from_pubchem_cid(pubchem_cid)

                if not pubchem_smiles:
                    st.session_state.final_smiles = generated_smiles
                    st.session_state.smiles_source = "LLM"

                    st.session_state.pubchem_validation = pubchem_data
                    st.session_state.pubchem_smiles = ""

                    st.warning("PubChem found the molecule, but did not return a SMILES.")
                    st.warning("The app will use the generated SMILES instead.")

                    with st.expander("Debug PubChem response"):
                        st.json(pubchem_data)

                else:
                    st.session_state.final_smiles = pubchem_smiles
                    st.session_state.smiles_source = "PubChem"

                    st.session_state.pubchem_cid = pubchem_cid
                    st.session_state.pubchem_name = molecule_name
                    st.session_state.pubchem_iupac_name = pubchem_iupac_name
                    st.session_state.pubchem_smiles = pubchem_smiles
                    st.session_state.molecular_formula = molecular_formula
                    st.session_state.molecular_weight = molecular_weight
                    st.session_state.cas_number = cas_number

                    st.session_state.pubchem_validation = {
                        "cid": pubchem_cid,
                        "pubchem_name": molecule_name,
                        "iupac_name": pubchem_iupac_name,
                        "smiles": pubchem_data.get("SMILES", ""),
                        "connectivity_smiles": pubchem_data.get("ConnectivitySMILES", ""),
                        "pubchem_smiles": pubchem_smiles,
                        "molecular_formula": molecular_formula,
                        "molecular_weight": molecular_weight,
                        "cas_number": cas_number,
                    }

                    st.success("PubChem SMILES found. The app will use PubChem.")
                    st.subheader("PubChem SMILES")
                    st.code(pubchem_smiles)

        except Exception as e:
            st.session_state.final_smiles = generated_smiles
            st.session_state.smiles_source = "LLM"

            st.session_state.pubchem_validation = None
            st.session_state.pubchem_smiles = ""

            st.warning("PubChem failed. The app will use the generated SMILES.")
            st.write(e)

    sync_molecule_record_from_session(st)

    st.divider()

    st.subheader("Selected SMILES for 3D Visualization")

    if st.session_state.final_smiles:
        st.success(f"Using: {st.session_state.smiles_source}")
        st.code(st.session_state.final_smiles)
    else:
        st.info("No final SMILES selected yet.")

    st.divider()
    display_molecule_record(st)



def render_supplier_suggestions_tab():
    st.header("Supplier Suggestions")
    st.subheader("Find reputable supplier search links")

    sync_molecule_record_from_session(st)

    molecule_name = get_canonical_name(st)
    smiles = get_canonical_smiles(st)
    cas_number = st.session_state.get("cas_number", "")
    session_id = st.session_state.get("session_id", "")

    if not molecule_name and not smiles:
        st.info("Generate and validate a molecule first.")
        return

    st.warning(
        "Supplier suggestions are informational only. ReagentScout does not sell chemicals, "
        "process orders, verify eligibility, or replace supplier safety and compliance checks."
    )

    st.subheader("Current Molecule")

    if molecule_name:
        st.write("**Molecule name:**")
        st.code(molecule_name)

    if smiles:
        st.write("**Selected SMILES:**")
        st.code(smiles)

    if cas_number:
        st.write("**CAS number:**")
        st.code(cas_number)

    region = st.selectbox(
        "Country / region",
        ["Switzerland", "EU", "US", "Canada", "Other"],
    )

    user_type = st.selectbox(
        "User type",
        ["Student", "Teacher", "Hobbyist", "Professional"],
    )

    quantity = st.selectbox(
        "Approximate quantity",
        ["Not sure", "mg", "g", "kg", "bulk"],
    )

    # -------------------------------------------------------------------------
    # Track Supplier Suggestions tab view once per session / molecule / settings
    # -------------------------------------------------------------------------
    supplier_tab_event_key = (
        f"supplier_tab_viewed_"
        f"{session_id}_"
        f"{molecule_name}_"
        f"{cas_number}_"
        f"{region}_"
        f"{user_type}_"
        f"{quantity}"
    )

    supplier_tab_event_key = "".join(
        char if char.isalnum() else "_"
        for char in supplier_tab_event_key.lower()
    )

    if not st.session_state.get(supplier_tab_event_key):
        track_app_event(
            session_id=session_id,
            event_type="supplier_tab_viewed",
            molecule_name=molecule_name,
            smiles=smiles,
            cas_number=cas_number,
            region=region,
            user_type=user_type,
            quantity=quantity,
        )

        st.session_state[supplier_tab_event_key] = True

    st.divider()

    # -------------------------------------------------------------------------
    # Safety and suitability gate
    # -------------------------------------------------------------------------
    risk_result = classify_sourcing_risk(
        molecule_name=molecule_name,
        smiles=smiles,
        user_type=user_type,
    )

    display_sourcing_risk(st, risk_result)

    # -------------------------------------------------------------------------
    # Track blocked supplier-link cases
    # -------------------------------------------------------------------------
    if not risk_result.get("show_supplier_links"):
        blocked_event_key = (
            f"supplier_links_blocked_"
            f"{session_id}_"
            f"{molecule_name}_"
            f"{cas_number}_"
            f"{region}_"
            f"{user_type}_"
            f"{quantity}_"
            f"{risk_result.get('risk_level')}"
        )

        blocked_event_key = "".join(
            char if char.isalnum() else "_"
            for char in blocked_event_key.lower()
        )

        if not st.session_state.get(blocked_event_key):
            track_app_event(
                session_id=session_id,
                event_type="supplier_links_blocked",
                molecule_name=molecule_name,
                smiles=smiles,
                cas_number=cas_number,
                region=region,
                user_type=user_type,
                quantity=quantity,
                risk_level=risk_result.get("risk_level"),
            )

            st.session_state[blocked_event_key] = True

        st.caption(
            "No supplier links are shown for this molecule/user-type combination."
        )
        return

    st.divider()

    # -------------------------------------------------------------------------
    # Supplier search queries
    # Priority: CAS number -> molecule name -> SMILES
    # -------------------------------------------------------------------------
    primary_query = cas_number or molecule_name or smiles
    backup_query = molecule_name or smiles

    encoded_primary_query = quote_plus(primary_query)

    encoded_backup_query = None
    if backup_query:
        encoded_backup_query = quote_plus(backup_query)

    st.caption(f"Primary supplier search query: {primary_query}")

    if backup_query and backup_query != primary_query:
        st.caption(f"Backup supplier search query: {backup_query}")

    # -------------------------------------------------------------------------
    # Find suppliers that match the selected region and user type
    # -------------------------------------------------------------------------
    matching_suppliers = []

    for supplier in SUPPLIERS:
        region_match = region in supplier["regions"] or region == "Other"
        user_match = user_type in supplier["user_types"]

        if region_match and user_match:
            matching_suppliers.append(supplier)

    if not matching_suppliers:
        st.info("No supplier suggestions found for this region and user type yet.")
        return

    st.subheader("Suggested supplier searches")

    st.info(
        "Supplier links are generated search links. Some supplier websites search better "
        "by CAS number, while others search better by molecule name. ReagentScout provides "
        "both options when available."
    )

    # -------------------------------------------------------------------------
    # Render supplier cards
    # -------------------------------------------------------------------------
    for supplier in matching_suppliers:
        supplier_url_primary = supplier["search_url_template"].format(
            query=encoded_primary_query
        )

        supplier_url_backup = None
        if encoded_backup_query:
            supplier_url_backup = supplier["search_url_template"].format(
                query=encoded_backup_query
            )

        supplier_key_raw = (
            f"{supplier['name']}_{region}_{user_type}_{primary_query}"
        )

        supplier_key_clean = "".join(
            char if char.isalnum() else "_"
            for char in supplier_key_raw.lower()
        )

        supplier_key = f"supplier_link_ready_{supplier_key_clean}"

        with st.container(border=True):
            st.markdown(f"### {supplier['name']}")
            st.write(f"**Category:** {supplier['category']}")
            st.write(
                f"**Supplier type:** "
                f"{supplier.get('supplier_type', 'Not specified')}"
            )
            st.write(f"**Regions:** {', '.join(supplier['regions'])}")
            st.write(f"**User type:** {user_type}")
            st.write(f"**Quantity selected:** {quantity}")
            st.write(f"**Primary query:** {primary_query}")

            if backup_query and backup_query != primary_query:
                st.write(f"**Backup query:** {backup_query}")

            if st.button(
                label=f"Prepare supplier search for {supplier['name']}",
                key=f"prepare_{supplier_key}",
            ):
                track_supplier_click(
                    session_id=session_id,
                    molecule_name=molecule_name,
                    smiles=smiles,
                    cas_number=cas_number,
                    supplier_name=supplier["name"],
                    supplier_url=supplier_url_primary,
                    region=region,
                    user_type=user_type,
                    quantity=quantity,
                    risk_level=risk_result.get("risk_level"),
                )

                st.session_state[supplier_key] = True

                st.success(
                    f"Supplier search prepared and tracked for {supplier['name']}."
                )

            if st.session_state.get(supplier_key):
                st.link_button(
                    label=f"Open {supplier['name']} search by CAS / primary query",
                    url=supplier_url_primary,
                )

                if (
                    supplier_url_backup
                    and backup_query
                    and backup_query != primary_query
                ):
                    st.link_button(
                        label=f"Open {supplier['name']} search by molecule name",
                        url=supplier_url_backup,
                    )

    # -------------------------------------------------------------------------
    # Sourcing-interest form
    # -------------------------------------------------------------------------
    st.divider()

    st.subheader("Request sourcing help")

    st.warning(
        "Beta data notice: this form records your sourcing-interest request locally for "
        "testing and product-validation purposes. Do not submit confidential, regulated, "
        "proprietary, or sensitive information. This does not place an order, does not "
        "confirm availability, and does not replace supplier compliance checks."
    )

    st.caption(
        "Optional beta feature: record sourcing interest for this molecule. "
        "This does not place an order and does not guarantee supplier availability."
    )

    with st.form("sourcing_interest_form"):
        purity = st.selectbox(
            "Requested purity",
            [
                "Not sure",
                "Technical grade",
                "95%+",
                "97%+",
                "98%+",
                "99%+",
                "Analytical standard",
            ],
        )

        intended_use = st.selectbox(
            "Intended use",
            [
                "Research",
                "Education",
                "Analytical standard",
                "Commercial evaluation",
                "Other",
            ],
        )

        institution = st.text_input(
            "Institution / company",
            placeholder="University, school, company, or lab name",
        )

        contact_email = st.text_input(
            "Contact email",
            placeholder="name@example.com",
        )

        notes = st.text_area(
            "Notes",
            placeholder=(
                "Optional: packaging size, delivery country, supplier preference, "
                "deadline, etc."
            ),
        )

        authorized_confirmation = st.checkbox(
            "I confirm that I am responsible for checking authorization, safety "
            "requirements, institutional rules, and local regulations."
        )

        beta_data_confirmation = st.checkbox(
            "I understand that this beta form records the submitted information locally "
            "for testing and product-validation purposes, and I will not submit confidential, "
            "regulated, proprietary, or sensitive information."
        )

        submitted = st.form_submit_button("Submit sourcing-interest request")

        if submitted:
            if not contact_email:
                st.error("Please enter a contact email.")
            elif "@" not in contact_email:
                st.error("Please enter a valid email address.")
            elif not authorized_confirmation:
                st.error(
                    "Please confirm that you are responsible for authorization, "
                    "safety, and regulatory checks."
                )
            elif not beta_data_confirmation:
                st.error(
                    "Please confirm that you understand the beta data notice."
                )
            else:
                track_sourcing_request(
                    session_id=session_id,
                    molecule_name=molecule_name,
                    smiles=smiles,
                    cas_number=cas_number,
                    region=region,
                    user_type=user_type,
                    quantity=quantity,
                    purity=purity,
                    intended_use=intended_use,
                    contact_email=contact_email,
                    institution=institution,
                    notes=notes,
                    risk_level=risk_result.get("risk_level"),
                )

                st.success(
                    "Sourcing-interest request saved locally. No order has been placed."
                )

    # -------------------------------------------------------------------------
    # MVP note
    # -------------------------------------------------------------------------
    st.divider()

    st.caption(
        "MVP note: these are generated search links, not live inventory checks. "
        "Later versions can add PubChem safety data, ECHA/OSHA/regulatory checks, "
        "supplier APIs, sponsored placement, and sponsored supplier ranking."
    )

    # -------------------------------------------------------------------------
    # Analytics summary and CSV downloads
    # Only visible in developer mode
    # -------------------------------------------------------------------------
    if DEV_MODE:
        st.divider()

        with st.expander("MVP analytics"):
            st.write("App events and supplier-search intent are saved locally.")

            summary = get_beta_analytics_summary()

            st.subheader("Beta summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Supplier tab views",
                    summary["supplier_tab_view_count"],
                )

            with col2:
                st.metric(
                    "Supplier search intents",
                    summary["supplier_search_intent_count"],
                )

            with col3:
                st.metric(
                    "Sourcing requests",
                    summary["sourcing_request_count"],
                )

            with col4:
                st.metric(
                    "Blocked supplier cases",
                    summary["supplier_links_blocked_count"],
                )

            col5, col6, col7 = st.columns(3)

            with col5:
                st.metric(
                    "Intent conversion rate",
                    f"{summary['event_conversion_rate']}%",
                )

            with col6:
                st.metric(
                    "Sourcing request rate",
                    f"{summary['sourcing_request_event_rate']}%",
                )

            with col7:
                st.metric(
                    "Blocked event rate",
                    f"{summary['blocked_event_rate']}%",
                )

            col8, col9, col10, col11 = st.columns(4)

            with col8:
                st.metric(
                    "Unique supplier-tab sessions",
                    summary["unique_supplier_tab_sessions"],
                )

            with col9:
                st.metric(
                    "Unique intent sessions",
                    summary["unique_supplier_intent_sessions"],
                )

            with col10:
                st.metric(
                    "Unique sourcing sessions",
                    summary["unique_sourcing_request_sessions"],
                )

            with col11:
                st.metric(
                    "Unique blocked sessions",
                    summary["unique_blocked_sessions"],
                )

            col12, col13 = st.columns(2)

            with col12:
                st.metric(
                    "Session intent rate",
                    f"{summary['session_conversion_rate']}%",
                )

            with col13:
                st.metric(
                    "Session sourcing-request rate",
                    f"{summary['sourcing_request_session_rate']}%",
                )

            st.divider()

            def display_count_table(title, count_dict):
                st.write(f"**{title}**")

                if not count_dict:
                    st.caption("No data yet.")
                    return

                table_rows = [
                    {
                        "Value": value,
                        "Count": count,
                    }
                    for value, count in count_dict.items()
                ]

                st.table(table_rows)

            st.subheader("Supplier-search intent")

            display_count_table(
                "Supplier intent by user type",
                summary["supplier_intent_by_user_type"],
            )

            display_count_table(
                "Supplier intent by region",
                summary["supplier_intent_by_region"],
            )

            display_count_table(
                "Supplier intent by molecule",
                summary["supplier_intent_by_molecule"],
            )

            display_count_table(
                "Supplier intent by supplier",
                summary["supplier_intent_by_supplier"],
            )

            st.divider()

            st.subheader("Sourcing requests")

            display_count_table(
                "Sourcing requests by user type",
                summary["sourcing_requests_by_user_type"],
            )

            display_count_table(
                "Sourcing requests by region",
                summary["sourcing_requests_by_region"],
            )

            display_count_table(
                "Sourcing requests by molecule",
                summary["sourcing_requests_by_molecule"],
            )

            display_count_table(
                "Sourcing requests by purity",
                summary["sourcing_requests_by_purity"],
            )

            display_count_table(
                "Sourcing requests by intended use",
                summary["sourcing_requests_by_intended_use"],
            )

            st.divider()

            st.subheader("Blocked supplier-link cases")

            display_count_table(
                "Blocked cases by user type",
                summary["blocked_by_user_type"],
            )

            display_count_table(
                "Blocked cases by region",
                summary["blocked_by_region"],
            )

            display_count_table(
                "Blocked cases by molecule",
                summary["blocked_by_molecule"],
            )

            display_count_table(
                "Blocked cases by risk level",
                summary["blocked_by_risk_level"],
            )

            st.divider()

            app_events_file = get_app_events_file_path()
            supplier_events_file = get_supplier_events_file_path()
            sourcing_requests_file = get_sourcing_requests_file_path()

            st.write("**App events file:**")
            st.code(app_events_file)

            if os.path.exists(app_events_file):
                with open(app_events_file, "rb") as file:
                    st.download_button(
                        label="Download app events CSV",
                        data=file,
                        file_name="app_events.csv",
                        mime="text/csv",
                        key="download_app_events_csv",
                    )
            else:
                st.info("No app events recorded yet.")

            st.write("**Supplier events file:**")
            st.code(supplier_events_file)

            if os.path.exists(supplier_events_file):
                with open(supplier_events_file, "rb") as file:
                    st.download_button(
                        label="Download supplier events CSV",
                        data=file,
                        file_name="supplier_events.csv",
                        mime="text/csv",
                        key="download_supplier_events_csv",
                    )
            else:
                st.info("No supplier events recorded yet.")

            st.write("**Sourcing requests file:**")
            st.code(sourcing_requests_file)

            if os.path.exists(sourcing_requests_file):
                with open(sourcing_requests_file, "rb") as file:
                    st.download_button(
                        label="Download sourcing requests CSV",
                        data=file,
                        file_name="sourcing_requests.csv",
                        mime="text/csv",
                        key="download_sourcing_requests_csv",
                    )
            else:
                st.info("No sourcing requests recorded yet.")

        
def reset_validation_state():
    st.session_state.pubchem_validation = None
    st.session_state.final_smiles = ""
    st.session_state.smiles_source = ""

def render_sidebar_status_panel():

    with st.sidebar:
        st.markdown("## Status Panel")
        st.divider()

        # ------------------------------------------------------------
        # Read current state
        # ------------------------------------------------------------
        selected_model = st.session_state.get("selected_model")
        molecule_name = st.session_state.get("molecule_name", "").strip()
        smiles = st.session_state.get("smiles", "").strip()
        final_smiles = st.session_state.get("final_smiles", "").strip()
        smiles_source = st.session_state.get("smiles_source", "").strip()

        model_done = bool(selected_model)
        name_done = bool(molecule_name)
        smiles_done = bool(smiles)
        final_smiles_done = bool(final_smiles)

        pubchem_used = smiles_source.lower().startswith("pubchem")
        generated_used = smiles_source.lower().startswith("generated")

        # ------------------------------------------------------------
        # Current molecule
        # ------------------------------------------------------------
        st.markdown("### Current Molecule")

        if molecule_name:
            st.success(molecule_name)
        else:
            st.info("No molecule selected yet.")

        # ------------------------------------------------------------
        # Progress
        # ------------------------------------------------------------
        total_steps = 5
        completed_steps = sum(
            [
                model_done,
                name_done,
                smiles_done,
                final_smiles_done,
                final_smiles_done,
            ]
        )

        st.progress(completed_steps / total_steps)

        # ------------------------------------------------------------
        # Workflow status
        # ------------------------------------------------------------
        st.markdown("### Workflow Status")

        st.markdown("✅ AI model selected" if model_done else "⬜ AI model selected")
        st.markdown("✅ Name identified" if name_done else "⬜ Name identified")
        st.markdown("✅ SMILES generated" if smiles_done else "⬜ SMILES generated")

        if pubchem_used and final_smiles_done:
            st.markdown("✅ PubChem validated")
        elif generated_used and final_smiles_done:
            st.markdown("⚠️ PubChem fallback used")
        elif smiles_done:
            st.markdown("⬜ PubChem not checked")
        else:
            st.markdown("⬜ PubChem validation")

        st.markdown(
            "✅ Ready for 2D diagram"
            if final_smiles_done
            else "⬜ Ready for 2D diagram"
        )

        st.markdown(
            "✅ Ready for 3D viewer"
            if final_smiles_done
            else "⬜ Ready for 3D viewer"
        )

        # ------------------------------------------------------------
        # SMILES source
        # ------------------------------------------------------------
        st.divider()

        st.markdown("### SMILES Source")

        if pubchem_used:
            st.success(smiles_source)
        elif generated_used:
            st.warning(smiles_source)
        else:
            st.info("Not selected yet.")

        # ------------------------------------------------------------
        # Selected SMILES
        # ------------------------------------------------------------
        if final_smiles:
            with st.expander("Show selected SMILES"):
                st.code(final_smiles)

        # ------------------------------------------------------------
        # Reset button
        # ------------------------------------------------------------
        st.divider()

        if st.button("Reset Molecule"):
            st.session_state.molecule_name = ""
            st.session_state.molecule_confidence = None
            st.session_state.molecule_explanation = ""

            st.session_state.smiles = ""
            st.session_state.smiles_confidence = None
            st.session_state.smiles_explanation = ""

            st.session_state.pubchem_validation = None
            st.session_state.final_smiles = ""
            st.session_state.smiles_source = ""

            st.rerun()


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide"
)



# Default session state


st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON)

initialize_session_state(st)
sync_molecule_record_from_session(st)

st.markdown(PAGE_HEADER)

with st.expander("Beta / limitations", expanded=False):
    st.markdown(BETA_NOTICE)


tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "AI Model",
        "Molecule Identification",
        "SMILES Generation",
        "PubChem Validation",
        "2D Structure",
        "3D Visualization",
        "Supplier Suggestions",
    ]
)
with tab0:
    render_model_selection_tab()

with tab1:
    render_molecule_name_tab(client)

with tab2:
    render_smiles_generation_tab(client)

with tab3:
    render_pubchem_validation_tab()

with tab4:
    render_2d_structure_tab()

with tab5:
    render_3d_visualization_tab()

with tab6:
    render_supplier_suggestions_tab()

# Sidebar status panel
render_sidebar_status_panel()
