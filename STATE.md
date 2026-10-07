# STATE

Last updated: 2026-10-07

## Built
- Repo on GitHub (public): lakiiibalint/flight-delay-prediction-lakehouse; `gh` authenticated, git uses gh credentials.
- `docker-compose.yml`: MinIO + ClickHouse 24.8 (ClickHouse `localhost:8123`, MinIO console `localhost:9001`, S3 API `localhost:9000`). MinIO image `bitnamilegacy/minio:2025.7.23-debian-12-r5`, digest-pinned (ADR-0001).
- `.env` (local, gitignored) copied from `.env.example`.
- ADRs (`docs/decisions/`): 0001 MinIO image sourcing, 0002 Bronze all strings, 0003 ClickHouse→MinIO via named collection, 0004 Silver dbt tests per layer.
- Diagrams (`docs/diagrams/`): `01-high-level-architecture.drawio`, `02-dataflow.drawio` (Bronze → Silver → Gold).
- Data: one BTS month (July 2026), `data/` gitignored.
- Bronze: `collector.py` — CSV → Parquet → MinIO bucket `bronze`, key `bts_ontime/year=2026/month=07/bts_ontime_2026_07.parquet` (631,970 rows, 109 string columns).
- Silver (dbt): `staging_flights` (table), `cleaned_flights` (table), with tests.
- Gold (dbt): `features_delay` (table), with tests. Features: `Reporting_Airline`, `Origin_Airport`, `Destination_Airport`, `Hour_Of_Departure`; label `Is_Dep_Delay_Greater_Than_15`.
- ML (`ml/`): `train_rf_delay.py` (RandomForest, split by `Flight_Date`, last 20% of dates = test, model saved to `ml/artifacts/`), `predict_rf_delay.py` (scores the test split → ClickHouse `predictions_delay`; writes `pr_auc` and `baseline_pr_auc` → `model_metrics`).
- Dagster (`orchestration/`): `run_collector` → `dbt_build` → `run_rf_delay_train` → `run_rf_delay_predict`, each a subprocess call. Runs from the host `.venv`, not from docker-compose.
- Power BI Desktop report on ClickHouse, two pages: `features_delay` (delay rate 29.34%, 615K flights, by hour/airline/airport/date) and `Model (jul 25-31)` (140K scored flights, predicted 29.62% vs. actual 28.57%, calibration by 0.05 bucket, PR AUC 0.47 vs. baseline 0.29, lift 1.63). File: `powerBI/flight_pred.pbix`.

Skeleton done (2026-10-07): one file → MinIO → dbt → Dagster → model → numbers in Power BI.

## Next
- Hardening pass / deepening layers; backfill to 12 months.

## Open decisions
- (none)

## Follow-ups (not now)
- Containerize Dagster + dbt + ML in the hardening pass (today only MinIO and ClickHouse are in docker-compose).
- ADRs deferred to thesis writing; decisions to cover: Dagster without `dagster-dbt` (subprocess assets), PR AUC as the model metric, 80/20 date split.
- Calibration: predicted probabilities span ~0.20–0.50 while actual rates per bucket span ~12–60% — the model is under-dispersed.
- `predict_rf_delay.py`: `build_results` hardcodes `"rf_v1"` instead of `MODEL_NAME`; ClickHouse host hardcoded to `localhost`.
- CLAUDE.md says BTS has 111 fields; the July 2026 CSV header has 109 real fields (+ trailing empty). Check against the BTS field list/readme.
- Column-set check at ingestion or in Silver to catch upstream schema changes (ADR-0002 consequence).
- Build MinIO from source at `RELEASE.2025-09-07T16-13-09Z` before submission; superseding ADR.
- Export diagrams as `.drawio.svg` so they render on GitHub.
