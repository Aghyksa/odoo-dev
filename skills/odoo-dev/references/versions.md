# Odoo 15–20 version differences

Author: [aghyksa](https://aghyksa.com). Verified 2026-10-14 against Odoo Community 15.0–19.0 source;
the 20 column and the 19 → 20 section verified 2026-11-09 against Odoo Community 20.0 source
(`odoo/release.py:15` `version_info = (20, 0, 0, FINAL, 0, '')`).
Paths are relative to the Odoo checkout root. When unsure, recheck with `odoo_env.py` or grep the project
version's base. In 19 most of the ORM moved to `odoo/orm/*.py` (fields, models, decorators,
table_objects). 20 adds `odoo/orm/cache.py` (ormcache), `models_cached.py`, `query.py`, and turns
`odoo/http.py` into the `odoo/http/` package.

| Topic | 15 | 16 | 17 | 18 | 19 | 20 | Proof |
|---|---|---|---|---|---|---|---|
| List view | `<tree>` | `<tree>` | `<tree>` | `<list>` | `<list>` | `<list>` | `ir_ui_view.py` view type `('list', 'List')` from 18, `('tree', 'Tree')` in 15–17; 20 `odoo/addons/base/models/ir_ui_view.py:157` |
| `attrs` / `states` in views | used | used | **removed**, use `invisible="expr"` / `readonly=` / `required=` | same as 17 | same as 17 | same as 17 | 17 `odoo/addons/base/models/ir_ui_view.py:394` "Since 17.0, the attrs and states attributes are no longer used"; 20 same message `:510` |
| Hidden list column | – | `column_invisible` | `column_invisible` | `column_invisible` | `column_invisible` | `column_invisible` | `ir_ui_view.py` 16–18; 20 `odoo/addons/base/models/ir_ui_view.py:34` `VIEW_MODIFIERS` |
| Form chatter | `<div class="oe_chatter">` | same | same | `<chatter/>` | `<chatter/>` | `<chatter/>` | `addons/sale/views/sale_order_views.xml` 17 `oe_chatter`, 18 `<chatter`; 20 `:1081` `<chatter/>` |
| Field `index` | bool only | `True`/`"btree"`/`"btree_not_null"`/`"trigram"` | same as 16 | same as 16 | same as 16 | same as 16 | 15 `odoo/fields.py:140` (`:param bool index`); 16+ `fields.py` `btree_not_null`; 19 `odoo/orm/fields.py:109`; 20 `odoo/orm/fields.py:107` |
| `precompute` | – | yes | yes | yes | yes | yes | `fields.py` 16+; 20 `odoo/orm/fields.py:298` |
| `fields.Json` | – | yes | yes | yes | yes | yes | `fields.py` 16+ `class Json`; 20 `odoo/orm/fields_misc.py:54` |
| read_group aggregation | `group_operator` | `group_operator` | `group_operator` | `aggregator` (`group_operator` deprecated) | `aggregator` | `aggregator` only; `group_operator` no longer mapped, logs "unknown parameter" and is ignored | 18 `odoo/fields.py:481` warning "Since Odoo 18, 'group_operator' is deprecated"; 20 `odoo/orm/fields.py:316` `aggregator`, warning `:564`, no `group_operator` anywhere in `odoo/` |
| `name_get` | yes | yes | yes (display_name compute) | **removed**, override `_compute_display_name` | same as 18 | same as 18 | `odoo/models.py` 15:1845, 16:1557, 17:1677 `def name_get`; 18:1793 only `_compute_display_name`; 19 `odoo/orm/models.py:1425`; 20 `odoo/orm/models.py:1504` |
| Access check | `check_access_rights` + `check_access_rule` | same | same | `check_access(operation)` (old ones still exist) | `check_access` (old ones still exist) | `check_access` only; `check_access_rights` / `check_access_rule` **removed** | 18 `odoo/models.py:4429` `def check_access(self, operation: str)`, `:4490` `check_access_rights`; 19 `odoo/orm/models.py:4106`, `:4168`, `:4182`; 20 `odoo/orm/models.py:3443` only |
| Translation in models | `_()` | `_()` | `_()` | `self.env._()` also available | same as 18 | same as 18 | 18 `odoo/api.py:788` `def _(self, source, ...)`; 20 `odoo/orm/environments.py:344` |
| `@api.private` (block RPC) | – | yes | yes | yes | yes | yes | 16 `odoo/api.py:384`, 18 `:448`, 19 `odoo/orm/decorators.py:324`, 20 `odoo/orm/decorators.py:289` |
| SQL unique / check | `_sql_constraints` | same | same | same | **`models.Constraint`**, `_sql_constraints` only warns "no longer supported" | same as 19 | 19 `odoo/orm/table_objects.py:79` `class Constraint`, `odoo/orm/model_classes.py:162-163`; 20 `odoo/orm/table_objects.py:88`, `odoo/orm/model_classes.py:175-176` |
| Multi-column index | `_auto_init` + `tools.create_index` | same | same | same | `models.Index` / `models.UniqueIndex` | same as 19 | 19 `odoo/orm/table_objects.py:125,185`; 20 `:150,221` |
| `ir.http._generate_routing_rules` | `@classmethod (cls, modules, converters)` | same as 15 | instance method `(self, modules, converters)` | same as 17 | same as 17 | same as 17 | `odoo/addons/base/models/ir_http.py` 15:262-263, 16:178-179, 17:249, 18:361, 19:381, 20:512 |
| Python minimum | – | – | – | – | 3.10 | **3.12** | `odoo/release.py:39` `MIN_PY_VERSION` 19 `(3, 10)`, 20 `(3, 12)` |
| Owl | 1.4.11 | 2.8.4 | 2.8.2 | 2.8.2 | 2.8.4 | **3.0.0-alpha.50** (see 19 → 20) | `addons/web/static/lib/owl/owl.js` 15:5604, 16:5869, 17:5826, 18:5826, 19:5869, 20:1808 |

