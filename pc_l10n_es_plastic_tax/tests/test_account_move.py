# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMovePlastic(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        # Solo tiene sentido con plan contable cargado
        self.has_chart = bool(self.company.chart_template)

    def _plastic_product(self):
        return self.env['product.product'].create({
            'name': 'Bolsa plástico test',
            'type': 'consu',
            'plastic_single_use': True,
            'kg_plastic_unit': 0.5,
        })

    def test_generate_sale_tax_line(self):
        if not self.has_chart:
            self.skipTest("Sin plan contable en la BD de test")
        partner = self.env['res.partner'].create({
            'name': 'Cliente plástico', 'plastic_tax_customer_mode': 'info_included'})
        prod = self._plastic_product()
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': prod.id, 'quantity': 100, 'price_unit': 1.0})],
        })
        self.assertTrue(move.plastic_needs_generation)
        move.action_generate_plastic_tax()
        tax_lines = move.invoice_line_ids.filtered('is_plastic_tax_line')
        self.assertEqual(len(tax_lines), 1)
        # 100 u x 0,5 kg = 50 kg x 0,45 = 22,5
        self.assertAlmostEqual(tax_lines.price_total and tax_lines.price_subtotal, 22.5, places=2)
        self.assertFalse(move.plastic_needs_generation)  # ya generado
