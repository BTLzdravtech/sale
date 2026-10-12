##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        vals = super()._prepare_stock_return_picking_line_vals_from_move(stock_move)
        if stock_move.company_id.country_code == "AR":
            vals["to_refund"] = True
        return vals

    def action_create_exchanges(self):
        if any(self.product_return_moves.mapped("to_refund")):
            raise UserError(_("You cannot create exchanges for return lines marked to refund."))
        return super(StockReturnPicking, self.with_context(is_exchange_move=True)).action_create_exchanges()


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    def _prepare_move_default_values(self, new_picking):
        vals = super()._prepare_move_default_values(new_picking)
        if self.env.context.get("is_exchange_move"):
            vals["is_exchange_move"] = True
        return vals

    def _prepare_picking_default_values_based_on(self, picking):
        vals = super()._prepare_picking_default_values_based_on(picking)
        if self.env.context.get("is_exchange_move"):
            vals["is_exchange_move"] = True
        return vals
