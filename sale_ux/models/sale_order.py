##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from datetime import timedelta

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _is_argentine_company(self):
        return self.country_code == "AR"

    def unlink(self):
        orders_with_invoices = self.filtered(lambda order: order._is_argentine_company() and order.invoice_ids)
        if orders_with_invoices:
            raise UserError(
                self.env._(
                    "You cannot delete this sales order because it has related invoices. "
                    "To preserve traceability, the record must remain archived or canceled."
                )
            )
        return super().unlink()

    internal_notes = fields.Html()
    payment_term_id = fields.Many2one(
        tracking=True,
    )
    force_invoiced_status = fields.Selection(
        [("no", "Nothing to Invoice"), ("invoiced", "Fully Invoiced")],
        tracking=True,
        copy=False,
    )
    commercial_partner_id = fields.Many2one(
        "res.partner",
        string="Commercial Entity",
        related="partner_id.commercial_partner_id",
        store=True,
        compute_sudo=True,
    )
    amount_uninvoiced = fields.Monetary(
        string="Un-invoiced",
        compute="_compute_amount_uninvoiced",
        help="Uninvoiced amount, regardless of invoice policy.",
    )
    amount_to_invoice = fields.Monetary(
        help=(
            "Total amount available for invoicing according to the invoice policy for each sale order line."
            "Down payments are not included in this calculation."
        )
    )

    @api.depends("invoice_ids.state", "currency_id", "amount_total")
    def _compute_amount_uninvoiced(self):
        for order in self:
            if not order._is_argentine_company() or order.invoice_status == "invoiced" or order.state != "sale":
                order.amount_uninvoiced = 0.0
                continue
            invoices = order.invoice_ids.filtered(
                lambda invoice: invoice.state == "posted" or invoice.payment_state == "invoicing_legacy"
            )
            order.amount_uninvoiced = order.amount_total - invoices._get_sale_order_invoiced_amount(order)

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if not self._is_argentine_company():
            return vals

        propagate_internal_notes = (
            self.env["ir.config_parameter"].sudo().get_param("sale.propagate_internal_notes") == "True"
        )
        propagate_note = self.env["ir.config_parameter"].sudo().get_param("sale.propagate_note") == "True"
        if propagate_internal_notes and self.internal_notes:
            vals["internal_notes"] = self.internal_notes
        if "narration" in vals and not propagate_note:
            vals.pop("narration")
        company = self.company_id
        if (
            not propagate_note
            and self.env["ir.config_parameter"].sudo().get_param("account.use_invoice_terms")
            and company.invoice_terms
        ):
            vals["narration"] = company.invoice_terms
        return vals

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id_show_update_prices(self):
        super()._onchange_pricelist_id_show_update_prices()
        if not self._is_argentine_company():
            return
        update_prices_automatically = safe_eval(
            self.env["ir.config_parameter"].sudo().get_param("sale_ux.update_prices_automatically", "False")
        )
        if self.order_line and update_prices_automatically:
            super()._recompute_prices()

    @api.onchange("fiscal_position_id")
    def _onchange_fiscal_position_id(self):
        self.ensure_one()
        if not self._is_argentine_company():
            return
        self.order_line.filtered(lambda line: not line.display_type)._compute_tax_ids()

    def action_cancel(self):
        ar_orders = self.filtered(lambda order: order._is_argentine_company())
        other_orders = self - ar_orders
        result = super(SaleOrder, other_orders).action_cancel() if other_orders else True
        for order in ar_orders:
            invoice_lines = (
                order.sudo().env["account.move.line"].search([("sale_line_ids", "in", order.order_line.ids)])
            )
            moves = invoice_lines.mapped("move_id").filtered(
                lambda move: move.move_type in ("out_invoice", "out_refund") and move.state not in ["cancel", "draft"]
            )
            invoices = moves.filtered(lambda move: move.move_type == "out_invoice")
            valid_invoices = all(
                invoice.payment_state == "reversed" and invoice.invoice_origin == order.name for invoice in invoices
            )
            if valid_invoices:
                refunds = moves.filtered(lambda move: move.move_type == "out_refund")
                valid_invoices = (
                    all(refund.payment_state == "paid" and refund.invoice_origin == order.name for refund in refunds)
                    if refunds
                    else False
                )
            if moves and not valid_invoices:
                raise UserError(
                    _("Unable to cancel this sale order. You must first cancel related bills and pickings.")
                )
            if order.locked:
                order_result = order._action_cancel()
            else:
                order_result = super(SaleOrder, order).action_cancel()
            if result in (True, None):
                result = order_result
        return result

    @api.constrains("force_invoiced_status")
    def check_force_invoiced_status(self):
        group = self.sudo().env.ref("base.group_system")
        for order in self.filtered(lambda record: record._is_argentine_company()):
            if order.force_invoiced_status and not self.env.user.has_group("base.group_system"):
                if group.privilege_id:
                    raise ValidationError(
                        _('Only users with "%s / %s" can Set Invoiced manually') % (group.privilege_id.name, group.name)
                    )
                raise ValidationError(_('Only users with "%s" can Set Invoiced manually') % group.name)

    def _get_update_prices_lines(self):
        lines = super()._get_update_prices_lines()
        lines_to_not_update_ids = self.env.context.get("lines_to_not_update_ids", [])
        return lines.filtered(lambda line: line.order_id.country_code != "AR" or line.id not in lines_to_not_update_ids)

    def action_update_prices(self):
        if not self:
            return
        return super().action_update_prices()

    def _create_invoices(self, grouped=False, final=False, date=None):
        invoices = super()._create_invoices(grouped=grouped, final=final, date=date)
        precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        filtered_invoices = invoices.filtered(
            lambda invoice: invoice.country_code == "AR"
            and float_is_zero(invoice.amount_total, precision_digits=precision)
            and all(line.quantity <= 0.0 for line in invoice.invoice_line_ids)
        )
        filtered_invoices.action_switch_move_type()
        for line in filtered_invoices.mapped("invoice_line_ids"):
            line.quantity = abs(line.quantity)
        return invoices

    def action_preview_sale_order(self):
        result = super().action_preview_sale_order()
        if self._is_argentine_company():
            result["target"] = "new"
        return result

    def _get_invoiceable_lines(self, final=False):
        result = super()._get_invoiceable_lines(final=final)
        dont_send_notes_to_invoices = (
            self.env["ir.config_parameter"].sudo().get_param("sale_ux.dont_send_notes_to_invoices", "False") == "True"
        )
        if dont_send_notes_to_invoices:
            result -= result.filtered(
                lambda line: line.order_id.country_code == "AR" and line.display_type == "line_note"
            )
        return result

    def _prepare_analytic_account_data(self, prefix=None):
        if (
            self._is_argentine_company()
            and self.env["ir.config_parameter"].sudo().get_param("sale_ux.analytic_account_without_company", "False")
            == "True"
        ):
            self.ensure_one()
            name = f"{prefix}: {self.name}" if prefix else self.name
            project_plan, _other_plans = self.env["account.analytic.plan"]._get_all_plans()
            return {
                "name": name,
                "code": self.client_order_ref,
                "company_id": False,
                "plan_id": project_plan.id,
                "partner_id": self.partner_id.id,
            }
        return super()._prepare_analytic_account_data(prefix=prefix)

    def _cron_clean_old_quotations(self, website=None):
        cancel_old_quotations = (
            self.env["ir.config_parameter"].sudo().get_param("sale_ux.cancel_old_quotations", "False") == "True"
        )
        if not cancel_old_quotations and not website:
            return super()._cron_clean_old_quotations(website=website)

        today = fields.Date.today()
        days_to_keep = int(self.env["ir.config_parameter"].sudo().get_param("sale_ux.days_to_keep_quotations", 30))
        domain = [
            ("state", "in", ["draft", "sent"]),
            ("date_order", "<", today - timedelta(days=days_to_keep)),
            ("country_code", "=", "AR"),
        ]
        if cancel_old_quotations and self.env.context.get("website_installed") and not website:
            domain.append(("website_id", "=", False))
        elif not cancel_old_quotations and website:
            domain.append(("website_id", "!=", False))
        for quotation in self.env["sale.order"].search(domain):
            quotation._action_cancel()
            quotation.message_post(body=_("This quotation has been automatically canceled due to its expiration."))
        return True

    @api.constrains("pricelist_id")
    def _check_changes_locked_orders(self):
        for order in self.filtered(lambda record: record._is_argentine_company() and record.state == "done"):
            raise ValidationError(_("You cannot modify already locked orders."))

    def get_update_included_pdf_params(self):
        result = super().get_update_included_pdf_params()
        if not self._is_argentine_company():
            return result
        auto_select_enabled = (
            self.env["ir.config_parameter"].sudo().get_param("sale_ux.auto_select_all_documents", "False") == "True"
        )
        if not auto_select_enabled:
            return result

        if self.available_quotation_document_ids and not self.quotation_document_ids:
            self.quotation_document_ids = self.available_quotation_document_ids
            selected_headers = self.quotation_document_ids.filtered(lambda document: document.document_type == "header")
            selected_footers = self.quotation_document_ids.filtered(lambda document: document.document_type == "footer")
            for header in result.get("headers", {}).get("files", []):
                if any(document.id == header["id"] for document in selected_headers):
                    header["is_selected"] = True
            for footer in result.get("footers", {}).get("files", []):
                if any(document.id == footer["id"] for document in selected_footers):
                    footer["is_selected"] = True

        for line in self.order_line:
            if line.available_product_document_ids and not line.product_document_ids:
                line.product_document_ids = line.available_product_document_ids
        for line_data in result.get("lines", []):
            line = self.order_line.filtered(lambda order_line: order_line.id == line_data["id"])
            if line and line.product_document_ids:
                for document in line_data.get("files", []):
                    if any(record.id == document["id"] for record in line.product_document_ids):
                        document["is_selected"] = True
        return result

    def copy(self, default=None):
        new_orders = super().copy(dict(default or {}))
        ar_pairs = [
            (old_order, new_order)
            for old_order, new_order in zip(self, new_orders)
            if old_order._is_argentine_company()
        ]
        if not ar_pairs:
            return new_orders
        new_ar_orders = self.browse([new_order.id for _old_order, new_order in ar_pairs])
        new_ar_orders._message_log_batch(
            bodies={
                new_order.id: _("This sale order was duplicated from %s", old_order._get_html_link())
                for old_order, new_order in ar_pairs
            }
        )
        for line in new_ar_orders.mapped("order_line").filtered(
            lambda record: False in record.mapped("tax_ids.active")
        ):
            line.tax_ids = [Command.unlink(tax.id) for tax in line.tax_ids.filtered(lambda tax: not tax.active)]
        return new_orders

    @api.depends("force_invoiced_status")
    def _compute_amount_to_invoice(self):
        forced_orders = self.filtered(lambda order: order._is_argentine_company() and order.force_invoiced_status)
        forced_orders.amount_to_invoice = 0.0
        super(SaleOrder, self - forced_orders)._compute_amount_to_invoice()

    def lock_sale_order(self):
        self.ensure_one()
        return self._is_argentine_company() and self.locked

    def _get_protected_fields(self):
        return (
            ["partner_id", "partner_invoice_id", "partner_shipping_id", "pricelist_id"]
            if self._is_argentine_company()
            else []
        )

    def write(self, vals):
        locked_orders = self.filtered(lambda order: order.lock_sale_order())
        protected_fields = locked_orders[:1]._get_protected_fields()
        if locked_orders and any(field in vals for field in protected_fields):
            modified_fields = list(set(protected_fields) & set(vals))
            fields_to_display = (
                self.env["ir.model.fields"].sudo().search([("name", "in", modified_fields), ("model", "=", self._name)])
            )
            if fields_to_display:
                raise UserError(
                    _(
                        "It is forbidden to modify the following fields in a locked order:\n%s",
                        "\n".join(fields_to_display.mapped("field_description")),
                    )
                )
        return super().write(vals)

    def _get_product_catalog_order_data(self, products, **kwargs):
        result = super()._get_product_catalog_order_data(products, **kwargs)
        if not self._is_argentine_company():
            return result
        for product in products:
            if product.product_tmpl_id.only_packagings and product.uom_ids:
                result[product.id]["uomDisplayName"] = product.uom_ids[0].display_name
        return result
