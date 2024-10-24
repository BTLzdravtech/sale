from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import ValidationError
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_gathering = fields.Boolean('Is Gathering?')
    gathering_balance = fields.Float(
        compute="_compute_gathering_balance",
        digits='Product Price',
        store=True,
        tracking=True,
        help='Balance entre la factura de acopio/anticipo y los retiros de mercaderia que realizo el cliente. Monto positivo es a favor del cliente'
    )
    gathering_amount = fields.Float(compute="_compute_gathering_amount", help='Monto, sin impuestos, acopiado inicialmente.')
    has_gathering_invoice = fields.Boolean(compute="_compute_has_gathering_invoice")

    @api.depends(
        'is_gathering',
        'state',
        'order_line.product_id',
        'order_line.price_unit',
        'order_line.qty_invoiced',
        'order_line.qty_to_invoice',
        'order_line.is_downpayment',
    )
    def _compute_gathering_balance(self):
        orders_gathering = self.filtered(
            lambda order: order.is_gathering and order.state == 'sale' and any(
                order.order_line.filtered('is_downpayment')
            )
        )

        for order in orders_gathering:
            total_downpayment_amount = 0
            for line in order.order_line.filtered('is_downpayment'):
                total_downpayment_amount += line.tax_id.with_context(round=False).compute_all(
                    line.price_unit,
                    currency=line.currency_id,
                    quantity=1,
                    product=line.product_id,
                    partner=line.order_id.partner_shipping_id)['total_included']

            total_amount_to_invoice_invoiced = 0
            for line in order.order_line.filtered(lambda x: not x.is_downpayment):
                price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                total_amount_to_invoice_invoiced += line.tax_id.compute_all(
                                price_reduce,
                                currency=line.currency_id,
                                quantity=line.qty_to_invoice + line.qty_invoiced,
                                product=line.product_id,
                                partner=line.order_id.partner_shipping_id)['total_included']

            order.gathering_balance = total_downpayment_amount - total_amount_to_invoice_invoiced

        (self - orders_gathering).gathering_balance = 0

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        invoiceable_lines = super()._get_invoiceable_lines(final=final)
        product_precision_digits = self.env['decimal.precision'].precision_get('Product Price')
        for rec in self.filtered(lambda x: x.is_gathering and float_compare(x.gathering_balance, 0.0, precision_digits=product_precision_digits) >= 0):
            for line in rec.order_line.filtered('is_downpayment'):
                if final:
                    invoiceable_lines |= line
            invoiceable_lines = invoiceable_lines.filtered(lambda line: line.display_type not in ['line_section', 'line_note'])
        return invoiceable_lines

    @api.constrains('is_gathering', 'amount_total')
    def _check_gathering_balance(self):
        product_precision_digits = self.env['decimal.precision'].precision_get(
            'Product Price')
        for rec in self.filtered('is_gathering'):
            if float_compare(rec.gathering_balance, 0.0, precision_digits=product_precision_digits) == -1:
                raise ValidationError(
                    _(
                        "The gathering balance will be negative (%s), you cannot make this modification"
                        " to the order. Order: %s" %
                        (rec.gathering_balance, rec.name)))

    def action_confirm(self):
        for order in self.filtered('is_gathering'):
            for line in order.order_line:
                line.write({
                    'initial_qty_gathered': line.product_uom_qty,
                    'product_uom_qty': 0
                })
        return super().action_confirm()

    @api.depends('order_line.initial_qty_gathered', 'is_gathering')
    def _compute_gathering_amount(self):
        orders_gathering = self.filtered(
            lambda x: x.is_gathering and x.order_line.filtered(lambda x: x.initial_qty_gathered > 0)
        )
        for order in orders_gathering:
            gathering_amount = 0
            for line in order.order_line.filtered(lambda x: x.initial_qty_gathered > 0):
                price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                gathering_amount += line.tax_id.compute_all(
                                price_reduce,
                                currency=line.currency_id,
                                quantity=line.initial_qty_gathered,
                                product=line.product_id,
                                partner=line.order_id.partner_shipping_id)['total_excluded']
            order.gathering_amount = gathering_amount
        (self - orders_gathering).gathering_amount = 0.0

    @api.depends('is_gathering', 'invoice_ids', 'invoice_ids.state')
    def _compute_has_gathering_invoice(self):
        orders_gathering = self.filtered('is_gathering')
        for rec in orders_gathering:
            rec.has_gathering_invoice = any(
                invoice._is_downpayment() for invoice in rec.invoice_ids if invoice.state != 'cancel'
            )
        (self - orders_gathering).has_gathering_invoice = False

    def action_lock(self):
        super(SaleOrder, self - self.filtered('is_gathering')).action_lock()
