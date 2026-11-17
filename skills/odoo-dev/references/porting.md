# Porting a module between versions (up or down)

Author: [aghyksa](https://aghyksa.com). Porting = the module's code installs and works on another Odoo
version. Moving data an installed module already holds is data migration (migration scripts, OpenUpgrade):
out of scope here. Say so explicitly when the module already holds data.

1. **Source and target.** Source = manifest prefix (`'17.0.1.2.0'` → 17), confirmed by syntax (`<tree>` vs
   `<list>`, `attrs`). Target = `odoo_env.py --conf <target conf> env`.
2. **Scan.** `odoo_env.py port-scan <module> --to <target>`. Every hit gets a fix or a written reason. The
   scan only knows the rows of `versions.md`, so also read every row between source and target there
   (all hops: 17 → 15 crosses 16).
3. **Fix per layer, re-scan after each:** manifest (`version` `<target>.0.x.y.z`, `depends` on renamed or
   merged core modules, `assets`) → Python → security files → views/data XML → reports → JS/SCSS → tests.
4. **Dependencies.** Every core model, field, method, and xmlid the module uses must exist on the target:
   `odoo_env.py --conf <target conf> model|field|method|xmlid ...`. Known breaks: "Core renames" in
   `versions.md`.
5. **Downgrade.** A feature missing on the target (`precompute`, `fields.Json`, trigram index before 16;
   `SQL()`, `search_fetch` before 17; `Domain` before 19, ...) needs a replacement. Never drop behavior
   silently; list each replacement in the report.
6. **Manifest version.** Odoo prefixes a version that does not start with `<serie>.`: `'18.0'` becomes
   `18.0.18.0` (18 `odoo/modules/module.py:456`), so a later `18.0.1.0.0` compares lower and its migration
   scripts are skipped.
7. **Proof on the target.**
   - `-i` on a fresh DB with module tests passing (`0 failed ... of N`, N > 0).
   - Every view of the module opens in the browser.
   - Reports render.
   - If an existing DB is in scope, also `-u` on a copy of it. A fresh install does not validate views,
     actions, or xmlids that DB still holds.
