# -*- coding: utf-8 -*-
{
    'name': 'Impuesto sobre envases de plástico no reutilizables',
    'version': '19.0.1.1.0',
    'summary': 'Impuesto especial del plástico (Ley 7/2022) en compras y ventas',
    'description': """
<div style="font-family:Arial,sans-serif;color:#222;line-height:1.5">
<h2 style="color:#0f4c81">Impuesto sobre envases de plástico no reutilizables (Ley 7/2022)</h2>
<p>Calcula, contabiliza, repercute y reporta el impuesto especial del plástico
(0,45 EUR/kg de plástico no reciclado) en compras, fabricación y ventas.</p>

<h3 style="color:#0f4c81">1. Qué hace</h3>
<ul>
<li>4 casos de compra (no aplica, informativa, agregada, autoliquidación UE) y 3 de venta.</li>
<li>Base neta: descuenta el plástico reciclado certificado (UNE-EN 15343).</li>
<li>Agrupación por tarifa y exención minimis por debajo de 5 kg/mes.</li>
<li>Devengo en fabricación, libro registro de existencias y borrador del modelo 592.</li>
<li>Nota legal en la factura (art. 82.8 aplicado / 75.1.c exento) con importe y kg.</li>
</ul>

<h3 style="color:#0f4c81">2. Configuración</h3>
<ul>
<li>Producto, pestaña Impuesto plástico: marcar Plástico de un solo uso, indicar Kg no reciclado/ud
y, si aplica, Kg reciclado certificado + Ref. certificado. No sujeto (art. 72) lo excluye.</li>
<li>Contacto, pestaña Ventas y Compras: fijar el modo de impuesto de cliente y/o proveedor.</li>
<li>Compañía: informar el CIP del Registro territorial.</li>
</ul>

<h3 style="color:#0f4c81">3. Uso en la factura</h3>
<p>En una factura en borrador con productos de plástico aparece un banner con el botón
Generar impuesto del plástico. Al pulsarlo se añade la línea de tasa (con IVA en venta) y,
en compra informativa o autoliquidación, su contrapartida (neto 0). Al imprimir la factura
aparece la nota legal con importe y kg.</p>

<h3 style="color:#0f4c81">4. Libro registro y modelo 592</h3>
<p>En Contabilidad, Impuesto plástico (libro registro), se listan los movimientos
(vendido / adquirido / fabricado / exento) con kg y cuota. Desde ahí, Imprimir, Borrador
modelo 592 genera el resumen (sección contributiva que cuadra con la cuenta 475 y sección de
exenciones).</p>

<h3 style="color:#0f4c81">5. Checklist de validación</h3>
<ol>
<li>Pestaña Impuesto plástico en producto guarda los kg.</li>
<li>Venta contributiva: línea de tasa con IVA 21% y kg correctos.</li>
<li>Base neta con reciclado reduce la base.</li>
<li>Dos tarifas generan dos líneas de tasa.</li>
<li>Compra informativa: línea de tasa + contrapartida (neto 0).</li>
<li>Minimis por debajo de 5 kg no genera cuota.</li>
<li>Impresión de factura con la nota legal.</li>
<li>Libro registro con kg y cuota.</li>
<li>Cierre de orden de fabricación registra el movimiento fabricado.</li>
<li>Borrador 592 cuadra con el libro registro.</li>
</ol>

<h3 style="color:#0f4c81">6. Advertencias</h3>
<ul>
<li>Ocultar las líneas internas de tasa en el PDF y la automatización de deducciones/A22
quedan como mejora posterior.</li>
<li>Verificar con Finanzas las cuentas contables (475 / 631) y el circuito.</li>
<li>El envío real del 592 a la AEAT y la certificación del reciclado son externos; el módulo
prepara la información.</li>
</ul>
<p style="color:#59748c">Process Control — módulo pc_l10n_es_plastic_tax (Odoo 19).</p>
</div>
""",
    'author': 'Process Control',
    'website': 'https://www.processcontrol.es',
    'license': 'LGPL-3',
    'category': 'Accounting/Localizations',
    'depends': ['account', 'l10n_es'],
    'data': [
        'security/ir.model.access.csv',
        'data/plastic_tax_data.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/account_move_views.xml',
        'views/plastic_ledger_views.xml',
        'report/plastic_592_report.xml',
        'report/invoice_report.xml',
    ],
    'installable': True,
    'application': False,
}
