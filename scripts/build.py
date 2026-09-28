"""Build a deterministic package and catalog for an immutable release tag."""

from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
package = root / "src/lazarr_search_engine"
namespace = {}
exec((package / "__init__.py").read_text(), namespace)
version = namespace["VERSION"]
output = root / "dist"
output.mkdir(exist_ok=True)
archive = output / "engine.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as stream:
    for path in sorted(package.glob("*.py")):
        info = zipfile.ZipInfo(path.name, date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        stream.writestr(info, path.read_bytes())
manifest = {
    "version": version,
    "api": 1,
    "sdk": ">=1.7,<2",
    "url": f"https://raw.githubusercontent.com/Drun555/lazarr-search-engine/v{version}/engine.zip",
    "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
}
(output / "catalog.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(archive)
