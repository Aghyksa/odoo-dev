# Native first

Author: [aghyksa](https://aghyksa.com). Check these candidates before building a new
model/field/cron/report/view. Verify each one in the project version's base/enterprise
(`odoo_env.py model ...`), and check whether its module is installed but unused in the project DB.

| Need | Native candidate |
|---|---|
| Field change log | `mail.thread` + `tracking=True` + chatter |
| Automation on create/write/time | `base_automation` + server action |
| Periodic schedule | `ir.cron` |
| Numbering | `ir.sequence` |
| Settings / toggles | `res.config.settings` + `config_parameter` |
| Approval | enterprise `approvals` (check conflicts with the project's custom approval module) |
| Wizard / dialog | `TransientModel` |
| Printing | QWeb report + `report.paperformat`; QR/barcode via `ir.actions.report.barcode()` |
| Email | `mail.template` |
| Reminder / task | `mail.activity` |
| Access | groups + `ir.rule` + `ir.model.access.csv`, not manual filtering in Python |
| Attachments / documents | `ir.attachment` / enterprise `documents` |
| Analysis | pivot / graph view, enterprise spreadsheet |
| Servicing customer-owned items (repair, inspection, refill) | `repair` (can be its own app: flag + root menu, `industry_fsm` pattern on `project.task`) |
| Multi-step warehouse flow | `delivery_steps` / `reception_steps` on `stock.warehouse` |
| Returns | `return_picking_type_id` + built-in Return button |
| Shelf locations & putaway | sub-locations + `stock.putaway.rule`, `removal_strategy_id` |
| Product / location labels | `product.label.layout` wizard, `stock.report_location_barcode` report |
| Stock / sales units | product `uom_id` + `product_uom` on SO lines (enable Units of Measure) |
| Derived data | `related=` / stored compute |

## How to decide

1. Write the need as one business sentence.
2. Find candidates in the table, trace their model/fields in the project version's base.
3. If native covers 80%+, use native and `_inherit` the rest.
4. If custom, record in the analysis doc: native options considered, `file:line`, and why they fall
   short.
