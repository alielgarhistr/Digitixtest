# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################


from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    sin_exist = fields.Boolean("Has Social Insurance")
    sin_no = fields.Char("Social Insurance No", )
    sin_date = fields.Date("Social Insurance Date")
    sin_end_date = fields.Date("Social Insurance  end Date")
    mi_exist = fields.Boolean("Has Medical Insurance")
    mi_no = fields.Char(string="Medical Insurance NO",
                        help='Medical  Insurance No')
    mi_date = fields.Date(string="Medical Insurance Date",
                          help='Medical  Insurance Date')
    mi_amount = fields.Float(string="Medical Insurance Amount",
                             digits=dp.get_precision('Payroll'))
    basic_salary = fields.Float(string="Basic Salary",
                                digits=dp.get_precision('Payroll'))
    variable_salary = fields.Float(string="Variable Salary",
                                   digits=dp.get_precision('Payroll'))
    allowances = fields.Float(string="Allowances",
                              digits=dp.get_precision('Payroll'))

    other_alw_ids = fields.One2many(comodel_name="hr.alw.line",
                                    inverse_name="contract_id",
                                    string="Other Allowances")

    def get_alw(self, alw_code):
        alw_id = self.other_alw_ids.filtered(lambda x: x.code == alw_code)
        return alw_id

    def calculate_eg_tax(self, amount):
        TAX_LEVELS = [
            [0, 40000, 0],
            [40000, 55000, 10],
            [55000, 70000, 15],
            [70000, 200000, 20],
            [200000, 400000, 22.5],
            [400000, 1200000, 25]
        ]

        annual_salary = amount * 12
        if annual_salary > 0:
            annual_salary -= 20000  

        print('amount-->', amount, 'annual_salary--->', annual_salary)
        tax_amounts = []
        total_tax = 0
        levels = []

        if annual_salary <= 600000:
            levels = TAX_LEVELS
        elif 600000 < annual_salary <= 700000:
            levels = TAX_LEVELS[1:]
            levels[0][0] = 0
        elif 700000 < annual_salary <= 800000:
            levels = TAX_LEVELS[2:]
            levels[0][0] = 0
        elif 800000 < annual_salary <= 900000:
            levels = TAX_LEVELS[3:]
            levels[0][0] = 0
        elif 900000 < annual_salary <= 1200000:
            levels = TAX_LEVELS[4:]
            levels[0][0] = 0
        elif annual_salary > 1200000:
            levels = TAX_LEVELS[5:]
            levels[0][0] = 0

        for level in levels:
            if annual_salary < level[0]:
                continue
            elif annual_salary > level[1]:
                tax_amount = (level[1] - level[0]) * level[2] / 100
                tax_amounts.append(tax_amount)
            else:
                tax_amount = (annual_salary - level[0]) * level[2] / 100
                tax_amounts.append(tax_amount)
                break

        if annual_salary > 1200000:
            extra_tax_amount = (annual_salary - 1200000) * 0.275
            tax_amounts.append(extra_tax_amount)

        if tax_amounts:
            total_tax = sum(tax_amounts) / 12
        return total_tax

class HrAlwLine(models.Model):
    _name = "hr.alw.line"
    alw_id = fields.Many2one(comodel_name="hr.alw", string="name",
                             required=True, translate=True)
    code = fields.Char(string="Code", required=True)
    amount = fields.Float(string="Amount", required=True)
    contract_id = fields.Many2one(comodel_name="hr.contract", string="Contract")

    @api.onchange('alw_id')
    def onchange_alw_id(self):
        self.code = self.alw_id.code
        self.amount = self.alw_id.amount


class HrAlow(models.Model):
    _name = "hr.alw"
    name = fields.Char(string="name", required=True, translate=True)
    code = fields.Char(string="Code", required=True)
    amount = fields.Float(string="Amount")

    @api.model
    def create(self, values):
        res = super(HrAlow, self).create(values)
        cat_id = self.env['hr.salary.rule.category'].search(
            [('code', '=', 'ALW')], limit=1)
        rule_obj = self.env['hr.salary.rule']
        condition_exp = 'result = contract.get_alw("%s") and contract.get_alw("%s").amount > 0 or False' % (
            values['code'], values['code'])
        amount_exp = 'result = contract.get_alw("%s").amount' % values['code']
        structure_id = self.env.ref('gs_hr_payroll_eg.hr_salary_structure_eg')
        print('inside create _name = "hr.alw"')
        print(condition_exp)
        print(structure_id)
        if not structure_id:
            structure_id = self.env['hr.salary.structure'].search([],limit=1)
        vals = {
            'name': values['name'],
            'category_id': cat_id.id,
            'struct_id':structure_id.id,
            'code': values['code'],
            'condition_select': 'python',
            'condition_python': condition_exp,
            'amount_select': 'code',
            'amount_python_compute': amount_exp,
            'sequence': 35
        }
        rule_obj.create(vals)
        return res

    def unlink(self):
        for rule in self.env['hr.salary.rule'].search(
                [('code', '=', self.code)]):
            rule.unlink()
        return super(HrAlow, self).unlink()
