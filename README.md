# School Tracker v2

A tool for managing school fees, payments, and results. Web-based, SQLite-backed.

**Status:** In development.

## About

v2 is the integrated version of School Tracker. It replaces the JSON-based CLI (v0) and the split web interface (v1) with a single web application backed by SQLite.

Built for small schools still tracking fees and exam scores by hand.

## Delivery Model

- **Local install** — runs on the school's own laptop. No internet required. Data stays with the school.
- **Online demo** — hosted version for demonstrations and trials.

Same code, same database, different data locations.

## Stack

Python · Flask · SQLite · ReportLab · Pandas

## Development Status

- [ ] Phase 1: Foundation (data layer, models, migration)
- [ ] Phase 2: Business logic (tracker, reports, PDF)
- [ ] Phase 3: Web layer (blueprints, templates)
- [ ] Phase 4: Features (multi-term, bulk ops, email, login)
- [ ] Phase 5: Deployment (local launcher, Render)

## Predecessor Projects

- [school_tracker-sys](https://github.com/aloismutharimi/school_tracker-sys) — v0, the CLI engine
- [school_tracker-web](https://github.com/aloismutharimi/school_tracker-web) — v1, the web interface on the CLI

## License

MIT