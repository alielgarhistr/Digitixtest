# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InvoiceIntegration(models.Model):
    _name = 'invoice.integration.config'

    name = fields.Char(string='Name')
    user_name = fields.Char(string='Username')
    password = fields.Char(string='Password')

    def auth_validate(self, username, password):
        response = {'success':False}
        if not username and not password:
            response['message'] = 'Missing Basic authentication.'
            return response
        else:
            invoice_config = self.env['invoice.integration.config'].sudo().search([], limit=1)
            if username == invoice_config.user_name and password == invoice_config.password:
                response['success'] = True
                # response['message'] = 'Login successfully.'
            else:
                response['success'] = False
                response['message'] = 'Login Failed username or password is incorrect.'

        return response
