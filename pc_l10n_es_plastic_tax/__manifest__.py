# -*- coding: utf-8 -*-
{
    'name': 'Impuesto sobre envases de plástico no reutilizables',
    'version': '19.0.1.0.0',
    'summary': 'Impuesto especial del plástico (Ley 7/2022) en compras y ventas',
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
