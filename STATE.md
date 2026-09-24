# STATE

Last updated: 2026-09-24

## Built
- Repo on GitHub (public): lakiiibalint/flight-delay-prediction-lakehouse; `gh` authenticated, git uses gh credentials.
- `docker-compose.yml`: MinIO + ClickHouse 24.8. Verified running: ClickHouse `localhost:8123` → `Ok.`, MinIO console `localhost:9001`, S3 API `localhost:9000`.
- MinIO image: `bitnamilegacy/minio:2025.7.23-debian-12-r5`, digest-pinned (ADR-0001). Official `minio/minio` image no longer pullable.
- `.env` (local, gitignored) copied from `.env.example`.
- `docs/decisions/0001-minio-image-sourcing.md` — ADR-0001.
- `docs/diagrams/01-high-level-architecture.drawio` — skeleton architecture diagram (final for skeleton phase).
- One BTS month on disk, not in git (`data/` gitignored): `data/landing/bts_ontime/bts_ontime_2026_07.csv` (~286 MB, already unzipped) + readme.html.

## Next
- Bronze ingestion script, written by hand: CSV → Parquet → MinIO bucket `bronze`, key `bts_ontime/year=2026/month=07/…`. Manual run, hardcoded; endpoint from env (`localhost:9000` host vs `minio:9000` in-container).
- Predict after writing, before running (data/system uncertainty).

## Open decisions
- S3 client: `boto3` vs `minio` package.
- Bronze schema: inferred types vs explicit schema vs all-strings (typing in Silver). Decide by month 2 at the latest — type drift across files breaks globbed `s3()` reads. Possibly ADR.
- Drop the trailing empty column from BTS CSV (trailing comma).

## Follow-ups (not now)
- Build MinIO from source at `RELEASE.2025-09-07T16-13-09Z` before submission; superseding ADR.
- Export diagram as `.drawio.svg` so it renders on GitHub.
- JOURNAL.md not started.
