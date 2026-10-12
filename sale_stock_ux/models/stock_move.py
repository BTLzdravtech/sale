##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    sale_id = fields.Many2one(
        related="sale_line_id.order_id",
    )
    is_exchange_move = fields.Boolean()

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        fields = super()._prepare_merge_moves_distinct_fields()
        fields.append("is_exchange_move")
        return fields

    @api.model_create_multi
    def create(self, vals_list):
        """La cantidad devuelta no deberia ser contada en nuevos movimientos de stock
        que se creen a partir de una orden de venta.
        Agregamos un HACK para que si esta instalado secondary unit sea recomputada en la creacion de
        movimientos de stock.
        TODO: Solo deberia impactar en movimientos de salida (uno o mas pasos)
        """
        for vals in vals_list:
            sale_line_id = vals.get("sale_line_id")
            sale_line = self.env["sale.order.line"].browse(sale_line_id)
            if (
                sale_line_id
                and sale_line.order_id.company_id.country_code == "AR"
                and vals.get("product_uom_qty") is not None
            ):
                vals["product_uom_qty"] -= sale_line.quantity_returned
                vals.pop("secondary_uom_qty", None)

        return super().create(vals_list)

    def _get_new_picking_values(self):
        """return create values for new picking that will be linked with group
        of moves in self.
        """
        res = super()._get_new_picking_values()
        values = {}
        sale = self.mapped("sale_line_id.order_id")
        propagate_internal_notes = (
            self.env["ir.config_parameter"].sudo().get_param("sale.propagate_internal_notes") == "True"
        )
        propagate_note = self.env["ir.config_parameter"].sudo().get_param("sale.propagate_note") == "True"
        if propagate_internal_notes and sale.internal_notes:
            values["note"] = sale.internal_notes
        if propagate_note and sale.note:
            values["observations"] = sale.note
        if values:
            res.update(values)

        return res
