"""
catalog.py - Faux Mainframe Dataset Catalog
Part of the Python Mainframe Experience Layer

Manages DSN (Data Set Name) allocation, resolution, and metadata.
All datasets live under the SIM_ROOT directory.
Catalog metadata is stored in a JSON file.
"""

import json
import os
from datetime import date

# --- Configuration ---
SIM_ROOT     = os.path.dirname(os.path.abspath(__file__))
CATALOG_FILE = os.path.join(SIM_ROOT, "catalog.json")
DATASET_DIR  = os.path.join(SIM_ROOT, "datasets")

# Valid RECFM types
VALID_RECFM = {"F", "FB", "V", "VB"}


# --- Catalog I/O ---

def _load_catalog() -> dict:
    """Load the catalog from disk. Returns empty dict if not found."""
    if not os.path.exists(CATALOG_FILE):
        return {}
    with open(CATALOG_FILE, "r") as f:
        return json.load(f)


def _save_catalog(catalog: dict):
    """Persist the catalog to disk."""
    os.makedirs(SIM_ROOT, exist_ok=True)
    with open(CATALOG_FILE, "w") as f:
        json.dump(catalog, f, indent=2)


# --- DSN Utilities ---

def _validate_dsn(dsn: str) -> bool:
    """
    Basic DSN validation.
    Must be uppercase, dot-separated qualifiers, max 44 chars.
    Each qualifier 1-8 alphanumeric/national chars, starting with alpha.
    """
    if not dsn or len(dsn) > 44:
        return False
    parts = dsn.split(".")
    for part in parts:
        if not part or len(part) > 8:
            return False
        if not part[0].isalpha():
            return False
        if not all(c.isalnum() or c in "@#$" for c in part):
            return False
    return True


def _dsn_to_path(dsn: str) -> str:
    """Convert a DSN like USER.DAVE.DATA to a file path under DATASET_DIR."""
    parts = dsn.upper().split(".")
    return os.path.join(DATASET_DIR, *parts) + ".txt"


# --- Public API ---

def allocate(dsn: str, recfm: str = "FB", lrecl: int = 80,
             description: str = "") -> bool:
    """
    Allocate a new dataset.
    Creates the physical file and adds a catalog entry.
    Returns True on success, False if DSN already exists or invalid.
    """
    dsn   = dsn.upper()
    recfm = recfm.upper()

    if not _validate_dsn(dsn):
        return False
    if recfm not in VALID_RECFM:
        return False

    catalog = _load_catalog()
    if dsn in catalog:
        return False

    # Create the physical file
    path = _dsn_to_path(dsn)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()

    # Add catalog entry
    catalog[dsn] = {
        "path":        os.path.relpath(path, SIM_ROOT),
        "recfm":       recfm,
        "lrecl":       lrecl,
        "created":     str(date.today()),
        "description": description
    }
    _save_catalog(catalog)
    return True


def delete(dsn: str) -> bool:
    """
    Delete a dataset. Removes the physical file and catalog entry.
    Returns True on success, False if not found.
    """
    dsn     = dsn.upper()
    catalog = _load_catalog()
    if dsn not in catalog:
        return False

    path = _dsn_to_path(dsn)
    if os.path.exists(path):
        os.remove(path)

    del catalog[dsn]
    _save_catalog(catalog)
    return True


def exists(dsn: str) -> bool:
    """Return True if DSN is in the catalog."""
    catalog = _load_catalog()
    return dsn.upper() in catalog


def resolve_path(dsn: str) -> str | None:
    """
    Return the full Windows path for a DSN, or None if not found.
    Use this to open/read/write the actual dataset file.
    """
    catalog = _load_catalog()
    entry   = catalog.get(dsn.upper())
    if not entry:
        return None
    return os.path.join(SIM_ROOT, entry["path"])


def get_entry(dsn: str) -> dict | None:
    """Return the full catalog entry for a DSN, or None if not found."""
    catalog = _load_catalog()
    return catalog.get(dsn.upper())


def listcat(prefix: str = "") -> list[dict]:
    """
    List catalog entries, optionally filtered by DSN prefix.
    Returns a list of dicts with 'dsn' added to each entry.
    """
    catalog = _load_catalog()
    results = []
    prefix  = prefix.upper()
    for dsn, entry in sorted(catalog.items()):
        if dsn.startswith(prefix):
            results.append({"dsn": dsn, **entry})
    return results


# --- Self test ---
if __name__ == "__main__":
    print("=== Catalog Self-Test ===\n")

    allocate("USER.DAVE.TEST",   recfm="FB", lrecl=80, description="Test dataset")
    allocate("USER.DAVE.SOURCE", recfm="FB", lrecl=80, description="Source members")
    allocate("SYS.PROC.LIBRARY", recfm="FB", lrecl=80, description="Proc library")

    print("LISTCAT ALL:")
    for e in listcat():
        print(f"  {e['dsn']:44s}  RECFM={e['recfm']}  LRECL={e['lrecl']}  {e['description']}")

    print(f"\nResolve USER.DAVE.TEST: {resolve_path('USER.DAVE.TEST')}")

    delete("USER.DAVE.TEST")

    print("\nLISTCAT after delete:")
    for e in listcat():
        print(f"  {e['dsn']:44s}  {e['description']}")

    print("\nDone.")