APP_TITLE = "ReagentScout"
APP_ICON = "🧭"

DEFAULT_MODEL = "gpt-4.1-mini"

DEV_MODE = False

AVAILABLE_MODELS = [
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4.1",
    "gpt-4o-mini",
    "gpt-4o",
]

PAGE_HEADER = """
# 🧭 ReagentScout
### Molecule discovery, validation, visualization, and supplier guidance
"""

BETA_NOTICE = """
### ⚠️ Beta / limitations

ReagentScout is an experimental tool. Molecule identification, SMILES generation, PubChem validation, safety classification, and supplier suggestions may be incomplete or incorrect.

Supplier links are generated search links only. ReagentScout does not sell chemicals, process orders, verify eligibility, confirm inventory, or replace supplier, institutional, legal, or safety checks.

Always verify molecule identity, CAS number, SDS information, local regulations, and supplier requirements before taking action.
"""