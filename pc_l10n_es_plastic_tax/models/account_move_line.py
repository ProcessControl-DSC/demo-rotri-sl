# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    kg_plastic_unit = fields.Float(
        related='product_id.product_tmpl_id.kg_plastic_unit', readonly=True)
    plastic_single_use = fields.Boolean(
        related='product_id.product_tmpl_id.plastic_single_use', readonly=True)
    kg_plastic_total = fields.Float(
        string='Kg plástico', compute='_compute_kg_plastic_total',
        digits=(16, 4), store=False,
        help='Kg de plástico no reciclado de la línea (cantidad x kg no reciclado/ud).')
    is_plastic_tax_line = fields.Boolean(
        string='Línea impuesto plástico', default=False, copy=False,
        help='Marca las líneas generadas por el impuesto del plástico.')

    @api.depends('quantity', 'product_id.product_tmpl_id.kg_plastic_unit',
                 'product_id.product_tmpl_id.kg_recycled_cert_unit',
                 'product_id.product_tmpl_id.plastic_single_use')
    def _compute_kg_plastic_total(self):
        for line in self:
            tmpl = line.product_id.product_tmpl_id
            if tmpl and tmpl.plastic_single_use:
                net = max(0.0, tmpl.kg_plastic_unit - tmpl.kg_recycled_cert_unit)
                line.kg_plastic_total = net * (line.quantity or 0.0)
            else:
                line.kg_plastic_total = 0.0
