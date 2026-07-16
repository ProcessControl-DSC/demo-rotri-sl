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
        'account.account', string='Cuenta autoliquidación',
        help='Contrapartida de la autoliquidación intracomunitaria (típicamente 631).')
    plastic_tax_account_cost_id = fields.Many2one(
        'account.account', string='Cuenta coste (informativa compra)',
        help='Contrapartida en COMPRA nacional cuando la tasa está incluida en el '
             'precio: se abona aquí para reclasificar el importe del plástico del '
             'coste de compra al tributo (631), a neto cero (típicamente 600).')
    plastic_tax_account_income_id = fields.Many2one(
        'account.account', string='Cuenta ingreso (informativa venta)',
        help='Contrapartida en VENTA cuando la tasa está incluida en el precio: '
             'menos ingreso (típicamente 700).')
    plastic_kg_from_weight = fields.Boolean(
        string='Calcular kg desde el peso',
        help='Si se activa, los kg de plástico se calculan como peso del producto '
             'por el porcentaje de plástico, en lugar de introducirlos a mano.')
    plastic_weight_field_id = fields.Many2one(
        'ir.model.fields', string='Campo de peso origen',
        domain="[('model','=','product.template'),('ttype','in',['float','monetary','integer'])]",
        help='Campo del producto del que se toma el peso técnico para calcular los kg '
             'de plástico. Por defecto el peso estándar del producto.')
    plastic_exempt_from_fiscal_pos = fields.Boolean(
        string='Exención por posición fiscal', default=True,
        help='Deriva la exención (exportación / intracomunitaria) de la posición '
             'fiscal de la factura.')
    plastic_first_seller = fields.Boolean(
        string='Fabricante o primer vendedor', default=True,
        help='La empresa fabrica o es el primer vendedor en territorio nacional, por '
             'lo que es sujeto pasivo del 592 y repercute el impuesto en ventas '
             'nacionales. Desmárcalo si la empresa es solo distribuidora (el impuesto '
             'ya lo devengó el proveedor o la importación): entonces la factura avisa '
             'si una venta nacional intenta repercutir el impuesto de nuevo.')
    plastic_hide_counterpart_pdf = fields.Boolean(
        string='Ocultar contrapartida en PDF', default=True)
    plastic_mo_registration = fields.Selection(
        [('per_mo', 'Por orden de fabricación'), ('daily', 'Agregado diario')],
        string='Registro de fabricación', default='per_mo')
    plastic_snapshot_interval = fields.Selection(
        [('month', 'Mensual'), ('quarter', 'Trimestral'), ('year', 'Anual')],
        string='Periodicidad existencias', default='month',
        help='Cada cuánto la acción planificada genera el snapshot de existencias en kg.')

    _PLASTIC_SNAP_CRON = 'pc_l10n_es_plastic_tax.ir_cron_plastic_snapshot'

    def _sync_plastic_snapshot_cron(self):
        cron = self.env.ref(self._PLASTIC_SNAP_CRON, raise_if_not_found=False)
        if not cron:
            return
        mapping = {'month': (1, 'months'), 'quarter': (3, 'months'), 'year': (1, 'years')}
        interval = self.env.company.plastic_snapshot_interval or 'month'
        num, typ = mapping[interval]
        cron.sudo().write({'interval_number': num, 'interval_type': typ})

    def write(self, vals):
        res = super().write(vals)
        if 'plastic_snapshot_interval' in vals:
            self._sync_plastic_snapshot_cron()
        return res
