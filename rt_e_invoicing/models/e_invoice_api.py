# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EInvoiceAPI(models.Model):
    _name = 'e.invoice.api'

    name = fields.Char(string='Name')
    url = fields.Char(string='URL')
