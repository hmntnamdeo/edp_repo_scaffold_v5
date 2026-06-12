#!/usr/bin/env python3
# unity_catalog/scripts/schema_diff.py
#
# CI quality gate — runs on every PR.
#
# Row filter binding policy:
#   Which tables need a row filter is an explicit decision recorded in
#   unity_catalog/terraform/table_bindings.yaml — NOT inferred from table name.
#   Table naming conventions on this platform are inconsistent (some tables
#   named dim_* carry row-level data and need filters; some fact_* tables do not).
#   The registry is the single source of truth.
#
# What this gate checks:
#   1. For any curated notebook changed in this PR that IS registered in
#      table_bindings.yaml — verify its filter column still appears in the notebook.
#      This catches accidental drops of the filter column during refactoring.
#   2. For any curated notebook changed in this PR that is NOT in the registry —
#      emit a WARNING (not a failure) so the reviewer is reminded to consider
#      whether this table should be registered.
#
# What this gate does NOT do:
#   Automatically require registration based on table name. That decision
#   belongs to the PR reviewer who has domain knowledge about the table.
#
# Called by .github/workflows/ci.yml:
#   - name: Unity Catalog schema diff — detect missing row filter bindings
#     run: python unity_catalog/scripts/schema_diff.py

import os
import sys
import subprocess
import yaml

# ── Load binding registry ─────────────────────────────────────────────────────

BINDINGS_PATH = "unity_catalog/terraform/table_bindings.yaml"

with open(BINDINGS_PATH) as f:
    registry = yaml.safe_load(f)

# Build lookup: (schema, table) -> binding entry
registered = {
    (b["schema"], b["table"]): b
    for b in registry["table_bindings"]
    if b.get("row_filter") and b.get("row_filter") != "none"
}

# ── Find changed curated notebooks in this PR ─────────────────────────────────

result = subprocess.run(
    ["git", "diff", "--name-only", "origin/develop...HEAD"],
    capture_output=True, text=True
)

changed_files = result.stdout.strip().split("\n")

curated_notebooks = [
    f for f in changed_files
    if f.startswith("databricks/notebooks/curated/")
    and f.endswith(".py")
    and "/infra/" not in f
]

print(f"Changed curated notebooks in this PR: {len(curated_notebooks)}")

# ── Check each changed notebook ───────────────────────────────────────────────

errors   = []
warnings = []

for notebook_path in curated_notebooks:
    parts = notebook_path.split("/")
    if len(parts) < 5:
        continue

    domain     = parts[3]
    table_name = parts[4].replace(".py", "")
    binding    = registered.get((domain, table_name))

    if binding:
        # Table is registered — verify filter column is still present in notebook
        filter_col = binding.get("filter_column", "")
        print(f"  REGISTERED: {domain}.{table_name} — checking filter column '{filter_col}'")

        with open(notebook_path) as f:
            content = f.read()

        if filter_col and filter_col not in content:
            errors.append(
                f"FILTER COLUMN DROPPED: {domain}.{table_name}\n"
                f"  Notebook:      {notebook_path}\n"
                f"  Filter column: '{filter_col}' not found in notebook.\n"
                f"  This column is bound as the row filter column in table_bindings.yaml.\n"
                f"  If the column was intentionally renamed:\n"
                f"    1. Update filter_column in table_bindings.yaml\n"
                f"    2. Add a migration script to rebind the filter on the existing table\n"
                f"    3. Raise a security review with the data lead\n"
            )

    else:
        # Table is not registered — warn the reviewer to make a conscious decision
        warnings.append(
            f"NOT REGISTERED: {domain}.{table_name}\n"
            f"  Notebook: {notebook_path}\n"
            f"  This table has no row filter binding.\n"
            f"  PR reviewer: confirm this table does not require row-level security.\n"
            f"  If it does, add an entry to {BINDINGS_PATH} in this PR.\n"
        )

# ── Report ────────────────────────────────────────────────────────────────────

if warnings:
    print("\n" + "-"*60)
    print("REVIEW REQUIRED — unregistered tables (not a failure):")
    print("-"*60)
    for w in warnings:
        print(f"\n  {w}")

if errors:
    print("\n" + "="*60)
    print("SCHEMA DIFF FAILED — filter column integrity errors:")
    print("="*60)
    for err in errors:
        print(f"\n{err}")
    print("="*60)
    sys.exit(1)
else:
    print("\nSCHEMA DIFF PASSED.")
    if warnings:
        print(f"  {len(warnings)} unregistered table(s) — reviewer must confirm no row filter needed.")
    sys.exit(0)
