# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    eta_code_type = fields.Selection([('GS1', 'GS1'), ('EGS', 'EGS')],
                                     string='ETA Code Type',
                                     default='GS1')
    gpc_code = fields.Char('GPC Code')

