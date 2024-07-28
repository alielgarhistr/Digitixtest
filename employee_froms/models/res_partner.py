from odoo import _, api, fields, models

    

class ResPrtner(models.Model):
    _inherit = "res.partner"   

    # company owner
    owner_name = fields.Char(string='Owner')
    building_no = fields.Integer(string='Building NO')
