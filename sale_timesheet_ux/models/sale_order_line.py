from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_project(self):
        if self.env.company.country_id.code == 'AR':
            self.ensure_one()
            project_so = self.order_id.project_id
            if project_so:
                project = self.env["project.project"].search([("id", "=", project_so.id)])
                if len(project) == 1:
                    return project
        return super()._timesheet_create_project()
