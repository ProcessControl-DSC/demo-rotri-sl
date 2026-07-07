# -*- coding: utf-8 -*-
import base64
import io
import csv
from odoo import api, fields, models, _


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
    move_state = fields.Selection(related='move_id.state', string='Estado factura', store=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        related='company_id.currency_id', string='Moneda', readonly=True)

    def action_export_csv(self):
        """Exporta las líneas seleccionadas a CSV (libro registro, formato AEAT-like)."""
        records = self or self.search([])
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=';')
        w.writerow(['Fecha', 'Referencia', 'Tipo', 'Producto', 'Kg', 'Cuota',
                    'Autoliquidacion', 'Exento', 'Motivo'])
        for r in records:
            w.writerow([r.date, r.name, dict(self._fields['entry_type'].selection).get(r.entry_type),
                        r.product_id.display_name or '', ('%.4f' % r.kg), ('%.2f' % r.amount),
                        'S' if r.self_assessment else 'N', 'S' if r.exempt else 'N',
                        r.exemption_reason or ''])
        data = base64.b64encode(buf.getvalue().encode('utf-8-sig'))
        att = self.env['ir.attachment'].create({
            'name': 'libro_registro_plastico.csv', 'type': 'binary',
            'datas': data, 'mimetype': 'text/csv'})
        return {'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % att.id, 'target': 'self'}


class PlasticStockSnapshot(models.Model):
    _name = 'l10n_es.plastic.stock.snapshot'
    _description = 'Existencias mensuales de plástico (kg)'
    _order = 'date desc, id desc'

    date = fields.Date(string='Fecha de corte', required=True, index=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    qty_on_hand = fields.Float(string='Unidades en stock', digits='Product Unit of Measure')
    kg_plastic = fields.Float(string='Kg plástico no reciclado', digits=(16, 4))
    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.company)

    @api.model
    def _cron_generate_snapshots(self):
        for company in self.env['res.company'].search([]):
            self.with_company(company).action_generate_snapshot()

    @api.model
    def action_generate_snapshot(self, date=None):
        """Genera el snapshot de existencias en kg de plástico a la fecha dada."""
        date = date or fields.Date.context_today(self)
        company = self.env.company
        self.search([('date', '=', date), ('company_id', '=', company.id)]).unlink()
        prods = self.env['product.product'].search([
            '|', ('product_tmpl_id.plastic_single_use', '=', True),
            ('plastic_single_use_var', '=', True)])
        created = self.env['l10n_es.plastic.stock.snapshot']
        for p in prods:
            e = p.plastic_effective()
            if not e['plastic_single_use'] or e['plastic_not_subject']:
                continue
            net = max(0.0, e['kg_plastic_unit'] - e['kg_recycled_cert_unit'])
            qty = p.with_company(company).qty_available
            if qty:
                created |= self.create({
                    'date': date, 'product_id': p.id, 'qty_on_hand': qty,
                    'kg_plastic': round(net * qty, 4), 'company_id': company.id})
        return created
