# safety_classifier.py


def classify_sourcing_risk(molecule_name, smiles, user_type):
    """
    Simple MVP sourcing-risk classifier.

    This is not a legal or regulatory determination.
    It is a conservative safety gate for whether ReagentScout should show
    direct supplier search links.
    """

    molecule_text = f"{molecule_name or ''} {smiles or ''}".lower()

    high_risk_keywords = [
        "cyanide",
        "azide",
        "picric acid",
        "nitric acid",
        "perchloric acid",
        "hydrogen peroxide",
        "ammonium nitrate",
        "potassium nitrate",
        "sodium nitrate",
        "chloroform",
        "benzene",
        "diethyl ether",
        "sodium metal",
        "potassium metal",
        "phosgene",
        "thionyl chloride",
        "acetyl chloride",
        "sulfuric acid",
        "hydrochloric acid",
    ]

    controlled_or_sensitive_keywords = [
        "pseudoephedrine",
        "ephedrine",
        "fentanyl",
        "morphine",
        "amphetamine",
        "methamphetamine",
        "cocaine",
        "lsd",
        "mdma",
        "ghb",
    ]

    common_low_risk_keywords = [
        "caffeine",
        "aspirin",
        "paracetamol",
        "acetaminophen",
        "ibuprofen",
        "glucose",
        "sucrose",
        "citric acid",
        "ascorbic acid",
        "coumarin",
    ]

    # -------------------------------------------------------------------------
    # Controlled / sensitive substances
    # -------------------------------------------------------------------------
    if any(term in molecule_text for term in controlled_or_sensitive_keywords):
        return {
            "risk_level": "blocked",
            "show_supplier_links": False,
            "title": "Supplier links blocked",
            "message": (
                "This molecule appears to be controlled, sensitive, or inappropriate "
                "for general sourcing suggestions. ReagentScout will not show supplier links."
            ),
        }

    # -------------------------------------------------------------------------
    # High-risk or hazardous substances
    # -------------------------------------------------------------------------
    if any(term in molecule_text for term in high_risk_keywords):
        if user_type == "Professional":
            return {
                "risk_level": "high_caution",
                "show_supplier_links": True,
                "title": "Professional-use caution",
                "message": (
                    "This molecule may be hazardous, restricted, or unsuitable for general users. "
                    "Supplier links are shown only for professional use and must be checked against "
                    "local laws, institutional rules, SDS documents, and supplier eligibility requirements."
                ),
            }

        return {
            "risk_level": "blocked",
            "show_supplier_links": False,
            "title": "Supplier links not shown",
            "message": (
                "This molecule may be hazardous, restricted, or unsuitable for general users. "
                "ReagentScout does not show supplier links for this user type."
            ),
        }

    # -------------------------------------------------------------------------
    # Students and hobbyists
    # -------------------------------------------------------------------------
    if user_type in ["Student", "Hobbyist"]:
        return {
            "risk_level": "educational_only",
            "show_supplier_links": False,
            "title": "Educational use only",
            "message": (
                "For students and hobbyists, ReagentScout currently provides molecule identity "
                "and visualization only. Direct supplier links are not shown."
            ),
        }

    # -------------------------------------------------------------------------
    # Common low-risk molecules
    # -------------------------------------------------------------------------
    if any(term in molecule_text for term in common_low_risk_keywords):
        return {
            "risk_level": "standard",
            "show_supplier_links": True,
            "title": "Standard sourcing guidance",
            "message": (
                "This appears to be a common molecule. Supplier search links are shown "
                "for informational purposes only."
            ),
        }

    # -------------------------------------------------------------------------
    # Default case
    # -------------------------------------------------------------------------
    return {
        "risk_level": "standard_caution",
        "show_supplier_links": True,
        "title": "Standard caution",
        "message": (
            "ReagentScout does not detect an obvious high-risk flag, but users must still "
            "check SDS documents, local regulations, and supplier eligibility requirements."
        ),
    }


def display_sourcing_risk(st, risk_result):
    """
    Displays the safety/suitability gate result in Streamlit.
    """

    risk_level = risk_result.get("risk_level")
    title = risk_result.get("title", "Sourcing guidance")
    message = risk_result.get("message", "")

    if risk_level == "blocked":
        st.error(f"{title}: {message}")

    elif risk_level in ["high_caution", "standard_caution"]:
        st.warning(f"{title}: {message}")

    elif risk_level == "educational_only":
        st.info(f"{title}: {message}")

    else:
        st.success(f"{title}: {message}")