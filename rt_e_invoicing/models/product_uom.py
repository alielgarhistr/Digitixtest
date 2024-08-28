# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductUoMInherit(models.Model):
    _inherit = 'uom.uom'
    
    uom_code = fields.Char(string='Code')