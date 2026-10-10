"""Build a static, reviewed catalog without importing or executing plugin code.

Python 3.11+ standard library only. The caller supplies GitHub I/O so integration
fixtures consume precisely the same output contract as the production publisher.
"""
import argparse
import hashlib
import io
import json
import re
import stat
import subprocess
import tempfile
import tomllib
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

MAX_PACKAGE = 64 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
OPEN_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC",
                 "MPL-2.0", "GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0",
                 "AGPL-3.0", "Unlicense", "CC0-1.0", "Zlib", "BSL-1.0"}


def require(condition, message):
    """Reject a candidate with a reviewable reason instead of emitting partial data."""
    if not condition:
        raise ValueError(message)


def inspect_package(payload, digest):
    """Return inert manifest/resources after size, path, duplicate and digest checks."""
    require(isinstance(payload, bytes) and len(payload) <= MAX_PACKAGE, "package size")
    require(hashlib.sha256(payload).hexdigest() == digest, "package SHA-256 mismatch")
    resources = {}
    expanded = 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        require(len(archive.infolist()) <= 512, "too many ZIP entries")
        for member in archive.infolist():
            name = member.filename
            parts = name.rstrip("/").split("/")
            require(name and not name.startswith("/") and "\\" not in name
                    and ":" not in name and all(p not in ("", ".", "..") for p in parts)
                    and all(not p.endswith((".", " ")) for p in parts)
                    and all(not re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p) for p in parts),
                    "unsafe ZIP path")
            require(not stat.S_ISLNK(member.external_attr >> 16), "ZIP symlink")
            require(name.casefold() not in resources, "duplicate ZIP path")
            expanded += member.file_size
            require(expanded <= MAX_EXPANDED, "expanded package quota")
            resources[name.casefold()] = (name, b"" if member.is_dir() else archive.read(member))
    files = {name: body for name, body in resources.values()}
    manifest = json.loads(files["manifest.json"])
    require(manifest.get("protocol") == 7 and manifest.get("api"), "current protocol required")
    require(re.fullmatch(r"[a-z0-9-][a-z0-9.-]{0,99}", manifest.get("id", "")), "invalid plugin id")
    require(manifest.get("component") or manifest.get("contributions"), "empty plugin")
    for field in ("component", "contributions"):
        if manifest.get(field):
            require(manifest[field] in files, f"missing {field}")
    host_version = "*"
    if manifest.get("contributions"):
        declaration = tomllib.loads(files[manifest["contributions"]].decode("utf-8"))["plugin"]
        require(all(declaration[k] == manifest[k] for k in ("id", "name", "version")), "declaration identity mismatch")
        host_version = declaration["host_version"]
    # Empty platform declarations mean portable; otherwise all mandatory native services must agree.
    platform_sets = [set(s["platforms"]) for s in manifest.get("services", {}).values() if s.get("platforms")]
    platforms = sorted(set.intersection(*platform_sets)) if platform_sets else []
    require(not platform_sets or platforms, "native services have no common platform")
    readme = files.get("README.md", b"").decode("utf-8")
    require(len(readme.encode()) <= 1024 * 1024, "README snapshot too large")
    # SVG stays an inert snapshot; renderers must disable resource resolution.
    icon = files.get("icon.svg", b"").decode("utf-8")
    require(len(icon.encode()) <= 256 * 1024, "icon snapshot too large")
    return {"manifest": manifest, "host_version": host_version,
            "platforms": platforms, "readme": readme, "icon": icon}


