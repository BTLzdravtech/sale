##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_status = fields.Selection(
        selection_add=[
            ("no", "Nothing to Deliver"),
        ],
        readonly=True,
        default="no",
    )
    force_delivery_status = fields.Selection(
        [
            ("no", "Nothing to Deliver"),
            ("full", "Fully Delivered"),
        ],
        tracking=True,
        copy=False,
    )

    with_returns = fields.Boolean(
        compute="_compute_with_returns",
        store=True,
    )

    @api.depends("order_line.quantity_returned")
    def _compute_with_returns(self):
        for order in self:
            order.with_returns = any(line.quantity_returned for line in order.order_line)

    def action_cancel(self):
        ar_orders = self.filtered(lambda order: order.company_id.country_code == "AR")
        for order in ar_orders.filtered(
            lambda order: order.picking_ids.filtered(lambda picking: picking.state == "done")
        ):
            raise UserError(
                _("Unable to cancel sale order %s as some deliveries" " have already been done.") % (order.name)
            )
        if ar_orders:
            super(SaleOrder, ar_orders.with_context(cancel_from_order=True)).action_cancel()
        if other_orders := self - ar_orders:
            super(SaleOrder, other_orders).action_cancel()
        return True

    @api.depends("picking_ids", "picking_ids.state", "force_delivery_status")
    def _compute_delivery_status(self):
        super()._compute_delivery_status()
        for order in self.filtered(lambda order: order.company_id.country_code == "AR"):
            if not order.picking_ids or all(picking.state == "cancel" for picking in order.picking_ids):
                order.delivery_status = "no"
                continue
            if order.force_delivery_status:
                order.delivery_status = order.force_delivery_status
                continue

    def write(self, vals):
        self.filtered(lambda order: order.company_id.country_code == "AR").check_force_delivery_status(vals)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        companies = self.env["res.company"].browse([vals["company_id"] for vals in vals_list if vals.get("company_id")])
        for vals in vals_list:
            company = companies.filtered(lambda record: record.id == vals.get("company_id")) or self.env.company
            if company.country_code == "AR":
                self.check_force_delivery_status(vals)
        return super().create(vals_list)

    @api.model
    def check_force_delivery_status(self, vals):
        if vals.get("force_delivery_status") and not self.env.user.has_group("base.group_system"):
            group = self.env.ref("base.group_system").sudo()
            if group.privilege_id:
                raise UserError(
                    _('Only users with "%s / %s" can Set Delivered manually') % (group.privilege_id.name, group.name)
                )
            else:
                raise UserError(_('Only users with "%s" can Set Delivered manually') % (group.name))

    def _get_protected_fields(self):
        protected_fields = super()._get_protected_fields()
        if self.env.company.country_code == "AR":
            protected_fields += ["picking_policy", "warehouse_id"]
        return protected_fields
