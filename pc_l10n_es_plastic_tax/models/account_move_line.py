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
        string='Línea impuesto plástico', default=False, copy=True,
        help='Marca las líneas generadas por el impuesto del plástico. Se copia en '
             'las facturas rectificativas para registrar la deducción.')
    is_plastic_counterpart = fields.Boolean(
        string='Contrapartida impuesto plástico', default=False, copy=True,
        help='Línea de contrapartida (neto 0) del impuesto del plástico. Se oculta '
             'en la impresión de la factura.')

    @api.depends('quantity', 'product_id')
    def _compute_kg_plastic_total(self):
        for line in self:
            if line.product_id:
                e = line.product_id.plastic_effective()
                if e['plastic_single_use'] and not e['plastic_not_subject']:
                    net = max(0.0, e['kg_plastic_unit'] - e['kg_recycled_cert_unit'])
                    line.kg_plastic_total = net * (line.quantity or 0.0)
                else:
                    line.kg_plastic_total = 0.0
            else:
                line.kg_plastic_total = 0.0
