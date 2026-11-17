# Views, menus, reports

Author: [aghyksa](https://aghyksa.com). View syntax per version: `versions.md`.

## Views

- **XPath anchors must exist in the arch of the Odoo the module runs on** (`odoo_env.py env` of that
  server). A newer local checkout can hide a missing anchor.
- **Readonly fields are not sent on save unless `force_save="1"`**
  (17 `addons/web/static/src/model/relational_model/record.js:596`).
- **An XML comment must not contain `--`** (XML 1.0). The file fails to load.

## Menus (`views/menu_items.xml`, last in the manifest)

- **One `<menuitem>` per line,** with every attribute on that line.
- **Flat `parent=`, indented 4 spaces per level,** with a blank line between top-level sections.
- **Attribute order:** `id`, `name`, `parent`, `action`, `sequence`, `web_icon`, `groups`.

```xml
<menuitem id="menu_my_root" name="My App" sequence="100" web_icon="my_module,static/description/icon.png" groups="base.group_user"/>
    <menuitem id="menu_my_record" name="Records" parent="menu_my_root" action="action_my_record" sequence="10"/>

    <menuitem id="menu_my_config" name="Configuration" parent="menu_my_root" sequence="90" groups="base.group_system"/>
        <menuitem id="menu_my_tag" name="Tags" parent="menu_my_config" action="action_my_tag" sequence="10"/>
```

## Custom pages (OWL client actions, dashboards)

- **Load the project's design/UI skill or guide before the first `static/src` edit**, if one exists. Decide
  what the eye finds first, second, third, then write the template.
- **Odoo components, never bare browser controls.** A picker is `Dropdown` + `DropdownItem`
  (`@web/core/dropdown/dropdown`, `dropdown_item`), not a native `<select>`. A `selected` class on the item
  already draws the checkmark (18 `addons/web/static/src/webclient/webclient.scss:70-90`).
- **A custom action gets a `path`** so the URL reads `/odoo/<path>` instead of `/odoo/action-<id>`
  (18 `odoo/addons/base/models/ir_actions.py:64`; lowercase, dash/underscore, no `action-`/`m-` prefix,
  `:76-86`). A client action can carry it (18 `addons/mail/views/discuss_channel_views.xml:122`).
- **Wide tables:** sticky first column on an opaque background (a translucent theme panel lets scrolled
  cells show through), short headers, `tabular-nums`, zero shown as a dash. Add an empty state and a
  warning when required setup is missing.
- **Reuse the project's theme tokens;** no new palette.
- **SCSS (18, libsass):** `clamp(2rem, 1.4rem + 1.6vw, 3rem)` fails with "Incompatible units" and the page
  shows "A css error occured, using an old style". The failed bundle stays cached in the running process:
  restart the server after the fix.
- **Render check:** data shaped like production (thin local data: read production read-only and feed it to
  the local page), screenshots at desktop and phone width, empty console, no CSS error banner.

## QWeb PDF (wkhtmltopdf)

- **wkhtmltopdf loads CSS from `report.url`** (17 `odoo/addons/base/models/ir_actions_report.py:252`),
  falling back to `web.base.url`. Point it at an address the server itself can reach.
- **wkhtmltopdf exit code 1 is accepted** (17 `ir_actions_report.py:521`), so a broken PDF can still return
  200. Check the rendered PDF (`pdftoppm -png`), not the status or the size.
- **wkhtmltopdf (old WebKit) has no `writing-mode`.** Rotate with `-webkit-transform: rotate(-90deg)`.
- **Render via `odoo-bin shell` + `_render_qweb_pdf`.** The local HTTP server must be running, or the
  output is unstyled.
