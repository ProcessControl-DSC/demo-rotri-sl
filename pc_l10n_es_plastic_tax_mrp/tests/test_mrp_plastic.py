# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.pc_l10n_es_plastic_tax.models.plastic_tax_lib import net_kg


@tagged('post_install', '-at_install')
class TestMrpPlastic(TransactionCase):

    def test_net_kg_produced(self):
        # verificación de la fórmula usada por el devengo de fabricación
        kg = net_kg({'qty': 200, 'kg_plastic_unit': 0.3,
                     'kg_recycled_cert_unit': 0.1, 'plastic_single_use': True})
        self.assertAlmostEqual(kg, 40.0, places=3)  # 200 * (0.3-0.1)

    def test_ledger_model_has_production_field(self):
        self.assertIn('production_id', self.env['l10n_es.plastic.ledger']._fields)
