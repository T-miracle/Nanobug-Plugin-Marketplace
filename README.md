# Nanobug Plugin Marketplace

[简体中文](README.zh-CN.md)

The official registry and delivery project for Nanobug plugins.

This repository currently contains the approved specification, four implementation tickets, testing ownership, and contributor/agent rules. The marketplace itself is not implemented or deployed yet.

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

Implementation commands will be documented when the corresponding tooling exists. Do not treat this planning bootstrap as a running service.
