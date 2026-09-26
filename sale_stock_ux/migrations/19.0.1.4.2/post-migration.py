from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    sale_orders = env["sale.order"].search([])
    env.add_to_compute(env["sale.order"]._fields["with_returns"], sale_orders)
    sale_orders._recompute_recordset(["with_returns"])

    sale_order_lines = env["sale.order.line"].search([])
    env.add_to_compute(env["sale.order.line"]._fields["delivery_status"], sale_order_lines)
    sale_order_lines._recompute_recordset(["delivery_status"])
