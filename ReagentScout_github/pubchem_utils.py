# pubchem_utils.py

import re
import requests


CAS_REGEX = re.compile(r"^\d{2,7}-\d{2}-\d$")


def is_valid_cas_number(value):
    """
    Basic CAS number format check.

    Examples:
    Aspirin: 50-78-2
    Caffeine: 58-08-2
    Paracetamol / Acetaminophen: 103-90-2
    """

    if not value:
        return False

    value = str(value).strip()

    return bool(CAS_REGEX.match(value))


def extract_cas_from_synonyms(synonyms):
    """
    Extracts the first CAS-like identifier from a PubChem synonym list.
    """

    if not synonyms:
        return ""

    for synonym in synonyms:
        synonym = str(synonym).strip()

        if is_valid_cas_number(synonym):
            return synonym

    return ""


def fetch_cas_number_from_pubchem_cid(cid):
    """
    Fetches PubChem synonyms using a PubChem CID and extracts a CAS number.

    Returns:
        CAS number as a string if found.
        Empty string if not found.
    """

    if not cid:
        return ""

    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
        + str(cid)
        + "/synonyms/JSON"
    )

    try:
        response = requests.get(url, timeout=15)
        data = response.json()

        synonyms = (
            data.get("InformationList", {})
            .get("Information", [{}])[0]
            .get("Synonym", [])
        )

        return extract_cas_from_synonyms(synonyms)

    except Exception:
        return ""