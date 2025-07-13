##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_update_prices(self):
        # DONETODO vk: lock for arg
        if self.env.company.country_code == 'AR':
            super().action_update_prices()
            self.order_line._compute_purchase_price()
            return True
        else:
            return super().action_update_prices()
