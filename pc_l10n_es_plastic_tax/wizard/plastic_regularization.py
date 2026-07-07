# -*- coding: utf-8 -*-
from odoo import fields, models, _


class PlasticRegularization(models.TransientModel):
    _name = 'l10n_es.plastic.regularization'
    _description = 'Regularización impuesto plástico (deducción art. 80)'

    date = fields.Date(string='Fecha', required=True, default=fields.Date.context_today)
    product_id = fields.Many2one('product.product', string='Producto')
    kg = fields.Float(string='Kg plástico a regularizar', digits=(16, 4), required=True)
    reason = fields.Selection([
        ('return', 'Devolución de cliente'),
        ('export_after', 'Producto exportado tras tributar'),
        ('destruction', 'Destrucción / no apto'),
    ], string='Motivo (art. 80)', required=True, default='return')
    note = fields.Char(string='Observaciones')

    def action_confirm(self):
        self.ensure_one()
        rate = self.env.company.plastic_tax_rate or 0.45
        self.env['l10n_es.plastic.ledger'].create({
            'name': _('Regularización %s') % dict(self._fields['reason'].selection).get(self.reason),
            'date': self.date, 'entry_type': 'deduction',
            'product_id': self.product_id.id if self.product_id else False,
            'kg': -abs(self.kg), 'amount': -abs(round(self.kg * rate, 2)),
            'exemption_reason': self.note or False,
            'company_id': self.env.company.id})
        return {'type': 'ir.actions.act_window_close'}
