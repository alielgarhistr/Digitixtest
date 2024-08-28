# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountTaxInherit(models.Model):
    _inherit = 'account.tax'

    code = fields.Char(string='Code')
    parent_code  = fields.Char(string='Parent Code')
