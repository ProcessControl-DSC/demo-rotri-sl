# -*- coding: utf-8 -*-
from odoo import fields, models


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
