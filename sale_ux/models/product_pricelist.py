##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    price = fields.Monetary(
        compute="_compute_price",
        help="Price for product specified on the context",
    )
    show_products = fields.Boolean(
        "Show in products",
        default=True,
        help="By selecting it allows you to display the pricelist with the price of that product in the products",
    )

    def _compute_price(self):
        self.price = 0.0
        if self.env.company.country_code != "AR":
            return

        if "pricelist_product_id" in self.env.context:
            active_id = self.env.context["pricelist_product_id"]
            model = "product.product"
        elif "pricelist_template_id" in self.env.context:
            active_id = self.env.context["pricelist_template_id"]
            model = "product.template"
        else:
            return

        product = self.env[model].browse(active_id)
        for pricelist in self:
            pricelist.price = product.with_context(pricelist=pricelist.id)._get_contextual_price()

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if self.env.company.country_code != "AR" or view_type != "form":
            return arch, view
        if (
            self.env.user.has_group("sales_team.group_sale_salesman")
            or self.env.user.has_group("sales_team.group_sale_salesman_all_leads")
        ) and not self.env.user.has_group("sales_team.group_sale_manager"):
            for node in arch.xpath("//form"):
                node.set("edit", "false")
        return arch, view

    def unlink(self):
        if self.env.company.country_code == "AR":
            confirmed_orders = self.env["sale.order"].search(
                [("pricelist_id", "in", self.ids), ("state", "=", "sale"), ("country_code", "=", "AR")],
                limit=1,
            )
            if confirmed_orders:
                raise UserError(
                    _(
                        "The price list cannot be deleted because it has confirmed sales. "
                        "In these cases, we recommend archiving the list."
                    )
                )
        return super().unlink()
