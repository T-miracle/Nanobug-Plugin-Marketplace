# Nanobug Plugin Marketplace

[简体中文](README.zh-CN.md)

The official registry and delivery project for Nanobug plugins.

Ticket 01 implements reviewed registry publication and native first installation in Nanobug. Download statistics, update notifications and version management remain in ticket 02; official plugin migration remains in tickets 03–04. See the [verification record](docs/verification/01-reviewed-install-2026-10-10.md) for the actual delivery status.

## Scope

- An in-editor marketplace for discovery, downloads, download counts, version history and compatible-version installation.
- Public, open-source plugins submitted through reviewed pull requests.
- Static registry data on GitHub Pages; plugin ZIPs on each author's GitHub Releases.
- Seven independently maintained official plugins; no bundled plugins in the final editor distribution.
- No separate marketplace website, ratings, payments, private plugin sources or extra backend.

## Documentation

- [Documentation index](docs/README.md)
- [Execution specification](docs/specs/plugin-marketplace.md)
- [Four tickets and testing plan](docs/tickets/README.md)
- [Publication records](docs/tickets/publication.json)
- [Agent instructions](AGENTS.md)

The Nanobug editor implements the native UI and installation runtime. Individual plugin repositories own plugin source and release assets. This repository owns registry data, review and publication workflows, statistics, and this project's planning records.

## Build and contribute

Python 3.11+ is sufficient for the catalog builder and its tests:

```powershell
# Validate registry invariants using deterministic ZIP and GitHub fixtures.
python -m unittest discover -s tests -v
# Build an empty catalog, or add --validator <inspect_package.exe> for registered plugins.
python marketplace.py --output dist
```

Submit a [registry record](registry/README.md) through a pull request. Every version requires human review. Ownership transfers use a [separate review](transfers/README.md). PR validation uses the trusted base builder and a pinned Nanobug `Package` validator; it never runs guest code. Build that validator from the revision in `.github/validator.json` with `cargo build --locked -p plugin-runtime --example inspect_package` in the Nanobug repository.

The `Reviewed catalog` workflow publishes only main-branch data to [catalog.json](https://t-miracle.github.io/Nanobug-Plugin-Marketplace/catalog.json). Pages must use **GitHub Actions** as its source. Only `dist/` is uploaded; there is no separate website. The registry starts empty until a real plugin passes review; controlled test packages are not published.

The native client keeps an inert catalog cache with its last successful fetch time. A failed refresh disables new market installations until a refresh succeeds. Details never fetch embedded Markdown images or resolve SVG file/network references. Explicit source and feedback controls open the reviewed GitHub repository. Installation requires consent, a matching SHA-256 and manifest, compatibility and workspace trust; existing installed IDs cannot be reinstalled through ticket 01.
