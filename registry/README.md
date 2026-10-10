# Reviewed registry

Only approved `<plugin-id>.json` records belong here. No test plugin is listed in production.

Submit one stable version per PR, starting from this shape:

```json
{
  "id": "your-plugin-id",
  "repository": "owner/plugin-repository",
  "maintainers": ["owner"],
  "summary": "What the plugin does",
  "category": "tools",
  "tags": ["example"],
  "versions": [{
    "version": "1.0.0",
    "commit": "full 40-character source commit",
    "tag": "v1.0.0",
    "asset": "plugin.zip",
    "published_at": "2026-10-10T00:00:00Z",
    "changelog": "Release notes captured for this review",
    "sha256": "lowercase 64-character SHA-256"
  }]
}
```

Use an SPDX-recognized open-source license at the pinned source commit. The repository owner must be among the maintainers. The reviewer must verify that the PR submitter controls that account/repository; listing a name does not prove ownership. For organizations, obtain an acknowledged organization maintainer review.

Every version needs a fresh registry PR and human review. Do not alter or remove existing version records. The validator resolves the tag to the pinned commit, checks the exact ZIP asset, verifies its digest and inspects it using Nanobug's public Package validator. It never runs plugin code. Source/build provenance and requested permission necessity still require review.

Ownership transfers require a **separate PR with no version changes**, acknowledgments from the previous and new owners, and a JSON receipt in `transfers/` containing `id`, `from_repository`, `from_maintainers`, `to_repository`, `to_maintainers`. New versions follow only after the transfer merges. Never reuse an identity for unrelated code.

The publisher snapshots `README.md`, optional `icon.svg`, the complete runtime manifest, declaration host constraint, and the intersection of native-service platform constraints from the digest-pinned package. Copy the release timestamp and notes into the immutable version record during review, so later edits to upstream Release text cannot silently rewrite history. An empty platform list means portable. No translation is invented. Download counts remain null until ticket 02.
