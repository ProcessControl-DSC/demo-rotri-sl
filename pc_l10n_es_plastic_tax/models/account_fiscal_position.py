# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    plastic_exempt = fields.Boolean(
        string='Exenta impuesto plástico',
        help='Las operaciones con esta posición fiscal están exentas del impuesto '
             '(exportación, entrega intracomunitaria...). Se registran en el libro '
             'sin cuota.')
    plastic_exempt_reason = fields.Selection([
        ('export', 'Exportación'),
        ('eu', 'Entrega intracomunitaria'),
        ('sanitary', 'Uso sanitario o médico'),
        ('animal_feed', 'Alimentación animal'),
    ], string='Motivo exención plástico')
    plastic_region = fields.Selection([
        ('national', 'Nacional'),
        ('intracom', 'Intracomunitaria'),
        ('extracom', 'Extracomunitaria'),
    ], string='Ámbito (plástico)', compute='_compute_plastic_region', store=True,
        help='Ámbito derivado automáticamente del país o grupo de países asociados '
             'a la posición fiscal: nacional (España), intracomunitaria (grupo UE) '
             'y extracomunitaria (todo lo demás, incluidas las posiciones sin país '
             'ni grupo asociado como Extracomunitaria/DUA).')

    @api.depends('country_id', 'country_group_id',
                 'country_group_id.country_ids')
    def _compute_plastic_region(self):
        es = self.env.ref('base.es', raise_if_not_found=False)
        eu = self.env.ref('base.europe', raise_if_not_found=False)
        eu_ids = set(eu.country_ids.ids) if eu else set()
        for fp in self:
            countries = fp.country_id
            if not countries and fp.country_group_id:
                countries = fp.country_group_id.country_ids
            cids = set(countries.ids)
            if es and cids == {es.id}:
                fp.plastic_region = 'national'
            elif cids and eu_ids and cids <= eu_ids:
                fp.plastic_region = 'intracom'
            else:
                # todo lo que no es nacional ni intracom (incl. sin país/grupo)
                fp.plastic_region = 'extracom'
