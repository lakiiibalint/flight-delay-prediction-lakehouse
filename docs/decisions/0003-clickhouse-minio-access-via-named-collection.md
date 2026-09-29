# 3. Access MinIO Bronze from ClickHouse via a named collection

- Status: Accepted
- Date: 2026-09-29
- Phase: Skeleton (thin end-to-end slice); Bronze → Silver boundary / storage–compute separation justification

## Context

Silver models (dbt on ClickHouse) must read the Bronze Parquet files in MinIO through ClickHouse's `s3()` table function. By default `s3()` takes the endpoint URL, access key and secret key as arguments in every query, which puts credentials into dbt SQL files that are committed to a public repository. We need a way to reach the bucket now, before the first dbt model is written, because every Silver model will depend on it.

## Decision Drivers

- Credentials never appear in versioned files (SQL, config), since the repo is public
- Single source of truth for the secrets: `.env`, already used by docker-compose and `collector.py`
- Readable dbt SQL: models should state *which file*, not *how to connect*
- Endpoint/bucket change in one place (e.g. MinIO replaced by a source-built image, or a cloud S3 later)
- No extra tooling at skeleton stage; runs in the existing docker-compose setup

## Considered Options

- Named collection in ClickHouse server config, keys injected via `from_env`
- Credentials inline in `s3()` calls
- Credentials passed from dbt (`env_var()` in models or a macro) into inline `s3()` calls
- Server-level `<s3>` endpoint credentials in ClickHouse config, URL still in each query

## Decision

We chose a **named collection (`minio_bronze`)** defined in `clickhouse/config.d/named_collections.xml`, with `access_key_id`/`secret_access_key` resolved via `from_env` from `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` (passed from `.env` by docker-compose). Queries use `s3(minio_bronze, filename='...')`. It is the only option that keeps secrets out of both SQL and git while also centralising the endpoint.

## Pros and Cons of the Options

### Named collection + `from_env` (chosen)
- Good: no credentials in SQL, config file or git; `.env` stays the single secret source
- Good: URL, bucket and format defined once; models only name the object key
- Good: native ClickHouse feature, no extra dependencies
- Cost accepted: connection details are invisible from the dbt project; a reader must know to look in ClickHouse config
- Cost accepted: changing the collection requires a ClickHouse restart (container recreate when env changes)

### Credentials inline in `s3()`
- Good: simplest; fully explicit, self-contained queries
- Bad: secrets in committed SQL
- Bad: URL and keys duplicated in every model
- **Rejected because:** it violates the "no credentials in versioned files" driver on a public repo.

### dbt `env_var()` feeding inline `s3()`
- Good: secrets stay in `.env`; connection visible from within the dbt project
- Bad: every model (or a macro) still assembles URL and keys; rendered SQL in `target/` contains the secrets
- Bad: couples the storage connection to dbt; ad-hoc queries in `clickhouse-client` need keys typed by hand
- **Rejected because:** it only moves the secret out of source files, not out of compiled SQL, and adds per-query boilerplate.

### Server-level `<s3>` endpoint credentials
- Good: keys out of SQL; native ClickHouse config
- Bad: full URL still repeated in each query; matching is by URL prefix, which is less explicit than a named reference
- **Rejected because:** it centralises credentials but not the endpoint, so it scores worse on readability and single-place change.

## Consequences

- dbt Silver models read Bronze with `s3(minio_bronze, filename='bts_ontime/year=.../month=.../....parquet')`.
- XML-defined users (incl. `default`) lack the `NAMED COLLECTION` grant by default; `clickhouse/users.d/default_named_collections.xml` enables `named_collection_control` and, because customising `default` interferes with the image entrypoint's user setup, also sets the password from `CLICKHOUSE_PASSWORD`.
- ClickHouse container now needs the MinIO env vars and the config file mount (`docker-compose.yml`); an env change requires `docker compose up -d clickhouse`, not a restart.
- Secrets are still visible to anyone with access to the container env or `preprocessed_configs/`; acceptable for a single-host thesis setup, to revisit (Docker secrets / Kubernetes Secrets) in the hardening pass.
- The endpoint is hardcoded to the compose service name `minio`; the planned source-built MinIO image (ADR-0001 follow-up) must keep that service name or this file must change.
