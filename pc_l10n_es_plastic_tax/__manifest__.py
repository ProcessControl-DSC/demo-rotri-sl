# -*- coding: utf-8 -*-
{
    'name': 'Impuesto sobre envases de plástico no reutilizables',
    'version': '19.0.4.3.1',
    'summary': 'Impuesto especial del plástico (Ley 7/2022) en compras y ventas',
    'description': """
<div style="font-family:Arial,sans-serif;color:#222;line-height:1.5">
<h2 style="color:#0f4c81">Impuesto sobre envases de plástico no reutilizables (Ley 7/2022)</h2>
<p>Calcula, contabiliza, repercute y reporta el impuesto del plástico (0,45 EUR/kg de plástico no reciclado) en compras, fabricación y ventas. Módulos: pc_l10n_es_plastic_tax (núcleo) + pc_l10n_es_plastic_tax_mrp (devengo en fabricación).</p>
<h3 style="color:#0f4c81">1. Configuración de la compañía</h3>
<p>Ajustes, Compañías, grupo "Impuesto del plástico": CIP, tipo (0,45), umbral minimis, periodo del 592 (mensual/trimestral), cuentas de impuesto repercutido (una 475 de pasivo corriente) y gasto (631), cálculo de kg desde el peso (campo configurable), exención por posición fiscal, ocultar contrapartida en PDF, registro de fabricación y periodicidad de existencias.</p>
<p><img src="/pc_l10n_es_plastic_tax/static/description/cfg_company.png" style="max-width:100%;border:1px solid #ccc"/></p>
<h3 style="color:#0f4c81">2. Configuración de productos</h3>
<p>Pestaña "Impuesto plástico": plástico de un solo uso, kg no reciclado/ud (o % si se calcula desde el peso), kg reciclado certificado + referencia (UNE-EN 15343), no sujeto (art. 72) y producto de tasa asociado. Con "Datos de plástico por variante" los valores se definen por variante.</p>
<p><img src="/pc_l10n_es_plastic_tax/static/description/prod_plastic.png" style="max-width:100%;border:1px solid #ccc"/></p>
<h3 style="color:#0f4c81">3. Configuración de contactos</h3>
<p>Modo de impuesto de cliente y de proveedor (no aplica / informativa / agregada / autoliquidación).</p>
<p><img src="/pc_l10n_es_plastic_tax/static/description/partner_mode.png" style="max-width:100%;border:1px solid #ccc"/></p>
<h3 style="color:#0f4c81">4. Flujo en la factura</h3>
<p>En una factura en borrador con productos de plástico aparece el aviso con el botón "Generar impuesto del plástico". Añade la línea de tasa (con IVA en venta) y la nota legal (art. 82.8 / 75.1.c). La contrapartida no se imprime. El movimiento se registra en el libro al confirmar.</p>
<p><img src="/pc_l10n_es_plastic_tax/static/description/invoice_banner.png" style="max-width:100%;border:1px solid #ccc"/></p>
<p><img src="/pc_l10n_es_plastic_tax/static/description/invoice_taxline.png" style="max-width:100%;border:1px solid #ccc"/></p>
<h3 style="color:#0f4c81">5. Libro registro, existencias y modelo 592</h3>
<p>Contabilidad, menú Impuesto plástico: libro registro (exportable a CSV), existencias mensuales en kg (acción planificada configurable) y regularización (art. 80). El borrador del modelo 592 resume la sección contributiva y la de exenciones.</p>
<p><img src="/pc_l10n_es_plastic_tax/static/description/libro.png" style="max-width:100%;border:1px solid #ccc"/></p>
<h3 style="color:#0f4c81">6. Carga inicial (cutover)</h3>
<p>Importación estándar de Odoo (CSV) de productos (kg/%), contactos (modos), compañía (CIP y cuentas) y saldo inicial de existencias.</p>
<p style="color:#59748c">Process Control — módulo pc_l10n_es_plastic_tax (Odoo 19). Capturas con empresa de ejemplo (datos anonimizados).</p>
</div>""",
    'author': 'Process Control',
    'website': 'https://www.processcontrol.es',
    'license': 'LGPL-3',
    'category': 'Accounting/Localizations',
    'depends': ['account', 'l10n_es'],
    'data': [
        'security/ir.model.access.csv',
        'data/plastic_tax_data.xml',
        'data/plastic_cron.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/account_fiscal_position_views.xml',
        'views/account_move_views.xml',
        'views/plastic_ledger_views.xml',
        'report/plastic_592_report.xml',
        'report/invoice_report.xml',
    ],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
