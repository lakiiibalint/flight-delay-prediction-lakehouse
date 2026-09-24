# CLAUDE.md

Operating rules for Claude Code in this repository. This is a contract, not background reading — follow it before generating anything.

## Project

Bachelor's thesis: a containerized, lakehouse-oriented data platform predicting US domestic flight delays from BTS (Bureau of Transportation Statistics) historical data. Two outputs: a defensible thesis (explicit technology justification via comparative ADRs) and a data engineering portfolio piece.

## Operating mode — read this first

- Default mode is **plan**: explain and pseudocode, don't write real code.
- Only write actual code when the message explicitly says **"implement this"**. Phrases like "let's build X" or "can you set up Y" stay at plan/pseudocode level unless the thing being asked for is scaffolding (below).
- Core logic is written by Bálint personally, for learning: dbt SQL, Dagster ops/assets, feature engineering, the ML pipeline. Don't write these even if asked to "help" — explain the approach, flag what to watch for, review what's written. "Implement this" doesn't override this category — it applies to scaffolding.
- Scaffolding can be generated freely, no trigger phrase needed: Dockerfiles, docker-compose.yml, pyproject.toml, config files (dbt_project.yml, profiles.yml, Dagster definitions.py boilerplate), project layout, this file.

## Build philosophy

- Skeleton-first: the dumbest possible end-to-end slice before deepening any layer. Current target: one file → MinIO → one dbt model → one Dagster asset → one number in Power BI, all via docker-compose. Hardcode aggressively at this stage.
- Manual run before orchestration: validate a pipeline stage by hand before wiring it into Dagster.
- Avoid over-engineering upfront. Don't scaffold the full per-component structure (independent Dockerfile/pyproject.toml per service) until the thin slice works end to end.
- Don't introduce tooling, abstractions, or structure that isn't earning its place yet.

## Predict-first (Bálint's practice, not something Claude Code performs)

Before running code at genuinely uncertain points, Bálint writes a one-line prediction with reasoning — this is a personal learning discipline, so don't generate the prediction on his behalf; that would defeat the point. Claude Code's role is to not collapse write→run into one uninterrupted step at an uncertain point — pause there, don't pre-empt it.

- **Mechanism uncertainty** (tool/system behavior — dbt/Dagster/ClickHouse semantics): he predicts *before* writing. plan → predict → write → run → compare → log breakpoint if wrong.
- **Data/system uncertainty** (own code against real external data — SQL cleaning, Python collectors): he predicts *after* writing, right before running. plan → write → predict → run → compare → log breakpoint if wrong.
- Unfamiliar syntax/libraries: covered by a short JIT learning block, not predicted.
- A breakpoint (predicted ≠ actual) gets logged as expected vs. actual — it's a data point for him, not something to smooth over.

## Per-feature loop

JIT learning block (1–1.5h) → minimal spike → manual end-to-end run → validate output → ADR (if a real decision was made) → JOURNAL.md entry → later hardening pass.

## ADRs

- MADR-style, single-file, via the `adr-author` skill.
- Hard rules for every ADR: explicit decision drivers, pros/cons for every option considered, stated rejection rationale for every alternative.
- Write immediately after the decision, while the reasoning is fresh — not batched at phase end.
- Location: `docs/decisions/`.

## Repo layout

- Monorepo, one repo for the whole platform.
- Per-component `src/`, independent `pyproject.toml` and `Dockerfile` per component — once past skeleton phase, not now.
- `docs/decisions/` — ADRs.
- `JOURNAL.md` — learning capture, one entry per feature-loop cycle.
- `STATE.md` — cross-session snapshot (what's built, what's next, open decisions). Update at the end of a working session so a fresh session can pick up without re-deriving context.
- `docs/diagrams/` — architecture diagrams (draw.io).

## Git workflow

- Branch-based development. No direct commits to `main`.
- One branch per feature-loop cycle or standalone change, prefixed `feat/`, `fix/`, `docs/`, `chore/` + kebab-case (e.g. `feat/bronze-ingestion`).
- Merge via PR (`gh pr create`), squash-merge, delete the branch. A feature PR carries its code, ADR, and JOURNAL.md entry together.

## Finalized stack — don't re-litigate without a new ADR

MinIO (Bronze/object storage) · ClickHouse (Silver/Gold, analytical warehouse) · dbt Core (transformations) · Dagster (orchestration) · scikit-learn RandomForest (ML) · FastAPI + Redis (serving, later phase) · Power BI Desktop (visualization) · Docker/docker-compose (containerized, Kubernetes-scalable) · Parquet (Bronze format).

Spark, Databricks, and Trino+Iceberg were deliberately rejected — justifying *not* using Spark is itself part of the thesis argument, don't undo that by defaulting back to it. ClickHouse is "lakehouse-oriented," not a true lakehouse engine (no native Iceberg/Delta table format) — be ready to address this distinction at defense, don't paper over it.

**MinIO packaging note:** the community-edition Docker image is frozen. MinIO stopped publishing images in Oct 2025 and archived the upstream repo in Feb 2026. As of Sep 2026 the official images are no longer pullable either (`minio/minio` removed from Docker Hub, `quay.io/minio/minio` requires auth). Per ADR-0001: use `bitnamilegacy/minio:2025.7.23-debian-12-r5` (digest-pinned in docker-compose.yml) as a stopgap; replace it with an image built from source at `RELEASE.2025-09-07T16-13-09Z` during the hardening pass, before submission. Security patching isn't the concern, a pinned reproducible image is. Don't propose switching object stores (SeaweedFS, Garage, RustFS) — rejected in ADR-0001.

## ML discipline

- Always establish a simple baseline before RandomForest — never skip it.
- Time-aware train/test splits only. Never shuffle flight data — temporal ordering must be respected.
- The Gold layer (dbt-built feature table) is the only correct ML training source.

## Data source

BTS Reporting Carrier On-Time Performance (1987–present), transtats.bts.gov. 111 fields, monthly grain, CSV via the site's own Download tool (one month per pull). Use Reporting Carrier, not Marketing Carrier (too few years covered). Skeleton phase: one year (12 files) before backfilling further back.

## Communication style

Concise, direct, low token use. No decorative formatting, no filler explanation of things already understood. Push back on imprecision — if something doesn't add up, say so before proceeding rather than smoothing over it.
