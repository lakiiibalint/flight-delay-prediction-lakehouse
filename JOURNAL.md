# JOURNAL

## 2026-09-29 — Bronze ingestion (CSV → Parquet → MinIO)

**Built:** `collector.py` reads one BTS month, writes Parquet, uploads to MinIO `bronze` bucket. Decision recorded in ADR-0002.

**Facts observed:**
- First run with pyarrow type inference: 110 columns → 36 int64, 30 double, 18 string, 1 date32, 25 `null` (all-empty columns + unnamed trailing column from trailing comma).
- After fix: 109 columns, all `string`, 631,970 rows. Empty fields stored as `""` (pyarrow default `strings_can_be_null=False`).
- `ConvertOptions.column_types` only types the listed columns; it doesn't select them. `include_columns` does, and it also sets the output column order.
- Script needs the venv activated and `.env` exported; Python doesn't read `.env` itself.

**What I learned / would do differently:**
- Check the header of the CSV wheter there is and extran unwanted column
- Parquet and CSV are structurally different formats, at first we need to read the csv to make a temporary schema, from there we can convert to parquet 

