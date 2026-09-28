# Lazarr Search Engine

Search query construction, candidate filtering/ranking, episode matching and Smart file associations for [Lazarr](https://github.com/Drun555/Lazarr).

## Boundaries and contract

This package runs locally in Lazarr. It does not access the database, network, credentials or torrent engine. The host supplies models from `lazarr.sdk` (SDK >=1.6,<2), language utilities, metadata, candidate evidence and the real torrent file list.

Engine API 1 contains:
- `provider_utils.search_titles(media)`: ordered search title alternatives; description evidence helpers are shared with provider adapters.
- `selection.reject_reason(candidate, requests, ...)` and `candidate_rank(candidate, requests)`: inexpensive shortlist filtering and ranking.
- `matcher.Matcher().evaluate(candidate, requests, files, infohash)`: evaluations, explanations and a download plan. The host validates and applies it.
- `associations.related_files(files, bindings)`: unambiguous video/audio/subtitle associations for the manual editor.

Tracker adapters, HTTP/Trawl, rate limiting, scheduling, persistence and downloads remain in Lazarr. Manual mappings are never overwritten by a policy update.

## Development

Use Python 3.12+ with a compatible Lazarr checkout installed (`pip install -e ../Lazarr -e . pytest ruff`). Run `pytest -q`, `ruff check src tests scripts`, then `python scripts/build.py`. Lazarr retains integration tests; this repository owns algorithm regression cases.

## Publish an update

1. Change algorithms and add regression fixtures/tests.
2. Increment VERSION in `src/lazarr_search_engine/__init__.py` and the package version in `pyproject.toml`.
3. Run the tests and `python scripts/build.py`.
4. Copy `dist/engine.zip` and `dist/catalog.json` to the repository root; commit these together with source changes.
5. Push an immutable tag `v<version>` for that commit before updating `main`.
6. Publish a GitHub release for the tag. Never replace an existing version/tag/archive.

The default catalog is `https://raw.githubusercontent.com/Drun555/lazarr-search-engine/main/catalog.json`. Archive URLs point at version tags; SHA-256 verifies the exact bytes. HTTPS and control of this repository are the trust boundary: packages are executable Python, not sandboxed rule files. Only configure a repository you trust.

Lazarr checks hourly, rejects incompatible/corrupt packages, pins a version for each operation and retains the previous package for rollback. No network access is required to use the installed or bundled version. Rollback pauses automatic updates until an explicit update. Breaking contract changes require a host release; compatible algorithm fixes do not.
