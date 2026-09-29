# 2. Store all Bronze columns as strings; apply types in Silver

- Status: Accepted
- Date: 2026-09-29
- Phase: Skeleton (thin end-to-end slice); Bronze layer / medallion layering justification

## Context

The BTS On-Time Performance CSV is untyped. Parquet is typed, so the Bronze ingestion step (CSV → Parquet → MinIO) has to assign a type to every column. The first run used pyarrow's default type inference on July 2026 (631,970 rows, 110 columns). It produced 36 int64, 30 double, 18 string, 1 date32 and 25 `null`-typed columns: every column that was entirely empty that month (e.g. `Div3*`–`Div5*`, plus the unnamed trailing column caused by the trailing comma). Bronze will contain one file per month, read together by ClickHouse through a globbed `s3()` read, so the schema has to be consistent across files. This must be settled before the second month is ingested.

## Decision Drivers

- Schema stability across monthly files (a single globbed read must not fail or silently coerce types)
- Fidelity to the source: Bronze should be a lossless, replayable copy of what BTS delivered
- Separation of concerns: typing and cleaning are transformations, and transformations belong in dbt
- Implementation and maintenance effort for a single developer
- Storage size and query cost on the Bronze layer

## Considered Options

- All columns as strings (typing deferred to Silver)
- Per-file type inference (pyarrow default)
- Explicit, hand-declared schema for all columns at ingestion

## Decision

We chose **all columns as strings** because it is the only option that is stable across files by construction while keeping Bronze a lossless copy of the source. All typing decisions move to dbt, where they are versioned, testable and visible in lineage.

## Pros and Cons of the Options

### All columns as strings (chosen)
- Good: identical schema for every month by construction; month-specific values can't cause type drift
- Good: lossless. Values such as leading-zero codes and time fields like `"0005"` are kept exactly as delivered
- Good: clean medallion boundary. Bronze = raw source, Silver = typed and cleaned
- Good: minimal ingestion code; malformed values don't break ingestion
- Cost accepted: all casting and parsing logic has to be written in dbt Silver models
- Cost accepted: somewhat larger files and weaker compression than typed columns; Bronze can't be queried usefully without casting

### Per-file type inference
- Good: zero configuration; the schema looks "typed" immediately
- Good: best compression per file
- Bad: types depend on each month's contents. Entirely empty columns become `null` type, and a column can switch between int64, double and string from one month to the next, which breaks globbed multi-file reads
- Bad: pyarrow's inference is an implicit decision that isn't reviewed or versioned
- **Rejected because:** it fails the schema-stability driver. The first file already has 25 `null`-typed columns, and any of them would conflict with a month where that column has values.

### Explicit hand-declared schema
- Good: stable and typed at the storage layer; best compression and directly queryable Bronze
- Good: schema changes at the source fail loudly
- Bad: requires declaring and maintaining types for all columns before the data has been profiled
- Bad: puts typing decisions (a transformation) in the ingestion script, outside dbt's versioning, tests and lineage; a wrong type can reject or alter source values at ingestion
- **Rejected because:** it duplicates work that belongs in Silver and weakens Bronze's role as a faithful copy of the source, at a higher maintenance cost for a single developer.

## Consequences

- Ingestion reads every column as string (pyarrow `ConvertOptions` with `column_types` and `include_columns` built from the CSV header) and drops the unnamed trailing column. Verified on July 2026: 109 columns, all `string`.
- Empty CSV fields are stored as `""`, not `NULL` (`strings_can_be_null=False`, pyarrow's default). This is the literal reading of the source: an empty field is an empty value. Bronze therefore contains no NULLs from empty fields.
- dbt Silver takes on all type casting (`toInt*OrNull`, date/time parsing), and data-quality tests belong there. Silver must convert `''` to `NULL` explicitly (`nullIf(col, '')` or the `...OrNull` casts). `IS NULL` checks and `count(col)` on Bronze columns do not detect missing values.
- Upstream schema changes (added or removed columns) are not caught by types in Bronze. A column-set check at ingestion or in Silver is a hardening-pass follow-up.
- The file first uploaded with inferred types (`bronze` bucket, key `bts_ontime/year=2026/month=07/bts_ontime_2026_07.parquet`) was overwritten in place by the all-strings file.
