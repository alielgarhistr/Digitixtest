from odoo import _, api, fields, models



class  ResCompany(models.Model):
    _inherit = 'res.company'

    contract_report = fields.Html(string='Contract Report')