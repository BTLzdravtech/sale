##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    available_lot_ids = fields.Many2many(
        'stock.lot',
        compute="_compute_available_lot_ids",
    )

    @api.depends('product_id')
    def _compute_available_lot_ids(self):
        for rec in self:
            if (rec.product_id.tracking in ['serial', 'lot']
               and rec.order_id.warehouse_id):
                location = rec.order_id.warehouse_id.lot_stock_id
                quants = self.env['stock.quant']._read_group([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', 'child_of', location.id),
                    ('quantity', '>', 0),
                    ('lot_id', '!=', False),
                 ],['lot_id'], ['reserved_quantity:sum', 'quantity:sum'] )
                available_lot_ids = [
                    quant[0].id for quant in quants
                    if quant[1] < quant[2]]
                rec.available_lot_ids = available_lot_ids
            else:
                rec.available_lot_ids = False