# Definition of done

Author: [aghyksa](https://aghyksa.com). Never report "done", "safe", or "ready to deploy" until every
relevant item below has proof from tool output in that session.

## Code

- [ ] `python -m py_compile` on every touched `.py`; XML parses.
- [ ] New model: ACL, record rule (branch/company when needed), search view, action, menu in
      `views/menu_items.xml` (last entry in manifest `data`).
- [ ] New group category: its highest group implied by `base.group_system`, never by `base.group_user`, with
      tests for both (`security.md`).
- [ ] Custom page (`static/src`): project design guide read first, Odoo components (no native `<select>`),
      action `path`, sticky first column on wide tables (`views-reports.md`).
- [ ] New stored field: index decided per `fields-index.md`; uniqueness via constraint.
- [ ] Compute has `@api.depends`; no duplicated data that can diverge.
- [ ] User-facing text via `_()` + placeholders.
- [ ] New/changed route: caller named, access checked before `sudo()`, refused request rolls back, no
      secret logged; anonymous / other-user / refused-request tests pass (`security.md`).
- [ ] Porting: every `port-scan` hit fixed or justified; proof on the target version (`porting.md` step 7).
- [ ] New module: complete `__manifest__.py` (`license`, `author`, `maintainer`, `website` per project
      convention), `depends` covers every referenced module, icon if the project requires one.
- [ ] `migrations/<version>/` folder exists → bump manifest version accordingly; without migrations,
      bump is optional.

## Proof

- [ ] Module tests pass: `0 failed, 0 error(s) of N tests`, N > 0.
- [ ] Regression tests of other touched modules pass; pre-existing errors are named, not hidden.
- [ ] `-u` (or `-i` for a new module) exits 0 with no `ERROR`.
- [ ] UI/print output → checked on a local server (screenshot / rendered PDF).
- [ ] Reported queries / numbers are measured, not estimated.

## Report & notes

- [ ] State what's pending: new module needs manual `-i` on deploy, prod data to fix, dependencies on
      other parties.
- [ ] Say whether the change needs a module update (stored field, view, data) or a worker restart
      (Python), in the project's own deploy terms: merged code alone is not deployed.
- [ ] Working docs (analysis, specs, plans) stay out of the module repo unless the project says otherwise.
- [ ] Project memory / graph updated if the project uses them.
- [ ] No `git add/commit/push/amend/rebase` without explicit user instruction.
