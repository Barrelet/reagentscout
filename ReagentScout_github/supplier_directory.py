# supplier_directory.py

"""
Supplier directory for ReagentScout.

MVP purpose:
- Provide reputable supplier search links.
- Categorize suppliers by region, user type, and supplier type.
- Keep this simple and editable for now.

Important:
These are generated search links, not live inventory integrations.
"""


SUPPLIERS = [
    {
        "name": "Sigma-Aldrich",
        "regions": ["Switzerland", "EU", "US", "Canada"],
        "user_types": ["Teacher", "Professional"],
        "category": "Research chemicals and laboratory reagents",
        "supplier_type": "Large research chemical supplier",
        "search_url_template": "https://www.sigmaaldrich.com/CH/en/search/{query}?focus=products",
    },
    {
        "name": "Fisher Scientific",
        "regions": ["US", "Canada", "EU"],
        "user_types": ["Teacher", "Professional"],
        "category": "Laboratory reagents, chemicals, and lab supplies",
        "supplier_type": "Large lab supplies distributor",
        "search_url_template": "https://www.fishersci.com/us/en/catalog/search/products?keyword={query}",
    },
    {
        "name": "TCI Chemicals",
        "regions": ["Switzerland", "EU", "US"],
        "user_types": ["Professional"],
        "category": "Specialty research chemicals and organic compounds",
        "supplier_type": "Specialty chemical supplier",
        "search_url_template": "https://www.tcichemicals.com/CH/en/search?q={query}",
    },
    {
        "name": "Carl Roth",
        "regions": ["Switzerland", "EU"],
        "user_types": ["Teacher", "Professional"],
        "category": "Laboratory chemicals, reagents, and life science products",
        "supplier_type": "European lab reagent supplier",
        "search_url_template": "https://www.carlroth.com/com/en/search?text={query}",
    },
    {
        "name": "VWR / Avantor",
        "regions": ["Switzerland", "EU", "US", "Canada"],
        "user_types": ["Teacher", "Professional"],
        "category": "Lab supplies, reagents, and research chemicals",
        "supplier_type": "Large lab supplies distributor",
        "search_url_template": "https://www.vwr.com/store/product?keyword={query}",
    },
    {
        "name": "Alfa Aesar",
        "regions": ["EU", "US", "Canada"],
        "user_types": ["Professional"],
        "category": "Research chemicals, metals, catalysts, and specialty materials",
        "supplier_type": "Specialty research chemical supplier",
        "search_url_template": "https://www.alfa.com/en/search/?q={query}",
    },
    {
        "name": "Apollo Scientific",
        "regions": ["EU"],
        "user_types": ["Professional"],
        "category": "Specialty research chemicals and building blocks",
        "supplier_type": "Specialty chemical supplier",
        "search_url_template": "https://www.apolloscientific.co.uk/search?q={query}",
    },
    {
        "name": "Cayman Chemical",
        "regions": ["US", "EU"],
        "user_types": ["Professional"],
        "category": "Biochemicals, analytical standards, and research compounds",
        "supplier_type": "Analytical standards and life science supplier",
        "search_url_template": "https://www.caymanchem.com/search?query={query}",
    },
]