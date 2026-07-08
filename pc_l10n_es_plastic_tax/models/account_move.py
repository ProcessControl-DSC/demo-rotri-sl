# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .plastic_tax_lib import compute_plastic_tax_lines, net_kg

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
        EXEMPTION_REASONS, string='Motivo exención plástico',
        help='Fuerza la exención de la factura. Si se deja vacío y la compañía lo '
             'permite, la exención se deriva de la posición fiscal.')
    plastic_needs_generation = fields.Boolean(
        string='Requiere impuesto plástico', compute='_compute_plastic_needs_generation')
    plastic_generated = fields.Boolean(string='Impuesto plástico generado', copy=False)
    plastic_footer_note = fields.Text(string='Nota plástico factura', copy=False)

    # ---------------------------------------------------------------- helpers
    def _plastic_party_mode(self):
        self.ensure_one()
        if self.move_type in ('out_invoice', 'out_refund'):
            return self.partner_id.plastic_tax_customer_mode or 'none', True
        if self.move_type in ('in_invoice', 'in_refund'):
            return self.partner_id.plastic_tax_supplier_mode or 'none', False
        return 'none', False

    def _plastic_exemption(self):
        """Devuelve (exento, motivo_label). Prioridad: campo manual > posición fiscal.

        La exención por posición fiscal solo aplica a VENTAS (entregas exentas). En
        compras intracomunitarias no hay exención: se autoliquida por el modo del
        proveedor. El motivo manual, si se informa, prevalece en ambos sentidos.
        """
        self.ensure_one()
        if self.plastic_exemption_reason:
            return True, dict(EXEMPTION_REASONS).get(self.plastic_exemption_reason)
        is_sale = self.move_type in ('out_invoice', 'out_refund')
        fp = self.fiscal_position_id
        if (is_sale and self.company_id.plastic_exempt_from_fiscal_pos
                and fp and fp.plastic_exempt):
            label = dict(EXEMPTION_REASONS).get(fp.plastic_exempt_reason) or _('exenta')
            return True, label
        return False, None

    def _plastic_period_range(self):
        self.ensure_one()
        d = self.invoice_date or fields.Date.context_today(self)
        if self.company_id.plastic_tax_period == 'month':
            start = d.replace(day=1)
            end = start + relativedelta(months=1, days=-1)
        else:
            q = (d.month - 1) // 3
            start = d.replace(month=q * 3 + 1, day=1)
            end = start + relativedelta(months=3, days=-1)
        return start, end

    def _plastic_source_kg(self):
        self.ensure_one()
        total = 0.0
        for l in self.invoice_line_ids.filtered(
                lambda x: x.display_type == 'product' and not x.is_plastic_tax_line):
            e = l.product_id.plastic_effective()
            total += net_kg({
                'qty': l.quantity, 'kg_plastic_unit': e['kg_plastic_unit'],
                'kg_recycled_cert_unit': e['kg_recycled_cert_unit'],
                'plastic_single_use': e['plastic_single_use'] and not e['plastic_not_subject'],
            })
        return total

    @api.depends('partner_id', 'move_type', 'invoice_line_ids.plastic_single_use',
                 'invoice_line_ids.is_plastic_tax_line', 'state', 'plastic_generated')
    def _compute_plastic_needs_generation(self):
        for move in self:
            need = False
            if (move.state == 'draft' and not move.plastic_generated
                    and move.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')):
                mode, _is = move._plastic_party_mode()
                exempt, _r = move._plastic_exemption()
                has_plastic = any(
                    l.plastic_single_use and not l.is_plastic_tax_line
                    for l in move.invoice_line_ids)
                need = bool(has_plastic and (mode != 'none' or exempt))
            move.plastic_needs_generation = need

    def _plastic_default_tax_product(self):
        return self.env.ref('pc_l10n_es_plastic_tax.product_tipa', raise_if_not_found=False)

    # ---------------------------------------------------------------- acción
    def action_generate_plastic_tax(self):
        default_prod = self._plastic_default_tax_product()
        for move in self:
            if move.state != 'draft':
                raise UserError(_("Solo se puede generar el impuesto en facturas en borrador."))
            company = move.company_id
            mode, is_sale = move._plastic_party_mode()
            exempt, reason = move._plastic_exemption()
            # limpiar líneas de tasa previas
            old = move.invoice_line_ids.filtered('is_plastic_tax_line')
            if old:
                move.invoice_line_ids = [(2, l.id) for l in old]
            total_kg = move._plastic_source_kg()

            if total_kg <= 0:
                move.plastic_footer_note = False
                move.plastic_generated = True
                continue
            # Exención (motivo manual o posición fiscal): sin cuota, nota 75.1.c
            if exempt:
                move.plastic_footer_note = NOTE_EXEMPT % {'reason': reason or _('exenta')}
                move.plastic_generated = True
                continue
            if mode == 'none':
                move.plastic_footer_note = False
                move.plastic_generated = True
                continue
            # Minimis por periodo: acumulado de plástico de las facturas confirmadas
            # del periodo (cuenten o no cuota), para que fraccionar no evite el impuesto
            start, end = move._plastic_period_range()
            move_types = ('out_invoice', 'out_refund') if is_sale else ('in_invoice', 'in_refund')
            prev = self.env['account.move'].search([
                ('company_id', '=', company.id), ('move_type', 'in', move_types),
                ('state', '=', 'posted'), ('invoice_date', '>=', start),
                ('invoice_date', '<=', end), ('id', '!=', move.id)])
            period_kg = sum(mv._plastic_source_kg() for mv in prev)
            minimis = company.plastic_tax_minimis_kg or 0.0
            if minimis and (period_kg + total_kg) < minimis:
                move.plastic_footer_note = False
                move.plastic_generated = True
                continue

            # Construir líneas por tarifa
            rate = company.plastic_tax_rate or 0.45
            src = move.invoice_line_ids.filtered(
                lambda l: l.display_type == 'product' and not l.is_plastic_tax_line)
            calc, prod_by_key = [], {}
            for l in src:
                e = l.product_id.plastic_effective()
                kp = e['tax_product'] or default_prod
                key = kp.id if kp else 0
                prod_by_key[key] = kp
                calc.append({'qty': l.quantity, 'kg_plastic_unit': e['kg_plastic_unit'],
                             'kg_recycled_cert_unit': e['kg_recycled_cert_unit'],
                             'plastic_single_use': e['plastic_single_use'] and not e['plastic_not_subject'],
                             'tariff_key': key})
            res = compute_plastic_tax_lines(calc, mode, is_sale, rate=rate, minimis_kg=0.0)
            if not res:
                move.plastic_footer_note = False
                move.plastic_generated = True
                continue
            sale_tax = company.account_sale_tax_id if is_sale else False
            acc_out = company.plastic_tax_account_output_id
            acc_exp = company.plastic_tax_account_expense_id
            acc_cost = company.plastic_tax_account_cost_id
            new_lines, tot_amount, tot_kg = [], 0.0, 0.0
            for r in res:
                prod = prod_by_key.get(r['tariff_key']) or default_prod
                if not prod:
                    raise UserError(_("No existe el producto de tasa del plástico."))
                vals = {
                    'display_type': 'product', 'product_id': prod.id,
                    'quantity': r['kg'], 'price_unit': rate * r['sign'],
                    'is_plastic_tax_line': True,
                    'name': (_('Impuesto plástico (%(rate)s EUR/kg) - %(kg)s kg')
                             % {'rate': rate, 'kg': r['kg']} if r['kind'] == 'tax'
                             else _('Impuesto plástico - contrapartida')),
                }
                if r['kind'] == 'tax':
                    if acc_out:
                        vals['account_id'] = acc_out.id
                else:  # contrapartida: coste (informativa) o autoliquidación (UE)
                    cp_acc = acc_exp if r.get('cp_kind') == 'autoliq' else acc_cost
                    if cp_acc:
                        vals['account_id'] = cp_acc.id
                # IVA solo en el cargo real de venta (agregada); nunca en el neto 0
                if is_sale and r['kind'] == 'tax' and r.get('charged') and sale_tax:
                    vals['tax_ids'] = [(6, 0, sale_tax.ids)]
                else:
                    vals['tax_ids'] = [(5, 0, 0)]
                new_lines.append((0, 0, vals))
                if r['kind'] == 'tax':
                    tot_amount += r['amount']
                    tot_kg += r['kg']
            move.invoice_line_ids = new_lines
            move.plastic_footer_note = NOTE_TAXED % {
                'amount': ('%.2f' % tot_amount), 'kg': ('%.3f' % tot_kg)}
            move.plastic_generated = True
        return True

    # ------------------------------------------------ libro registro al confirmar
    def _plastic_create_ledger(self):
        Ledger = self.env['l10n_es.plastic.ledger']
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
                continue
            Ledger.search([('move_id', '=', move.id)]).unlink()
            is_refund = move.move_type in ('out_refund', 'in_refund')
            is_sale = move.move_type in ('out_invoice', 'out_refund')
            exempt, reason = move._plastic_exemption()
            total_kg = move._plastic_source_kg()
            if total_kg <= 0:
                continue
            base_type = 'sold' if is_sale else 'purchased'
            if exempt:
                Ledger.create({
                    'name': move.name or _('Factura'), 'date': move.invoice_date or fields.Date.context_today(move),
                    'entry_type': base_type, 'kg': round(total_kg, 4), 'amount': 0.0,
                    'exempt': True, 'exemption_reason': reason,
                    'move_id': move.id, 'company_id': move.company_id.id})
                continue
            for l in move.invoice_line_ids.filtered(
                    lambda x: x.is_plastic_tax_line and x.price_unit > 0):
                sign = -1 if is_refund else 1
                Ledger.create({
                    'name': move.name or _('Factura'),
                    'date': move.invoice_date or fields.Date.context_today(move),
                    'entry_type': 'deduction' if is_refund else base_type,
                    'product_id': l.product_id.id,
                    'kg': round(l.quantity * sign, 4),
                    'amount': round(l.price_subtotal * sign, 2),
                    'move_id': move.id, 'company_id': move.company_id.id})

    def action_post(self):
        res = super().action_post()
        self._plastic_create_ledger()
        return res

    def _get_move_lines_to_report(self):
        # Oculta en el PDF las líneas de contrapartida (neto 0) del impuesto plástico
        lines = super()._get_move_lines_to_report()
        if self.company_id.plastic_hide_counterpart_pdf:
            lines = lines.filtered(
                lambda l: not (l.is_plastic_tax_line and l.price_total < 0))
        return lines
