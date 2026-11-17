---
name: odoo-dev
description: >
  Odoo 15-20 development rules with source proof: trace before coding, native first, TDD, index
  decisions, version differences, porting a module up or down between versions, controller and model
  security, ORM/test/view/report traps. Use for ANY Odoo work: fields, models, inherits, views/xpath,
  wizards, QWeb reports, cron, controllers/API, ACL/record rules/groups, porting or migrating a module,
  tests, performance, Settings, a security review, or a traceback / ParseError / "Field does not exist" /
  missing xmlid / slow query. Also for "does Odoo already have X" and "where is this model/field/xmlid".
license: MIT
metadata:
  author: aghyksa
  url: https://github.com/Aghyksa/odoo-dev
  version: 2.2.0
---

# Odoo Dev

Author: [aghyksa](https://aghyksa.com). Project `AGENTS.md` / `CLAUDE.md` and user instructions win over
this skill. One goal: **never guess**. Every claim about an Odoo API or behavior needs a `file:line` from
the project's own version. Not found → say "not in base", never invent it.

## Tool

`python3 <skill-dir>/scripts/odoo_env.py <cmd>`, where `<skill-dir>` is the folder holding this
`SKILL.md`. Run it from the project. Read-only, stdlib only, Python 3.8+.

| Command | Gives |
|---|---|
| `env` | version, odoo_root, conf, db, python, addons roots. Act on every `note` / `WARNING`, else pass `--conf` |
| `model M`, `field M F`, `xmlid MOD.ID` | where it is defined and extended, in that version |
| `method M NAME` | override chain in load order; flags overrides without `super()` |
| `routes MOD` | each HTTP route with auth, csrf, sudo; flags public + sudo |
| `port-scan PATH --to V` | `file:line` of APIs that break on version V, up or down |

Config lookup order: `--conf`, `$ODOO_RC`, an `odoo-bin -c` entry in `.vscode/launch.json` or
`.claude/launch.json`, a `*.conf` in the project or its parents, then `~/.odoorc` and `$ODOO_CONF_DIRS`
(default `~/odoo/conf:/etc/odoo`). The Odoo source must be on disk (a Docker-only setup: mount or clone
the matching version and pass `--conf`).

## Workflow

1. `env`. If the project has a code graph or index (e.g. `graphify-out/graph.json`), query it before
   grep or read.
2. Trace the real definitions (`model` / `field` / `method` / `xmlid`) before writing code.
3. Native first: official module → configure → `_inherit` → custom. Going custom needs the native option
   considered and why it falls short, with `file:line` (`references/native-first.md`).
4. TDD: a test that fails for the right reason, then code, then pass. A test that passes immediately must
   be shown able to fail.
5. Done = proven: `references/definition-of-done.md`.

## Read before you act

| When | Read |
|---|---|
| An API that may differ by version, or code copied from another version | `references/versions.md` |
| Porting a module to another version (up or down) | `references/porting.md` |
| New stored field, index, unique, compute, related | `references/fields-index.md` |
| Routes/controllers, `sudo()`, groups, rules, raw SQL, HTML in messages | `references/security.md` |
| ORM behavior, transactions, cron, data files, translations | `references/orm-traps.md` |
| Views, menus, QWeb/PDF reports, custom OWL pages/dashboards | `references/views-reports.md` |
| Writing or running tests | `references/testing.md` |

## Always

- New model: ACL, a record rule when companies/branches apply, search view, action, and a menu in
  `views/menu_items.xml` (last in the manifest).
- Security data is never `noupdate="1"`. Settings go through `res.config.settings` + `config_parameter`.
- New group category: `base.group_system` implies its highest group (Manager over User), so every
  current and future admin gets it without manual assignment. Never default it to every user: plain
  users get it by manual assignment only (`references/security.md`).
- User text in `_()` with `%s` / `%(name)s` placeholders, never an f-string inside `_()`.
- Plain field names without the project prefix (the prefix belongs to module names).
- A bug in a shared function or wrapper is fixed there once; then grep every caller.
- No `git add/commit/push/amend` without an explicit user instruction.
