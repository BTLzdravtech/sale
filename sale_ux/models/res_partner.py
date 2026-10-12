from odoo import _, api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        if self.env.company.country_code != "AR":
            return partners

        pricelist = self.env["product.pricelist"].search(
            [("company_id", "in", [False, self.env.company.id])],
            limit=1,
            order="sequence",
        )
        defaults = self.env["ir.default"]._get_model_defaults(self._name)
        for partner, vals in zip(partners, vals_list):
            if "specific_property_product_pricelist" in vals or partner.parent_id:
                continue

            default_pricelist_id = vals.get("property_product_pricelist") or defaults.get("property_product_pricelist")
            partner.specific_property_product_pricelist = (
                default_pricelist_id if default_pricelist_id and default_pricelist_id != pricelist.id else False
            )
        return partners

    @api.model
    def get_import_templates(self):
        if self.env.context.get("res_partner_search_mode") == "customer":
            return [
                {
                    "label": _("Import Template for Customers"),
                    "template": "/sale_ux/static/xls/res_partner.xlsx",
                }
            ]
        return super().get_import_templates()
