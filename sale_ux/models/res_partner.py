from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'


    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        if view_type == "form" and self.env.company.country_code == "AR":
            view_id = self.env.ref("sale_ux.view_contact_allow_any_user_as_salesman_ar").id
        return super().get_view(view_id=view_id, view_type=view_type, **options)
