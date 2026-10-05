##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("move_type", "partner_id", "partner_id.lang", "company_id")
    def _compute_narration(self):
        ar_moves = self.filtered(lambda move: move.country_code == "AR")
        super(AccountMove, self - ar_moves)._compute_narration()

        propagate_note = self.env["ir.config_parameter"].sudo().get_param("sale.propagate_note") == "True"
        if propagate_note:
            invoices_to_compute = ar_moves.filtered(lambda move: not move.invoice_origin)
        else:
            invoices_to_compute = ar_moves
        super(AccountMove, invoices_to_compute)._compute_narration()

    def action_post(self):
        res = super().action_post()
        for move in self.filtered(lambda record: record.country_code == "AR"):
            downpayment_lines = move.line_ids.sale_line_ids.filtered(
                lambda line: line.is_downpayment and not line.display_type
            )
            for downpayment_line in downpayment_lines:
                if move.currency_id == downpayment_line.currency_id:
                    continue
                downpayment_invoice_line = move.invoice_line_ids.filtered(
                    lambda line: line.is_downpayment and line.sale_line_ids.ids == downpayment_line.ids
                )
                downpayment_invoice_line.ensure_one()
                downpayment_line.price_unit = move.currency_id._convert(
                    downpayment_invoice_line.price_unit,
                    downpayment_line.currency_id,
                    move.company_id,
                    move.invoice_date or fields.Date.today(),
                )
        return res
