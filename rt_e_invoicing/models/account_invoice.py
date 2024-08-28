# -*- coding: utf-8 -*-

import requests
import json
import time
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    '''
        Notes:
        'out_invoice'        # Customer Invoice
        'in_invoice'         # Vendor Bill
        'out_refund'         # Customer Credit Note
        'in_refund'          # Vendor Credit Note
    '''
    is_signed = fields.Boolean('Is Signed', copy=False)
    signed_doc = fields.Text('Signed Document', copy=False)
    eta_sign = fields.Boolean(copy=False)
    eta_id = fields.Char('Document ID', copy=False)
    eta_submission = fields.Char('Document Submission', copy=False)
    eta_error_field = fields.Text(string='Summary', copy=False)
    eta_status = fields.Selection(
        [('draft', 'Draft'), ('submitted', 'Submitted'), ('valid', 'Valid'), ('invalid', 'Invalid'),
         ('error', 'Error')],
        default='draft', copy=False, tracking=True)
    branch_id = fields.Integer(string='Branch ID', default=0, required=True)
    eta_reference = fields.Char(string='Eta Reference', copy=False)
    po_reference = fields.Char(string='PO Reference', copy=False)
    gtn_reference = fields.Char(string='GTN', copy=False)

    # def update_price_unit(self):
    #
    #     for line in self.invoice_line_ids:
    #         price = 0.0
    #         if line.price_include_tax:
    #
    #             # line.onchange_price_or_tax()
    #             for tax in line.tax_ids:
    #                 if tax.parent_code == 'T1' and tax.amount_type == 'percent':
    #                     tax_percentage = (tax.amount + 100) / 100
    #                     price = round(float(line.price_include_tax) / tax_percentage, 2)
    #         if self.line_ids:
    #             self.line_ids.with_context(check_move_validity=False)
    #         line.update({'price_unit': price})

    def _get_id_srv_base_url(self):
        id_srv_base_url = self.env['e.invoice.api'].sudo().search([('name', '=', 'id_srv_base_url')], limit=1).url
        return id_srv_base_url

    def _get_base_url(self):
        base_url = self.env['e.invoice.api'].sudo().search([('name', '=', 'base_url')], limit=1).url
        return base_url

    def _get_token(self):
        id_srv_base_url = self._get_id_srv_base_url()
        token_api = '/connect/token'
        client_id = self.env['e.invoice.config'].sudo().search([('name', '=', 'e_invoice_config')], limit=1).client_id
        client_secret = self.env['e.invoice.config'].sudo().search([('name', '=', 'e_invoice_config')],
                                                                   limit=1).client_secret

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'grant_type': 'client_credentials',
            'scope': 'InvoicingAPI',
            'client_id': client_id,
            'client_secret': client_secret
        }
        resp = requests.post(id_srv_base_url + token_api, headers=headers, data=payload, verify=False)
        resp_json = resp.json()

        return resp_json['access_token']

    def sent_invoice_eta(self):
        self.write({'eta_sign': True})
        self.env.cr.commit()

        if self.is_signed != True or self.eta_sign != True:
            raise UserError("Your invoice has not been signed yet")

        # this condition if inovice send from put request
        if self.signed_doc:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def _sent_invoice_eta(self, doc):
        base_url = self._get_base_url()
        doc_api = '/api/v1.0/documentsubmissions'
        token = self._get_token()

        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }

        resp = requests.post(base_url + doc_api, headers=headers, data=doc.encode('utf-8'), verify=False)

        return resp

    def _get_invoice_info(self, uuid):
        base_url = self._get_base_url()
        doc_api = '/api/v1.0/documents/{0}/raw'.format(uuid)
        token = self._get_token()

        headers = {
            'Authorization': 'Bearer ' + token,
        }
        time.sleep(7)
        resp = requests.get(base_url + doc_api, headers=headers, verify=False)

        return resp

    def _get_invoice_pdf(self, uuid):
        base_url = self._get_base_url()
        doc_api = '/api/v1.0/documents/{0}/pdf'.format(uuid)
        token = self._get_token()

        headers = {
            'Authorization': 'Bearer ' + token,
        }
        time.sleep(15)
        resp = requests.get(base_url + doc_api, headers=headers, verify=False)

        return resp

    def get_inovice_info_schedule(self):
        # get submitted inovices
        invoices_submitted = self.search([('eta_status', 'in', ('submitted', 'error'))])
        if invoices_submitted:
            for invoice in invoices_submitted:
                if invoice.eta_id:
                    # get invoice status
                    resp_doc = invoice._get_invoice_info(invoice.eta_id)
                    resp_doc_json = resp_doc.json()

                    # check if invoice is valid
                    if resp_doc_json['status'] == 'Valid':
                        invoice.write({
                            'eta_status': 'valid',
                        }
                        )
                        invoice.env.cr.commit()

                        # get invoice pdf
                        resp_doc_pdf = invoice._get_invoice_pdf(invoice.eta_id)
                        attachment = self.env['ir.attachment'].sudo().create({
                            'name': invoice.eta_id + '.pdf',
                            'type': 'binary',
                            'datas': base64.encodebytes(resp_doc_pdf.content),
                            'res_model': 'account.move',
                            'res_id': invoice.id,
                            'mimetype': 'application/x-pdf',
                            # 'datas_fname':invoice.eta_id+'.pdf',
                        })
                        invoice.message_post(attachment_ids=[attachment.id])
                        invoice.env.cr.commit()
                    # check if invoice is not valid
                    elif resp_doc_json['status'] == 'Invalid':
                        validation_res = resp_doc_json['validationResults']
                        summary = []
                        for validation in validation_res['validationSteps']:
                            if validation['error'] != None:
                                summary.append(validation['error']['error'])
                                print("validation['error']", validation_res['validationSteps'])

                        invoice.write({
                            'eta_status': 'invalid',
                            'eta_error_field': summary,
                        }
                        )

                        invoice.message_post(body='<b>ETA Error: </b>' + json.dumps(validation_res['validationSteps']))
                        invoice.env.cr.commit()
                    # check if invoice still in process
                    elif resp_doc_json['status'] == 'Submitted' or resp_doc_json['status'] == 'submitted':
                        invoice.message_post(body='This invoice is still being processed by ETA.')
                        invoice.env.cr.commit()

    # inherited function
    def _reverse_moves(self, default_values_list=None, cancel=False):
        ''' Reverse a recordset of account.move.
        If cancel parameter is true, the reconcilable or liquidity lines
        of each original move will be reconciled with its reverse's.
        :param default_values_list: A list of default values to consider per move.
                                    ('type' & 'reversed_entry_id' are computed in the method).
        :return:                    An account.move recordset, reverse of the current self.
        '''
        if not default_values_list:
            default_values_list = [{} for move in self]

        if cancel:
            lines = self.mapped('line_ids')
            # Avoid maximum recursion depth.
            if lines:
                lines.remove_move_reconcile()

        reverse_type_map = {
            'entry': 'entry',
            'out_invoice': 'out_refund',
            'out_refund': 'entry',
            'in_invoice': 'in_refund',
            'in_refund': 'entry',
            'out_receipt': 'entry',
            'in_receipt': 'entry',
        }

        move_vals_list = []
        for move, default_values in zip(self, default_values_list):
            default_values.update({
                'move_type': reverse_type_map[move.move_type],
                'reversed_entry_id': move.id,
            })

            # By: Rightechs 'get eta reference'
            if move.eta_id:
                default_values.update({
                    'eta_reference': move.eta_id,
                })

            move_vals_list.append(
                move.with_context(move_reverse_cancel=cancel)._reverse_move_vals(default_values, cancel=cancel))

        reverse_moves = self.env['account.move'].create(move_vals_list)
        for move, reverse_move in zip(self, reverse_moves.with_context(check_move_validity=False)):
            # Update amount_currency if the date has changed.
            if move.date != reverse_move.date:
                for line in reverse_move.line_ids:
                    if line.currency_id:
                        line._onchange_currency()
            reverse_move._recompute_dynamic_lines(recompute_all_taxes=False)
        reverse_moves._check_balanced()

        # Reconcile moves together to cancel the previous one.
        if cancel:
            reverse_moves.with_context(move_reverse_cancel=cancel)._post(soft=False)
            for move, reverse_move in zip(self, reverse_moves):
                lines = move.line_ids.filtered(
                    lambda x: (x.account_id.reconcile or x.account_id.internal_type == 'liquidity')
                              and not x.reconciled
                )
                for line in lines:
                    counterpart_lines = reverse_move.line_ids.filtered(
                        lambda x: x.account_id == line.account_id
                                  and x.currency_id == line.currency_id
                                  and not x.reconciled
                    )
                    (line + counterpart_lines).with_context(move_reverse_cancel=cancel).reconcile()

        return reverse_moves


