# -*- coding: utf-8 -*-
{
    'name': "HR Attendance Sheet And Policies",

    'summary': """Managing  Attendance Sheets for Employees""",
    'description': """Employees Attendance Sheet Management """,
    "author": "Global Solutions",
    "website": "https://globalsolutions.dev",
    'category': 'hr',
    'version': '15.0.0.01',
    'images': ['static/description/bannar.jpg'],
    'depends': ['base',
                'hr',
                'hr_payroll',
                'hr_holidays',
                'hr_attendance'],
    'data': [
        'data/ir_sequence.xml',
        'data/data2.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/change_att_data_view.xml',
        'views/hr_attendance_sheet_view.xml',
        'views/hr_attendance_policy_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_public_holiday_view.xml',
        'views/attendance_sheet_batch_view.xml',

    ],

    'license': 'OPL-1',
    'demo': [
        'demo/demo.xml',
    ],
}