def build_catalog(entries, baseline, fetch, validate=None, transfers=()):
    """Validate reviewed registry entries against GitHub and immutable base records.

    `fetch` returns JSON for api.github.com and bytes for Release assets. It must
    enforce HTTPS and bounded reads. Failures abort the complete publication.
    Ownership changes use a separate, manually reviewed transfer before versions.
    """
    previous = {e["id"]: e for e in baseline}
    seen = set()
    plugins = []
    for entry in entries:
        identity, repo = entry["id"], entry["repository"]
        require(identity not in seen, "duplicate plugin ID")
        seen.add(identity)
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo), "GitHub repository required")
        maintainers = entry["maintainers"]
        require(maintainers and all(re.fullmatch(r"[A-Za-z0-9-]+", m) for m in maintainers), "maintainers required")
        require(entry["category"] and entry["summary"] and isinstance(entry["tags"], list), "listing metadata required")
        old = previous.get(identity)
        if old:
            if old["repository"] != repo or old["maintainers"] != maintainers:
                transfer = {"id": identity, "from_repository": old["repository"], "from_maintainers": old["maintainers"],
                            "to_repository": repo, "to_maintainers": maintainers}
                require(transfer in transfers and old["versions"] == entry["versions"],
                        "ownership changes require separate transfer review without version changes")
            old_versions = {v["version"]: v for v in old["versions"]}
            new_versions = {v["version"]: v for v in entry["versions"]}
            require(all(new_versions.get(v) == record for v, record in old_versions.items()), "published version is immutable")
        api = "https://api.github.com/repos/" + repo
        repository = fetch(api)
        require(not repository["private"], "repository must be public")
        require(repository["owner"]["login"].casefold() in {m.casefold() for m in maintainers}, "repository owner must acknowledge maintenance")
        versions, version_ids = [], set()
        for release in entry["versions"]:
            version, commit, tag, asset = (release[k] for k in ("version", "commit", "tag", "asset"))
            require(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version), "stable semver required")
            require(version not in version_ids, "duplicate version")
            version_ids.add(version)
            require(re.fullmatch(r"[0-9a-f]{40}", commit), "full source commit required")
            license_info = fetch(api + "/license?ref=" + commit)
            license_id = license_info["license"]["spdx_id"]
            require(license_id in OPEN_LICENSES, "recognized open-source license required")
            quoted_tag = urllib.parse.quote(tag, safe="")
            require(fetch(api + "/commits/" + quoted_tag)["sha"] == commit, "Release tag/source commit mismatch")
            details = fetch(api + "/releases/tags/" + quoted_tag)
            require(not details["draft"] and not details["prerelease"], "stable published Release required")
            require(isinstance(release["changelog"], str) and len(release["changelog"].encode()) <= 1024 * 1024, "changelog quota")
            require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", release["published_at"]), "UTC release timestamp required")
            if not old or version not in {v["version"] for v in old["versions"]}:
                require(release["changelog"] == (details.get("body") or "") and release["published_at"] == details["published_at"], "new release snapshot must match upstream")
            candidates = [a for a in details["assets"] if a["name"] == asset]
            require(len(candidates) == 1 and asset.endswith(".zip"), "one exact ZIP asset required")
            download = candidates[0]["browser_download_url"]
            require(download.startswith("https://github.com/" + repo + "/releases/download/"), "asset repository mismatch")
            payload = fetch(download)
            snapshot = inspect_package(payload, release["sha256"])
            if validate:
                validate(payload)
            require(snapshot["manifest"]["id"] == identity and snapshot["manifest"]["version"] == version, "package identity mismatch")
            versions.append(dict(snapshot, version=version, commit=commit, license=license_id,
                                 url=download, asset_id=candidates[0]["id"], sha256=release["sha256"],
                                 published_at=release["published_at"], changelog=release["changelog"],
                                 withdrawn=False))
        require(versions, "at least one reviewed version required")
        plugins.append({k: entry[k] for k in ("id", "repository", "maintainers", "summary", "category", "tags")} |
                       {"versions": versions, "downloads": None})
    require(set(previous).issubset(seen), "withdraw versions explicitly; do not erase history")
    return {"schema": 1, "plugins": sorted(plugins, key=lambda p: p["id"])}


def fetch_github(url):
    """Read public GitHub resources only, bounded, with no credentials sent to assets."""
    request = urllib.request.Request(url, headers={"User-Agent": "Nanobug-Plugin-Marketplace",
                                                "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        require(response.url.startswith("https://"), "HTTPS redirect required")
        payload = response.read(MAX_PACKAGE + 1)
    require(len(payload) <= MAX_PACKAGE, "response too large")
    return json.loads(payload) if url.startswith("https://api.github.com/") else payload


def main():
    """Build into an explicit output directory; CI deploys only reviewed main commits."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("registry"))
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--baseline-dir", type=Path)
    parser.add_argument("--transfers", type=Path, default=Path("transfers"))
    parser.add_argument("--validator", type=Path, help="Built Nanobug inspect_package executable")
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    entries = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.registry.glob("*.json"))]
    # Main-branch publishing preserves already-reviewed notes; PR validation supplies an explicit base.
    baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline else entries
    if args.baseline_dir:
        baseline = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.baseline_dir.glob("*.json"))]
    transfers = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.transfers.glob("*.json"))]
    require(not entries or args.validator and args.validator.is_file(), "Nonempty publication requires Nanobug Package validator")
    def validate(payload):
        """Only the pinned host validator executes, never code or commands from an incoming package."""
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder) / "candidate.zip"
            package.write_bytes(payload)
            subprocess.run([str(args.validator.resolve()), str(package)], check=True, timeout=60,
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    catalog = build_catalog(entries, baseline, fetch_github, validate, transfers)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / ".nojekyll").touch()


if __name__ == "__main__":
    main()
