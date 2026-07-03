# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    plastic_single_use = fields.Boolean(
        string='Plástico de un solo uso',
        help='El producto es un envase de plástico no reutilizable sujeto a la Ley 7/2022.')
    kg_plastic_unit = fields.Float(
        string='Kg plástico no reciclado / ud',
        digits=(16, 4),
        help='Kilogramos de plástico no reciclado por unidad.')
    kg_recycled_cert_unit = fields.Float(
        string='Kg plástico reciclado certificado / ud',
        digits=(16, 4),
        help='Kilogramos de plástico reciclado por unidad, acreditado por entidad '
             'certificadora (UNE-EN 15343). Se descuenta de la base imponible.')
    recycled_cert_ref = fields.Char(
        string='Ref. certificado reciclado',
        help='Referencia del certificado UNE-EN 15343 del plástico reciclado.')
    plastic_not_subject = fields.Boolean(
        string='No sujeto (art. 72)',
        help='Operación no sujeta al impuesto: exportación por el contribuyente, '
             'plásticos incorporados (tintas, adhesivos) o productos no destinados '
             'a envase. Se excluye del cálculo.')
    plastic_tax_product_id = fields.Many2one(
        'product.product',
        string='Producto de tasa asociado',
        help='Producto de tasa (por tarifa) usado al generar la línea del impuesto. '
             'Si se deja vacío se usa el producto de tasa por defecto del módulo.')
