# ORM, data, and transaction traps

Author: [aghyksa](https://aghyksa.com). Each line was verified in source; version given where it differs.

## ORM

- **Non-stored computes need `@api.depends` too.** Cache invalidation follows field dependencies
  (17 `odoo/models.py:6775` `modified`).
- **`id` of a record from `new()` or an onchange is a `NewId`.** Use `record._origin.id`
  (15 `odoo/models.py:5767`, 20 `odoo/orm/models.py:5945`).
- **Many2one without `ondelete`:** `set null` when optional, `cascade`/`restrict` when required
  (17 `odoo/fields.py:3043-3045`). Set it explicitly.
- **Postgres sorts NULL last on ASC.** A cron with `order='last_run asc'` + limit never reaches NULL rows.
  Use `order='last_run asc nulls first'` (17+, `odoo/models.py:77`).
- **Transactions run in REPEATABLE READ** (17 `odoo/sql_db.py:24`). A long transaction never sees rows
  other transactions committed after its first query; re-reading in a loop does not help.

## Transactions and cron

- **Commit point:** a request commits when the handler returns and rolls back on exception (proof in
  `security.md`). Error handling that returns instead of raising needs a savepoint.
- **Cron batches:**
  - ≤18: `env.cr.commit()` per batch.
  - 18: `_notify_progress`.
  - 19+: `_commit_progress`.
  - One failing record must not undo the batch, so use a savepoint per record.

## Data files

- **Records in a `noupdate="1"` block are created on install and never updated by `-u`**
  (17 `odoo/tools/convert.py:363`). A fix to such a record needs a migration or a data patch.
- **`<function>` inside a `noupdate="1"` block runs only on install** (17 `odoo/tools/convert.py:276-278`).
  Put one-time seeding in a post-init hook or a migration.

## Translations

- **`-u` does not overwrite translations already in the DB** unless `--i18n-overwrite`
  (18 `odoo/modules/loading.py:236`, `odoo/tools/config.py:290`).
- **A `.po` entry with no `#:` occurrence line is not imported** (18 `odoo/tools/translate.py:836`).
  Regenerate with `--i18n-export` and merge the old msgstr.
- **Source strings in English**, translations in `i18n/<lang>.po`.
