# STATE

Last updated: 2026-09-29

## Built
- Repo on GitHub (public): lakiiibalint/flight-delay-prediction-lakehouse; `gh` authenticated, git uses gh credentials.
- `docker-compose.yml`: MinIO + ClickHouse 24.8. Verified running: ClickHouse `localhost:8123` → `Ok.`, MinIO console `localhost:9001`, S3 API `localhost:9000`.
- MinIO image: `bitnamilegacy/minio:2025.7.23-debian-12-r5`, digest-pinned (ADR-0001). Official `minio/minio` image no longer pullable.
- `.env` (local, gitignored) copied from `.env.example`.
- `docs/decisions/0001-minio-image-sourcing.md` — ADR-0001.
- `docs/decisions/0002-bronze-schema-all-strings.md` — ADR-0002: Bronze all strings, empty fields stored as `""`, typing in Silver.
- Architecture diagram `docs/diagrams/01-high-level-architecture.drawio` exists only on branch `docs/architecture-diagram` (not merged into `main`).
- One BTS month on disk, not in git (`data/` gitignored): `data/landing/bts_ontime/bts_ontime_2026_07.csv` (~286 MB, already unzipped) + readme.html.
- Bronze ingestion: `collector.py` (hand-written, hardcoded, run manually). CSV → Parquet (`data/bronze_staging/`) → MinIO bucket `bronze`, key `bts_ontime/year=2026/month=07/bts_ontime_2026_07.parquet`. Verified: 631,970 rows, 109 columns, all `string`, trailing empty column dropped, empty fields = `""`.
- Python env: root `.venv` from `requirements.txt` (pyarrow, boto3). Run: `source .venv/bin/activate; set -a; source .env; set +a; python collector.py`.

## Next
- First dbt model: read the Bronze Parquet from MinIO via ClickHouse `s3()`; Silver casts must handle `''` (`nullIf` / `...OrNull`).
- JOURNAL.md entry for the Bronze ingestion cycle.

## Open decisions
- (none open for Bronze)

## Follow-ups (not now)
- CLAUDE.md says BTS has 111 fields; the July 2026 CSV header has 109 real fields (+ trailing empty). Check against the BTS field list/readme.
- Column-set check at ingestion or in Silver to catch upstream schema changes (ADR-0002 consequence).
- Build MinIO from source at `RELEASE.2025-09-07T16-13-09Z` before submission; superseding ADR.
- Merge the architecture diagram branch; export diagram as `.drawio.svg` so it renders on GitHub.
