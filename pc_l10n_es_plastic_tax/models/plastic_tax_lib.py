# -*- coding: utf-8 -*-
"""Lógica pura del impuesto sobre envases de plástico no reutilizables (Ley 7/2022).

Sin dependencias de Odoo: facilita el testeo unitario y la revisión funcional.
Núcleo algorítmico generado con asistencia IA (kimi) y verificado para Odoo 19.
"""

DEFAULT_RATE = 0.45          # EUR / kg de plástico no reciclado (art. 77)
DEFAULT_MINIMIS_KG = 5.0     # exención por debajo de 5 kg/mes (art. 73)


def net_kg(line):
    """Kg de plástico NO reciclado de una línea (base imponible, art. 76).

    line: dict con qty, kg_plastic_unit, kg_recycled_cert_unit, plastic_single_use.
    El plástico reciclado solo resta si está certificado (campo kg_recycled_cert_unit).
    """
    if not line.get('plastic_single_use'):
        return 0.0
    qty = line.get('qty', 0.0) or 0.0
    kg_unit = line.get('kg_plastic_unit', 0.0) or 0.0
    kg_rec = line.get('kg_recycled_cert_unit', 0.0) or 0.0
    per_unit = max(0.0, kg_unit - kg_rec)
    total = per_unit * qty
    return total if total > 0 else 0.0


def compute_plastic_tax_lines(invoice_lines, party_mode, is_sale,
                              rate=DEFAULT_RATE, minimis_kg=DEFAULT_MINIMIS_KG):
    """Devuelve las líneas de tasa a generar en una factura.

    party_mode: 'none' | 'info_included' | 'aggregated' | 'self_assessment'
                (self_assessment solo en compras intracomunitarias).
    is_sale: True venta, False compra.
    Retorna lista de dicts: {tariff_key, kg, amount, sign, kind, self_assessment}
        kind: 'tax' (línea de tasa) | 'counterpart' (contrapartida neto 0).
    Lista vacía => sin tasa (no aplica o exención minimis).
    """
    if party_mode == 'none':
        return []
    if party_mode == 'self_assessment' and is_sale:
        raise ValueError("self_assessment solo aplica a compras")

    # Agrupar kg por tarifa (art. agrupación por producto de tasa)
    tariff_kgs = {}
    for line in invoice_lines:
        kg = net_kg(line)
        if kg <= 0:
            continue
        key = line.get('tariff_key', 'default')
        tariff_kgs[key] = tariff_kgs.get(key, 0.0) + kg

    if not tariff_kgs:
        return []

    # Exención minimis (< umbral en el periodo)
    if sum(tariff_kgs.values()) < minimis_kg:
        return []

    # 'aggregated' => cargo real (una sola línea). 'info_included'/'self_assessment'
    # => la tasa ya está en el precio => línea + contrapartida (neto 0).
    charged = (party_mode == 'aggregated')
    sa = (party_mode == 'self_assessment')
    cp_kind = 'autoliq' if sa else 'cost'
    result = []
    for key, kg in tariff_kgs.items():
        # redondear primero los kg y derivar el importe de ese kg redondeado, para
        # que la nota al pie y el libro registro (que parten del kg redondeado) cuadren
        kg = round(kg, 4)
        amount = round(kg * rate, 2)
        result.append({'tariff_key': key, 'kg': kg, 'amount': amount, 'sign': 1,
                       'kind': 'tax', 'self_assessment': sa, 'charged': charged})
        if not charged:
            result.append({'tariff_key': key, 'kg': kg, 'amount': amount, 'sign': -1,
                           'kind': 'counterpart', 'self_assessment': sa, 'cp_kind': cp_kind})
    return result
