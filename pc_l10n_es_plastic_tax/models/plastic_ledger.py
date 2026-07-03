# -*- coding: utf-8 -*-
from odoo import fields, models


class PlasticLedger(models.Model):
    _name = 'l10n_es.plastic.ledger'
    _description = 'Libro registro impuesto plástico (Ley 7/2022)'
    _order = 'date desc, id desc'

    name = fields.Char(string='Referencia', required=True)
    date = fields.Date(string='Fecha', required=True, index=True)
    entry_type = fields.Selection([
        ('purchased', 'Adquirido'),
        ('produced', 'Fabricado'),
        ('sold', 'Vendido'),
        ('deduction', 'Deducción'),
        ('adjustment', 'Ajuste'),
    ], string='Tipo de movimiento', required=True, index=True)
    product_id = fields.Many2one('product.product', string='Producto')
    kg = fields.Float(string='Kg plástico no reciclado', digits=(16, 4))
    amount = fields.Monetary(string='Cuota', currency_field='currency_id')
    self_assessment = fields.Boolean(string='Autoliquidación')
    exempt = fields.Boolean(string='Exento')
    exemption_reason = fields.Char(string='Motivo exención')
    move_id = fields.Many2one('account.move', string='Factura', ondelete='set null')
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        related='company_id.currency_id', string='Moneda', readonly=True)