class AccountInvoiceLineInherit(models.Model):
    _inherit = 'account.move.line'

    value_difference = fields.Float(string="Value Difference", default=0.0)
    # price_include_tax = fields.Float('Price Including Tax')
    price_include_tax = fields.Float(string='Unit Price(Include Tax)')

    # @api.constrains('price_unit')
    # def check_price(self):
    #     for line in self:
    #         if line.move_id.move_type in ['out_invoice', 'out_refund']:
    #             if line.price_unit == 0:
    #                 raise UserError(_('Price Unit must be greater than Zero!'))

    @api.onchange('price_include_tax', 'tax_ids')
    def onchange_price_or_tax(self):
        for line in self:
            if line.price_include_tax and line.tax_ids:
                print('xxxx1')
                if line.credit > 0.0:
                    price = 0.0
                    t1_tax = []
                    for tax in line.tax_ids:
                        if tax.amount_type == 'percent' and tax.parent_code == 'T1':
                            t1_tax.append(tax.id)
                        if len(t1_tax) >= 1:
                            print('xxxx2')
                            tax_percentage = (tax.amount + 100) / 100
                            price = round(float(line.price_include_tax) / tax_percentage, 2)
                        else:
                            print('xxxx3')
                            price = line.price_include_tax
                    line.price_unit = price
