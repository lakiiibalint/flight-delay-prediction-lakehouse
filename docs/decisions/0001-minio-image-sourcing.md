# 1. Source the MinIO image from bitnamilegacy now, build from source before submission

- Status: Accepted
- Date: 2026-09-24
- Phase: Skeleton (thin end-to-end slice); Bronze layer / object storage justification

## Context

MinIO is the finalized Bronze-layer object store. MinIO stopped publishing community images in Oct 2025 and archived the upstream repo in Feb 2026; the plan was to pin `minio/minio:RELEASE.2025-09-07T16-13-09Z`. On first `docker compose up` the pull failed: `minio/minio` no longer exists on Docker Hub (404), and `quay.io/minio/minio` rejects anonymous pulls (401). The skeleton is blocked until some MinIO image is obtainable, so the image source must be decided now — the choice of MinIO itself is not in question.

## Decision Drivers

- Unblocks the skeleton immediately (skeleton-first build philosophy)
- Reproducibility: the environment must rebuild identically for examiners, independent of third-party registry decisions
- Change cost: stays inside the finalized stack, no re-verification of downstream S3 client behavior
- Effort proportional to phase: skeleton only exercises the S3 API surface, which is identical across builds
- Defensibility at the thesis defense

## Considered Options

- Prebuilt `bitnamilegacy/minio:2025.7.23-debian-12-r5` (digest-pinned) now; build from source before submission
- Build MinIO from archived source at `RELEASE.2025-09-07T16-13-09Z` now
- Switch to another S3-compatible store (SeaweedFS, Garage, RustFS)

## Decision

We chose **bitnamilegacy/minio now, with build-from-source as a mandatory pre-submission hardening step**, because it unblocks the skeleton at zero build cost while the S3 API the pipeline depends on is unaffected by how the binary was produced; the permanent reproducibility fix is deferred to the hardening pass, where it is a drop-in image swap.

## Pros and Cons of the Options

### bitnamilegacy now, build from source later (chosen)
- Good: one-line image swap plus minor compose adjustments (no `command:`, data path `/bitnami/minio/data`); same env vars
- Good: pinned by tag and sha256 digest, so it is byte-identical while it remains available
- Good: has stayed available ~13 months since Bitnami's Aug 2025 legacy cutover — adequate for a weeks-long skeleton phase
- Cost accepted: still depends on a third-party registry that has already signalled deprecation; could disappear
- Cost accepted: July 2025 build, slightly older than the originally researched Sep 2025 release; two build sources exist until the swap

### Build from source now
- Good: only genuinely permanent fix — no registry dependency, exact researched release
- Good: fully auditable build, strong reproducibility argument at defense
- Bad: adds a Go build stage and Dockerfile maintenance during the skeleton phase, where nothing downstream benefits from it
- **Rejected because:** it pays the effort cost now for a reproducibility gain that matters only at submission, contradicting the skeleton-first driver — deferred, not discarded.

### Switch to another S3-compatible store (SeaweedFS, Garage, RustFS)
- Good: actively maintained projects with published images
- Bad: leaves the finalized stack, requires re-justifying the Bronze layer and re-verifying S3 client behavior (dbt/ClickHouse `s3()` access, Python clients)
- Bad: no durability advantage over building MinIO from source
- **Rejected because:** it solves a packaging problem by replacing a component, a larger change than option 2 with no additional benefit against the drivers.

## Consequences

- Skeleton is unblocked; the pipeline's S3 contract is unchanged, so the later swap to a self-built image requires no downstream edits.
- Known open item: a hardening-pass task to build MinIO from source at `RELEASE.2025-09-07T16-13-09Z` and replace the bitnamilegacy image before submission. This will warrant a short follow-up ADR superseding this one.
- If bitnamilegacy is pulled before then, the build-from-source step is pulled forward — no re-decision needed.
- Defense framing: the incident illustrates the supply-chain risk of relying on vendor-published images for a now-unmaintained open-source project, and why the final environment controls its own build.
