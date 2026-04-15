# Plugin Catalog System Design

**Date:** 2026-04-14
**Status:** Approved
**Purpose:** Build a searchable, enriched catalog of Claude Code plugins, skills, agents, and frameworks from 24 cloned repositories and their external references. Produce curated plugin sets for 7 project types and 8 user personas.

---

## Architecture

Four components, built as a single Claude Code plugin called `catalog`:

```
┌─────────────────────────────────────────────────┐
│                  catalog plugin                  │
├──────────┬──────────┬───────────┬───────────────┤
│ Ingester │ Enricher │ Classifier│  MCP Server   │
│ (Python) │ (Python) │ (Python)  │  (Python)     │
├──────────┴──────────┴───────────┴───────────────┤
│              catalog.db (SQLite)                 │
└─────────────────────────────────────────────────┘
```

- **Ingester** — Recursively scans local repos for plugin manifests, skill files, agent definitions, hook configs, and docs. Extracts GitHub URLs from READMEs/awesome-lists for enrichment.
- **Enricher** — Hits GitHub API via `gh api` to pull stars, forks, last commit, topics, license for all discovered external repos. Caches in SQLite.
- **Classifier** — Hybrid: keyword matching first pass, AI classification second pass for ambiguous components.
- **MCP Server** — Stdio MCP server exposing search, recommend, similar, stats, and ingest tools.

---

## SQLite Schema

```sql
CREATE TABLE repos (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    name TEXT,
    description TEXT,
    stars INTEGER,
    forks INTEGER,
    last_repo_commit TEXT,
    license TEXT,
    topics JSON,
    is_local INTEGER DEFAULT 0,
    fetched_at TEXT
);

CREATE TABLE components (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER REFERENCES repos(id),
    name TEXT,
    type TEXT,                    -- plugin|skill|agent|hook|command|framework
    description TEXT,
    file_path TEXT,
    file_last_commit TEXT,        -- per-file, not per-repo
    file_last_author TEXT,
    version TEXT,
    triggers TEXT,
    tools_used JSON,
    metadata JSON,
    tags JSON,
    project_types JSON,
    personas JSON,
    source_url TEXT
);

CREATE TABLE similarities (
    id INTEGER PRIMARY KEY,
    component_a INTEGER REFERENCES components(id),
    component_b INTEGER REFERENCES components(id),
    similarity_score REAL,        -- 0.0-1.0
    similarity_type TEXT,         -- near-duplicate|fork|derivative|same-purpose
    notes TEXT,
    UNIQUE(component_a, component_b)
);

CREATE INDEX idx_components_type ON components(type);
CREATE INDEX idx_components_repo ON components(repo_id);
CREATE INDEX idx_similarities_a ON similarities(component_a);
CREATE INDEX idx_similarities_b ON similarities(component_b);
```

---

## Ingestion Pipeline

### Phase 1: Local Deep Scan

For each of the 24 cloned repos, discover components by file pattern:

| Pattern | Component Type |
|---|---|
| `**/plugin.json` | plugin manifest |
| `**/skills/**/*.md` (YAML frontmatter) | skill |
| `**/agents/**/*.md` (YAML frontmatter) | agent |
| `**/hooks/**/*.{md,json}` | hook |
| `**/commands/**/*.md` (YAML frontmatter) | command |
| `**/CLAUDE.md`, `**/.claude/**` | framework/config |
| `**/package.json`, `**/pyproject.toml` | framework/tool |

For each file:
- Parse YAML frontmatter or JSON for structured fields
- `git log -1 --format="%aI|%an" -- <filepath>` for file-level commit date/author
- Extract raw text for keyword extraction and similarity fingerprinting
- Store normalized content fingerprint for duplicate detection

### Phase 2: URL Extraction and Enrichment

- Regex-extract GitHub URLs from all markdown files
- Deduplicate
- `gh api repos/{owner}/{repo}` for metadata (stars, forks, topics, license, last push)
- Check for `plugin.json` at root of external repos to discover remote components
- Rate limiting: batches of 50, 1-second pause between batches

### Phase 3: Similarity Detection

- Compare all component pairs within the same `type`
- Normalized token-level Jaccard similarity
- Threshold: > 0.6 flags as candidate
- Classify relationship: `fork` | `derivative` | `same-purpose` | `near-duplicate`
- Store score, type, and diff summary in `similarities` table

