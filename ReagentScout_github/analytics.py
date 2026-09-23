# analytics.py

import csv
import os
from datetime import datetime, timezone


DATA_DIR = "data"
SUPPLIER_EVENTS_FILE = os.path.join(DATA_DIR, "supplier_events.csv")
APP_EVENTS_FILE = os.path.join(DATA_DIR, "app_events.csv")
SOURCING_REQUESTS_FILE = os.path.join(DATA_DIR, "sourcing_requests.csv")


def ensure_data_dir():
    """
    Creates the local data directory if it does not already exist.
    """

    os.makedirs(DATA_DIR, exist_ok=True)


def write_event_to_csv(file_path, event):
    """
    Appends an event dictionary to a CSV file.
    Creates headers automatically if the file does not exist.
    """

    ensure_data_dir()

    file_exists = os.path.exists(file_path)

    with open(file_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=event.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(event)


def read_csv_rows(file_path):
    """
    Safely reads rows from a CSV file.
    Returns an empty list if the file does not exist yet.
    """

    if not os.path.exists(file_path):
        return []

    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def count_values(rows, column_name):
    """
    Counts values in a list of CSV rows.
    Used for simple local analytics summaries.
    """

    counts = {}

    for row in rows:
        value = row.get(column_name, "")

        if not value:
            value = "Unknown"

        counts[value] = counts.get(value, 0) + 1

    return dict(
        sorted(
            counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )


def calculate_percentage(numerator, denominator):
    """
    Calculates a percentage safely.
    """

    if denominator == 0:
        return 0.0

    return round((numerator / denominator) * 100, 1)


def track_app_event(
    session_id,
    event_type,
    molecule_name="",
    smiles="",
    cas_number="",
    region="",
    user_type="",
    quantity="",
    risk_level="",
):
    """
    Tracks general app events.

    Examples:
    - supplier_tab_viewed
    - molecule_validated
    - supplier_links_blocked
    """

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id or "",
        "event_type": event_type or "",
        "molecule_name": molecule_name or "",
        "smiles": smiles or "",
        "cas_number": cas_number or "",
        "region": region or "",
        "user_type": user_type or "",
        "quantity": quantity or "",
        "risk_level": risk_level or "",
    }

    write_event_to_csv(APP_EVENTS_FILE, event)


def track_supplier_click(
    session_id,
    molecule_name,
    smiles,
    cas_number,
    supplier_name,
    supplier_url,
    region,
    user_type,
    quantity,
    risk_level,
):
    """
    Tracks supplier-search intent.

    MVP note:
    In Streamlit, this tracks when a user requests/prepares a supplier link.
    It is not yet a true external-site click tracker.
    """

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id or "",
        "event_type": "supplier_search_intent",
        "molecule_name": molecule_name or "",
        "smiles": smiles or "",
        "cas_number": cas_number or "",
        "supplier_name": supplier_name or "",
        "supplier_url": supplier_url or "",
        "region": region or "",
        "user_type": user_type or "",
        "quantity": quantity or "",
        "risk_level": risk_level or "",
    }

    write_event_to_csv(SUPPLIER_EVENTS_FILE, event)


def get_supplier_events_file_path():
    """
    Returns the path to the local supplier-events CSV file.
    """

    ensure_data_dir()
    return SUPPLIER_EVENTS_FILE


def get_app_events_file_path():
    """
    Returns the path to the local app-events CSV file.
    """

    ensure_data_dir()
    return APP_EVENTS_FILE

