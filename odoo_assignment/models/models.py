from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    discount_percentage = fields.Float(
        string="Discount Percentage",
        help="Set a percentage discount for the product. Value must be between 0 and 100."
    )

    @api.depends('list_price', 'discount_percentage')
    def _compute_discounted_price(self):
        for product in self:
            if 0 < product.discount_percentage <= 100:
                product.discounted_price = product.list_price * (1 - product.discount_percentage / 100)
            else:
                product.discounted_price = product.list_price

    discounted_price = fields.Float(
        string="Discounted Price",
        compute="_compute_discounted_price",
        store=True
    )

    def _prepare_invoice_line(self, line):
        """
        Ensure that the invoice reflects the discounted price.
        """
        res = super(SaleOrder, self)._prepare_invoice_line(line)
        res['price_unit'] = line.price_unit  # Ensure price_unit reflects the discounted price
        return res



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        """
        Ensure the discounted price is applied when creating a sale order line.
        """
        product = self.env['product.product'].browse(vals.get('product_id'))
        if product and product.product_tmpl_id.discount_percentage > 0:
            vals['price_unit'] = product.product_tmpl_id.discounted_price
        else:
            vals['price_unit'] = product.lst_price
        return super(SaleOrderLine, self).create(vals)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Apply the discounted price when the product is changed.
        """
        if self.product_id and self.product_id.product_tmpl_id.discount_percentage > 0:
            self.price_unit = self.product_id.product_tmpl_id.discounted_price
        else:
            self.price_unit = self.product_id.lst_price