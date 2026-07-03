# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    plastic_tax_cip = fields.Char(
        string='CIP impuesto plástico',
        help='Código de Identificación Plástico del Registro territorial (AEAT).')