def get_beta_analytics_summary():
    """
    Returns a simple local analytics summary for the ReagentScout beta.

    Key metrics:
    - supplier_search_intent / supplier_tab_viewed
    - supplier_links_blocked / supplier_tab_viewed
    - sourcing_request_submitted / supplier_tab_viewed
    """

    app_rows = read_csv_rows(APP_EVENTS_FILE)
    supplier_rows = read_csv_rows(SUPPLIER_EVENTS_FILE)
    sourcing_rows = read_csv_rows(SOURCING_REQUESTS_FILE)

    supplier_tab_views = [
        row for row in app_rows
        if row.get("event_type") == "supplier_tab_viewed"
    ]

    supplier_links_blocked = [
        row for row in app_rows
        if row.get("event_type") == "supplier_links_blocked"
    ]

    supplier_search_intents = [
        row for row in supplier_rows
        if row.get("event_type") == "supplier_search_intent"
    ]

    sourcing_requests = [
        row for row in sourcing_rows
        if row.get("event_type") == "sourcing_request_submitted"
    ]

    supplier_tab_sessions = {
        row.get("session_id")
        for row in supplier_tab_views
        if row.get("session_id")
    }

    supplier_blocked_sessions = {
        row.get("session_id")
        for row in supplier_links_blocked
        if row.get("session_id")
    }

    supplier_intent_sessions = {
        row.get("session_id")
        for row in supplier_search_intents
        if row.get("session_id")
    }

    sourcing_request_sessions = {
        row.get("session_id")
        for row in sourcing_requests
        if row.get("session_id")
    }

    summary = {
        "app_event_count": len(app_rows),

        "supplier_tab_view_count": len(supplier_tab_views),
        "supplier_links_blocked_count": len(supplier_links_blocked),
        "supplier_search_intent_count": len(supplier_search_intents),
        "sourcing_request_count": len(sourcing_requests),

        "unique_supplier_tab_sessions": len(supplier_tab_sessions),
        "unique_blocked_sessions": len(supplier_blocked_sessions),
        "unique_supplier_intent_sessions": len(supplier_intent_sessions),
        "unique_sourcing_request_sessions": len(sourcing_request_sessions),

        "event_conversion_rate": calculate_percentage(
            len(supplier_search_intents),
            len(supplier_tab_views),
        ),

        "session_conversion_rate": calculate_percentage(
            len(supplier_intent_sessions),
            len(supplier_tab_sessions),
        ),

        "blocked_event_rate": calculate_percentage(
            len(supplier_links_blocked),
            len(supplier_tab_views),
        ),

        "blocked_session_rate": calculate_percentage(
            len(supplier_blocked_sessions),
            len(supplier_tab_sessions),
        ),

        "sourcing_request_event_rate": calculate_percentage(
            len(sourcing_requests),
            len(supplier_tab_views),
        ),

        "sourcing_request_session_rate": calculate_percentage(
            len(sourcing_request_sessions),
            len(supplier_tab_sessions),
        ),

        "supplier_intent_by_user_type": count_values(
            supplier_search_intents,
            "user_type",
        ),

        "supplier_intent_by_region": count_values(
            supplier_search_intents,
            "region",
        ),

        "supplier_intent_by_molecule": count_values(
            supplier_search_intents,
            "molecule_name",
        ),

        "supplier_intent_by_supplier": count_values(
            supplier_search_intents,
            "supplier_name",
        ),

        "blocked_by_user_type": count_values(
            supplier_links_blocked,
            "user_type",
        ),

        "blocked_by_region": count_values(
            supplier_links_blocked,
            "region",
        ),

        "blocked_by_molecule": count_values(
            supplier_links_blocked,
            "molecule_name",
        ),

        "blocked_by_risk_level": count_values(
            supplier_links_blocked,
            "risk_level",
        ),

        "sourcing_requests_by_user_type": count_values(
            sourcing_requests,
            "user_type",
        ),

        "sourcing_requests_by_region": count_values(
            sourcing_requests,
            "region",
        ),

        "sourcing_requests_by_molecule": count_values(
            sourcing_requests,
            "molecule_name",
        ),

        "sourcing_requests_by_purity": count_values(
            sourcing_requests,
            "purity",
        ),

        "sourcing_requests_by_intended_use": count_values(
            sourcing_requests,
            "intended_use",
        ),
    }

    return summary


def track_sourcing_request(
    session_id,
    molecule_name,
    smiles,
    cas_number,
    region,
    user_type,
    quantity,
    purity,
    intended_use,
    contact_email,
    institution,
    notes,
    risk_level,
):
    """
    Tracks a local sourcing-interest request.

    MVP note:
    This does not place an order.
    It only records that a user expressed sourcing interest.
    """

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id or "",
        "event_type": "sourcing_request_submitted",
        "molecule_name": molecule_name or "",
        "smiles": smiles or "",
        "cas_number": cas_number or "",
        "region": region or "",
        "user_type": user_type or "",
        "quantity": quantity or "",
        "purity": purity or "",
        "intended_use": intended_use or "",
        "contact_email": contact_email or "",
        "institution": institution or "",
        "notes": notes or "",
        "risk_level": risk_level or "",
    }

    write_event_to_csv(SOURCING_REQUESTS_FILE, event)


def get_sourcing_requests_file_path():
    """
    Returns the path to the local sourcing-requests CSV file.
    """

    ensure_data_dir()
    return SOURCING_REQUESTS_FILE