Other 19 proof: `column_invisible` in `odoo/addons/base/models/ir_ui_view.py`, `<chatter` in
`addons/sale/views/sale_order_views.xml`, `self.env._` in `odoo/orm/environments.py:315`, `precompute`
and `aggregator` in `odoo/orm/fields.py` (`group_operator` warning `:485-486`), `class Json` in
`odoo/orm/fields_misc.py:55`.

## 19 → 20 changes

19-era snippets that break or misbehave on 20. Proof is 20 source unless marked 19.

| Topic | 19 | 20 | Proof |
|---|---|---|---|
| Config params | `env['ir.config_parameter'].get_param(key, default)` / `set_param(key, value)` | **removed**; typed `get_str/get_bool/get_int/get_float(key, default)` and `set_str/set_bool/set_int/set_float(key, value)`. Missing or invalid value returns `default`. `get_*` check read access, so call on `.sudo()` from non-admin code. Values cached in ormcache `'stable'` | 19 `odoo/addons/base/models/ir_config_parameter.py:60,82`; 20 same file `:66-78` (`set_*`), `:100-124` (`get_*`, access check `:101`), `:131` `@api.ormcache('key', 'type_', cache='stable')`, `:40` `_clear_cache_name = 'stable'` |
| Settings `config_parameter=` | works | still works, reads through `get_str` / `get_bool` | `odoo/addons/base/models/res_config.py:220-223,268,281` |
| Clear an ormcache | `self.env.registry.clear_cache('routing')` | **`Registry.clear_cache` removed**; `self.env.transaction.invalidate_ormcache('routing')` (default `'default'`). Cache groups in `_CACHES_BY_KEY`; models set `_clear_cache_name` to auto-invalidate on write | 19 `odoo/orm/registry.py:999`; 20 `odoo/orm/environments.py:833` (class `Transaction` `:579`), `odoo/orm/registry.py:66`, `odoo/orm/models.py:486`; example `addons/website/models/website_rewrite.py:181` |
| `ormcache` import | `from odoo.tools import ormcache` | `@api.ormcache(...)` (`from odoo import api`); `odoo.tools.ormcache` still works but warns "Since 20.0 import ormcache from odoo.api" | 19 `odoo/tools/cache.py:61`; 20 `odoo/orm/cache.py:59`, `odoo/api/__init__.py:5`, `odoo/tools/__init__.py:24-27` |
| `read_group` | public `read_group(domain, fields, groupby, offset, limit, orderby, lazy)` returns dicts (deprecated) | `read_group(domain, groupby, aggregates, having, offset, limit, order)` returns list of tuples, same contract as `_read_group`; a 19-style positional call passes `fields` as `groupby`. Dict output for UI: `formatted_read_group` | 19 `odoo/orm/models.py:2755`; 20 `odoo/orm/models.py:1932`, `:1996`; `addons/web/models/models.py:1022` (19 `:802`) |
| `api` exports | `api.deprecated`, `api.Self` | both gone; added `api.ormcache`, `api.CommandValue` | 19 `odoo/api/__init__.py:10,21`; 20 `odoo/api/__init__.py:5,21` |
| `models` exports | `models.check_method_name` | gone; added `models.CachedModel` (`_clear_cache_name = 'stable'`), `models.Query`, `models.TableSQL` | 19 `odoo/models/__init__.py:28`; 20 `odoo/models/__init__.py:24,26`, `odoo/orm/models_cached.py:10,17` |
| New column default fill | `Field.update_db_notnull` → `models._init_column` | `Field.update_db` → `_init_column_data` (fills NULLs from `default`/compute on non-empty tables) | 19 `odoo/orm/fields.py:1148`; 20 `odoo/orm/fields.py:1251-1253`, `:1299` |
| HTTP layer | single module `odoo/http.py` | package `odoo/http/` (`router.py`, `routing_map.py`, `dispatcher.py`, `session.py`, ...); `from odoo.http import request, route, Controller` unchanged | 20 `odoo/http/__init__.py:14,19`, `odoo/http/routing_map.py:73,122`, `db_filter` `odoo/http/router.py:87` |
| JS URL router | `router.stateToUrl` / `router.urlToState` on the exported `router` object, patchable | unchanged (also 18); patch with `patch(router, {...})` then `router.replaceState(router.urlToState(new URL(location)))` | `addons/web/static/src/core/browser/router.js` 18:409-410, 19:418-419, 20:451-452; precedent `addons/project/static/src/project_sharing/router.js:5-30` |
| Owl version | Owl 2.8.4 | Owl `3.0.0-alpha.50` | 19 `addons/web/static/lib/owl/owl.js:5869`; 20 `owl.js:1808`, exports `:23-81` |
| Owl state / refs | `useState({...})`; `this.x = useRef("x")` + `t-ref="x"` | `proxy({...})`; class field `x = signal.ref()` + `t-ref="this.x"`, read with `this.x()`. `useState` / `useRef` not exported and not in the compat layer | 19 `addons/web/static/src/webclient/navbar/navbar.js:44`, `navbar.xml:5`; 20 `webclient/webclient.js:39`, `webclient/navbar/navbar.js:43,169`, `navbar.xml:5` |
| Owl listeners | `useExternalListener(target, ev, cb)` | `useListener(target, ev, cb)` | 19 `addons/web/static/src/webclient/webclient.js:63`; 20 same file `:67` |
| Owl props | `static props = {...}` | `props = props({...})` or `useProps({...})` with `t.*` types; core dialogs use `static propsSchema`. New `signal`, `computed`, `asyncComputed`, `effect`, `Plugin` / `usePlugin` | 20 `addons/web/static/src/views/fields/properties/property_selection.js:9-14`, `webclient/actions/action_dialog.js:10,18`, `owl.js:23-81` |
| Owl templates | bare names (`t-on-click="onClick"`) | component members via `this.` (`t-on-click.prevent="this._openAppMenuSidebar"`); `t-esc` deprecated, use `t-out` | 19 `addons/web/static/src/webclient/navbar/navbar.xml:77`; 20 same file `:71`, `owl.js:5589-5591` |
| Owl 2 compat | – | shims for `owl.props`, `owl.status`, `useComponent`, `useLayoutEffect`, `useEnv`, `useSubEnv`, `render()` | `addons/web/static/src/owl2/owl3_compatibility_layer.js:56-58,66,90,98`, `addons/web/static/src/owl2/utils.js:9-16` |
| HttpCase registry guard | – | HttpCase patches `Registry.new` to raise "cannot call Registry.new during testing"; a request whose DB fails `dbfilter` gives 500. Conf with `dbfilter` → pass `--db-filter='^<db>$'` (dbfilter wins over `-d`) | `odoo/tests/common.py:662-666`; `odoo/http/router.py:100-120` |
| CLI flags | – | new `--stop` (alias of `--stop-after-init`), `--db-system`, `--gevent-workers`, `--unsafe-policy`; `--test-enable`, `--test-tags`, `--test-file`, `--db-filter` unchanged | `odoo/tools/config.py:472`, `:436`, `:504`, `:282`; `:322`, `:324`, `:320`, `:313` |

