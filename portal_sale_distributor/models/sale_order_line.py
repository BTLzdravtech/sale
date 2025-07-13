##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _compute_purchase_price(self):
        # DONETODO vk: lock for arg
        if self.company_id.country_id == self.env.ref('base.ar'):
            self = self.sudo()
            super()._compute_purchase_price()
        else:
            return super()._compute_purchase_price()
