# 4. Place dbt data tests in the Silver model that introduces each assumption

- Status: Accepted
- Date: 2026-09-30
- Phase: Skeleton → Silver deepening; data quality / validation strategy

## Context

Silver is split into two dbt models: `staging_flights` (1:1 with the Bronze Parquet; rename, cast, `''` → NULL, materialized as a table) and `cleaned_flights` (cleaning rules: deduplication, filtering, plausibility fixes). Both are materialized as ClickHouse tables. dbt data tests (`schema.yml`) must live somewhere, and where they live determines what a failure tells us and whether bad data propagates downstream. The decision is needed now, before the first tests are written and before `cleaned_flights` gains logic.

## Decision Drivers

- A failing test points to the single model (and transformation step) that broke
- Bad data is stopped before it reaches downstream models (`dbt build` skips children of failed tests)
- No duplicated tests across layers (maintenance cost for a single developer)
- Tests are cheap to run: they query ClickHouse tables, not MinIO
- Defensible data-quality story for the thesis: each layer has an explicit, checked contract

## Considered Options

- Layered: each model tests the assumptions it introduces (staging = source/cast contract, cleaned = cleaning rules)
- Tests only on `staging_flights`
- Tests only on `cleaned_flights` (end of Silver)
- Same full test set on both models

## Decision

We chose **layered tests**: `staging_flights` tests that the source arrived and the casts worked (row count vs Bronze, `not_null` on always-populated fields such as `Flight_Date`/`Origin_Airport`, `accepted_values [0, 1]` on flag columns, cast NULL-rate sanity). `cleaned_flights` tests the rules it applies (uniqueness of the flight key, value ranges on delays, filtered records actually absent). It scores best on failure localisation and stopping propagation, without duplicating tests.

## Pros and Cons of the Options

### Layered, per introduced assumption (chosen)
- Good: a failure names the layer and the kind of problem (upstream/cast vs cleaning logic)
- Good: `dbt build` halts at staging if the source contract breaks, so `cleaned_flights` is never built on bad input
- Good: no duplication; each test has one home
- Cost accepted: two `schema.yml` blocks to keep in sync with two models; a reader must know which layer owns which check

### Tests only on `staging_flights`
- Good: one place; catches upstream schema/format changes early
- Bad: cleaning logic (dedup, filters) is never verified
- **Rejected because:** the most error-prone code, the cleaning rules, would have no checks.

### Tests only on `cleaned_flights`
- Good: tests the data that Gold actually consumes
- Bad: a cast or source problem surfaces one layer late and is indistinguishable from a cleaning bug
- Bad: staging is built and consumed unchecked
- **Rejected because:** it loses failure localisation, the primary driver.

### Same test set on both models
- Good: maximum coverage
- Bad: every check maintained twice; tests that are meant to fail on staging (e.g. uniqueness before dedup) must be special-cased
- **Rejected because:** duplication costs maintenance without adding information over the layered approach.

## Consequences

- `staging_flights` gets a `schema.yml` now (skeleton); `cleaned_flights` tests are added together with each cleaning rule, not in bulk.
- A uniqueness test needs a flight key; staging does not yet carry `Flight_Number_Reporting_Airline`, so it must be added to staging before dedup can be tested in `cleaned_flights`.
- Bronze itself stays untested by dbt: there is no dbt `source` relation over MinIO yet (staging reads `s3()` directly). Source tests/freshness become possible once an S3-engine source table exists (hardening pass).
- Test severity is `error` by default; downgrading specific plausibility checks to `warn` is a later, per-test decision.
