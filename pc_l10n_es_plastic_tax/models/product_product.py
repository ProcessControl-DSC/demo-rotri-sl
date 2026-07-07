# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    plastic_variant_specific = fields.Boolean(
        related='product_tmpl_id.plastic_variant_specific', readonly=True)
    plastic_single_use_var = fields.Boolean(string='Plástico un solo uso (variante)')
    plastic_not_subject_var = fields.Boolean(string='No sujeto (variante)')
    plastic_pct_var = fields.Float(string='% plástico (variante)', digits=(16, 6))
    kg_plastic_unit_var = fields.Float(string='Kg plástico no reciclado/ud (variante)', digits=(16, 6))
    kg_recycled_cert_unit_var = fields.Float(string='Kg reciclado cert./ud (variante)', digits=(16, 6))
    plastic_tax_product_var_id = fields.Many2one('product.product', string='Producto tasa (variante)')

    def plastic_effective(self):
        """Valores de plástico efectivos: por variante si el template lo activa,
        si no los del template. Devuelve dict homogéneo para toda la lógica."""
        self.ensure_one()
        t = self.product_tmpl_id
        if t.plastic_variant_specific:
            company = self.env.company
            if company.plastic_kg_from_weight:
                fname = company.plastic_weight_field_id.name or 'weight'
                w = self[fname] if fname in self._fields else (self.weight or 0.0)
                kg = (w or 0.0) * (self.plastic_pct_var or 0.0)
            else:
                kg = self.kg_plastic_unit_var
            return {
                'plastic_single_use': self.plastic_single_use_var,
                'plastic_not_subject': self.plastic_not_subject_var,
                'kg_plastic_unit': kg,
                'kg_recycled_cert_unit': self.kg_recycled_cert_unit_var,
                'tax_product': self.plastic_tax_product_var_id or t.plastic_tax_product_id,
            }
        return {
            'plastic_single_use': t.plastic_single_use,
            'plastic_not_subject': t.plastic_not_subject,
            'kg_plastic_unit': t.kg_plastic_unit,
            'kg_recycled_cert_unit': t.kg_recycled_cert_unit,
            'tax_product': t.plastic_tax_product_id,
        }
