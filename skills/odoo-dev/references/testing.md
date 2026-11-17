# Testing Odoo

Author: [aghyksa](https://aghyksa.com).

## Runner

Take `python`, `odoo_root`, `conf`, `db` from `odoo_env.py env`. If the project `AGENTS.md` / `CLAUDE.md`
defines its own command (a shell wrapper, `docker compose run`, ...), use that.

```bash
<python> <odoo_root>/odoo-bin -c <conf> -d <db> -u <module> \
  --test-enable --test-tags=/<module> --stop-after-init --max-cron-threads=0 \
  --http-port=<free port> > <scratch>/<module>.log 2>&1; echo exit=$?
grep -E "FAIL: |ERROR: |tests\.(stats|result)" <scratch>/<module>.log
```

- New module: `-i <module>` once; `-u` on a DB without that module runs 0 tests yet still exits 0.
- Port clash with the dev server → tests fail to start; use another port.
- Conf pins `dbfilter` (e.g. `^prod$`) and `-d` is another DB → add `--db-filter='^<db>$'`. `dbfilter`
  wins over `-d` (`odoo/http/router.py:100-120` in 20), so HttpCase `url_open` hits a DB outside the
  filter; on 20 that returns 500 "cannot call Registry.new during testing" (`odoo/tests/common.py:662-666`).
- Pass means `exit=0` and the line `0 failed, 0 error(s) of N tests` with N > 0.
- Single class: `--test-tags=/<module>:<ClassName>`.
- Native module tests (e.g. `/repair`) only run if that module is included in `-u`; in a project DB full
  of custom guards, errors in native setUpClass usually come from project guards, not our change.
  Read the traceback: no frame from our module → report it as pre-existing.

## TDD cycle

1. Write a test for one behavior; the test name describes the behavior.
2. Run it: it must fail because the feature is missing (AttributeError for a missing field, assert
   mismatch). Failing from a typo/fixture is not a valid RED.
3. Minimal code until it passes.
4. Run the full module + other touched modules (regression).
5. A test that passes immediately (code already exists) must be shown to fail: disable the code
   temporarily in `odoo-bin shell`, then `env.cr.rollback()`.

## Common patterns

- Shared base class: `class XCommon(TransactionCase)` with setup + helpers; other test classes inherit
  it, not another test class (inheriting a test class reruns all its tests).
- `@tagged("post_install", "-at_install")` for tests needing other modules fully loaded.
- HTTP endpoint: `HttpCase` + `self.url_open(...)`; setUpClass data is visible to requests because the
  test cursor is shared.
- Outgoing calls: `unittest.mock.patch("odoo.addons.<mod>.models.<file>.requests.request")`.
- `queue_job`: context `queue_job__no_delay=True` runs jobs inline in tests.
- Unique constraint: `with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.env.cr.savepoint(): ...; record.flush_recordset()`.
- Report: `self.env.ref("<xmlid>")._render_qweb_html(report.report_name, ids)[0]`.
- Onchange: call the onchange method directly on the record (or `env[model].new({...})`).
- Record rule: run `search` with `.with_user(user)`; superuser bypasses rules.
- Route security (`HttpCase`, per route): request without token/session → 401/403; as user A with user
  B's record id → 403/404; a request the server refuses (constraint, overlap, wrong channel) → assert
  `search_count` is unchanged. The last one catches a catch-all that answers 400 but still commits what
  was written before the raise, since the request's commit happens after the handler returns.

## Traps (verified in source)

- **`assertRaises` wraps the block in a savepoint and rolls it back** (17 `odoo/tests/common.py:446-450`).
  It cannot show what a caller that catches the error would commit; test that through the real route.
- **`env.flush_all()` (16+) before raw SQL** or reading an `_auto=False` SQL view.
- **Tracking values are written in precommit** (17 `addons/mail/models/mail_thread.py:502`). Run
  `self.env.flush_all()` + `self.env.cr.precommit.run()` before asserting tracking or chatter messages.
- **Tours and browser tests need `websocket-client` in the venv.** Without it they are skipped with only a
  warning (17 `odoo/tests/common.py:1011-1013`). A "pass" with 0 tours ran proves nothing.
- **Feed tests the same types the client sends** (JS sends strings for char/selection, ids as int).
- **Version-specific test APIs** (`SavepointCase`, `Form` import, `freeze_time`): `versions.md`.

## Verification outside tests

- UI: run the project preview server, check form/list/buttons, read console errors.
- PDF reports: `views-reports.md`.
