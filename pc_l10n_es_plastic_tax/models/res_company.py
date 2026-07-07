# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    plastic_tax_cip = fields.Char(
        string='CIP impuesto plástico',
        help='Código de Identificación Plástico del Registro territorial (AEAT).')
    plastic_tax_rate = fields.Float(
        string='Tipo impuesto plástico (EUR/kg)', default=0.45, digits=(16, 4))
    plastic_tax_minimis_kg = fields.Float(
        string='Umbral minimis (kg/periodo)', default=5.0, digits=(16, 4))
    plastic_tax_period = fields.Selection(
        [('month', 'Mensual'), ('quarter', 'Trimestral')],
        string='Periodo del modelo 592', default='quarter')
    plastic_tax_account_output_id = fields.Many2one(
        'account.account', string='Cuenta impuesto repercutido',
        help='Cuenta donde se contabiliza la tasa (típicamente 475).')
    plastic_tax_account_expense_id = fields.Many2one(
        'account.account', string='Cuenta gasto/autoliquidación',
        help='Cuenta de gasto o contrapartida (típicamente 631).')
    plastic_kg_from_weight = fields.Boolean(
        string='Calcular kg desde el peso',
        help='Si se activa, los kg de plástico se calculan como peso del producto '
             'por el porcentaje de plástico, en lugar de introducirlos a mano.')
    plastic_exempt_from_fiscal_pos = fields.Boolean(
        string='Exención por posición fiscal', default=True,
        help='Deriva la exención (exportación / intracomunitaria) de la posición '
             'fiscal de la factura.')
    plastic_hide_counterpart_pdf = fields.Boolean(
        string='Ocultar contrapartida en PDF', default=True)
    plastic_mo_registration = fields.Selection(
        [('per_mo', 'Por orden de fabricación'), ('daily', 'Agregado diario')],
        string='Registro de fabricación', default='per_mo')
