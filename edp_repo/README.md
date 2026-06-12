# EDP Data Platform

Enterprise Data Platform — DNA to EDP migration programme.
Azure · Databricks Unity Catalog · Power BI Premium
May 2026 – January 2027

## Before you write a single line of code

Read `docs/naming_conventions.md`. Every schema name, branch name,
folder name, and notebook variable follows the conventions in that file.
Copilot reads `.github/copilot/instructions.md` which summarises the same rules.

## Three golden rules

1. Never commit directly to `main` or `develop`. Always work on a feature branch.
2. Never deploy by clicking in the Azure portal, ADF, or Databricks UI.
   The pipeline is the only deployment mechanism.
3. Never hardcode environment-specific values (catalog names, connection strings,
   storage accounts). They belong in `config/` files.

## Repository structure

| Folder | Purpose |
|--------|---------|
| `.github/` | CI/CD workflows, branch protection, Copilot instructions |
| `adf/` | Azure Data Factory pipeline JSON definitions |
| `databricks/` | Notebooks, DAB bundle config, migrations, utils |
| `unity_catalog/` | Terraform for UC schema, grants, row filters |
| `powerbi/` | Semantic models (.pbip) and standard reports |
| `mapping_files/` | Streamlit app and schemas for 70 mapping files |
| `infrastructure/` | Bicep templates for ADLS, Databricks, Key Vault |
| `config/` | Per-environment config and source system registry |
| `tests/` | Unit, integration, Great Expectations suites |
| `docs/` | Naming conventions, ways of working, runbook, ADRs |

## Quick links

- Naming conventions: `docs/naming_conventions.md`
- Ways of working: `docs/ways_of_working.md`
- Source registry: `config/source_systems.yml`
- CI pipeline: `.github/workflows/ci.yml`
- Copilot config: `.github/copilot/instructions.md`

## Branching strategy

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Mirrors production exactly | 2 approvals, no force push |
| `develop` | Integration branch | 1 approval (data lead), all CI gates |
| `feature/[component]-[layer]-[scope]` | All new work | PR to develop |
| `hotfix/[desc]` | Emergency fixes | Branches from main |

## Naming — three rules

- **Layer names**: Landing · EUH · Curated (never Bronze/Silver/Gold)
- **Source IDs**: Short codes from `config/source_systems.yml` (BLP, ARB, KBL...)
- **Env IDs**: In dev/UAT source pathway schema names only (A59, X59...). Never in prod.
