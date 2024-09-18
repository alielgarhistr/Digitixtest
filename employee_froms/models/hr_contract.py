from odoo import models, fields, api
from num2words import num2words

class HrContract(models.Model):
    _inherit = 'hr.contract'

    wage_in_ar_words = fields.Char(string="Wage in Words (Arabic)", compute='_compute_wage_in_ar_words')

    
    @api.depends('wage','basic_salary')
    def _compute_wage_in_ar_words(self):
        print("inside _compute_wage_in_ar_words")
        for record in self:
            if record.wage:
                record.wage_in_ar_words = num2words(record.wage, to='cardinal', lang='ar').capitalize()
                print(record.wage_in_ar_words)
            else:
                record.wage_in_ar_words = ''


