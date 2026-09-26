import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    pricelist_ids = fields.One2many(
        "product.pricelist",
        compute="_compute_pricelist_ids",
        string="Pricelists",
    )

    def _compute_pricelist_ids(self):
        for rec in self:
            rec.pricelist_ids = rec.pricelist_ids.search([("show_products", "=", True)])
            rec.pricelist_ids.with_context(pricelist_product_id=rec.id)._compute_price()

    @api.model
    def _get_tax_included_unit_price_from_price(
        self,
        product_price_unit,
        product_taxes,
        fiscal_position=None,
        product_taxes_after_fp=None,
    ):
        if (
            self.env.company.country_code == "AR"
            and fiscal_position
            and not fiscal_position.deduct_price_included_taxes
        ):
            fiscal_position = False
        return super()._get_tax_included_unit_price_from_price(
            product_price_unit,
            product_taxes,
            product_taxes_after_fp=product_taxes_after_fp,
            fiscal_position=fiscal_position,
        )
