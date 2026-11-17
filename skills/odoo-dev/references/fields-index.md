# New fields: index, unique, compute

Author: [aghyksa](https://aghyksa.com). Source: `index` parameter docs in `odoo/fields.py` (16–18, line
`:param str index`), `odoo/orm/fields.py:109` (19) and `odoo/orm/fields.py:107` (20). In 15 `index` is
boolean only (`fields.py:140`).

## Why decide per field

An index speeds up `search`, filters, `group by`, record rule joins, and foreign key checks when a parent
record is deleted, but each index adds `INSERT/UPDATE` cost and DB size. Decide from how the data will be
searched, including needs that will reasonably follow (reports, reminders, API lookups).

## Decision table

| Usage | Choice | Example |
|---|---|---|
| Many2one filtered, joined by record rules, or One2many inverse | `index=True` | `order_id` on lines, `categ_id` |
| Many2one mostly empty / optional | `index="btree_not_null"` (16+) | `vendor_id`, `technician_id`, optional `product_id` |
| Date/Datetime used in date filters, reports, or reminders | `index=True`; if filled later `"btree_not_null"` | `date_received`, `date_done`, `expiration_date` |
| Char searched with `ilike` (code, number, reference) | `index="trigram"` (16+, GIN `gin_trgm_ops`) | `code`, `reference` |
| Char exact lookup from API / integration | `index="btree_not_null"` | `external_id` |
| Stored related used in filter/group | `related=..., store=True, index=True` | `warehouse_id` on lines |
| Value must be unique | `_sql_constraints = [("x_uniq", "unique(x)", msg)]` (≤18) or `models.Constraint` (19+) | `code` |
| Boolean, short selection, small master table (tens of rows) | no index | flags, category master |

A native field often searched by custom code but not indexed can get an index via inherit, just set the
attribute: `sale_order_id = fields.Many2one(index="btree_not_null")`. Case: native
`repair.order.sale_order_id` has no index yet is counted every time an SO form opens (`repair_count`).

## Compute, related, store

- Compute needs complete `@api.depends` (including dotted paths), otherwise stored values go stale.
- `store=True` only when searched, grouped, used in record rules, or expensive to recompute.
- Derived data uses `related=` (readonly) or compute; never copy a value into a second field.
- Compute with `readonly=False` + `precompute=True` (16+) for defaults the user can still edit.
- A new stored column with `default` is auto-filled for existing rows on upgrade
  (`odoo/fields.py` `update_db_notnull` → `models._init_column`; 20: `odoo/orm/fields.py:1251-1253`
  `update_db` → `_init_column_data` `:1299`), so a migration is only needed for values that differ from
  the default.

## Verify the index actually exists

Odoo index name: `<table>__<column>_index` (`odoo/tools/sql.py` `make_index_name`). Check its type:

```bash
psql -h localhost -d <db> -Atc "select indexname, regexp_replace(indexdef, '^.*USING ', '')
  from pg_indexes where tablename = '<table>' order by 1"
```

`btree_not_null` shows as `btree (...) WHERE (... IS NOT NULL)`, trigram as `gin (... gin_trgm_ops)`.
Changing the index type of a field that already has an index does not rebuild the old index in an
installed DB; a fresh DB is correct immediately.

Test that guards the index (uses `odoo.tools.sql.index_exists` + `make_index_name`):

```python
INDEXED = (("repair_order", "sale_order_id"), ("my_model_line", "code"))

def test_search_columns_indexed(self):
    missing = ["%s.%s" % (t, c) for t, c in INDEXED
               if not index_exists(self.env.cr, make_index_name(t, c))]
    self.assertFalse(missing)
```
