# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .plastic_tax_lib import compute_plastic_tax_lines, net_kg, DEFAULT_RATE

EXEMPTION_REASONS = [
    ('export', 'Exportación'),
    ('eu', 'Entrega intracomunitaria'),
    ('sanitary', 'Uso sanitario o médico'),
    ('animal_feed', 'Alimentación animal'),
]

NOTE_TAXED = _(
    "Conforme al artículo 82.8 de la Ley 7/2022, el importe correspondiente al "
    "impuesto especial sobre los envases de plástico no reutilizables asciende a "
    "%(amount)s EUR (%(kg)s kg de plástico no reciclado).")
NOTE_EXEMPT = _(
    "Operación exenta del impuesto especial sobre los envases de plástico no "
    "reutilizables (art. 75.1.c de la Ley 7/2022): %(reason)s.")


class AccountMove(models.Model):
    _inherit = 'account.move'

    plastic_exemption_reason = fields.Selection(
        EXEMPTION_REASONS, string='Motivo exención plástico')
    plastic_needs_generation = fields.Boolean(
        string='Requiere impuesto plástico', compute='_compute_plastic_needs_generation')
    plastic_footer_note = fields.Text(string='Nota plástico factura', copy=False)

    def _plastic_party_mode(self):
        self.ensure_one()
        if self.move_type in ('out_invoice', 'out_refund'):
            return self.partner_id.plastic_tax_customer_mode or 'none', True
        if self.move_type in ('in_invoice', 'in_refund'):
            return self.partner_id.plastic_tax_supplier_mode or 'none', False
        return 'none', False

    @api.depends('partner_id', 'move_type', 'invoice_line_ids.plastic_single_use',
                 'invoice_line_ids.is_plastic_tax_line', 'state')
    def _compute_plastic_needs_generation(self):
        for move in self:
            need = False
            if move.state == 'draft' and move.move_type in (
                    'out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
                mode, _is_sale = move._plastic_party_mode()
                has_plastic = any(
                    l.plastic_single_use and not l.is_plastic_tax_line
                    for l in move.invoice_line_ids)
                has_tax = any(l.is_plastic_tax_line for l in move.invoice_line_ids)
                need = bool(mode != 'none' and has_plastic and not has_tax)
            move.plastic_needs_generation = need

    def _plastic_default_tax_product(self):
        return self.env.ref('pc_l10n_es_plastic_tax.product_tipa', raise_if_not_found=False)

    def action_generate_plastic_tax(self):
        default_prod = self._plastic_default_tax_product()
        for move in self:
            if move.state != 'draft':
                raise UserError(_("Solo se puede generar el impuesto en facturas en borrador."))
            mode, is_sale = move._plastic_party_mode()
            if mode == 'none':
                raise UserError(_("El contacto no tiene configurado el modo de impuesto del plástico."))
            # limpiar líneas de tasa previas (idempotente)
            old = move.invoice_line_ids.filtered('is_plastic_tax_line')
            if old:
                move.invoice_line_ids = [(2, l.id) for l in old]
            # construir entrada para la lógica pura
            src = move.invoice_line_ids.filtered(
                lambda l: l.display_type == 'product' and not l.is_plastic_tax_line)
            calc_lines = []
            prod_by_key = {}
            for l in src:
                tmpl = l.product_id.product_tmpl_id
                key_prod = tmpl.plastic_tax_product_id or default_prod
                key = key_prod.id if key_prod else 0
                prod_by_key[key] = key_prod
                calc_lines.append({
                    'qty': l.quantity,
                    'kg_plastic_unit': tmpl.kg_plastic_unit,
                    'kg_recycled_cert_unit': tmpl.kg_recycled_cert_unit,
                    # no sujeto (art. 72) => se excluye del cálculo
                    'plastic_single_use': tmpl.plastic_single_use and not tmpl.plastic_not_subject,
                    'tariff_key': key,
                })
            res = compute_plastic_tax_lines(calc_lines, mode, is_sale, rate=DEFAULT_RATE)
            # limpiar asientos de libro registro previos de esta factura (idempotente)
            self.env['l10n_es.plastic.ledger'].search([('move_id', '=', move.id)]).unlink()
            ledger_date = move.invoice_date or fields.Date.context_today(move)
            total_plastic_kg = sum(net_kg(cl) for cl in calc_lines)
            if not res:
                # sin cuota: exención (minimis o motivo de exención en venta)
                if total_plastic_kg > 0 and move.plastic_exemption_reason:
                    reason = dict(EXEMPTION_REASONS).get(move.plastic_exemption_reason, '')
                    move.plastic_footer_note = NOTE_EXEMPT % {'reason': reason}
                    self.env['l10n_es.plastic.ledger'].create({
                        'name': move.name or _('Borrador'),
                        'date': ledger_date,
                        'entry_type': 'sold' if is_sale else 'purchased',
                        'kg': round(total_plastic_kg, 4), 'amount': 0.0,
                        'exempt': True, 'exemption_reason': reason,
                        'move_id': move.id, 'company_id': move.company_id.id,
                    })
                else:
                    move.plastic_footer_note = False
                continue
            sale_tax = move.company_id.account_sale_tax_id if is_sale else False
            new_lines = []
            total_amount = 0.0
            total_kg = 0.0
            for r in res:
                prod = prod_by_key.get(r['tariff_key']) or default_prod
                if not prod:
                    raise UserError(_("No existe el producto de tasa del plástico."))
                vals = {
                    'display_type': 'product',
                    'product_id': prod.id,
                    'quantity': r['kg'],
                    'price_unit': DEFAULT_RATE * r['sign'],
                    'is_plastic_tax_line': True,
                    'name': (_('Impuesto plástico (%(rate)s EUR/kg) - %(kg)s kg')
                             % {'rate': DEFAULT_RATE, 'kg': r['kg']}
                             if r['kind'] == 'tax'
                             else _('Impuesto plástico - contrapartida')),
                }
                if is_sale and r['kind'] == 'tax' and sale_tax:
                    vals['tax_ids'] = [(6, 0, sale_tax.ids)]
                else:
                    vals['tax_ids'] = [(5, 0, 0)]
                new_lines.append((0, 0, vals))
                if r['kind'] == 'tax':
                    total_amount += r['amount']
                    total_kg += r['kg']
                    self.env['l10n_es.plastic.ledger'].create({
                        'name': move.name or _('Borrador'),
                        'date': ledger_date,
                        'entry_type': 'sold' if is_sale else 'purchased',
                        'product_id': prod.id,
                        'kg': r['kg'], 'amount': r['amount'],
                        'self_assessment': r['self_assessment'],
                        'move_id': move.id, 'company_id': move.company_id.id,
                    })
            move.invoice_line_ids = new_lines
            move.plastic_footer_note = NOTE_TAXED % {
                'amount': ('%.2f' % total_amount), 'kg': ('%.3f' % total_kg)}
        return True
