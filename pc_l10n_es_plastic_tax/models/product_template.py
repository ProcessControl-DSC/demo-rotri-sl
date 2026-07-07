# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    plastic_single_use = fields.Boolean(
        string='Plástico de un solo uso',
        help='El producto es un envase de plástico no reutilizable sujeto a la Ley 7/2022.')
    plastic_not_subject = fields.Boolean(
        string='No sujeto (art. 72)',
        help='Operación no sujeta al impuesto: exportación por el contribuyente, '
             'plásticos incorporados (tintas, adhesivos) o productos no destinados '
             'a envase. Se excluye del cálculo.')
    plastic_pct = fields.Float(
        string='% plástico no reciclado', digits=(16, 6),
        help='Fracción de plástico no reciclado sobre el peso del producto (0-1). '
             'Solo se usa si la compañía calcula los kg desde el peso.')
    kg_plastic_unit = fields.Float(
        string='Kg plástico no reciclado / ud', digits=(16, 6),
        compute='_compute_kg_plastic_unit', store=True, readonly=False,
        help='Kilogramos de plástico no reciclado por unidad. Si la compañía calcula '
             'desde el peso, se computa como peso x % plástico.')
    kg_recycled_cert_unit = fields.Float(
        string='Kg plástico reciclado certificado / ud', digits=(16, 6),
        help='Kilogramos de plástico reciclado por unidad, acreditado por entidad '
             'certificadora (UNE-EN 15343). Se descuenta de la base imponible.')
    recycled_cert_ref = fields.Char(string='Ref. certificado reciclado')
    plastic_tax_product_id = fields.Many2one(
        'product.product', string='Producto de tasa asociado',
        help='Producto de tasa (por tarifa) usado al generar la línea del impuesto. '
             'Si se deja vacío se usa el producto de tasa por defecto del módulo.')

    @api.depends('weight', 'plastic_pct', 'plastic_single_use',
                 'company_id.plastic_kg_from_weight')
    def _compute_kg_plastic_unit(self):
        for tmpl in self:
            company = tmpl.company_id or self.env.company
            if company.plastic_kg_from_weight and tmpl.plastic_single_use:
                tmpl.kg_plastic_unit = (tmpl.weight or 0.0) * (tmpl.plastic_pct or 0.0)
            # si no, se mantiene el valor manual (readonly=False + store)
