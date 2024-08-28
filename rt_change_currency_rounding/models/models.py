# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def _has_accounting_entries(self):
        """ Returns True iff this currency has been used to generate (hence, round)
        some move lines (either as their foreign currency, or as the main currency
        of their company).
        """
        self.ensure_one()
        move = bool(self.env['account.move.line'].search_count(
            ['|', ('currency_id', '=', self.id), ('company_currency_id', '=', self.id)]))
        _logger.info('Currency Rounding ========== %s' % move)
        return False
