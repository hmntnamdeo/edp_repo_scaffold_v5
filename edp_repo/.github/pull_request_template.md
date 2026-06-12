## Summary
<!-- What does this PR do? -->

## Type of change
- [ ] Landing layer (ADF / ingestion)
- [ ] EUH transformation
- [ ] Curated model
- [ ] Unity Catalog (schema / grants / row filters)
- [ ] Power BI semantic model
- [ ] Mapping files
- [ ] Infrastructure
- [ ] Config
- [ ] Documentation

## Source system involved
<!-- Which source ID(s)? e.g. BLP, ARB, KBL -->

## Schema names used in dev
<!-- e.g. dev_catalog.feat_spend_v2_sourcing -->

## Data reload classification (required for EUH / Curated changes)
Which rows are affected?
- [ ] No existing rows affected
- [ ] Targeted window — FROM: ___ TO: ___
- [ ] All historical rows — full reprocess required

Reload approach:
- [ ] ALTER TABLE + targeted UPDATE (new column)
- [ ] MERGE for specific window
- [ ] Staging table + swap (full reprocess)
- [ ] No action on existing rows

Estimated reprocess runtime (measured in UAT): ___

## Orchestration config changes
Tables added / changed / deactivated:
| Table | Load type | Dependencies | run_order |
|-------|-----------|--------------|-----------|
|       |           |              |           |

Rollback script included: [ ] Yes — path: ___

## Checklist
- [ ] Feature branch named `feature/[component]-[layer]-[scope]`
- [ ] No hardcoded catalog names, connection strings, or env values
- [ ] DDL changes are in `migrations/` not inside the notebook
- [ ] Unit tests added / updated (min 80% coverage)
- [ ] Great Expectations suite updated if table schema changed
- [ ] `docs/naming_conventions.md` followed throughout
- [ ] CODEOWNERS will auto-assign the right reviewers