## More differences 15–20

Verified 2026-11-11 against Community 15.0–20.0 source. Read `A → B` both ways: porting down replaces B by A.

| Topic | Change | Proof |
|---|---|---|
| User groups | ≤18 `res.users.groups_id` → 19+ `group_ids` (+ `all_group_ids`); `res.groups.users` → `user_ids`; `trans_implied_ids` → `all_implied_ids` | 18 `odoo/addons/base/models/res_users.py:386`; 19 `:257-258`, `res_groups.py:17,71`; 20 `res_users.py:250` |
| Group category | ≤18 `res.groups.category_id` → 19+ `privilege_id` (model `res.groups.privilege`) | 18 `res_users.py:191`; 19 `res_groups.py:36`, `res_groups_privilege.py:5`; 20 `res_groups.py:44` |
| Group check | ≤17 `self.user_has_groups(spec)` → 18+ `self.env.user.has_groups(spec)`; `has_group(xmlid)` in all | 17 `odoo/models.py:1542`; 18 `odoo/addons/base/models/res_users.py:1168`; 20 `:1164` |
| Domains | ≤18 `odoo.osv.expression` → 19 `odoo.fields.Domain` (expression warns) → 20 `odoo/osv` removed | 19 `odoo/orm/domains.py:196`, `odoo/osv/expression.py:173`; 20 `odoo/orm/domains.py:193` |
| `_cr` / `_uid` / `_context` | plain ≤18 → deprecated 19+, use `self.env.cr/uid/context` | 19 `odoo/orm/models.py:5931`; 20 `:5398` |
| Fetch API | 15 none; 16 `_read_group(domain, fields, groupby)`; 17+ `_read_group(domain, groupby, aggregates)`, `search_fetch`, `fetch` | 16 `odoo/models.py:2188`; 17 `:1857,1627,3826`; 20 `odoo/orm/models.py:1996,1452,3098` |
| SQL builder | ≤16 `cr.execute(query, params)` → 17+ `odoo.tools.SQL` | 17 `odoo/tools/sql.py:31`; 20 `:49` |
| Name search | 16+ `_rec_names_search`; ≤16 `_name_search(name, args, …)` → 17 `_name_search(name, domain, …)` → 18+ `_search_display_name(operator, value)` | 16 `odoo/models.py:504,1634`; 17 `:1756`; 18 `:1810`; 20 `odoo/orm/models.py:1521` |
| `@api.returns` | ≤18 → removed 19 | 18 `odoo/api.py:359`; absent in 19/20 `odoo/orm/decorators.py` |
| Recursion check | `_check_recursion` / `_check_m2m_recursion` → 18+ `_has_cycle()`; old ones warn 18, deprecated 19, removed 20 | 18 `odoo/models.py:5999,6063`; 19 `odoo/orm/models.py:5706`; 20 `:5125` |
| Company check | `check_company` + `_check_company_auto` 15+; `_check_company_domain` 17+ | 15 `odoo/models.py:516`; 17 `:4051` |
| Ormcache clear | ≤16 `registry.clear_caches()` → 17–19 `registry.clear_cache(*names)` → 20 see 19 → 20 table | 16 `odoo/modules/registry.py:685`; 17 `:710`; 19 `odoo/orm/registry.py:999` |
| `ir.cron` | `numbercall` / `doall` removed 18; progress `_notify_progress` 18 → `_commit_progress` 19+ | 17 `ir_cron.py:67`; 18 `:734`; 19 `:823,846`; 20 `:872` |
| `company_dependent` | ≤17 stored as `ir.property` rows → 18+ jsonb column, `ir.property` gone | 17 `odoo/fields.py:172`; 18 `:774` |
| Access data files | ≤19 `ir.model.access.csv` (`perm_*`) + `ir.rule` → 20 `ir.access.csv` (`id,name,model_id,group_id/id,operation,domain`) + `ir.access` records | 20 `addons/hr/security/ir.access.csv:1`, `odoo/addons/base/models/ir_access.py:66` |
| Action `view_mode` default | ≤17 `tree,form` → 18+ `list,form` | 17 `ir_actions.py:280`; 18 `:312` |
| QWeb output | `t-raw` deprecated 16+; 19 still compiles `t-esc`/`t-raw` → 20 only `t-out` / `t-field` | 16 `ir_qweb.py:2065`; 19 `:2487,2497`; 20 `:1752` |
| Tests | `SavepointCase` ≤16, gone 17; `Form` in `tests/form.py` 17+, `odoo.tests.common.Form` shim 17–19, gone 20 (`from odoo.tests import Form` works 15–20); class attr `freeze_time`: 18 date string, 19+ a `freeze_time(...)` patcher | 16 `odoo/tests/common.py:826`; 17 `:86`; 18 `:950,1057`; 19 `:1067,2753`; 20 `:3166` |
| JS modules | `odoo.define` loader exists 15–20 but addons usage 558 (16) → 2 (17): legacy widgets gone in 17; `@odoo-module` header optional 18+ under `static/src` | 17 `addons/web/static/src/module_loader.js`; 18 `odoo/tools/js_transpiler.py:675` |
| Mail tracking | ≤19 `_track_subtype` / `_track_template` → 20 `_track_log_get_default_subtype` / `_track_template_parameters` (`mail.track.mixin`) | 19 `addons/mail/models/mail_thread.py:633,743`; 20 `:704,778`, `mail_track_mixin.py:23` |
| Core renames | 17: `mail.channel` → `discuss.channel`, `stock.move.line.qty_done` → `quantity`. 19: `hr.contract` (module `hr_contract`) → `hr.version` in `hr` (`employee.version_id`), `res.partner.mobile` removed | 17 `addons/mail/models/discuss/discuss_channel.py`, `addons/stock/models/stock_move_line.py:36`; 19 `addons/hr/models/hr_version.py:35`, `hr_employee.py:48`; 18 `res_partner.py:285` (`mobile`, absent in 19) |
| Order NULLS | `order='x asc nulls first'` accepted 17+ | 17 `odoo/models.py:77` |

## Using this table

- Take the version from `odoo_env.py env`, not from the project folder name.
- Porting a module (up or down): `references/porting.md`; `odoo_env.py port-scan` turns these rows into
  `file:line` hits. "Removed" rows make install or the page fail, not just warn.
- Anything not in this table: grep that version's base, record `file:line`, and add the row here if
  useful.
