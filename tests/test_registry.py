"""Exercise reviewed inputs through the same catalog builder used by Pages."""
import hashlib
import copy
import io
import json
import os
from pathlib import Path
import unittest
import zipfile

from marketplace import build_catalog


class RegistryTests(unittest.TestCase):
    """Keep package bytes real; replace only the GitHub network boundary."""

    def fixture(self):
        """Build one stable-byte contract fixture shared by every failure scenario."""
        manifest = b'{"id":"test.notes","name":"Notes","version":"1.0.0","protocol":7,"api":{"base":"^1"},"contributions":"plugin.toml","storage_limit":1024}'
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(zipfile.ZipInfo("manifest.json"), manifest)
            package.writestr(zipfile.ZipInfo("plugin.toml"), '[plugin]\nid="test.notes"\nname="Notes"\nversion="1.0.0"\nhost_version=">=0.1.0"\n')
            package.writestr(zipfile.ZipInfo("README.md"), "# Notes\nOriginal author documentation.\n\n" + "Long original text / 插件原文。\n\n" * 160)
            package.writestr(zipfile.ZipInfo("icon.svg"), '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#4682b4" d="M2 2h20v20H2z"/></svg>')
        payload = archive.getvalue()
        entry = {
            "id": "test.notes", "repository": "author/notes", "maintainers": ["author"],
            "summary": "A notes plugin", "category": "tools", "tags": ["notes"],
            "versions": [{"version": "1.0.0", "commit": "a" * 40,
                          "tag": "v1.0.0", "asset": "notes.zip", "published_at": "2026-10-10T00:00:00Z", "changelog": "First release",
                          "sha256": hashlib.sha256(payload).hexdigest()}],
        }
        responses = {
            "https://api.github.com/repos/author/notes": {"private": False, "owner": {"login": "author"}},
            "https://api.github.com/repos/author/notes/license?ref=" + "a" * 40: {"license": {"spdx_id": "MIT"}},
            "https://api.github.com/repos/author/notes/commits/v1.0.0": {"sha": "a" * 40},
            "https://api.github.com/repos/author/notes/releases/tags/v1.0.0": {
                "draft": False, "prerelease": False, "published_at": "2026-10-10T00:00:00Z",
                "body": "First release", "assets": [{"name": "notes.zip", "id": 123,
                    "browser_download_url": "https://github.com/author/notes/releases/download/v1.0.0/notes.zip"}]},
            "https://github.com/author/notes/releases/download/v1.0.0/notes.zip": payload,
        }
        return entry, responses, payload

    def test_reviewed_release_becomes_installable_catalog_without_executing_package(self):
        entry, responses, payload = self.fixture()
        catalog = build_catalog([entry], [], responses.__getitem__)
        self.assertEqual(catalog["plugins"][0]["versions"][0]["manifest"]["id"], "test.notes")
        self.assertTrue(catalog["plugins"][0]["versions"][0]["readme"].startswith("# Notes\nOriginal author documentation."))
        self.assertIn("<svg", catalog["plugins"][0]["versions"][0]["icon"])
        self.assertIsNone(catalog["plugins"][0]["downloads"])
        # Export the exact production-builder output for cross-repository consumer tests.
        if destination := os.environ.get("NANOBUG_CONTRACT_FIXTURE"):
            output = Path(destination)
            output.mkdir(parents=True, exist_ok=True)
            (output / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (output / "notes.zip").write_bytes(payload)

    def test_reject_changed_published_version_or_unreviewed_owner_transfer(self):
        entry, responses, _ = self.fixture()
        for field, value in [("sha256", "0" * 64), ("commit", "b" * 40), ("tag", "replacement")]:
            with self.subTest(field=field):
                changed = copy.deepcopy(entry)
                changed["versions"][0][field] = value
                with self.assertRaisesRegex(ValueError, "immutable"):
                    build_catalog([changed], [entry], responses.__getitem__)
        changed = dict(entry, maintainers=["other"])
        with self.assertRaisesRegex(ValueError, "transfer"):
            build_catalog([changed], [entry], responses.__getitem__)

    def test_reject_upstream_mutation_unstable_or_non_open_release(self):
        entry, responses, _ = self.fixture()
        api = "https://api.github.com/repos/author/notes"
        cases = [(api + "/commits/v1.0.0", "sha", "b" * 40, "commit mismatch"),
                 (api + "/releases/tags/v1.0.0", "prerelease", True, "stable"),
                 (api, "private", True, "public"),
                 (api + "/license?ref=" + "a" * 40, "license", {"spdx_id": "NOASSERTION"}, "license")]
        for url, key, value, message in cases:
            with self.subTest(case=message):
                changed = copy.deepcopy(responses)
                changed[url][key] = value
                with self.assertRaisesRegex(ValueError, message):
                    build_catalog([entry], [], changed.__getitem__)

    def test_reject_tampered_and_unsafe_archive_without_extraction(self):
        entry, responses, payload = self.fixture()
        url = "https://github.com/author/notes/releases/download/v1.0.0/notes.zip"
        responses[url] = payload + b"modified"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            build_catalog([entry], [], responses.__getitem__)
        archive = io.BytesIO(payload)
        with zipfile.ZipFile(archive, "a") as package:
            package.writestr("../outside", "must not extract")
        responses[url] = archive.getvalue()
        entry["versions"][0]["sha256"] = hashlib.sha256(responses[url]).hexdigest()
        with self.assertRaisesRegex(ValueError, "unsafe ZIP"):
            build_catalog([entry], [], responses.__getitem__)


if __name__ == "__main__":
    unittest.main()
