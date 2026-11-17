# Security

Author: [aghyksa](https://aghyksa.com). ACL and record rules do not protect a `sudo()` call.

## Controllers / API

- **Every route names who may call it.** `odoo_env.py routes <module>` lists auth, csrf, and sudo per route.
  The default `auth` is `'user'` (17 `odoo/http.py:877`, 20 `odoo/http/routing_map.py:298`).
- **`auth='public'` / `'none'` (or a custom token wrapper) plus `sudo()` hands the records to anyone who can
  reach the URL.**
  - Authenticate first, then check as the real user before `sudo()`:
    `record.with_user(user).check_access('read')` (18+; ≤17 `check_access_rights` + `check_access_rule`).
  - Scope searches by the caller (`employee_id = caller`), never by an id from the URL alone.
- **A handler that returns normally is committed.**
  - Proof: 20 `odoo/http/retrying.py:112`; 16–19 `odoo/service/model.py` `retrying()` (16 `:192`,
    19 `:239`); 15 `odoo/http.py:264`.
  - So a `try/except` that turns an exception into an error response keeps everything written before the
    raise. Example: a check that raises after INSERT in an overridden `create`.
  - Wrap the write in `with self.env.cr.savepoint():`, or roll back in the catch-all.
  - When a shared wrapper or decorator does the catching, fix it there once, then grep every route that
    uses it.
- **Never store secrets in logs, chatter, or fields:** tokens, passwords, OTPs, base64 files/PDFs. Mask them
  before an API log writes the request or response.
- **Touching or migrating a vendored module with routes: porting is not auditing.** Run `routes`, check each
  one, and report findings even when they are out of scope.

## Models

- **`sudo()` keeps the uid and only sets superuser mode** (17 `odoo/models.py:5941`).
  `with_user(bot).sudo()` acts as the bot with all rights.
- **Computes and onchanges run as the current user.** A compute on a shared model (sale order, picking)
  that reads an ACL-restricted model raises AccessError for normal users. Read only the needed values with
  `sudo()`, aggregated (`_read_group`), and never return the sudo records.
- **`<menuitem groups="a,-b">` links `a` and unlinks `b`; it never replaces the existing groups**
  (17 `odoo/tools/convert.py:322-326`).
- **A new group category gives its highest group to every Settings admin.** In the same security file:
  `<record id="base.group_system" model="res.groups"><field name="implied_ids" eval="[(4, ref('group_x_manager'))]"/></record>`
  (15 `addons/website/security/website_security.xml:26-27`, 18 `addons/product/security/product_security.xml:28-29`,
  `addons/mail/data/mail_groups.xml` 19 `:19-20`, 20 `:20-21`).
  - Highest only: lower groups follow through the top group's `implied_ids` (Manager implies User).
  - Never by default to every user: `base.group_user` (or any broad group) never implies the new group, no
    mass `users`, no default user template. Plain users get it by manual assignment only. The new group
    implying `base.group_user` is fine. Test that a plain `base.group_user` user does not see its menu.
  - Reaches current admins on install and admins added later: 15-18 copy implied groups to the users on
    write (18 `odoo/addons/base/models/res_users.py:1495-1497`), 19+ compute effective groups from implied
    ones (19 `odoo/addons/base/models/res_users.py:447-449`).
  - The other native pattern, `users` = `base.user_root` + `base.user_admin`
    (18 `addons/stock/security/stock_security.xml:29`), reaches only the `admin` login, not other admins.
  - Test: `new_test_user(env, 'x', groups='base.group_user,base.group_system').has_group('<module>.<top group>')`,
    with no manual group assignment in `setUpClass`.
- **Access lives in data, not in Python filtering:** groups + `ir.model.access` + `ir.rule` (≤19), or
  `ir.access` (20; see `versions.md`). Multi-company: `check_company=True` + `_check_company_auto` (15+).
- **Raw SQL bypasses ACL, record rules, and company checks.** Use params or `SQL()` (17+). Never put user
  input in the query with an f-string or `%`.
- **HTML:**
  - `message_post` escapes a `str` body and keeps `Markup` (17 `addons/mail/models/mail_thread.py:2220`).
  - Build HTML with `Markup` + escaped values.
  - In QWeb use `t-out`, never `t-raw`.

## Tests per route (`HttpCase`)

- No credentials → 401/403.
- User A with user B's id → 403/404.
- Refused request → `search_count` unchanged.
- Details: `testing.md`.
