##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_purchase_price(self):
        if self.env.company.country_id.code == 'AR':
            self = self.sudo()
            super()._compute_purchase_price()
        else:
            super()._compute_purchase_price()
