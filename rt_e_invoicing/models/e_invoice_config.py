# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EInvoiceAPI(models.Model):
    _name = 'e.invoice.config'

    name = fields.Char(string='Name')
    client_id = fields.Char(string='Client ID')
    client_secret = fields.Char(string='Client Secret')
