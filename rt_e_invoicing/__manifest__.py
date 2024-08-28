# -*- coding: utf-8 -*-
{
    'name': "E-Invoicing",

    'author': "Rightechs Solutions",
    'website': "https://rightechs.info",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Invoicing & Payments',
    'version': '0.1',

    'depends': ['base','account','product'],

    'data': [
        'security/ir.model.access.csv',
        'views/account_tax.xml',
        'views/tax_data.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/account_invoice.xml',
        # 'views/res_config_settings.xml', # not work with sales module
        'views/product_uom.xml',
        'views/product_uom_data.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/e_invoice_integration.xml',
        'views/e_invoice_api.xml',
        'views/e_invoice_config.xml',
        'views/menu.xml',
        'data/cron.xml',
        'wizard/action_sent_eta_wiz.xml'
    ],
}