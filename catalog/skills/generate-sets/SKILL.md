---
name: catalog-generate-sets
description: >
  Generate curated plugin/skill sets for project types and personas from the catalog database.
  Produces markdown files with ranked recommendations, duplicate resolution, and gap analysis.
  Use after ingestion to produce actionable toolkit documents.
---

# Generate Catalog Sets

Generate curated plugin sets for all 7 project types and 8 personas.

## Output

Writes to `docs/plans/catalog-sets/`:
- 7 project type files (e.g., `devops-toolkit.md`)
- 8 persona files (e.g., `platform-engineer.md`)

Each file contains ranked recommendations with:
- Install instructions and version info
- Star counts and maintenance dates
- Duplicate alternatives collapsed
- CLAUDE.md additions for the context
- Coverage gaps
