# Lazarr Search Engine

Search query construction, candidate filtering/ranking, episode matching and Smart file associations for [Lazarr](https://github.com/Drun555/Lazarr).

## Boundaries and contract

This package runs locally in Lazarr. It does not access the database, network, credentials or torrent engine. The host supplies models from `lazarr.sdk` (SDK >=1.7,<2), language utilities, metadata, candidate evidence and the real torrent file list.

Engine API 1 contains:
- `provider_utils.search_queries(media, season=None, year=None)`: complete ordered queries, including the requested named season and its premiere year. Optional for older hosts/engines. Season metadata uses `number`, `title`, and `air_date`; generic season labels are ignored.
- `provider_utils.search_titles(media)`: ordered search title alternatives; description evidence helpers are shared with provider adapters.
- `selection.assess_candidate(candidate, request, stage=1, criteria=())`: recomputed stage score, grouped signals, thresholds and blockers. Weights and thresholds are centralized in `selection.py`; reports require SDK 1.7.
- `selection.reject_reason(candidate, requests, ...)` and `candidate_rank(candidate, requests)`: inexpensive shortlist filtering and ranking.
- `matcher.Matcher().evaluate(candidate, requests, files, infohash)`: evaluations, explanations and a download plan. The host validates and applies it.
- `associations.related_files(files, bindings)`: unambiguous video/audio/subtitle associations for the manual editor.

A standalone `TV-N`/`ТВ-N` release tag may denote broadcast order. When the release confirms a requested season by its distinctive metadata title and a single premiere year, that season supplies the hint for files without season numbers. Explicit file seasons and provider episode mappings remain authoritative; no series-specific offsets are used.

Tracker adapters, HTTP/Trawl, rate limiting, scheduling, persistence and downloads remain in Lazarr. Manual mappings are never overwritten by a policy update.

Before broad discovery, the host refreshes topics selected for completed subtasks of the same task and season. The engine evaluates these refreshed candidates with the same scoring rules. If they cover every requested episode, the host can skip broad discovery; otherwise it searches normally and retains the refreshed candidates for comparison. Manual alternative searches always continue broad discovery. This ordering belongs to the host because it requires persisted selections and network access; it does not add a scoring bonus or bypass episode checks.

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

## Scoring and manual fallback

Title/topic/files thresholds are 20/40/100. Identity contributes one strongest
signal (ID 120, named season + year 90, series alias + year 70, name only 20).
Season numbers contribute +30 or -10. Episode coverage contributes +10/-10 in
titles, replaced by +60/-20/0 for matched/missing/ambiguous actual files.
Required contradictions block automatic selection regardless of the total.
An otherwise plausible release with missing/ambiguous episodes remains a manual
candidate; the host recommends its highest scoring option and asks for explicit
file mapping before downloading. Engine tests cover this distinction.
