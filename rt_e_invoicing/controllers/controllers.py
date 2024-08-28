# -*- coding: utf-8 -*-
import datetime
import pytz
import json
import base64

from odoo.http import request, Controller, route

from . import common
import logging

_logger = logging.getLogger(__name__)


class EInvoicing(Controller):
    @route('/odoo/api/v1/invoices', type='http', auth='public', csrf=False, methods=['GET'])
    def get_invoices(self, **kw):
        response = common.authenticate(**kw)
        if response['success'] == False:
            return common.json_response(response)

        response['success'] = True
        response['invoices'] = self.unsigned_invoices()

        return common.json_response(response, 200)

    @route('/odoo/api/v1/invoices', type='http', auth='public', csrf=False, methods=['PUT'])
    def update_invoice(self, **kw):
        response = common.authenticate(**kw)
        if not response['success']:
            return common.json_response(response)

        if 'invoice_number' in kw:
            if kw['invoice_number'] != '':
                invoice_obj = request.env['account.move'].sudo().search([('name', '=', kw['invoice_number']),
                                                                         ('eta_sign', '=', True)])
                if 'signed_doc' in kw:
                    if kw['signed_doc'] != '':
                        if invoice_obj.eta_sign and (invoice_obj.eta_status not in ('valid', 'submitted')):
                            # send to eta
                            resp = invoice_obj._sent_invoice_eta(kw['signed_doc'])
                            if resp.status_code in (202, 200):
                                _logger.info('json_resp:', resp.text)
                                json_resp = resp.json()
                                # check if submissionId not null
                                if json_resp['submissionId'] is not None:
                                    invoice_obj.write({
                                        'eta_status': 'submitted',
                                        'eta_id': json_resp['acceptedDocuments'][0]['uuid'],
                                        'eta_submission': json_resp['submissionId'],
                                        'eta_error_field': None,
                                    }
                                    )
                                else:
                                    invoice_obj.message_post(body='<b>ETA Error: </b>' + resp.text)
                                    if json_resp and 'acceptedDocuments' in json_resp \
                                            and json_resp['acceptedDocuments']:
                                        invoice_obj.write({
                                            'eta_id': json_resp['acceptedDocuments'][0]['uuid'],
                                            'eta_submission': json_resp['submissionId'],
                                        })

                                    # return error if invoice did not take submission Id
                                    invoice_obj.write({
                                        'eta_status': 'error',
                                        'signed_doc': kw['signed_doc'],
                                        'is_signed': True,
                                    })

                            else:
                                json_resp = resp.json()
                                invoice_obj.message_post(body='<b>ETA Error: </b>' + resp.text)
                                # Check if acceptedDocument UID in Response
                                if json_resp and 'acceptedDocuments' in json_resp and json_resp['acceptedDocuments']:
                                    invoice_obj.write({
                                        'eta_id': json_resp['acceptedDocuments'][0]['uuid'],
                                        'eta_submission': json_resp['submissionId'],
                                    })
                                # return error if invoice did not take submission Id
                                invoice_obj.write({
                                    'eta_status': 'error',
                                    'signed_doc': kw['signed_doc'],
                                    'is_signed': True,
                                })

                        invoice_obj.write({'signed_doc': kw['signed_doc'], 'is_signed': True})
                        response['success'] = True
                    else:
                        response['success'] = False
                        response['message'] = 'Signed doc should not be empty.'
                        return common.json_response(response, 403)

            else:
                response['success'] = False
                response['message'] = 'Invoice should not be empty.'
                return common.json_response(response, 403)
        else:
            response['success'] = False
            response['message'] = '`invoice_number` key must be added.'
            return common.json_response(response, 403)

        return common.json_response(response, 200)

    def unsigned_invoices(self):
        invoices = []
        invoice_obj = request.env['account.move'].sudo()
        invoices_unsigned = invoice_obj.search(
            [('state', '=', 'posted'), ('eta_sign', '=', True), ('eta_status', 'not in', ('submitted', 'valid'))])
        # company_obj = request.env.user.company_id
        for invoice_unsigned in invoices_unsigned:
            _logger.info('invoice_unsigned.date ============== %s - INV Number %s ' % (
            invoice_unsigned.invoice_date, invoice_unsigned.name))
            if invoice_unsigned.move_type == 'out_invoice' or invoice_unsigned.move_type == 'in_invoice':
                invoice_type = 'I'
            elif invoice_unsigned.move_type == 'out_refund' or invoice_unsigned.move_type == 'in_refund':
                invoice_type = 'C'
                invoice_ref = invoice_unsigned.eta_reference

            invoice = {
                "issuer": {
                    "address": {
                        "branchID": str(invoice_unsigned.branch_id),
                        "country": invoice_unsigned.company_id.country_id.code,
                        "governate": invoice_unsigned.company_id.state_id.name,
                        "regionCity": invoice_unsigned.company_id.city,
                        "street": invoice_unsigned.company_id.street,
                        "buildingNumber": invoice_unsigned.company_id.street2
                    },
                    "type": invoice_unsigned.company_id.issuer_type,
                    "id": invoice_unsigned.company_id.vat,
                    "name": invoice_unsigned.company_id.name
                },
                "receiver": {
                    "address": {
                        "country": invoice_unsigned.partner_id.country_id.code,
                        "governate": invoice_unsigned.partner_id.state_id.name,
                        "regionCity": invoice_unsigned.partner_id.city,
                        "street": invoice_unsigned.partner_id.street,
                        "buildingNumber": invoice_unsigned.partner_id.street2
                    },
                    "type": invoice_unsigned.partner_id.receiver_type,
                    "id": invoice_unsigned.partner_id.vat or '',
                    "name": invoice_unsigned.partner_id.name
                },
                "documentType": invoice_type,
                "documentTypeVersion": "1.0",
                "dateTimeIssued": self.convert_date_to_datetime(invoice_unsigned.invoice_date),
                "taxpayerActivityCode": invoice_unsigned.company_id.activity_code,
                "internalID": invoice_unsigned.name,
                "purchaseOrderReference": invoice_unsigned.po_reference or "",
                "salesOrderReference": invoice_unsigned.invoice_origin or "",
            }

            # check if invoice is credit note
            if invoice_type == 'C':
                if invoice_ref:
                    invoice['references'] = [invoice_ref]
                else:
                    invoice['references'] = []

            # inovice lines
            invoice_lines = []
            for invoice_line in invoice_unsigned.invoice_line_ids:
                if invoice_line.exclude_from_invoice_tab == False and invoice_line.product_id:
                    inv_line = {
                        'description': invoice_line.name,
                        'itemType': invoice_line.product_id.eta_code_type,
                        'itemCode': invoice_line.product_id.gpc_code,
                        'unitType': invoice_line.product_uom_id.uom_code or 'EA',
                        'quantity': invoice_line.quantity,
                    }

                    if invoice_line.currency_id.name == 'EGP':
                        # unit value
                        amount_sold = round(0.0, 5)
                        currency_exchange_rate = round(0.0, 5)
                        amountEGP = round(invoice_line.price_unit, 5)
                        total = round(invoice_line.price_total, 5)

                    else:
                        # unit value                   
                        eg_currency = invoice_unsigned.company_id.currency_id
                        currency_id = invoice_line.currency_id.with_context(date=invoice_unsigned.invoice_date)
                        rate = invoice_line.currency_id._get_conversion_rate(invoice_line.currency_id, eg_currency,
                                                                             invoice_unsigned.company_id,
                                                                             date=invoice_unsigned.invoice_date)
                        _logger.info('raaaaaaaaaaaate ==== ', rate)
                        # rate =  invoice_line.price_subtotal_signed / invoice_line.price_subtotal
                        amount_sold = round(invoice_line.price_unit, 5)
                        price_unit_signed = currency_id._convert(invoice_line.price_unit, eg_currency,
                                                                 invoice_unsigned.company_id,
                                                                 invoice_unsigned.invoice_date, round=True)
                        price_total_signed = currency_id._convert(invoice_line.price_total, eg_currency,
                                                                  invoice_unsigned.company_id,
                                                                  invoice_unsigned.invoice_date, round=True)

                        _logger.info('invoice_line.price_unit =========== ', invoice_line.price_unit)
                        _logger.info('price_unit_signed =========== ', round(price_unit_signed,5))

                        _logger.info('invoice_line.price_total =========== ', invoice_line.price_total)
                        _logger.info('price_total_signed =========== ', round(price_total_signed, 5))

                        currency_exchange_rate = round(rate, 5)
                        amountEGP = round(price_unit_signed, 5)
                        total = round(price_total_signed, 5)
                        _logger.info('total =============== ', total)

                    inv_line['unitValue'] = {
                        'currencySold': invoice_line.currency_id.name,
                        'amountEGP': abs(amountEGP),
                        'amountSold': abs(amount_sold),
                        'currencyExchangeRate': abs(currency_exchange_rate),
                    }
                    inv_line['salesTotal'] = round(abs(invoice_line.quantity * amountEGP), 5)
                    inv_line['valueDifference'] = invoice_line.value_difference  # ???
                    inv_line['totalTaxableFees'] = 0.0  # ???
                    inv_line['discount'] = {
                        'rate': invoice_line.discount,
                        'amount': inv_line['salesTotal'] * (invoice_line.discount / 100)
                    }
                    inv_line['netTotal'] = abs(invoice_line.balance)
                    inv_line['itemsDiscount'] = 0.0  # ???

                    taxable_items = []
                    for tax_id in invoice_line.tax_ids:
                        # check if currency EGP
                        if invoice_line.currency_id.name == 'EGP':
                            tax_rate = tax_id.amount
                            tax_amount = round(
                                abs((inv_line['netTotal'] - inv_line['itemsDiscount']) * (tax_id.amount / 100)), 5)
                        else:
                            tax_rate = tax_id.amount
                            tax_amount = round(
                                abs((inv_line['netTotal'] - inv_line['itemsDiscount']) * (tax_rate / 100)), 5)
                            _logger.info("abs((inv_line['netTotal'] === ", abs((inv_line['netTotal'])))
                            _logger.info('tax_rate ============== ', tax_rate, tax_amount)

                        if tax_id.parent_code:
                            taxable_item = {
                                "taxType": tax_id.parent_code,
                                "subType": tax_id.code,
                                "rate": abs(tax_rate),
                                "amount": tax_amount
                            }
                        else:
                            taxable_item = {
                                "taxType": tax_id.code,
                                # "subType": "N/A",
                                "rate": abs(tax_rate),
                                "amount": tax_amount
                            }
                        taxable_items.append(taxable_item)
                    inv_line['taxableItems'] = taxable_items

                    inv_line['total'] = abs(total)

                    invoice_lines.append(inv_line)
            invoice['invoiceLines'] = invoice_lines

            total_sales_amount = 0.0
            total_discount = 0.0
            total_net_mount = 0.0
            total_items_discount_amount = 0.0
            total_amount = 0.0
            for invoice_line in invoice_lines:
                total_sales_amount += invoice_line['salesTotal']
                total_discount += invoice_line['discount']['amount']
                total_net_mount += invoice_line['netTotal']
                total_items_discount_amount += invoice_line['itemsDiscount']
                total_amount += invoice_line['total']
            invoice['totalSalesAmount'] = round(total_sales_amount, 5)
            invoice['totalDiscountAmount'] = total_discount
            invoice['netAmount'] = round(abs(total_net_mount), 5)
            # get total tax
            tax_totals = []
            move_lines = request.env['account.move.line'].sudo().search([('move_id', '=', invoice_unsigned.id)])
            for move_line in move_lines:
                if move_line.tax_line_id:
                    # _logger.info('move_line.tax_line_id',move_line.tax_line_id)
                    tax_obj = request.env['account.tax'].sudo().search([('id', '=', move_line.tax_line_id.id)], limit=1)
                    # check if currency EGP
                    if invoice_unsigned.currency_id.name == 'EGP':
                        tax_total_amount = round(move_line.price_total, 5)
                    else:
                        tax_total_amount = round(move_line.price_total * currency_exchange_rate, 5)

                    if tax_obj.parent_code:
                        tax_total = {
                            "taxType": tax_obj.parent_code,
                            "amount": abs(tax_total_amount)
                        }
                    else:
                        tax_total = {
                            "taxType": tax_obj.code,
                            "amount": abs(tax_total_amount)
                        }
                    tax_totals.append(tax_total)
            invoice['taxTotals'] = tax_totals
            # collect_taxes = self.collect_taxes(tax_totals)
            # invoice['taxTotals']  = collect_taxes

            invoice['extraDiscountAmount'] = 0.0  # ???
            invoice['totalItemsDiscountAmount'] = total_items_discount_amount
            invoice['totalAmount'] = round(abs(total_amount), 5)

            invoices.append(invoice)

        return invoices

    def convert_date_to_datetime(self, date):
        datetime_invoice = date.strftime("%Y-%m-%dT%H:%M:%SZ")
        return datetime_invoice

    def collect_taxes(self, tax_totals):
        taxs_temp = []
        for tax in tax_totals:
            if len(taxs_temp) == 0:
                taxs_temp.append(tax)
            else:
                for tax_temp in taxs_temp:
                    if tax_temp['taxType'] == tax['taxType']:
                        new_tax_value = {
                            'taxType': tax['taxType'],
                            'amount': tax_temp['amount'] + tax['amount'],
                        }
                        taxs_temp.remove(tax_temp)
                        taxs_temp.append(new_tax_value)
                    else:
                        taxs_temp.append(tax)

        return taxs_temp
