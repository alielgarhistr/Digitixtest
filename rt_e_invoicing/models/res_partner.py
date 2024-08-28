# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        res = currency_rates.get(to_currency.id) / currency_rates.get(from_currency.id)
        print('round res ========= ', round(res, 5))
        return round(res, 5)


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    receiver_type = fields.Selection([('B', 'Business in Egypt'), ('F', 'Foreigner'), ('P', 'Natural person')],
                                     string='Receiver Type', default='B')
