# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.pc_l10n_es_plastic_tax.models.plastic_tax_lib import (
    compute_plastic_tax_lines,
)


def _line(qty, kg, rec=0.0, plastic=True, key='A'):
    return {'qty': qty, 'kg_plastic_unit': kg, 'kg_recycled_cert_unit': rec,
            'plastic_single_use': plastic, 'tariff_key': key}


@tagged('post_install', '-at_install')
class TestPlasticTaxLib(TransactionCase):

    def test_01_venta_agregada_cargo(self):
        # venta agregada = cargo real, una sola línea
        r = compute_plastic_tax_lines([_line(100, 0.1)], 'aggregated', True)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['kg'], 10.0)
        self.assertEqual(r[0]['amount'], 4.5)
        self.assertEqual(r[0]['kind'], 'tax')
        self.assertTrue(r[0]['charged'])

    def test_01b_venta_informativa_neto0(self):
        # venta informativa (incluida) = línea + contrapartida, neto 0, no cargo
        r = compute_plastic_tax_lines([_line(100, 0.1)], 'info_included', True)
        self.assertEqual(len(r), 2)
        tax = [x for x in r if x['kind'] == 'tax'][0]
        cp = [x for x in r if x['kind'] == 'counterpart'][0]
        self.assertFalse(tax['charged'])
        self.assertEqual(cp['cp_kind'], 'cost')
        self.assertEqual(tax['amount'], cp['amount'])

    def test_02_venta_2_tarifas(self):
        r = compute_plastic_tax_lines(
            [_line(50, 0.2, key='A'), _line(100, 0.15, key='B')], 'aggregated', True)
        self.assertEqual(len(r), 2)
        a = [x for x in r if x['tariff_key'] == 'A'][0]
        b = [x for x in r if x['tariff_key'] == 'B'][0]
        self.assertEqual(a['kg'], 10.0)
        self.assertEqual(b['kg'], 15.0)
        self.assertEqual(b['amount'], 6.75)

    def test_03_compra_info_included_contrapartida(self):
        r = compute_plastic_tax_lines([_line(200, 0.05)], 'info_included', False)
        self.assertEqual(len(r), 2)
        tax = [x for x in r if x['kind'] == 'tax'][0]
        cp = [x for x in r if x['kind'] == 'counterpart'][0]
        self.assertEqual(tax['sign'], 1)
        self.assertEqual(cp['sign'], -1)
        self.assertEqual(tax['amount'], cp['amount'])  # neto 0

    def test_04_compra_self_assessment(self):
        r = compute_plastic_tax_lines([_line(100, 0.1)], 'self_assessment', False)
        self.assertEqual(len(r), 2)
        self.assertTrue(all(x['self_assessment'] for x in r))
        cp = [x for x in r if x['kind'] == 'counterpart'][0]
        self.assertEqual(cp['cp_kind'], 'autoliq')

    def test_05_compra_aggregated(self):
        r = compute_plastic_tax_lines([_line(100, 0.1)], 'aggregated', False)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['kind'], 'tax')
        self.assertEqual(r[0]['amount'], 4.5)

    def test_06_base_neta_reciclado(self):
        # 100 u x (0.1 - 0.06) = 4 kg; minimis_kg=0 para no aplicar la exención
        r = compute_plastic_tax_lines([_line(100, 0.1, rec=0.06)], 'info_included', True,
                                      minimis_kg=0.0)
        self.assertEqual(r[0]['kg'], 4.0)
        self.assertEqual(r[0]['amount'], 1.8)

    def test_07_minimis_exento(self):
        r = compute_plastic_tax_lines([_line(10, 0.1)], 'info_included', True, minimis_kg=5.0)
        self.assertEqual(r, [])

    def test_08_linea_sin_plastico_ignorada(self):
        r = compute_plastic_tax_lines(
            [_line(100, 0.1, plastic=False), _line(100, 0.1)], 'aggregated', True)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['kg'], 10.0)

    def test_09_none_sin_lineas(self):
        self.assertEqual(compute_plastic_tax_lines([_line(100, 0.1)], 'none', True), [])

    def test_10_self_assessment_venta_error(self):
        with self.assertRaises(ValueError):
            compute_plastic_tax_lines([_line(100, 0.1)], 'self_assessment', True)
