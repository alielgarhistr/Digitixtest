# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    issuer_type = fields.Selection([('B', 'Business in Egypt'),('F', 'Foreigner'),('P', 'Natural person')],
        string='Issuer Type', default='B', required=True)
    activity_code = fields.Char(string='Activity Code')
