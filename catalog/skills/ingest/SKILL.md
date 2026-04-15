---
name: catalog-ingest
description: >
  Ingest plugins, skills, agents, and frameworks from local repos into the catalog database.
  Pulls repos, scans for components, enriches with GitHub API data, detects duplicates, and flags suspicious code.
  Use when you want to refresh the catalog or after cloning new repos.
---

# Catalog Ingest

Run the catalog ingestion pipeline against local repositories.

## Usage

Invoke this skill to scan all repos in the configured directory, or specify a path for a single repo.

The pipeline:
1. Pulls all repos to get latest changes
2. Detects new repos in the directory
3. Scans for plugin manifests, skills, agents, hooks, commands
4. Extracts GitHub URLs from READMEs and fetches metadata (stars, forks, topics)
5. Detects near-duplicate components
6. Security-scans ingested code and tombstones suspicious entries
7. Classifies components by project type and persona

Use `--refresh-github` to re-fetch GitHub API data for external repos.
Use `--force` to re-ingest all components regardless of git change detection.
