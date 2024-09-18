# -*- coding: utf-8 -*-
{
   'name': 'Print Employee forms',
    'summary': """Generate PDF Report of   Employee froms""",
    'summary': """Generate PDF Report of  Employee froms""",
    'version': '15.0.1.0.0',
    'author': 'Ali ELgarhi',
    'company': 'Strategizeit.us',
    'maintainer': 'Strategizeit.us',
    'website': "https://strategizeit.us/",
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_contract','web','hr_holidays','l10n_ch'],
    'data': [
        'views/res_company_view.xml',
        'views/added_fields.xml',
        'report/report_paper_format.xml',
        'report/contract_report.xml',
        'report/report_contract.xml',
        'report/employee_contract.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'assets':{
    'web.report_assets_common': [
            '/employee_froms/static/src/css/font.css',
        ]
    }
    ,
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
