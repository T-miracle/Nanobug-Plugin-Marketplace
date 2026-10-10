"""Export a controlled, locally built WASM package through the production catalog builder.

Run from repository root: python -m tests.export_wasm_fixture <ZIP> <output-dir>.
The fake GitHub adapter is test-only; these records never enter the registry.
"""
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from marketplace import build_catalog


def main():
    """Inspect existing bytes without running guest code and export exact registry contract output."""
    payload = Path(sys.argv[1]).read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    version = manifest["version"]
    entry = {"id": manifest["id"], "repository": "fixture/controlled", "maintainers": ["fixture"],
             "summary": "Controlled WASM integration fixture", "category": "testing", "tags": ["controlled"],
             "versions": [{"version": version, "commit": "a" * 40, "tag": "v" + version, "asset": "plugin.zip",
                           "sha256": hashlib.sha256(payload).hexdigest(), "published_at": "2026-10-10T00:00:00Z", "changelog": "Controlled build"}]}
    api = "https://api.github.com/repos/fixture/controlled"
    url = "https://github.com/fixture/controlled/releases/download/v" + version + "/plugin.zip"
    responses = {api: {"private": False, "owner": {"login": "fixture"}},
                 api + "/license?ref=" + "a" * 40: {"license": {"spdx_id": "MIT"}},
                 api + "/commits/v" + version: {"sha": "a" * 40},
                 api + "/releases/tags/v" + version: {"draft": False, "prerelease": False,
                     "published_at": "2026-10-10T00:00:00Z", "body": "Controlled build",
                     "assets": [{"id": 456, "name": "plugin.zip", "browser_download_url": url}]}, url: payload}
    catalog = build_catalog([entry], [], responses.__getitem__)
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    (output / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "notes.zip").write_bytes(payload)


if __name__ == "__main__":
    main()
