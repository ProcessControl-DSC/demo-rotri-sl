# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.addons.pc_l10n_es_plastic_tax.models.plastic_tax_lib import net_kg


class PlasticLedger(models.Model):
    _inherit = 'l10n_es.plastic.ledger'

    production_id = fields.Many2one('mrp.production', string='Orden de fabricación',
                                    ondelete='set null')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def button_mark_done(self):
        res = super().button_mark_done()
        Ledger = self.env['l10n_es.plastic.ledger']
        for prod in self:
            if prod.state != 'done':
                continue
            tmpl = prod.product_id.product_tmpl_id
            if not tmpl.plastic_single_use or tmpl.plastic_not_subject:
                continue
            qty = prod.qty_produced or prod.product_qty
            kg = net_kg({'qty': qty, 'kg_plastic_unit': tmpl.kg_plastic_unit,
                         'kg_recycled_cert_unit': tmpl.kg_recycled_cert_unit,
                         'plastic_single_use': True})
            if kg <= 0:
                continue
            date = fields.Date.context_today(prod)
            if prod.company_id.plastic_mo_registration == 'daily':
                # agregar por día + producto (rendimiento a escala)
                existing = Ledger.search([
                    ('entry_type', '=', 'produced'), ('date', '=', date),
                    ('product_id', '=', prod.product_id.id),
                    ('company_id', '=', prod.company_id.id),
                    ('production_id', '=', False)], limit=1)
                if existing:
                    existing.kg += round(kg, 4)
                    continue
                Ledger.create({
                    'name': 'Fabricación %s' % date, 'date': date, 'entry_type': 'produced',
                    'product_id': prod.product_id.id, 'kg': round(kg, 4), 'amount': 0.0,
                    'company_id': prod.company_id.id})
            else:
                Ledger.search([('production_id', '=', prod.id)]).unlink()
                Ledger.create({
                    'name': prod.name, 'date': date, 'entry_type': 'produced',
                    'product_id': prod.product_id.id, 'kg': round(kg, 4), 'amount': 0.0,
                    'production_id': prod.id, 'company_id': prod.company_id.id})
        return res
