# Search engine development

This repository owns search and matching algorithms. Keep all runtime imports limited to the standard library, relative package modules, and the documented Lazarr SDK/language helpers. No database, network, process or filesystem side effects in algorithm code.

For a bug, add a regression case using public or synthetic metadata and file paths. Never commit tracker credentials, cookies, downloaded torrents or user databases.

Run pytest and ruff before publishing. Follow README's versioned package workflow: an immutable version tag must exist before main advertises its archive. Do not reuse a released version. API-breaking changes need a coordinated Lazarr release.
