# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMovePlastic(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.has_chart = bool(self.company.chart_template)

    def _plastic_product(self, kg=0.5, rec=0.0):
        return self.env['product.product'].create({
            'name': 'Bolsa plástico test', 'type': 'consu',
            'plastic_single_use': True, 'kg_plastic_unit': kg,
            'kg_recycled_cert_unit': rec})

    def _invoice(self, partner, prod, qty=100):
        return self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': partner.id,
            'invoice_date': '2026-05-04',
            'invoice_line_ids': [(0, 0, {
                'product_id': prod.id, 'quantity': qty, 'price_unit': 1.0})]})

    def test_generate_sale_tax_line(self):
        if not self.has_chart:
            self.skipTest("Sin plan contable")
        partner = self.env['res.partner'].create({
            'name': 'Cliente plástico', 'plastic_tax_customer_mode': 'aggregated'})
        move = self._invoice(partner, self._plastic_product(kg=0.5))
        self.assertTrue(move.plastic_needs_generation)
        move.action_generate_plastic_tax()
        tax = move.invoice_line_ids.filtered('is_plastic_tax_line')
        self.assertEqual(len(tax), 1)
        self.assertAlmostEqual(tax.price_subtotal, 22.5, places=2)  # 100*0.5*0.45
        self.assertFalse(move.plastic_needs_generation)
        # libro registro solo al confirmar
        self.assertEqual(self.env['l10n_es.plastic.ledger'].search_count(
            [('move_id', '=', move.id)]), 0)
        move.action_post()
        self.assertEqual(self.env['l10n_es.plastic.ledger'].search_count(
            [('move_id', '=', move.id), ('exempt', '=', False)]), 1)

    def test_variant_specific_kg(self):
        # plástico por variante: cada variante con su kg
        attr = self.env['product.attribute'].create({'name': 'Talla PT'})
        v1, v2 = self.env['product.attribute.value'].create([
            {'name': 'S', 'attribute_id': attr.id}, {'name': 'L', 'attribute_id': attr.id}])
        tmpl = self.env['product.template'].create({
            'name': 'Envase variante', 'type': 'consu',
            'plastic_single_use': True, 'plastic_variant_specific': True,
            'attribute_line_ids': [(0, 0, {'attribute_id': attr.id,
                                           'value_ids': [(6, 0, [v1.id, v2.id])]})]})
        variants = tmpl.product_variant_ids
        variants[0].write({'plastic_single_use_var': True, 'kg_plastic_unit_var': 0.2})
        variants[1].write({'plastic_single_use_var': True, 'kg_plastic_unit_var': 0.8})
        e0 = variants[0].plastic_effective()
        e1 = variants[1].plastic_effective()
        self.assertEqual(e0['kg_plastic_unit'], 0.2)
        self.assertEqual(e1['kg_plastic_unit'], 0.8)

    def test_kg_from_weight_percentage(self):
        # 7.1: % se interpreta como porcentaje (0-100), no fracción
        self.company.plastic_kg_from_weight = True
        p = self.env['product.product'].create({
            'name': 'QA tapón', 'type': 'consu', 'plastic_single_use': True,
            'weight': 0.05, 'plastic_pct': 50.0})
        self.assertAlmostEqual(p.product_tmpl_id.kg_plastic_unit, 0.025, places=6)
        self.company.plastic_kg_from_weight = False

    def test_refund_registers_deduction(self):
        # 7.3: la rectificativa registra la deducción en el libro
        if not self.has_chart:
            self.skipTest("Sin plan contable")
        partner = self.env['res.partner'].create({
            'name': 'Cliente refund', 'plastic_tax_customer_mode': 'aggregated'})
        move = self._invoice(partner, self._plastic_product(kg=0.5))
        move.action_generate_plastic_tax()
        move.action_post()
        refund = move._reverse_moves([{'invoice_date': move.invoice_date}])
        refund.action_post()
        ded = self.env['l10n_es.plastic.ledger'].search(
            [('move_id', '=', refund.id), ('entry_type', '=', 'deduction')])
        self.assertTrue(ded)
        self.assertLess(ded[0].kg, 0)

    def test_exemption_reason_no_tax(self):
        if not self.has_chart:
            self.skipTest("Sin plan contable")
        partner = self.env['res.partner'].create({
            'name': 'Cliente export', 'plastic_tax_customer_mode': 'info_included'})
        move = self._invoice(partner, self._plastic_product(kg=0.5))
        move.plastic_exemption_reason = 'export'
        move.action_generate_plastic_tax()
        self.assertFalse(move.invoice_line_ids.filtered('is_plastic_tax_line'))
        self.assertIn('75.1.c', move.plastic_footer_note or '')
        move.action_post()
        led = self.env['l10n_es.plastic.ledger'].search([('move_id', '=', move.id)])
        self.assertTrue(led.exempt)
