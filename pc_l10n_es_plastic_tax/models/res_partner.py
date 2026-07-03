# -*- coding: utf-8 -*-
from odoo import fields, models

SUPPLIER_MODES = [
    ('none', 'No aplica'),
    ('info_included', 'Contribución informativa (incluida en precio)'),
    ('aggregated', 'Contribución agregada (línea aparte)'),
    ('self_assessment', 'Autoliquidación (intracomunitaria)'),
]
CUSTOMER_MODES = [
    ('none', 'No aplica'),
    ('info_included', 'Contribución informativa'),
    ('aggregated', 'Contribución agregada'),
]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    plastic_tax_supplier_mode = fields.Selection(
        SUPPLIER_MODES, string='Modo impuesto plástico (compra)', default='none')
    plastic_tax_customer_mode = fields.Selection(
        CUSTOMER_MODES, string='Modo impuesto plástico (venta)', default='none')