---

## MCP Server Tools

### `catalog_search`
Primary discovery tool.
- **query** (string) — free-text search against name, description, tags
- **type** (string?) — plugin|skill|agent|hook|command|framework
- **project_type** (string?) — devops|app-deploy|policy-as-code|docs|sales-marketing|big-data|finops
- **persona** (string?) — platform-engineer|cloud-sre|data-engineer|ml-engineer|sales|marketing|accounting|director-vp
- **min_stars** (int?) — minimum repo stars
- **sort_by** (string?) — relevance|stars|recent
- **limit** (int?) — default 20
- Returns: array of components with repo metadata, similarity count

### `catalog_recommend`
Curated plugin set for a project type and/or persona.
- **project_type** (string?)
- **persona** (string?)
- Returns: ranked list, duplicates collapsed to best variant with alternatives linked

### `catalog_similar`
Near-duplicates for a component.
- **component_id** (int)
- Returns: similar components with scores, types, notes, file_last_commit

### `catalog_stats`
Overview metrics.
- Returns: counts by type, top repos, coverage gaps, most/least maintained

### `catalog_ingest`
Trigger re-ingestion.
- **path** (string?) — specific repo or all
- **refresh_github** (bool) — re-fetch API data
- Returns: new/updated/removed counts

---

## Hybrid Classification Engine

### Pass 1: Keyword Dictionaries

| Project Type | Keywords |
|---|---|
| devops | terraform, pulumi, github-actions, ci/cd, pipeline, helm, argocd, ansible, jenkins, gitlab-ci |
| app-deploy | kubernetes, k8s, cloud-run, cloudflare, docker, container, deployment, ingress, service-mesh |
| policy-as-code | kyverno, opa, rego, gatekeeper, sentinel, policy, compliance, admission-controller |
| docs | documentation, mkdocs, docusaurus, sphinx, readme, confluence, backstage, catalog-info |
| sales-marketing | presentation, pitch, proposal, slide, marketing, campaign, branding, collateral |
| big-data | dbt, bigquery, snowflake, mongodb, spark, airflow, dagster, data-pipeline, etl, warehouse |
| finops | cost, billing, budget, finops, pricing, cloud-cost, usage-report, chargeback |

Persona dictionaries: `platform-engineer` inherits devops + app-deploy keywords plus "platform", "self-service", "golden-path"; `director-vp` matches "dashboard", "report", "summary", "overview", "metrics"; etc.

### Pass 2: AI Classification

Components matching zero categories sent in batches of 20 to Haiku-tier model for semantic classification. AI is additive — never removes keyword-matched tags.

### Coverage Report

Post-classification summary: components per project type and persona, categories with < 5 matches flagged as gaps.

---

## Output: Plugin Sets

### Project Type Sets (7 files)

Stored in `docs/plans/catalog-sets/`, e.g. `devops-toolkit.md`:
- Recommended Plugins (with install info, stars, similar alternatives)
- Recommended Skills (with source, last maintained date)
- Recommended Agents
- Recommended MCP Servers
- CLAUDE.md Additions for this project type
- Gaps (missing coverage)

### Persona Sets (8 files)

E.g. `platform-engineer.md`:
- Always-On Plugins (user scope)
- Project-Contextual Plugins (project scope)
- Suggested CLAUDE.md Preferences
- Suggested Hooks

### Generation

`/catalog generate-sets` skill runs queries for all project types and personas, deduplicates across sets, resolves similarity clusters (picks best variant by stars + recency), writes markdown files. Re-runnable after re-ingestion.

---

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Storage | SQLite | Relational queries needed for faceted search by type/persona/popularity |
| Schema style | Flat + JSON columns | Discovery use case, not complex reporting; simpler ingestion |
| Ingestion depth | Deep scan + follow external links | Awesome-lists are primarily link collections; need GitHub API for popularity |
| Query interface | MCP server | Native Claude Code integration, structured I/O, no context pollution |
| Tagging | Hybrid keyword + AI | Fast for obvious matches, smart for ambiguous; keeps API costs low |
| Similarity tracking | Per-component with scores | Duplicates are expected; users need to pick the best-maintained variant |
| File dating | Per-file git log | Repo-level dates mislead; a skill untouched for a year in an active repo is still stale |
